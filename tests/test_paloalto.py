from fastapi.testclient import TestClient
from app.main import app
from app.services.paloalto_excel import rows_from_sheet_values, build_template_bytes, COLUMN_FIELD_MAP

client = TestClient(app)

def generate_one(row):
    response = client.post("/api/paloalto/generate-bulk", json={"rows": [row]})
    assert response.status_code == 200
    return response.json()["results"][0]

def test_set_basic():
    result = generate_one({"action": "set", "rule_name": "RULE1"})
    assert result["error"] is None
    assert result["command"] == 'set rulebase security rules "RULE1" disabled no action allow'

def test_set_not_disabled_emits_disabled_no():
    result = generate_one({"action": "set", "rule_name": "RULE1", "disabled": False})
    assert "disabled no" in result["command"]

def test_set_with_vsys_and_multi_values():
    result = generate_one({
        "action": "set",
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
    })
    command = result["command"]
    assert command.startswith('set vsys vsys1 rulebase security rules "RULE1"')
    assert "from [ trust dmz ]" in command
    assert "source 10.0.0.0/24" in command
    assert "application [ ssl web-browsing ]" in command
    assert 'log-setting "default"' in command
    assert "log-end yes" in command

def test_set_disabled_and_description():
    result = generate_one({
        "action": "set",
        "rule_name": "RULE1",
        "disabled": True,
        "description": "temporary block"
    })
    command = result["command"]
    assert "disabled yes" in command
    assert 'description "temporary block"' in command

def test_delete_whole_rule():
    result = generate_one({"action": "delete", "rule_name": "RULE1", "vsys": "vsys2"})
    assert result["command"] == 'delete vsys vsys2 rulebase security rules "RULE1"'

def test_delete_single_field_object():
    result = generate_one({"action": "delete", "rule_name": "RULE1", "source": "1.1.1.1"})
    assert result["command"] == 'delete rulebase security rules "RULE1" source "1.1.1.1"'

def test_delete_rejects_multiple_fields():
    result = generate_one({"action": "delete", "rule_name": "RULE1", "source": "1.1.1.1", "destination": "2.2.2.2"})
    assert result["error"] is not None

def test_delete_rejects_multiple_values_in_one_field():
    result = generate_one({"action": "delete", "rule_name": "RULE1", "source": "1.1.1.1,2.2.2.2"})
    assert result["error"] is not None

def test_move_top():
    result = generate_one({"action": "move", "rule_name": "RULE1", "move_position": "top"})
    assert result["command"] == 'move rulebase security rules "RULE1" top'

def test_move_before_requires_anchor():
    result = generate_one({"action": "move", "rule_name": "RULE1", "move_position": "before"})
    assert result["error"] is not None

def test_move_before_with_anchor():
    result = generate_one({"action": "move", "rule_name": "RULE1", "move_position": "before", "anchor_rule": "RULE0"})
    assert result["command"] == 'move rulebase security rules "RULE1" before "RULE0"'

def test_missing_rule_name():
    result = generate_one({"action": "set", "rule_name": ""})
    assert result["error"] is not None

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
                {"action": "set", "rule_name": "RULE1", "source": "10.0.0.1"},
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
    data_row = ["set", "vsys1", "RULE1", "FALSE", "allow", "trust", "10.0.0.0/24",
                "any", "untrust", "any", "application-default", "ssl,web-browsing",
                "desc", "yes", "default", "", ""]
    blank_row = [None] * len(headers)
    rows = rows_from_sheet_values([headers, data_row, blank_row])
    assert len(rows) == 1
    row = rows[0]
    assert row["action"] == "set"
    assert row["rule_name"] == "RULE1"
    assert row["disabled"] is False
    assert row["rule_action"] == "allow"
    assert row["application"] == "ssl,web-browsing"

def test_rows_from_sheet_values_newline_multivalue():
    # Simulates pasting multiple rows copied from Excel into one cell
    headers = [header for header, _ in COLUMN_FIELD_MAP]
    data_row = ["set", "", "RULE1", "FALSE", "allow", "", "1.1.1.1\n2.2.2.2\n3.3.3.3",
                "", "", "", "", "", "", "", "", "", ""]
    rows = rows_from_sheet_values([headers, data_row])
    assert rows[0]["source"] == "1.1.1.1\n2.2.2.2\n3.3.3.3"

def test_rows_from_sheet_values_empty():
    assert rows_from_sheet_values([]) == []
    assert rows_from_sheet_values([["action"]]) == []
