"""分析计划 + 执行路由（含流式）—— 支持多轮对话 rounds"""
import json
import os
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from engine.data_loader import get_data_info
from engine.llm_agent import AnalysisStep
from engine.step_executor import execute_step
from backend.deps import pm, get_agent, logger
from backend.models.schemas import AnalysisRequest, StepExecuteRequest, PlanStreamRequest, ExecuteStreamRequest

router = APIRouter(tags=["analysis"])

# 图表命名前缀
def _chart_prefix(round_idx: int) -> str:
    return f"round{round_idx}"


def _new_round(user_input: str, plan_explanation: str, steps: list) -> dict:
    """创建新 round"""
    return {
        "id": int(datetime.now().timestamp() * 1000),
        "user_input": user_input,
        "plan_explanation": plan_explanation,
        "steps": steps,
        "current_step": 0,
        "created_at": datetime.now().isoformat(),
    }


@router.post("/analysis/plan")
async def plan_analysis(req: AnalysisRequest):
    data = pm.load_project(req.project_id)
    df = data["dataframe"]
    if df is None:
        raise HTTPException(400, "项目无数据")

    info = get_data_info(df)
    agent = get_agent(req.project_id)
    plan = agent.plan_analysis(req.user_input, info)

    state = data["state"]
    new_steps = [{"type": s.type, "description": s.description,
                  "params": s.params, "status": "pending"} for s in plan.steps]
    rnd = _new_round(req.user_input, plan.raw_response, new_steps)

    if "rounds" not in state:
        state["rounds"] = []
    state["rounds"].append(rnd)
    state["current_round"] = len(state["rounds"]) - 1
    pm.save_state(req.project_id, state)
    pm.save_chat_history(req.project_id, agent.chat_history)

    return {
        "explanation": plan.raw_response,
        "steps": new_steps,
        "round_index": state["current_round"],
        "rounds": state["rounds"],
    }


@router.post("/analysis/plan/stream")
async def plan_analysis_stream(req: PlanStreamRequest):
    data = pm.load_project(req.project_id)
    df = data["dataframe"]
    if df is None:
        raise HTTPException(400, "项目无数据")

    info = get_data_info(df)
    agent = get_agent(req.project_id)

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
            explanation = parsed.get("explanation", "")
        except (json.JSONDecodeError, KeyError):
            steps = []
            explanation = ""

        state = data["state"]
        if steps:
            rnd = _new_round(req.user_input, explanation, steps)
            if "rounds" not in state:
                state["rounds"] = []
            state["rounds"].append(rnd)
            state["current_round"] = len(state["rounds"]) - 1
            pm.save_state(req.project_id, state)
        pm.save_chat_history(req.project_id, agent.chat_history)

        yield f"data: {json.dumps({'done': True, 'steps': steps, 'round_index': state.get('current_round', -1)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


def _current_round_steps(state: dict):
    """获取当前 round 的 steps 引用"""
    cr = state.get("current_round", -1)
    if cr < 0 or cr >= len(state.get("rounds", [])):
        raise HTTPException(400, "没有活动的分析轮次，请先发送分析请求")
    return state["rounds"][cr]


@router.post("/analysis/execute")
async def execute_analysis_step(req: StepExecuteRequest):
    data = pm.load_project(req.project_id)
    df = data["dataframe"]
    state = data["state"]
    rnd = _current_round_steps(state)
    step = rnd["steps"][req.step_index]
    step_type = step["type"]
    params = step.get("params", {})
    round_idx = state["current_round"]

    try:
        result = execute_step(step_type, params, df)

        explanation = ""
        if result["metrics"] or result["text"]:
            try:
                agent = get_agent(req.project_id)
                agent_step = AnalysisStep(
                    id=req.step_index + 1,
                    type=step_type,
                    description=step.get("description", ""),
                )
                explanation = agent.explain_result(agent_step, result["metrics"], result["text"])
            except Exception:
                logger.warning("LLM 解读失败", exc_info=True)

        rnd["steps"][req.step_index]["status"] = "done"
        rnd["steps"][req.step_index]["llm_explanation"] = explanation
        pm.save_state(req.project_id, state)

        prefix = _chart_prefix(round_idx)
        for j, chart in enumerate(result["charts"]):
            pm.save_chart(req.project_id, f"{prefix}_step{req.step_index + 1}_chart{j + 1}", chart)

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
        rnd["steps"][req.step_index]["status"] = "error"
        pm.save_state(req.project_id, state)
        return {"status": "error", "result": str(e)}


@router.post("/analysis/execute/stream")
async def execute_analysis_step_stream(req: ExecuteStreamRequest):
    data = pm.load_project(req.project_id)
    df = data["dataframe"]
    state = data["state"]
    rnd = _current_round_steps(state)
    step = rnd["steps"][req.step_index]
    step_type = step["type"]
    params = step.get("params", {})
    round_idx = state["current_round"]

    try:
        result = execute_step(step_type, params, df)

        rnd["steps"][req.step_index]["status"] = "done"
        pm.save_state(req.project_id, state)

        prefix = _chart_prefix(round_idx)
        for j, chart in enumerate(result["charts"]):
            pm.save_chart(req.project_id, f"{prefix}_step{req.step_index + 1}_chart{j + 1}", chart)

        if step_type == "clean":
            data_path = os.path.join("projects", req.project_id, "data", "original.csv")
            result["result_df"].to_csv(data_path, index=False)

        async def generate():
            yield f"data: {json.dumps({'type': 'result', 'text': result['text'], 'chart_count': len(result['charts'])})}\n\n"

            if result["metrics"] or result["text"]:
                agent = get_agent(req.project_id)
                agent_step = AnalysisStep(
                    id=req.step_index + 1,
                    type=step_type,
                    description=step.get("description", ""),
                )
                full_explanation = ""
                try:
                    for chunk in agent.explain_result_stream(agent_step, result["metrics"], result["text"]):
                        full_explanation += chunk
                        yield f"data: {json.dumps({'type': 'explanation', 'chunk': chunk})}\n\n"
                except Exception:
                    logger.warning("LLM 流式解读失败，尝试同步", exc_info=True)
                    try:
                        full_explanation = agent.explain_result(agent_step, result["metrics"], result["text"])
                        yield f"data: {json.dumps({'type': 'explanation', 'chunk': full_explanation})}\n\n"
                    except Exception:
                        logger.warning("LLM 同步解读也失败", exc_info=True)

                rnd["steps"][req.step_index]["llm_explanation"] = full_explanation
                pm.save_state(req.project_id, state)

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except Exception as e:
        logger.warning("步骤执行失败", exc_info=True)
        rnd["steps"][req.step_index]["status"] = "error"
        pm.save_state(req.project_id, state)

        error_msg = str(e)

        async def error_gen():
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"

        return StreamingResponse(error_gen(), media_type="text/event-stream")
