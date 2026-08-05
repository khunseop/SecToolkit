from fastapi.testclient import TestClient
from app.main import app
from app.services.paloalto_excel import rows_from_sheet_values, build_template_bytes, apply_defaults, COLUMN_FIELD_MAP

client = TestClient(app)

def generate_one(row):
    response = client.post("/api/paloalto/generate-bulk", json={"rows": [row]})
    assert response.status_code == 200
    return response.json()["results"][0]

def generate_one_service(row):
    response = client.post("/api/paloalto/generate-service-bulk", json={"rows": [row]})
    assert response.status_code == 200
    return response.json()["results"][0]

def test_service_object_basic():
    result = generate_one_service({"name": "TCP-443", "protocol": "tcp", "port": "443"})
    assert result["error"] is None
    assert result["command"] == "set service TCP-443 protocol tcp port 443"

def test_service_object_with_vsys():
    result = generate_one_service({"name": "TCP-443", "protocol": "tcp", "port": "443", "vsys": "vsys1"})
    assert result["command"] == "set vsys vsys1 service TCP-443 protocol tcp port 443"

def test_service_object_requires_name():
    result = generate_one_service({"name": "", "protocol": "tcp", "port": "443"})
    assert result["error"] is not None

def test_service_object_invalid_protocol():
    result = generate_one_service({"name": "X", "protocol": "icmp", "port": "443"})
    assert result["error"] is not None

def test_set_basic():
    result = generate_one({"action": "set", "rule_name": "RULE1"})
    assert result["error"] is None
    assert result["command"] == 'set rulebase security rules "RULE1" disabled no action allow'

def test_set_returns_object_counts_per_field():
    result = generate_one({
        "action": "set",
        "rule_name": "RULE1",
        "source": "10.0.0.1,10.0.0.2,10.0.0.3",
        "destination": "any",
        "service": "TCP_80,TCP_443",
    })
    assert result["counts"] == {"source": 3, "destination": 1, "service": 2}

def test_set_counts_omits_empty_fields():
    result = generate_one({"action": "set", "rule_name": "RULE1"})
    assert result["counts"] == {}

def test_delete_and_move_have_no_counts():
    result = generate_one({"action": "delete", "rule_name": "RULE1"})
    assert result.get("counts") is None
    result = generate_one({"action": "move", "rule_name": "RULE1", "move_position": "top"})
    assert result.get("counts") is None

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

def test_rows_from_sheet_values_continuation_rows():
    # rule_name이 빈 행은 바로 위 정책의 연속 행으로 취급되어 다중값 필드가 콤마로 이어붙는다
    headers = [header for header, _ in COLUMN_FIELD_MAP]

    rule_row = ["set", "", "Web_Access", "FALSE", "allow", "", "10.10.10.0/24", "", "",
                "192.168.1.100", "TCP_80", "", "웹 서버 접근 허용", "", "", "", ""]
    continuation_source = ["", "", "", "", "", "", "10.10.20.0/24", "", "", "", "", "", "", "", "", "", ""]
    continuation_service = ["", "", "", "", "", "", "", "", "", "", "TCP_8080", "", "", "", "", "", ""]

    rows = rows_from_sheet_values([headers, rule_row, continuation_source, continuation_service])
    assert len(rows) == 1
    merged = rows[0]
    assert merged["rule_name"] == "Web_Access"
    assert merged["source"] == "10.10.10.0/24,10.10.20.0/24"
    assert merged["service"] == "TCP_80,TCP_8080"
    assert merged["destination"] == "192.168.1.100"
    assert merged["description"] == "웹 서버 접근 허용"

def test_rows_from_sheet_values_leading_continuation_row_kept_as_error_row():
    # 정책 없이 시작하는 빈 rule_name 행은 병합할 대상이 없으므로 그대로 별도 행으로 남는다
    headers = [header for header, _ in COLUMN_FIELD_MAP]
    orphan_row = ["set", "", "", "", "", "", "1.1.1.1", "", "", "", "", "", "", "", "", "", ""]
    rows = rows_from_sheet_values([headers, orphan_row])
    assert len(rows) == 1
    assert rows[0]["rule_name"] == ""

def test_rows_from_sheet_values_normalizes_rule_action_case():
    headers = [header for header, _ in COLUMN_FIELD_MAP]
    data_row = ["set", "", "RULE1", "FALSE", "Allow", "", "1.1.1.1", "", "", "", "", "", "", "", "", "", ""]
    rows = rows_from_sheet_values([headers, data_row])
    assert rows[0]["rule_action"] == "allow"

def test_rows_from_sheet_values_column_order_independent():
    # 헤더 이름으로 매핑하므로 컬럼 순서를 바꿔도 결과는 동일해야 한다
    headers = ["rule_name", "source", "작업유형", "destination"]
    data_row = ["RULE1", "1.1.1.1", "set", "2.2.2.2"]
    rows = rows_from_sheet_values([headers, data_row])
    assert len(rows) == 1
    assert rows[0]["rule_name"] == "RULE1"
    assert rows[0]["source"] == "1.1.1.1"
    assert rows[0]["action"] == "set"
    assert rows[0]["destination"] == "2.2.2.2"

def test_apply_defaults_fills_missing_and_blank_fields():
    defaults = {
        "vsys": "vsys1", "disabled": False, "rule_action": "deny",
        "from_zone": "trust", "source": "any", "source_user": "any",
        "to_zone": "untrust", "destination": "any", "service": "application-default",
        "application": "any", "description": "default desc", "log_end": "yes", "log_setting": "default",
    }
    # vsys 컬럼 자체가 없고(row에 키 없음), destination은 빈 문자열
    row = {"action": "", "rule_name": "RULE1", "source": "10.0.0.1", "destination": ""}
    filled = apply_defaults([row], defaults)[0]
    assert filled["action"] == "set"
    assert filled["vsys"] == "vsys1"
    assert filled["destination"] == "any"
    assert filled["source"] == "10.0.0.1"  # 이미 값이 있으면 기본값으로 덮어쓰지 않는다
    assert filled["rule_name"] == "RULE1"

def test_rows_from_sheet_values_empty():
    assert rows_from_sheet_values([]) == []
    assert rows_from_sheet_values([["action"]]) == []
