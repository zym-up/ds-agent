"""FastAPI 应用入口"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from engine import sanitize_json

# 全局修复 Starlette 的 JSONResponse.render：自动剔除 NaN/Infinity
_starlette_render = JSONResponse.render
def _safe_render(self, content):
    return json.dumps(sanitize_json(content), ensure_ascii=False, allow_nan=False).encode("utf-8")
JSONResponse.render = _safe_render

from backend.routers import config as config_router
from backend.routers import projects as projects_router
from backend.routers import analysis as analysis_router
from backend.routers import reports as reports_router

app = FastAPI(title="数据科学家 Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 挂载 API 路由 ──
app.include_router(config_router.router, prefix="/api")
app.include_router(projects_router.router, prefix="/api")
app.include_router(analysis_router.router, prefix="/api")
app.include_router(reports_router.router, prefix="/api")


# ── 静态文件（生产环境 Vue 前端） ──
def _get_content_type(file_path: str) -> str:
    ext_map = {
        ".js": "application/javascript", ".css": "text/css",
        ".html": "text/html", ".json": "application/json",
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".svg": "image/svg+xml", ".ico": "image/x-icon",
    }
    for ext, ct in ext_map.items():
        if file_path.endswith(ext):
            return ct
    return "application/octet-stream"


fastapi_app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_dist = os.path.join(fastapi_app_dir, "frontend", "dist")

if os.path.exists(frontend_dist) and os.path.exists(os.path.join(frontend_dist, "index.html")):
    @app.get("/assets/{file_path:path}")
    async def serve_assets(file_path: str):
        full_path = os.path.join(frontend_dist, "assets", file_path)
        if os.path.exists(full_path) and not os.path.isdir(full_path):
            with open(full_path, "rb") as f:
                return Response(content=f.read(), media_type=_get_content_type(full_path))
        raise HTTPException(status_code=404)

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith(("api/", "docs", "openapi.json")):
            raise HTTPException(status_code=404)
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and not os.path.isdir(file_path):
            with open(file_path, "rb") as f:
                return Response(content=f.read(), media_type=_get_content_type(file_path))
        index_path = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "rb") as f:
                return Response(content=f.read(), media_type="text/html")
        raise HTTPException(status_code=404)

    print(f"[OK] Frontend static files: {frontend_dist}")
else:
    print(f"[WARN] Frontend dist not found: {frontend_dist}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8502)
