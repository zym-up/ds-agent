"""FastAPI 应用入口"""
import sys
import os
from typing import Optional
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import json
import shutil

from engine.data_loader import load_file, get_data_info
from engine.config import load_config, save_config, LLMConfig
from engine.llm_agent import LLMAdapter, AnalysisAgent, AnalysisStep
from engine.project_manager import ProjectManager
from engine.data_cleaner import clean_pipeline
from engine.eda import eda_pipeline
from engine.modeler import train_regression, evaluate_regression, split_data, feature_importance, residual_plot
from engine.reporter import generate_html_report, build_section

from backend.models.schemas import (
    LLMConfigSchema, AnalysisRequest, StepExecuteRequest, GenerateReportRequest,
    MergeDataRequest, ConcludeRequest, PlanStreamRequest, ExecuteStreamRequest,
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


def _get_agent():
    """获取 AnalysisAgent 实例（每次新建，确保使用最新 config）"""
    config = load_config()
    adapter = LLMAdapter(config.llm)
    return AnalysisAgent(adapter)


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
async def create_project(name: str, file: UploadFile = File(...)):
    tmp_path = f"temp_{file.filename}"
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    project_id = pm.create_project(name, tmp_path)
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
    agent = _get_agent()
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
    agent = _get_agent()

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


# ──────────────────────────────────────────────
# Analysis — Execute Step
# ──────────────────────────────────────────────

def _build_metrics(step_type: str, step_params: dict, df, result_df, result):
    """构造传给 LLM 解读的指标字典"""
    if step_type == "clean":
        return result  # clean_pipeline 返回的 summary dict
    elif step_type == "eda":
        stats_summary = {}
        for k, v in result.get("stats_summary", {}).items():
            stats_summary[k] = str(v)
        return {"行数": result["row_count"], "列数": result["column_count"], "统计摘要": stats_summary}
    elif step_type == "model":
        return result  # metrics dict
    return {}


def _load_chart_html(project_id: str, step_index: int) -> str:
    """从磁盘加载步骤关联的图表 HTML"""
    chart_dir = os.path.join("projects", project_id, "charts")
    html = ""
    j = 1
    while True:
        chart_path = os.path.join(chart_dir, f"step{step_index + 1}_chart{j}.html")
        if os.path.exists(chart_path):
            with open(chart_path, "r", encoding="utf-8") as f:
                html += f.read()
            j += 1
        else:
            break
    return html


@app.post("/api/analysis/execute")
async def execute_step(req: StepExecuteRequest):
    data = pm.load_project(req.project_id)
    df = data["dataframe"]
    state = data["state"]
    step = state["steps"][req.step_index]
    step_type = step["type"]
    params = step.get("params", {})

    charts = []
    result_text = ""
    metrics = {}
    result_df = df

    try:
        if step_type == "clean":
            result_df, summary = clean_pipeline(df, **params)
            result_text = json.dumps(summary, ensure_ascii=False, indent=2)
            metrics = summary

        elif step_type == "eda":
            numeric_cols = params.get("columns") or df.select_dtypes(include=["number"]).columns.tolist()
            result = eda_pipeline(df, numeric_columns=numeric_cols)
            charts = result["charts"]
            result_text = f"行数: {result['row_count']}, 列数: {result['column_count']}"
            metrics = _build_metrics("eda", params, df, result_df, result)

        elif step_type == "model":
            target = params.get("target", "")
            model_type = params.get("model_type", "linear")
            numeric_cols = [c for c in df.select_dtypes(include=["number"]).columns if c != target]
            model_df = df[numeric_cols + [target]].dropna()
            X_train, X_test, y_train, y_test = split_data(model_df, target)
            model, _ = train_regression(X_train, y_train, model_type)
            eval_metrics = evaluate_regression(model, X_test, y_test)
            _, imp_fig = feature_importance(model, numeric_cols)
            charts.append(imp_fig)
            y_pred = model.predict(X_test)
            res_fig = residual_plot(y_test, y_pred)
            charts.append(res_fig)
            result_text = json.dumps(eval_metrics, ensure_ascii=False, indent=2)
            metrics = eval_metrics

        elif step_type == "report":
            result_text = "报告生成请使用 /api/report/generate 端点"

        # LLM 解读
        explanation = ""
        if metrics:
            try:
                agent = _get_agent()
                agent_step = AnalysisStep(
                    id=req.step_index + 1,
                    type=step_type,
                    description=step.get("description", ""),
                )
                explanation = agent.explain_result(agent_step, metrics)
            except Exception:
                pass

        state["steps"][req.step_index]["status"] = "done"
        state["steps"][req.step_index]["llm_explanation"] = explanation
        pm.save_state(req.project_id, state)

        # 保存图表
        for j, chart in enumerate(charts):
            pm.save_chart(req.project_id, f"step{req.step_index + 1}_chart{j + 1}", chart)

        # 持久化清洗后的数据
        if step_type == "clean":
            data_path = os.path.join("projects", req.project_id, "data", "original.csv")
            result_df.to_csv(data_path, index=False)

        return {
            "status": "done",
            "result": result_text,
            "llm_explanation": explanation,
        }

    except Exception as e:
        state["steps"][req.step_index]["status"] = "error"
        pm.save_state(req.project_id, state)
        return {"status": "error", "result": str(e)}


@app.post("/api/analysis/execute/stream")
async def execute_step_stream(req: ExecuteStreamRequest):
    data = pm.load_project(req.project_id)
    df = data["dataframe"]
    state = data["state"]
    step = state["steps"][req.step_index]
    step_type = step["type"]
    params = step.get("params", {})

    charts = []
    result_text = ""
    metrics = {}
    result_df = df

    try:
        if step_type == "clean":
            result_df, summary = clean_pipeline(df, **params)
            result_text = json.dumps(summary, ensure_ascii=False, indent=2)
            metrics = summary

        elif step_type == "eda":
            numeric_cols = params.get("columns") or df.select_dtypes(include=["number"]).columns.tolist()
            result = eda_pipeline(df, numeric_columns=numeric_cols)
            charts = result["charts"]
            result_text = f"行数: {result['row_count']}, 列数: {result['column_count']}"
            metrics = _build_metrics("eda", params, df, result_df, result)

        elif step_type == "model":
            target = params.get("target", "")
            model_type = params.get("model_type", "linear")
            numeric_cols = [c for c in df.select_dtypes(include=["number"]).columns if c != target]
            model_df = df[numeric_cols + [target]].dropna()
            X_train, X_test, y_train, y_test = split_data(model_df, target)
            model, _ = train_regression(X_train, y_train, model_type)
            eval_metrics = evaluate_regression(model, X_test, y_test)
            _, imp_fig = feature_importance(model, numeric_cols)
            charts.append(imp_fig)
            y_pred = model.predict(X_test)
            res_fig = residual_plot(y_test, y_pred)
            charts.append(res_fig)
            result_text = json.dumps(eval_metrics, ensure_ascii=False, indent=2)
            metrics = eval_metrics

        elif step_type == "report":
            result_text = "报告生成请使用 /api/report/generate 端点"

        state["steps"][req.step_index]["status"] = "done"
        pm.save_state(req.project_id, state)

        for j, chart in enumerate(charts):
            pm.save_chart(req.project_id, f"step{req.step_index + 1}_chart{j + 1}", chart)

        if step_type == "clean":
            data_path = os.path.join("projects", req.project_id, "data", "original.csv")
            result_df.to_csv(data_path, index=False)

        async def generate():
            yield f"data: {json.dumps({'type': 'result', 'text': result_text})}\n\n"

            if metrics:
                agent = _get_agent()
                agent_step = AnalysisStep(
                    id=req.step_index + 1,
                    type=step_type,
                    description=step.get("description", ""),
                )
                full_explanation = ""
                try:
                    for chunk in agent.explain_result_stream(agent_step, metrics):
                        full_explanation += chunk
                        yield f"data: {json.dumps({'type': 'explanation', 'chunk': chunk})}\n\n"
                except Exception:
                    try:
                        full_explanation = agent.explain_result(agent_step, metrics)
                        yield f"data: {json.dumps({'type': 'explanation', 'chunk': full_explanation})}\n\n"
                    except Exception:
                        pass

                state["steps"][req.step_index]["llm_explanation"] = full_explanation
                pm.save_state(req.project_id, state)

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except Exception as e:
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
    if req.include_conclusion and selected_steps:
        step_data = [{"type": s["type"], "explanation": s.get("llm_explanation", "")}
                     for s in selected_steps]
        try:
            agent = _get_agent()
            conclusion = "".join(list(agent.summarize_conclusions(step_data, req.user_notes)))
        except Exception:
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

    agent = _get_agent()

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
# Static Files (production)
# ──────────────────────────────────────────────

if os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8502)
