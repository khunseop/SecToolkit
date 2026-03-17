from fastapi import FastAPI, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
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

# Static & Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

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
async def test_pac_api(request: PacRequest):
    return PacService.test_pac(request.pac_url, request.target_url)

@app.post("/api/diff-pac")
async def diff_pac_api(request: PacDiffRequest):
    return PacService.diff_pac(request.prod_url, request.test_url, request.sample_url)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
