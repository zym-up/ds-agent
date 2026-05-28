"""分析对话页面"""
import streamlit as st
import json
from engine.data_loader import get_data_info
from engine.config import load_config
from engine.llm_agent import LLMAdapter, AnalysisAgent, AnalysisStep
from engine.data_cleaner import clean_pipeline
from engine.eda import eda_pipeline
from engine.modeler import train_regression, evaluate_regression, split_data, feature_importance, residual_plot
from engine.project_manager import ProjectManager


def show():
    st.title("🔬 分析对话")
    if "project_name" in st.session_state:
        st.info(f"📊 当前项目: **{st.session_state.project_name}**")

    if "df" not in st.session_state:
        st.warning("请先在「数据上传」页面上传数据并创建项目。")
        return

    df = st.session_state.df
    data_info = st.session_state.data_info

    if "agent" not in st.session_state:
        config = st.session_state.get("config", load_config())
        adapter = LLMAdapter(config.llm)
        st.session_state.agent = AnalysisAgent(adapter)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "analysis_state" not in st.session_state:
        st.session_state.analysis_state = {"steps": [], "current_step": 0}

    left_col, center_col, right_col = st.columns([2, 3, 1.5])

    with left_col:
        st.subheader("💬 对话")

        chat_container = st.container(height=400)
        with chat_container:
            for msg in st.session_state.chat_history[-20:]:
                role_label = "🤖 Agent" if msg["role"] == "assistant" else "👤 你"
                st.markdown(f"**{role_label}:** {msg['content']}")
                st.divider()

        user_input = st.chat_input("描述你的分析需求...")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})

            # 构建增强输入：含已完成步骤摘要
            enhanced_input = user_input
            steps = st.session_state.analysis_state.get("steps", [])
            done_steps = [s for s in steps if s.get("status") == "done"]
            if done_steps:
                context_parts = ["\n\n---\n当前已完成的分析步骤:\n"]
                for i, s in enumerate(done_steps):
                    exp = s.get("llm_explanation", "")
                    context_parts.append(f"步骤{i+1} ({s['type']}): {s['description']}")
                    if exp:
                        context_parts.append(f"  解读: {exp[:200]}")
                enhanced_input = user_input + "\n".join(context_parts)

            agent = st.session_state.agent
            plan = agent.plan_analysis(enhanced_input, data_info)
            st.session_state.chat_history.append({
                "role": "assistant", "content": plan.raw_response
            })

            if plan.steps:
                st.session_state.analysis_state["steps"] = [
                    {"type": s.type, "description": s.description,
                     "params": s.params, "status": s.status}
                    for s in plan.steps
                ]
                st.session_state.analysis_state["current_step"] = 0

            st.session_state.agent.chat_history = st.session_state.chat_history

            if "project_id" in st.session_state:
                pm = ProjectManager()
                pm.save_chat_history(st.session_state.project_id,
                                     st.session_state.chat_history)

            st.rerun()

    with center_col:
        st.subheader("📈 结果")

        if "last_result" in st.session_state:
            result = st.session_state.last_result
            if result.get("llm_explanation"):
                with st.container(border=True):
                    st.markdown(f"🤖 **AI 解读:** {result['llm_explanation']}")
            if result.get("text"):
                st.markdown(result["text"])
            if result.get("charts"):
                for chart in result["charts"]:
                    st.plotly_chart(chart, use_container_width=True)
            if result.get("dataframe") is not None:
                st.dataframe(result["dataframe"], use_container_width=True)

    with right_col:
        st.subheader("📋 分析步骤")

        steps = st.session_state.analysis_state.get("steps", [])
        if not steps:
            st.info("在对话区描述你的分析需求，Agent 将为你规划步骤。")
            return

        for i, step in enumerate(steps):
            status_icon = {"pending": "○", "running": "⟳", "done": "✓", "error": "✗"}
            icon = status_icon.get(step.get("status", "pending"), "○")

            col_s, col_b = st.columns([4, 1])
            with col_s:
                st.markdown(f"{icon} **步骤 {i+1}**: {step['description'][:30]}...")
            with col_b:
                if step["status"] == "pending" and st.button("▶", key=f"run_{i}"):
                    execute_step(i, step, df)

        if steps and all(s.get("status") == "done" for s in steps):
            st.success("所有步骤已完成！前往「报告导出」生成报告。")


def execute_step(step_index: int, step_def: dict, df):
    step_type = step_def["type"]
    params = step_def.get("params", {})
    text = ""
    charts = []
    result_df = df
    metrics_for_llm = {}

    try:
        if step_type == "clean":
            result_df, summary = clean_pipeline(df, **params)
            text = f"### 数据清洗完成\n```json\n{json.dumps(summary, ensure_ascii=False, indent=2)}\n```"
            metrics_for_llm = summary

        elif step_type == "eda":
            numeric_cols = params.get("columns") or df.select_dtypes(include=["number"]).columns.tolist()
            result = eda_pipeline(df, numeric_columns=numeric_cols)
            charts = result["charts"]
            text = f"### 探索性分析\n- 行数: {result['row_count']}\n- 列数: {result['column_count']}"
            stats_summary = {}
            for k, v in result.get("stats_summary", {}).items():
                stats_summary[k] = str(v)
            metrics_for_llm = {
                "行数": result["row_count"],
                "列数": result["column_count"],
                "统计摘要": stats_summary,
            }

        elif step_type == "model":
            target = params.get("target", "")
            model_type = params.get("model_type", "linear")
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            if target in numeric_cols:
                numeric_cols.remove(target)
            model_df = df[numeric_cols + [target]].dropna()
            X_train, X_test, y_train, y_test = split_data(model_df, target)
            model, train_info = train_regression(X_train, y_train, model_type)
            metrics = evaluate_regression(model, X_test, y_test)
            _, imp_fig = feature_importance(model, numeric_cols)
            charts.append(imp_fig)
            y_pred = model.predict(X_test)
            res_fig = residual_plot(y_test, y_pred)
            charts.append(res_fig)
            text = f"### 建模结果 ({model_type})\n"
            for k, v in metrics.items():
                text += f"- {k}: {v}\n"
            metrics_for_llm = metrics

        elif step_type == "report":
            text = "报告生成请前往「报告导出」页面。"
            metrics_for_llm = {}

        # --- LLM 流式解读（失败时 fallback 到非流式）---
        explanation_text = ""
        if metrics_for_llm and "agent" in st.session_state:
            agent_step = AnalysisStep(
                id=step_index + 1,
                type=step_type,
                description=step_def["description"],
            )
            try:
                with st.spinner("AI 正在解读结果..."):
                    explanation_text = st.write_stream(
                        st.session_state.agent.explain_result_stream(agent_step, metrics_for_llm)
                    )
            except Exception:
                pass

            if not explanation_text:
                try:
                    explanation_text = st.session_state.agent.explain_result(
                        agent_step, metrics_for_llm
                    )
                except Exception:
                    pass
        # --- 解读结束 ---

        st.session_state.analysis_state["steps"][step_index]["status"] = "done"
        st.session_state.analysis_state["steps"][step_index]["llm_explanation"] = explanation_text
        st.session_state.last_result = {
            "text": text, "charts": charts,
            "dataframe": result_df.head(50) if result_df is not None else None,
            "llm_explanation": explanation_text,
        }

        if "project_id" in st.session_state:
            pm = ProjectManager()
            pm.save_state(st.session_state.project_id, st.session_state.analysis_state)
            for j, chart in enumerate(charts):
                pm.save_chart(st.session_state.project_id,
                              f"step{step_index+1}_chart{j+1}", chart)

    except Exception as e:
        st.session_state.analysis_state["steps"][step_index]["status"] = "error"
        st.session_state.last_result = {"text": f"执行出错: {str(e)}", "charts": [], "dataframe": None, "llm_explanation": ""}

    st.rerun()
