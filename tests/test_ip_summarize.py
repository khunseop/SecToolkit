from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_ip_summarize_adjacent_merge():
    response = client.post(
        "/api/ip-summarize",
        json={"ip_list": "10.0.0.0/25\n10.0.0.128/25"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["results"] == [{"cidr": "10.0.0.0/24", "netmask": "10.0.0.0 255.255.255.0"}]
    assert data["errors"] == []

def test_ip_summarize_non_adjacent_not_merged():
    response = client.post(
        "/api/ip-summarize",
        json={"ip_list": "10.0.0.0/25\n10.0.1.0/25"}
    )
    assert response.status_code == 200
    data = response.json()
    cidrs = [r["cidr"] for r in data["results"]]
    assert cidrs == ["10.0.0.0/25", "10.0.1.0/25"]

def test_ip_summarize_range_collapsed():
    response = client.post(
        "/api/ip-summarize",
        json={"ip_list": "192.168.1.0-192.168.1.255"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["results"] == [{"cidr": "192.168.1.0/24", "netmask": "192.168.1.0 255.255.255.0"}]

def test_ip_summarize_invalid_line_reported_as_error():
    response = client.post(
        "/api/ip-summarize",
        json={"ip_list": "10.0.0.1\nnot-an-ip"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["errors"] == ["not-an-ip"]
    assert data["results"] == [{"cidr": "10.0.0.1/32", "netmask": "10.0.0.1 255.255.255.255"}]

def test_ip_summarize_class_c_mode():
    response = client.post(
        "/api/ip-summarize",
        json={"ip_list": "10.0.0.5\n10.0.0.200", "class_c": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["results"] == [{"cidr": "10.0.0.0/24", "netmask": "10.0.0.0 255.255.255.0"}]

def test_ip_summarize_sorted_ascending():
    response = client.post(
        "/api/ip-summarize",
        json={"ip_list": "10.0.2.0/24\n10.0.0.0/24"}
    )
    assert response.status_code == 200
    data = response.json()
    cidrs = [r["cidr"] for r in data["results"]]
    assert cidrs == ["10.0.0.0/24", "10.0.2.0/24"]
