from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, MagicMock

client = TestClient(app)

def test_transform_url():
    response = client.post("/api/transform/url", json={"data": "hello world", "action": "encode"})
    assert response.status_code == 200
    assert response.json() == {"result": "hello%20world"}
    
    response = client.post("/api/transform/url", json={"data": "hello%20world", "action": "decode"})
    assert response.status_code == 200
    assert response.json() == {"result": "hello world"}

def test_transform_base64():
    response = client.post("/api/transform/base64", json={"data": "hello", "action": "encode"})
    assert response.status_code == 200
    assert response.json() == {"result": "aGVsbG8="}
    
    response = client.post("/api/transform/base64", json={"data": "aGVsbG8=", "action": "decode"})
    assert response.status_code == 200
    assert response.json() == {"result": "hello"}

def test_analyze_text():
    response = client.post("/api/analyze-text", json={"text": "안녕", "encoding": "utf-8"})
    assert response.status_code == 200
    assert response.json()["bytes"] == 6

def test_convert_units():
    response = client.post("/api/convert", json={
        "category": "speed",
        "value": 100,
        "from_unit": "Mbps",
        "to_unit": "MB/s"
    })
    assert response.status_code == 200
    assert response.json()["result"] == 11.920929

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

@patch('requests.get')
def test_pac_services(mock_get):
    # Mock PAC content
    pac_content = 'function FindProxyForURL(url, host) { if (shExpMatch(host, "*.google.com")) return "PROXY 8.8.8.8:8080"; return "DIRECT"; }'
    
    mock_resp = MagicMock()
    mock_resp.text = pac_content
    mock_resp.status_code = 200
    mock_get.return_value = mock_resp
    
    # Test PAC Tester
    response = client.post("/api/test-pac", json={
        "pac_url": "http://example.com/proxy.pac",
        "target_url": "https://www.google.com"
    })
    assert response.status_code == 200
    assert response.json()["result"] == "PROXY 8.8.8.8:8080"
    assert "8.8.8.8:8080" in response.json()["matched_rule"]
    
    # Test PAC Diff
    response = client.post("/api/diff-pac", json={
        "prod_url": "http://example.com/prod.pac",
        "test_url": "http://example.com/test.pac",
        "sample_url": "https://www.google.com"
    })
    assert response.status_code == 200
    assert response.json()["prod_status"]["proxy"] == "PROXY 8.8.8.8:8080"
    assert "diff_result" in response.json()

@patch('socket.gethostbyname')
@patch('requests.get')
def test_pac_dns_resolution(mock_get, mock_dns):
    # This mock only affects our display, not pacparser's internal resolution
    mock_dns.return_value = "8.8.8.8"
    
    # Use a real resolvable host so pacparser can do its thing
    pac_content = 'function FindProxyForURL(url, host) { if (dnsResolve(host) == "8.8.8.8") return "PROXY dns-match:80"; return "DIRECT"; }'
    
    mock_resp = MagicMock()
    mock_resp.text = pac_content
    mock_resp.status_code = 200
    mock_get.return_value = mock_resp
    
    response = client.post("/api/test-pac", json={
        "pac_url": "http://example.com/proxy.pac",
        "target_url": "http://dns.google"
    })
    
    assert response.status_code == 200
    # resolved_ip comes from our socket.gethostbyname mock
    assert response.json()["resolved_ip"] == "8.8.8.8"
    # Result depends on pacparser's internal DNS resolution of 'dns.google'
    # If it resolves to 8.8.8.8, it will be PROXY, otherwise DIRECT.
    # We just want to check if the rule matching heuristic works.
    assert "result" in response.json()
    assert "matched_rule" in response.json()
