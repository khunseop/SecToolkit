from fastapi import FastAPI, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from app.services.transformer import TransformerService
from app.services.analyzer import AnalyzerService
import json
import os

app = FastAPI(title="SecToolkit")

# API Models
class DecodeRequest(BaseModel):
    data: str
    type: str

class ByteCountRequest(BaseModel):
    text: str
    encoding: str

class ConvertRequest(BaseModel):
    value: float
    from_unit: str

class JsonRequest(BaseModel):
    data: str

# 정적 파일 설정 (Bootstrap 등 로컬 에셋 서빙용)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 템플릿 설정
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/decode")
async def decode_api(request: DecodeRequest):
    result = TransformerService.decode_data(request.data, request.type)
    return {"decoded": result}

@app.post("/api/count-bytes")
async def count_bytes_api(request: ByteCountRequest):
    result = TransformerService.count_bytes(request.text, request.encoding)
    return {"bytes": result}

@app.post("/api/convert")
async def convert_api(request: ConvertRequest):
    result = AnalyzerService.convert_network_unit(request.value, request.from_unit)
    return result

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
