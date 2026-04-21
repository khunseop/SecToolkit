from fastapi import APIRouter, UploadFile, File
from app.schemas.analyzer import ConvertRequest, JsonRequest, DnsLookupRequest, DnsLookupResponse
from app.services.analyzer import AnalyzerService
import json

router = APIRouter(tags=["Analyzer"])

@router.get("/units")
async def get_units():
    return {k: list(v.keys()) for k, v in AnalyzerService.CONVERSION_MAP.items()}

@router.get("/system-proxy")
async def get_system_proxy_api():
    return AnalyzerService.get_system_proxy_settings()

@router.post("/dns-lookup", response_model=DnsLookupResponse)
async def dns_lookup_api(request: DnsLookupRequest):
    return AnalyzerService.resolve_dns(request.host)

@router.post("/convert")
async def convert_api(request: ConvertRequest):
    return AnalyzerService.convert_units(
        request.category, request.value, request.from_unit, request.to_unit
    )

@router.post("/beautify-json")
async def beautify_json_api(request: JsonRequest):
    result = AnalyzerService.beautify_json(request.data)
    return result

@router.post("/extract-har")
async def extract_har_api(file: UploadFile = File(...)):
    content = await file.read()
    try:
        har_data = json.loads(content)
        result = AnalyzerService.extract_har_headers(har_data)
        return {"results": result}
    except Exception as e:
        return {"error": str(e)}
