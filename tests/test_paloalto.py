from fastapi.testclient import TestClient
from app.main import app

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
