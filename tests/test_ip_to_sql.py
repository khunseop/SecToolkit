from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_ip_to_sql_single_ip():
    response = client.post(
        "/api/transform/iptosql",
        json={"data": "192.168.0.1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "192.168.0.%" in data["patterns"]
    assert "WHERE ip_address LIKE '192.168.0.%'" in data["sql_where"]

def test_ip_to_sql_cidr():
    response = client.post(
        "/api/transform/iptosql",
        json={"data": "10.0.0.0/24"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "10.0.0.%" in data["patterns"]

def test_ip_to_sql_range():
    response = client.post(
        "/api/transform/iptosql",
        json={"data": "172.16.0.1 - 172.16.0.255"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "172.16.0.%" in data["patterns"]

def test_ip_to_sql_mixed_invalid():
    response = client.post(
        "/api/transform/iptosql",
        json={"data": "1.1.1.1\ninvalid-ip\n2.2.2.2/24"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "1.1.1.%" in data["patterns"]
    assert "2.2.2.%" in data["patterns"]
    assert len(data["patterns"]) == 2
