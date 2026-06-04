"""报告生成 + 下载 路由 — 支持多轮对话 rounds"""
import json
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from engine.reporter import generate_html_report, build_section
from backend.deps import pm, get_agent, load_chart_html, logger
from backend.models.schemas import GenerateReportRequest, ConcludeRequest

router = APIRouter(tags=["reports"])


def _collect_all_done_steps(state: dict) -> list:
    """收集所有 rounds 中已完成的步骤，返回 [{round_idx, step_idx, step, user_input}]"""
    result = []
    for ri, rnd in enumerate(state.get("rounds", [])):
        for si, step in enumerate(rnd.get("steps", [])):
            if step.get("status") == "done":
                result.append({
                    "round_idx": ri,
                    "step_idx": si,
                    "step": step,
                    "user_input": rnd.get("user_input", ""),
                })
    return result


@router.post("/report/generate")
async def generate_report(req: GenerateReportRequest):
    data = pm.load_project(req.project_id)
    state = data["state"]
    done_items = _collect_all_done_steps(state)

    if req.step_indices:
        # 筛选指定索引的步骤（兼容旧版 step_indices 是全局索引或按 round）
        selected = []
        for idx in req.step_indices:
            if idx < len(done_items):
                selected.append(done_items[idx])
    else:
        selected = done_items

    sections = []
    for item in selected:
        chart_html = load_chart_html(req.project_id, item["round_idx"], item["step_idx"])
        title = item["step"].get("description", "")
        if item["user_input"]:
            title = f"【{item['user_input']}】{title}"
        sections.append(build_section(
            title=title,
            text=item["step"].get("llm_explanation", ""),
            chart_html=chart_html,
        ))

    conclusion = ""
    if req.conclusion:
        conclusion = req.conclusion
    elif req.include_conclusion and selected:
        step_data = [{"type": s["step"]["type"],
                      "explanation": s["step"].get("llm_explanation", "")}
                     for s in selected]
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
    done_items = _collect_all_done_steps(state)

    if req.step_indices:
        selected = [done_items[i] for i in req.step_indices if i < len(done_items)]
    else:
        selected = done_items

    step_data = [{"type": s["step"]["type"],
                  "explanation": s["step"].get("llm_explanation", "")}
                 for s in selected]

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
