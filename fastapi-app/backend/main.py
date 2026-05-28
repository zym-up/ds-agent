"""FastAPI 应用入口"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import json
import shutil

from engine.data_loader import load_file, get_data_info
from engine.config import load_config, save_config, LLMConfig
from engine.llm_agent import LLMAdapter, AnalysisAgent
from engine.project_manager import ProjectManager
from engine.data_cleaner import clean_pipeline
from engine.eda import eda_pipeline
from engine.modeler import train_regression, evaluate_regression, split_data, feature_importance, residual_plot
from engine.reporter import generate_html_report, build_section

from models.schemas import (
    LLMConfigSchema, AnalysisRequest, StepExecuteRequest, GenerateReportRequest,
)

app = FastAPI(title="数据科学家 Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pm = ProjectManager()


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/config")
async def get_config():
    return load_config().to_dict()


@app.post("/api/config")
async def update_config(config: LLMConfigSchema):
    app_config = load_config()
    app_config.llm = LLMConfig(**config.model_dump())
    save_config(app_config)
    return {"status": "ok"}


@app.post("/api/config/test")
async def test_connection(config: LLMConfigSchema):
    adapter = LLMAdapter(LLMConfig(**config.model_dump()))
    ok, msg = adapter.test_connection()
    return {"success": ok, "message": msg}


@app.post("/api/data/upload")
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


@app.get("/api/projects")
async def list_projects():
    return pm.list_projects()


@app.post("/api/projects")
async def create_project(name: str, file: Optional[UploadFile] = File(None)):
    from typing import Optional
    data_path = None
    if file:
        tmp_path = f"temp_{file.filename}"
        with open(tmp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        data_path = tmp_path

    project_id = pm.create_project(name, data_path)

    if data_path:
        os.unlink(data_path)

    return {"project_id": project_id}


@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    data = pm.load_project(project_id)
    meta = data["meta"]
    state = data["state"]
    chat = data["chat_history"]
    preview = None
    data_info_dict = {}
    if data["dataframe"] is not None:
        preview = data["dataframe"].head(10).to_dict(orient="records")
        data_info_dict = get_data_info(data["dataframe"])
    return {"meta": meta, "state": state, "chat_history": chat,
            "preview": preview, "data_info": data_info_dict}


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    pm.delete_project(project_id)
    return {"status": "ok"}


@app.post("/api/analysis/plan")
async def plan_analysis(req: AnalysisRequest):
    config = load_config()
    adapter = LLMAdapter(config.llm)
    agent = AnalysisAgent(adapter)

    data = pm.load_project(req.project_id)
    df = data["dataframe"]
    if df is None:
        raise HTTPException(400, "项目无数据")

    info = get_data_info(df)
    plan = agent.plan_analysis(req.user_input, info)

    state = data["state"]
    state["steps"] = [{"type": s.type, "description": s.description,
                        "params": s.params, "status": "pending"} for s in plan.steps]
    pm.save_state(req.project_id, state)
    pm.save_chat_history(req.project_id, agent.chat_history)

    return {"explanation": plan.raw_response, "steps": state["steps"]}


@app.post("/api/analysis/execute")
async def execute_step(req: StepExecuteRequest):
    data = pm.load_project(req.project_id)
    df = data["dataframe"]
    state = data["state"]
    step = state["steps"][req.step_index]

    try:
        result_text = ""

        if step["type"] == "clean":
            df, summary = clean_pipeline(df, **step.get("params", {}))
            result_text = json.dumps(summary, ensure_ascii=False)

        elif step["type"] == "eda":
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            result = eda_pipeline(df, numeric_columns=numeric_cols)
            result_text = f"行数: {result['row_count']}, 列数: {result['column_count']}"

        elif step["type"] == "model":
            target = step["params"].get("target", "")
            model_type = step["params"].get("model_type", "linear")
            numeric_cols = [c for c in df.select_dtypes(include=["number"]).columns if c != target]
            model_df = df[numeric_cols + [target]].dropna()
            X_train, X_test, y_train, y_test = split_data(model_df, target)
            model, _ = train_regression(X_train, y_train, model_type)
            metrics = evaluate_regression(model, X_test, y_test)
            result_text = json.dumps(metrics, ensure_ascii=False)

        state["steps"][req.step_index]["status"] = "done"
        pm.save_state(req.project_id, state)

        data_path = os.path.join("projects", req.project_id, "data", "original.csv")
        df.to_csv(data_path, index=False)

        return {"status": "done", "result": result_text}

    except Exception as e:
        state["steps"][req.step_index]["status"] = "error"
        pm.save_state(req.project_id, state)
        return {"status": "error", "result": str(e)}


@app.post("/api/report/generate")
async def generate_report(req: GenerateReportRequest):
    data = pm.load_project(req.project_id)
    df = data["dataframe"]
    state = data["state"]

    sections = []
    for step in state.get("steps", []):
        if step["status"] == "done":
            sections.append(build_section(title=step["description"]))

    rows, cols = df.shape if df is not None else (0, 0)
    html = generate_html_report(
        title=req.title, sections=sections, conclusion=req.conclusion,
        data_source=data["meta"]["name"], rows=rows, cols=cols,
    )

    report_path = pm.save_report(req.project_id, html)
    return {"path": report_path}


@app.get("/api/report/download/{project_id}")
async def download_report(project_id: str):
    reports_dir = os.path.join("projects", project_id, "reports")
    if not os.path.exists(reports_dir):
        raise HTTPException(404, "无报告")
    files = sorted(os.listdir(reports_dir), reverse=True)
    if not files:
        raise HTTPException(404, "无报告")
    return FileResponse(os.path.join(reports_dir, files[0]))


if os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8502)
