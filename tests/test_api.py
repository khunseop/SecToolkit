from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_decode_url():
    response = client.post("/api/decode", json={"data": "hello%20world", "type": "url"})
    assert response.status_code == 200
    assert response.json() == {"decoded": "hello world"}

def test_decode_base64():
    response = client.post("/api/decode", json={"data": "aGVsbG8=", "type": "base64"})
    assert response.status_code == 200
    assert response.json() == {"decoded": "hello"}

def test_count_bytes():
    response = client.post("/api/count-bytes", json={"text": "안녕", "encoding": "utf-8"})
    assert response.status_code == 200
    assert response.json() == {"bytes": 6}

def test_convert_network_unit():
    # Mbps to MB/s
    response = client.post("/api/convert", json={"value": 100, "from_unit": "mbps"})
    assert response.status_code == 200
    assert response.json() == {"mbps": 100, "mbs": 12.5}

    # MB/s to Mbps
    response = client.post("/api/convert", json={"value": 10, "from_unit": "mbs"})
    assert response.status_code == 200
    assert response.json() == {"mbps": 80, "mbs": 10}

def test_beautify_json():
    response = client.post("/api/beautify-json", json={"data": '{"a":1,"b":2}'})
    assert response.status_code == 200
    assert "formatted" in response.json()
    assert '"a": 1' in response.json()["formatted"]

def test_extract_har():
    har_content = {
        "log": {
            "entries": [
                {
                    "request": {
                        "method": "GET",
                        "url": "https://example.com",
                        "headers": [
                            {"name": "Authorization", "value": "Bearer token123"}
                        ]
                    }
                }
            ]
        }
    }
    import json
    from io import BytesIO
    file_content = json.dumps(har_content).encode('utf-8')
    response = client.post("/api/extract-har", files={"file": ("test.har", BytesIO(file_content), "application/json")})
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["headers"]["Authorization"] == "Bearer token123"
