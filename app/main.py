from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from app.services.transformer import TransformerService
import os

app = FastAPI(title="SecToolkit")

# API Models
class DecodeRequest(BaseModel):
    data: str
    type: str

class ByteCountRequest(BaseModel):
    text: str
    encoding: str

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
