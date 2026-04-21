from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os

from app.api.routers import transformer, analyzer, pac

app = FastAPI(title="SecToolkit")

# Static & Templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

app.mount("/static", StaticFiles(directory=os.path.join(PROJECT_ROOT, "static")), name="static")

@app.get("/", response_class=HTMLResponse)
async def index():
    with open(os.path.join(PROJECT_ROOT, "templates", "index.html"), "r", encoding="utf-8") as f:
        return f.read()

# Register Routers
app.include_router(transformer.router, prefix="/api")
app.include_router(analyzer.router, prefix="/api")
app.include_router(pac.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    # Windows stability settings
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, http="h11", loop="asyncio")
