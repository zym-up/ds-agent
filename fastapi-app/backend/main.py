"""FastAPI 应用入口"""
import sys
import os
import logging
from typing import Optional
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import json
import shutil

from engine.data_loader import load_file, get_data_info
from engine.config import load_config, save_config, LLMConfig
from engine.llm_agent import LLMAdapter, AnalysisAgent, AnalysisStep
from engine.project_manager import ProjectManager
from engine.step_executor import execute_step
from engine.reporter import generate_html_report, build_section

from backend.models.schemas import (
    LLMConfigSchema, AnalysisRequest, StepExecuteRequest, GenerateReportRequest,
    MergeDataRequest, ConcludeRequest, PlanStreamRequest, ExecuteStreamRequest,
)

logger = logging.getLogger(__name__)

app = FastAPI(title="数据科学家 Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pm = ProjectManager()
_agent_cache: dict = {}


def _get_agent(project_id: str = None):
    """获取 AnalysisAgent 实例（按 project_id 缓存以保持对话连续）"""
    if project_id and project_id in _agent_cache:
        return _agent_cache[project_id]
    config = load_config()
    adapter = LLMAdapter(config.llm)
    agent = AnalysisAgent(adapter)
    if project_id:
        try:
            project_data = pm.load_project(project_id)
            if project_data.get("chat_history"):
                agent.set_chat_history(project_data["chat_history"])
        except Exception:
            pass
        _agent_cache[project_id] = agent
    return agent


# ──────────────────────────────────────────────
# Health & Config
# ──────────────────────────────────────────────

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


# ──────────────────────────────────────────────
# Data Upload (preview only, no project)
# ──────────────────────────────────────────────

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


# ──────────────────────────────────────────────
# Projects CRUD
# ──────────────────────────────────────────────

@app.get("/api/projects")
async def list_projects():
    return pm.list_projects()


@app.post("/api/projects")
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


@app.get("/api/projects/{project_id}")
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


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    pm.delete_project(project_id)
    return {"status": "ok"}


# ──────────────────────────────────────────────
# Project Info & Data Management
# ──────────────────────────────────────────────

@app.get("/api/projects/{project_id}/info")
async def get_project_info(project_id: str):
    return pm.get_project_info(project_id)


@app.get("/api/projects/{project_id}/data")
async def list_data_files(project_id: str):
    return pm.list_data_files(project_id)


@app.post("/api/projects/{project_id}/data")
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


@app.post("/api/projects/{project_id}/data/merge")
async def merge_data(project_id: str, req: MergeDataRequest):
    df = pm.merge_selected_data(project_id, req.selected_files)
    info = get_data_info(df)
    return {"rows": len(df), "cols": len(df.columns), "info": info}


# ──────────────────────────────────────────────
# Analysis — Plan
# ──────────────────────────────────────────────

@app.post("/api/analysis/plan")
async def plan_analysis(req: AnalysisRequest):
    data = pm.load_project(req.project_id)
    df = data["dataframe"]
    if df is None:
        raise HTTPException(400, "项目无数据")

    info = get_data_info(df)
    agent = _get_agent(req.project_id)
    plan = agent.plan_analysis(req.user_input, info)

    state = data["state"]
    state["steps"] = [{"type": s.type, "description": s.description,
                       "params": s.params, "status": "pending"} for s in plan.steps]
    state["current_step"] = 0
    pm.save_state(req.project_id, state)
    pm.save_chat_history(req.project_id, agent.chat_history)

    return {"explanation": plan.raw_response, "steps": state["steps"]}


@app.post("/api/analysis/plan/stream")
async def plan_analysis_stream(req: PlanStreamRequest):
    data = pm.load_project(req.project_id)
    df = data["dataframe"]
    if df is None:
        raise HTTPException(400, "项目无数据")

    info = get_data_info(df)
    agent = _get_agent(req.project_id)

    messages = [
        {"role": "system", "content": agent.build_system_prompt()},
        {"role": "user", "content": f"""当前数据集信息：
- 行数: {info.get('shape', [0, 0])[0]}
- 列数: {info.get('shape', [0, 0])[1]}
- 数值列: {info.get('numeric_columns', [])}
- 分类型列: {info.get('categorical_columns', [])}
- 列名: {info.get('columns', [])}

用户的请求: {req.user_input}

请给出分析计划（JSON 格式）。"""},
    ]

    async def generate():
        full_response = ""
        for chunk in agent.llm.chat_stream(messages):
            full_response += chunk
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"

        agent.chat_history.append({"role": "user", "content": req.user_input})
        agent.chat_history.append({"role": "assistant", "content": full_response})

        # 解析 JSON 提取计划步骤
        try:
            if "```json" in full_response:
                json_str = full_response.split("```json")[1].split("```")[0]
            elif "```" in full_response:
                json_str = full_response.split("```")[1].split("```")[0]
            else:
                json_str = full_response

            parsed = json.loads(json_str.strip())
            steps = [{"type": s["type"], "description": s["description"],
                       "params": s.get("params", {}), "status": "pending"}
                     for s in parsed.get("steps", [])]
        except (json.JSONDecodeError, KeyError):
            steps = []

        state = data["state"]
        state["steps"] = steps
        state["current_step"] = 0
        pm.save_state(req.project_id, state)
        pm.save_chat_history(req.project_id, agent.chat_history)

        yield f"data: {json.dumps({'done': True, 'steps': steps})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


def _load_chart_html(project_id: str, step_index: int) -> str:
    """从磁盘加载步骤关联的图表 HTML"""
    chart_dir = os.path.join("projects", project_id, "charts")
    html_parts = []
    j = 1
    while j <= 100:
        chart_path = os.path.join(chart_dir, f"step{step_index + 1}_chart{j}.html")
        if os.path.exists(chart_path):
            with open(chart_path, "r", encoding="utf-8") as f:
                html_parts.append(f.read())
            j += 1
        else:
            break
    return "".join(html_parts)


@app.post("/api/analysis/execute")
async def execute_analysis_step(req: StepExecuteRequest):
    data = pm.load_project(req.project_id)
    df = data["dataframe"]
    state = data["state"]
    step = state["steps"][req.step_index]
    step_type = step["type"]
    params = step.get("params", {})

    try:
        result = execute_step(step_type, params, df)

        explanation = ""
        if result["metrics"]:
            try:
                agent = _get_agent(req.project_id)
                agent_step = AnalysisStep(
                    id=req.step_index + 1,
                    type=step_type,
                    description=step.get("description", ""),
                )
                explanation = agent.explain_result(agent_step, result["metrics"])
            except Exception:
                logger.warning("LLM 解读失败", exc_info=True)

        state["steps"][req.step_index]["status"] = "done"
        state["steps"][req.step_index]["llm_explanation"] = explanation
        pm.save_state(req.project_id, state)

        for j, chart in enumerate(result["charts"]):
            pm.save_chart(req.project_id, f"step{req.step_index + 1}_chart{j + 1}", chart)

        if step_type == "clean":
            data_path = os.path.join("projects", req.project_id, "data", "original.csv")
            result["result_df"].to_csv(data_path, index=False)

        return {
            "status": "done",
            "result": result["text"],
            "llm_explanation": explanation,
            "chart_count": len(result["charts"]),
        }

    except Exception as e:
        logger.warning("步骤执行失败", exc_info=True)
        state["steps"][req.step_index]["status"] = "error"
        pm.save_state(req.project_id, state)
        return {"status": "error", "result": str(e)}


@app.post("/api/analysis/execute/stream")
async def execute_analysis_step_stream(req: ExecuteStreamRequest):
    data = pm.load_project(req.project_id)
    df = data["dataframe"]
    state = data["state"]
    step = state["steps"][req.step_index]
    step_type = step["type"]
    params = step.get("params", {})

    try:
        result = execute_step(step_type, params, df)

        state["steps"][req.step_index]["status"] = "done"
        pm.save_state(req.project_id, state)

        for j, chart in enumerate(result["charts"]):
            pm.save_chart(req.project_id, f"step{req.step_index + 1}_chart{j + 1}", chart)

        if step_type == "clean":
            data_path = os.path.join("projects", req.project_id, "data", "original.csv")
            result["result_df"].to_csv(data_path, index=False)

        async def generate():
            yield f"data: {json.dumps({'type': 'result', 'text': result['text'], 'chart_count': len(result['charts'])})}\n\n"

            if result["metrics"]:
                agent = _get_agent(req.project_id)
                agent_step = AnalysisStep(
                    id=req.step_index + 1,
                    type=step_type,
                    description=step.get("description", ""),
                )
                full_explanation = ""
                try:
                    for chunk in agent.explain_result_stream(agent_step, result["metrics"]):
                        full_explanation += chunk
                        yield f"data: {json.dumps({'type': 'explanation', 'chunk': chunk})}\n\n"
                except Exception:
                    logger.warning("LLM 流式解读失败，尝试同步", exc_info=True)
                    try:
                        full_explanation = agent.explain_result(agent_step, result["metrics"])
                        yield f"data: {json.dumps({'type': 'explanation', 'chunk': full_explanation})}\n\n"
                    except Exception:
                        logger.warning("LLM 同步解读也失败", exc_info=True)

                state["steps"][req.step_index]["llm_explanation"] = full_explanation
                pm.save_state(req.project_id, state)

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except Exception as e:
        logger.warning("步骤执行失败", exc_info=True)
        state["steps"][req.step_index]["status"] = "error"
        pm.save_state(req.project_id, state)

        async def error_gen():
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        return StreamingResponse(error_gen(), media_type="text/event-stream")


# ──────────────────────────────────────────────
# Reports
# ──────────────────────────────────────────────

@app.get("/api/projects/{project_id}/reports")
async def list_reports(project_id: str):
    return pm.list_reports(project_id)


@app.post("/api/report/generate")
async def generate_report(req: GenerateReportRequest):
    data = pm.load_project(req.project_id)
    state = data["state"]
    all_steps = state.get("steps", [])

    # 筛选步骤
    if req.step_indices:
        selected_steps = [all_steps[i] for i in req.step_indices if i < len(all_steps)]
    else:
        selected_steps = [s for s in all_steps if s.get("status") == "done"]

    # 构建 sections（含图表 HTML）
    sections = []
    for i, step in enumerate(all_steps):
        if step in selected_steps:
            chart_html = _load_chart_html(req.project_id, i)
            sections.append(build_section(
                title=step.get("description", ""),
                text=step.get("llm_explanation", ""),
                chart_html=chart_html,
            ))

    # AI 综合结论
    conclusion = ""
    if req.conclusion:
        conclusion = req.conclusion
    elif req.include_conclusion and selected_steps:
        step_data = [{"type": s["type"], "explanation": s.get("llm_explanation", "")}
                     for s in selected_steps]
        try:
            agent = _get_agent(req.project_id)
            conclusion = "".join(list(agent.summarize_conclusions(step_data, req.user_notes)))
        except Exception:
            logger.warning("AI 结论生成失败", exc_info=True)
            conclusion = "分析完成"

    df = data["dataframe"]
    rows, cols = df.shape if df is not None else (0, 0)
    html = generate_html_report(
        title=req.title, sections=sections, conclusion=conclusion,
        data_source=data["meta"]["name"], rows=rows, cols=cols,
    )

    report_path = pm.save_report(req.project_id, html)
    return {"path": report_path, "report_name": os.path.basename(report_path)}


@app.post("/api/report/conclude/stream")
async def conclude_stream(req: ConcludeRequest):
    data = pm.load_project(req.project_id)
    state = data["state"]
    all_steps = state.get("steps", [])

    if req.step_indices:
        selected_steps = [all_steps[i] for i in req.step_indices if i < len(all_steps)]
    else:
        selected_steps = [s for s in all_steps if s.get("status") == "done"]

    step_data = [{"type": s["type"], "explanation": s.get("llm_explanation", "")}
                 for s in selected_steps]

    agent = _get_agent(req.project_id)

    async def generate():
        try:
            for chunk in agent.summarize_conclusions(step_data, req.user_notes):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/api/report/download/{project_id}")
async def download_report(project_id: str):
    reports_dir = os.path.join("projects", project_id, "reports")
    if not os.path.exists(reports_dir):
        raise HTTPException(404, "无报告")
    files = sorted(os.listdir(reports_dir), reverse=True)
    if not files:
        raise HTTPException(404, "无报告")
    return FileResponse(os.path.join(reports_dir, files[0]))


@app.get("/api/report/download/{project_id}/{report_name}")
async def download_specific_report(project_id: str, report_name: str):
    report_path = os.path.join("projects", project_id, "reports", report_name)
    if not os.path.exists(report_path):
        raise HTTPException(404, f"报告 {report_name} 不存在")
    return FileResponse(report_path)


# ──────────────────────────────────────────────
# Charts
# ──────────────────────────────────────────────

@app.get("/api/projects/{project_id}/charts/{chart_name}")
async def get_chart(project_id: str, chart_name: str):
    chart_path = os.path.join("projects", project_id, "charts", chart_name)
    if not os.path.exists(chart_path):
        raise HTTPException(404, f"图表 {chart_name} 不存在")
    return FileResponse(chart_path, media_type="text/html")


# ──────────────────────────────────────────────
# Static Files (production)
# ──────────────────────────────────────────────

from fastapi.responses import HTMLResponse, Response
import os

# 获取 fastapi-app 目录的绝对路径
fastapi_app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_dist = os.path.join(fastapi_app_dir, "frontend", "dist")

print(f"查找前端文件: {frontend_dist}")

def get_file_content_type(file_path: str) -> str:
    """根据文件扩展名返回正确的 Content-Type"""
    if file_path.endswith('.js'):
        return 'application/javascript'
    elif file_path.endswith('.css'):
        return 'text/css'
    elif file_path.endswith('.html'):
        return 'text/html'
    elif file_path.endswith('.json'):
        return 'application/json'
    elif file_path.endswith('.png'):
        return 'image/png'
    elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
        return 'image/jpeg'
    elif file_path.endswith('.svg'):
        return 'image/svg+xml'
    elif file_path.endswith('.ico'):
        return 'image/x-icon'
    else:
        return 'application/octet-stream'

if os.path.exists(frontend_dist) and os.path.exists(os.path.join(frontend_dist, "index.html")):
    
    @app.get("/assets/{file_path:path}")
    async def serve_assets(file_path: str):
        """处理 assets 文件夹下的所有文件"""
        full_path = os.path.join(frontend_dist, "assets", file_path)
        if os.path.exists(full_path) and not os.path.isdir(full_path):
            content_type = get_file_content_type(full_path)
            with open(full_path, 'rb') as f:
                content = f.read()
            return Response(content=content, media_type=content_type)
        raise HTTPException(status_code=404)
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """处理所有前端路由"""
        # API 请求不处理
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            raise HTTPException(status_code=404)
        
        # 完整的文件路径
        file_path = os.path.join(frontend_dist, full_path)
        
        # 如果文件存在，直接返回
        if os.path.exists(file_path) and not os.path.isdir(file_path):
            content_type = get_file_content_type(file_path)
            with open(file_path, 'rb') as f:
                content = f.read()
            return Response(content=content, media_type=content_type)
        
        # 其他情况返回 index.html（支持 Vue Router）
        index_path = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_path):
            with open(index_path, 'rb') as f:
                content = f.read()
            return Response(content=content, media_type='text/html')
        
        raise HTTPException(status_code=404)
    
    print(f"[OK] Frontend static files: {frontend_dist}")
else:
    print(f"[WARN] Frontend dist not found: {frontend_dist}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8502)
