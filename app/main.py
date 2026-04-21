from fastapi import FastAPI, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from app.services.transformer import TransformerService
from app.services.analyzer import AnalyzerService
from app.services.pac_service import PacService
import json
import os

app = FastAPI(title="SecToolkit")

# API Models
class TransformRequest(BaseModel):
    data: str
    action: str

class ByteCountRequest(BaseModel):
    text: str
    encoding: str

class ConvertRequest(BaseModel):
    category: str
    value: float
    from_unit: str
    to_unit: str

class JsonRequest(BaseModel):
    data: str

class PacRequest(BaseModel):
    pac_url: str
    target_url: str

class PacDiffRequest(BaseModel):
    prod_url: str
    test_url: str
    sample_url: str

class PacGroupsRequest(BaseModel):
    groups: list

# Static & Templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

app.mount("/static", StaticFiles(directory=os.path.join(PROJECT_ROOT, "static")), name="static")

@app.get("/", response_class=HTMLResponse)
async def index():
    with open(os.path.join(PROJECT_ROOT, "templates", "index.html"), "r", encoding="utf-8") as f:
        return f.read()

# API Endpoints
@app.get("/api/units")
async def get_units():
    return {k: list(v.keys()) for k, v in AnalyzerService.CONVERSION_MAP.items()}

@app.post("/api/transform/url")
async def transform_url_api(request: TransformRequest):
    result = TransformerService.url_transform(request.data, request.action)
    return {"result": result}

@app.post("/api/transform/base64")
async def transform_base64_api(request: TransformRequest):
    result = TransformerService.base64_transform(request.data, request.action)
    return {"result": result}

@app.post("/api/analyze-text")
async def analyze_text_api(request: ByteCountRequest):
    result = TransformerService.analyze_text(request.text, request.encoding)
    return result

@app.post("/api/convert")
async def convert_api(request: ConvertRequest):
    return AnalyzerService.convert_units(
        request.category, request.value, request.from_unit, request.to_unit
    )

@app.post("/api/beautify-json")
async def beautify_json_api(request: JsonRequest):
    result = AnalyzerService.beautify_json(request.data)
    return result

@app.post("/api/extract-har")
async def extract_har_api(file: UploadFile = File(...)):
    content = await file.read()
    try:
        har_data = json.loads(content)
        result = AnalyzerService.extract_har_headers(har_data)
        return {"results": result}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/test-pac")
async def test_pac_api(request: PacRequest, fastapi_req: Request):
    return PacService.test_pac(request.pac_url, request.target_url, fastapi_req.client.host)

@app.post("/api/diff-pac")
async def diff_pac_api(request: PacDiffRequest, fastapi_req: Request):
    return PacService.diff_pac(request.prod_url, request.test_url, request.sample_url, fastapi_req.client.host)

@app.get("/api/pac-groups")
async def get_pac_groups_api():
    return PacService.get_pac_groups()

@app.post("/api/pac-groups")
async def save_pac_groups_api(request: PacGroupsRequest):
    success = PacService.save_pac_groups(request.groups)
    return {"success": success}

if __name__ == "__main__":
    import uvicorn
    # Windows에서 httptools 관련 500 에러 및 루프 문제를 방지하기 위해 http="h11" 및 loop="asyncio" 설정
    # 또한 객체 직접 전달보다 "app.main:app" 문자열 전달이 Windows 환경에서 더 안정적임
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, http="h11", loop="asyncio")
