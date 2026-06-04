"""Health & Config 路由"""
import os
import shutil

from fastapi import APIRouter, UploadFile, File
from engine.data_loader import load_file, get_data_info
from engine.config import load_config, save_config, LLMConfig
from engine.llm_agent import LLMAdapter
from backend.models.schemas import LLMConfigSchema

router = APIRouter(tags=["config"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/config")
async def get_config():
    return load_config().to_dict()


@router.post("/config")
async def update_config(config: LLMConfigSchema):
    app_config = load_config()
    app_config.llm = LLMConfig(**config.model_dump())
    save_config(app_config)
    return {"status": "ok"}


@router.post("/config/test")
async def test_connection(config: LLMConfigSchema):
    adapter = LLMAdapter(LLMConfig(**config.model_dump()))
    ok, msg = adapter.test_connection()
    return {"success": ok, "message": msg}


@router.post("/data/upload")
async def upload_data(file: UploadFile = File(...)):
    tmp_path = f"temp_{file.filename}"
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        df = load_file(tmp_path)
        info = get_data_info(df)
        return {"columns": info["columns"], "dtypes": info["dtypes"],
                "shape": list(info["shape"]), "preview": df.head(10).to_dict(orient="records")}
    finally:
        os.unlink(tmp_path)
