from fastapi import APIRouter
from app.schemas.transformer import TransformRequest, ByteCountRequest, IpToSqlRequest
from app.services.transformer import TransformerService

router = APIRouter(tags=["Transformer"])

@router.post("/transform/url")
async def transform_url_api(request: TransformRequest):
    result = TransformerService.url_transform(request.data, request.action)
    return {"result": result}

@router.post("/transform/base64")
async def transform_base64_api(request: TransformRequest):
    result = TransformerService.base64_transform(request.data, request.action)
    return {"result": result}

@router.post("/transform/iptosql")
async def transform_ip_to_sql_api(request: IpToSqlRequest):
    result = TransformerService.ip_to_sql_transform(request.data)
    return result

@router.post("/analyze-text")
async def analyze_text_api(request: ByteCountRequest):
    result = TransformerService.analyze_text(request.text, request.encoding)
    return result
