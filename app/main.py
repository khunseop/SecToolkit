from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os

from app.api.routers import transformer, analyzer, pac

app = FastAPI(title="SecToolkit")

# Static & Templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # /app
PROJECT_ROOT = os.path.dirname(BASE_DIR)              # /root
TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "templates")

app.mount("/static", StaticFiles(directory=os.path.join(PROJECT_ROOT, "static")), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    try:
        # 최신 FastAPI/Starlette 버전에서는 request 객체를 첫 번째 인자로 반드시 전달해야 함
        return templates.TemplateResponse(
            request,
            "index.html", 
            {"request": request}
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return HTMLResponse(content=f"Jinja2 Render Error:<br><pre>{error_details}</pre>", status_code=500)

# Register Routers
app.include_router(transformer.router, prefix="/api")
app.include_router(analyzer.router, prefix="/api")
app.include_router(pac.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    # Windows stability settings
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, http="h11", loop="asyncio")
