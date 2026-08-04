from fastapi.testclient import TestClient
from app.main import app
from app.services.paloalto_excel import rows_from_sheet_values, build_template_bytes, COLUMN_FIELD_MAP

client = TestClient(app)

def test_create_basic():
    response = client.post(
        "/api/paloalto/generate",
        json={"action": "create", "rule_name": "RULE1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["command"] == 'set rulebase security rules "RULE1" action allow'

def test_create_with_vsys_and_multi_values():
    response = client.post(
        "/api/paloalto/generate",
        json={
            "action": "create",
            "rule_name": "RULE1",
            "vsys": "vsys1",
            "from_zone": "trust,dmz",
            "source": "10.0.0.0/24",
            "to_zone": "untrust",
            "destination": "any",
            "application": "ssl\nweb-browsing",
            "service": "application-default",
            "log_end": "yes",
            "log_setting": "default"
        }
    )
    assert response.status_code == 200
    command = response.json()["command"]
    assert command.startswith('set vsys vsys1 rulebase security rules "RULE1"')
    assert "from [ trust dmz ]" in command
    assert "source 10.0.0.0/24" in command
    assert "application [ ssl web-browsing ]" in command
    assert 'log-setting "default"' in command
    assert "log-end yes" in command

def test_create_disabled_and_description():
    response = client.post(
        "/api/paloalto/generate",
        json={
            "action": "create",
            "rule_name": "RULE1",
            "disabled": True,
            "description": "temporary block"
        }
    )
    command = response.json()["command"]
    assert "disabled yes" in command
    assert 'description "temporary block"' in command

def test_delete():
    response = client.post(
        "/api/paloalto/generate",
        json={"action": "delete", "rule_name": "RULE1", "vsys": "vsys2"}
    )
    assert response.json()["command"] == 'delete vsys vsys2 rulebase security rules "RULE1"'

def test_move_top():
    response = client.post(
        "/api/paloalto/generate",
        json={"action": "move", "rule_name": "RULE1", "move_position": "top"}
    )
    assert response.json()["command"] == 'move rulebase security rules "RULE1" top'

def test_move_before_requires_anchor():
    response = client.post(
        "/api/paloalto/generate",
        json={"action": "move", "rule_name": "RULE1", "move_position": "before"}
    )
    assert "error" in response.json()

def test_move_before_with_anchor():
    response = client.post(
        "/api/paloalto/generate",
        json={"action": "move", "rule_name": "RULE1", "move_position": "before", "anchor_rule": "RULE0"}
    )
    assert response.json()["command"] == 'move rulebase security rules "RULE1" before "RULE0"'

def test_missing_rule_name():
    response = client.post(
        "/api/paloalto/generate",
        json={"action": "create", "rule_name": ""}
    )
    assert "error" in response.json()

def test_defaults_roundtrip():
    payload = {
        "vsys": "vsys1",
        "disabled": False,
        "rule_action": "deny",
        "from_zone": "trust",
        "source": "any",
        "source_user": "any",
        "to_zone": "untrust",
        "destination": "any",
        "service": "application-default",
        "application": "any",
        "description": "",
        "log_end": "yes",
        "log_setting": "default"
    }
    save_response = client.post("/api/paloalto/defaults", json=payload)
    assert save_response.json()["success"] is True

    get_response = client.get("/api/paloalto/defaults")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["rule_action"] == "deny"
    assert data["vsys"] == "vsys1"

def test_generate_bulk_mixed_success_and_error():
    response = client.post(
        "/api/paloalto/generate-bulk",
        json={
            "rows": [
                {"action": "create", "rule_name": "RULE1", "source": "10.0.0.1"},
                {"action": "delete", "rule_name": ""},
                {"action": "move", "rule_name": "RULE2", "move_position": "top"}
            ]
        }
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 3
    assert results[0]["error"] is None
    assert 'source 10.0.0.1' in results[0]["command"]
    assert results[1]["error"] is not None
    assert results[2]["command"] == 'move rulebase security rules "RULE2" top'

def test_template_download():
    response = client.get("/api/paloalto/template")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/vnd.openxmlformats")
    assert len(response.content) > 0

def test_template_bytes_are_valid_workbook():
    import openpyxl
    import io
    content = build_template_bytes()
    wb = openpyxl.load_workbook(io.BytesIO(content))
    ws = wb.active
    headers = [cell.value for cell in ws[1]]
    assert headers == [header for header, _ in COLUMN_FIELD_MAP]

def test_rows_from_sheet_values():
    headers = [header for header, _ in COLUMN_FIELD_MAP]
    data_row = ["create", "vsys1", "RULE1", "FALSE", "allow", "trust", "10.0.0.0/24",
                "any", "untrust", "any", "application-default", "ssl,web-browsing",
                "desc", "yes", "default", "", ""]
    blank_row = [None] * len(headers)
    rows = rows_from_sheet_values([headers, data_row, blank_row])
    assert len(rows) == 1
    row = rows[0]
    assert row["action"] == "create"
    assert row["rule_name"] == "RULE1"
    assert row["disabled"] is False
    assert row["rule_action"] == "allow"
    assert row["application"] == "ssl,web-browsing"

def test_rows_from_sheet_values_empty():
    assert rows_from_sheet_values([]) == []
    assert rows_from_sheet_values([["action"]]) == []
