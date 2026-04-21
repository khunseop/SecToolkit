from fastapi import APIRouter, Request
from app.schemas.pac import PacRequest, PacDiffRequest, PacGroupsRequest
from app.services.pac_service import PacService

router = APIRouter(tags=["PAC Tool"])

@router.post("/test-pac")
async def test_pac_api(request: PacRequest, fastapi_req: Request):
    return PacService.test_pac(request.pac_url, request.target_url, fastapi_req.client.host)

@router.post("/diff-pac")
async def diff_pac_api(request: PacDiffRequest, fastapi_req: Request):
    return PacService.diff_pac(request.prod_url, request.test_url, request.sample_url, fastapi_req.client.host)

@router.get("/pac-groups")
async def get_pac_groups_api():
    return PacService.get_pac_groups()

@router.post("/pac-groups")
async def save_pac_groups_api(request: PacGroupsRequest):
    success = PacService.save_pac_groups(request.groups)
    return {"success": success}
