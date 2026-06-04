"""项目 CRUD + 数据管理 + 图表 路由"""
import os
import shutil

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from engine.data_loader import get_data_info
from backend.deps import pm
from backend.models.schemas import MergeDataRequest

router = APIRouter(tags=["projects"])


@router.get("/projects")
async def list_projects():
    return pm.list_projects()


@router.post("/projects")
async def create_project(name: str = Form(...), file: UploadFile = File(...)):
    tmp_path = f"temp_{file.filename}"
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        project_id = pm.create_project(name, tmp_path)
    finally:
        os.unlink(tmp_path)

    data_files = pm.list_data_files(project_id)
    df = pm.merge_selected_data(project_id, [f["name"] for f in data_files])
    info = get_data_info(df)
    return {
        "project_id": project_id,
        "data_files": data_files,
        "rows": len(df),
        "cols": len(df.columns),
        "info": info,
    }


@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    data = pm.load_project(project_id)
    meta = data["meta"]
    state = data["state"]
    chat = data["chat_history"]
    data_files = pm.list_data_files(project_id)
    info = {}
    if data["dataframe"] is not None:
        info = get_data_info(data["dataframe"])
    return {
        "meta": meta, "state": state, "chat_history": chat,
        "data_files": data_files, "data_info": info,
    }


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    pm.delete_project(project_id)
    return {"status": "ok"}


@router.get("/projects/{project_id}/info")
async def get_project_info(project_id: str):
    return pm.get_project_info(project_id)


@router.get("/projects/{project_id}/data")
async def list_data_files(project_id: str):
    return pm.list_data_files(project_id)


@router.post("/projects/{project_id}/data")
async def add_data(project_id: str, file: UploadFile = File(...)):
    tmp_path = f"temp_{file.filename}"
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        saved_path = pm.add_data(project_id, tmp_path)
        data_files = pm.list_data_files(project_id)
        return {"saved_path": saved_path, "data_files": data_files}
    finally:
        os.unlink(tmp_path)


@router.post("/projects/{project_id}/data/merge")
async def merge_data(project_id: str, req: MergeDataRequest):
    df = pm.merge_selected_data(project_id, req.selected_files)
    info = get_data_info(df)
    return {"rows": len(df), "cols": len(df.columns), "info": info}


@router.get("/projects/{project_id}/charts/{chart_name}")
async def get_chart(project_id: str, chart_name: str):
    chart_path = os.path.join("projects", project_id, "charts", chart_name)
    if not os.path.exists(chart_path):
        raise HTTPException(404, f"图表 {chart_name} 不存在")
    return FileResponse(chart_path, media_type="text/html")


@router.get("/projects/{project_id}/reports")
async def list_reports(project_id: str):
    return pm.list_reports(project_id)
