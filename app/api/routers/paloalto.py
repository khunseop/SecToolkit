from fastapi import APIRouter
from app.schemas.paloalto import PolicyRuleRequest, PolicyDefaults
from app.services.paloalto import PaloAltoService

router = APIRouter(tags=["PaloAlto"])

@router.post("/paloalto/generate")
async def generate_paloalto_command_api(request: PolicyRuleRequest):
    return PaloAltoService.generate_command(request)

@router.get("/paloalto/defaults")
async def get_paloalto_defaults_api():
    return PaloAltoService.get_defaults()

@router.post("/paloalto/defaults")
async def save_paloalto_defaults_api(request: PolicyDefaults):
    success = PaloAltoService.save_defaults(request.model_dump())
    return {"success": success}
