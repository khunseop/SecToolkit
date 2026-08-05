from fastapi import APIRouter, UploadFile, File
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
import io

from app.schemas.paloalto import PolicyRuleRequest, PolicyDefaults, BulkGenerateRequest, ServiceBulkGenerateRequest
from app.services.paloalto import PaloAltoService
from app.services.paloalto_excel import build_template_bytes, parse_uploaded_excel

router = APIRouter(tags=["PaloAlto"])

@router.get("/paloalto/defaults")
async def get_paloalto_defaults_api():
    return PaloAltoService.get_defaults()

@router.post("/paloalto/defaults")
async def save_paloalto_defaults_api(request: PolicyDefaults):
    success = PaloAltoService.save_defaults(request.model_dump())
    return {"success": success}

@router.post("/paloalto/generate-bulk")
async def generate_paloalto_bulk_api(request: BulkGenerateRequest):
    return PaloAltoService.generate_bulk(request.rows)

@router.post("/paloalto/generate-service-bulk")
async def generate_paloalto_service_bulk_api(request: ServiceBulkGenerateRequest):
    return PaloAltoService.generate_service_bulk(request.rows)

@router.get("/paloalto/template")
async def download_paloalto_template_api():
    content = build_template_bytes()
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=paloalto_policy_template.xlsx"}
    )

@router.post("/paloalto/generate-bulk-excel")
async def generate_paloalto_bulk_excel_api(file: UploadFile = File(...)):
    content = await file.read()
    try:
        rows = await run_in_threadpool(parse_uploaded_excel, content)
    except Exception as e:
        return {"error": f"Failed to read Excel file: {str(e)}"}

    results = []
    for index, row in enumerate(rows):
        try:
            request = PolicyRuleRequest(**row)
        except Exception as e:
            results.append({"row_index": index, "command": None, "error": f"Invalid row data: {str(e)}"})
            continue
        outcome = PaloAltoService.generate_command(request)
        results.append({"row_index": index, "command": outcome.get("command"), "error": outcome.get("error")})

    return {"results": results}
