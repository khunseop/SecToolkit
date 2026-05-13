from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_ip_intersect_simple():
    response = client.post(
        "/api/ip-intersect",
        json={
            "list_a": "10.0.0.0/24",
            "list_b": "10.0.0.50\n192.168.1.1"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["matches"]) == 1
    assert data["matches"][0]["overlap"] == "10.0.0.50"
    assert data["matches"][0]["source_a"] == "10.0.0.0/24"
    assert data["matches"][0]["source_b"] == "10.0.0.50"

def test_ip_intersect_range():
    response = client.post(
        "/api/ip-intersect",
        json={
            "list_a": "172.16.0.0-172.16.0.255",
            "list_b": "172.16.0.100-172.16.0.200"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["matches"]) == 1
    assert data["matches"][0]["overlap"] == "172.16.0.100 - 172.16.0.200"

def test_ip_intersect_mixed():
    response = client.post(
        "/api/ip-intersect",
        json={
            "list_a": "1.1.1.0/24\n8.8.8.8",
            "list_b": "1.1.1.100-1.1.2.0\n8.8.0.0/16"
        }
    )
    assert response.status_code == 200
    data = response.json()
    # 1.1.1.0/24 intersects with 1.1.1.100-1.1.2.0 (overlap: 1.1.1.100-1.1.1.255)
    # 8.8.8.8 intersects with 8.8.0.0/16 (overlap: 8.8.8.8)
    assert len(data["matches"]) == 2
    overlaps = [m["overlap"] for m in data["matches"]]
    assert "1.1.1.100 - 1.1.1.255" in overlaps
    assert "8.8.8.8" in overlaps
