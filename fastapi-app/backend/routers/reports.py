"""报告生成 + 下载 路由"""
import json
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from engine.reporter import generate_html_report, build_section
from backend.deps import pm, get_agent, load_chart_html, logger
from backend.models.schemas import GenerateReportRequest, ConcludeRequest

router = APIRouter(tags=["reports"])


@router.post("/report/generate")
async def generate_report(req: GenerateReportRequest):
    data = pm.load_project(req.project_id)
    state = data["state"]
    all_steps = state.get("steps", [])

    if req.step_indices:
        selected_steps = [all_steps[i] for i in req.step_indices if i < len(all_steps)]
    else:
        selected_steps = [s for s in all_steps if s.get("status") == "done"]

    sections = []
    for i, step in enumerate(all_steps):
        if step in selected_steps:
            chart_html = load_chart_html(req.project_id, i)
            sections.append(build_section(
                title=step.get("description", ""),
                text=step.get("llm_explanation", ""),
                chart_html=chart_html,
            ))

    conclusion = ""
    if req.conclusion:
        conclusion = req.conclusion
    elif req.include_conclusion and selected_steps:
        step_data = [{"type": s["type"], "explanation": s.get("llm_explanation", "")}
                     for s in selected_steps]
        try:
            agent = get_agent(req.project_id)
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


@router.post("/report/conclude/stream")
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

    agent = get_agent(req.project_id)

    async def generate():
        try:
            for chunk in agent.summarize_conclusions(step_data, req.user_notes):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/report/download/{project_id}")
async def download_report(project_id: str):
    reports_dir = os.path.join("projects", project_id, "reports")
    if not os.path.exists(reports_dir):
        raise HTTPException(404, "无报告")
    files = sorted(os.listdir(reports_dir), reverse=True)
    if not files:
        raise HTTPException(404, "无报告")
    return FileResponse(os.path.join(reports_dir, files[0]))


@router.get("/report/download/{project_id}/{report_name}")
async def download_specific_report(project_id: str, report_name: str):
    report_path = os.path.join("projects", project_id, "reports", report_name)
    if not os.path.exists(report_path):
        raise HTTPException(404, f"报告 {report_name} 不存在")
    return FileResponse(report_path)
