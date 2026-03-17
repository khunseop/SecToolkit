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
    assert response.json() == {"bytes": 6}  # 한글 한 글자 3바이트(UTF-8)

    response = client.post("/api/count-bytes", json={"text": "안녕", "encoding": "euc-kr"})
    assert response.status_code == 200
    assert response.json() == {"bytes": 4}  # 한글 한 글자 2바이트(EUC-KR)
