"""分析对话页面"""
import streamlit as st
import json
import os
import logging
import pandas as pd
from engine.data_loader import get_data_info
from engine.config import load_config
from engine.llm_agent import LLMAdapter, AnalysisAgent, AnalysisStep
from engine.step_executor import execute_step
from engine.project_manager import ProjectManager
from engine.reporter import generate_html_report, build_section

logger = logging.getLogger(__name__)


def show():
    st.title("🔬 分析对话")

    # --- 未打开项目 ---
    if "project_id" not in st.session_state:
        st.warning("请先新建项目，或从侧边栏「📁 历史项目」中打开已有项目。")
        return

    pm = ProjectManager()
    project_id = st.session_state.project_id
    project_name = st.session_state.get("project_name", "")

    # --- 项目信息弹窗 ---
    @st.dialog("📋 项目信息")
    def show_project_info():
        try:
            info = pm.get_project_info(project_id)
            st.metric("项目名称", info["name"])
            c1, c2 = st.columns(2)
            c1.metric("创建时间", info["created_at"][:19])
            c2.metric("分析步骤", f"{info['steps_count']} 个")
            c1.metric("数据文件", f"{info['data_files_count']} 个")
            c2.metric("总行数", f"{info['total_rows']:,}")
            st.metric("报告数", f"{info['reports_count']} 个")
        except Exception as e:
            st.error(f"无法加载项目信息: {e}")

    # --- 上传数据弹窗 ---
    @st.dialog("📤 追加数据")
    def show_upload_dialog():
        st.caption(f"新数据将与 **{project_name}** 已有数据按列名匹配、按行拼接")
        uploaded = st.file_uploader("选择数据文件", type=["csv", "xlsx", "xls"], key="dialog_uploader")
        if uploaded:
            tmp_path = f"temp_{uploaded.name}"
            with open(tmp_path, "wb") as f:
                f.write(uploaded.getbuffer())
            try:
                pm.add_data(project_id, tmp_path)
                data_files = pm.list_data_files(project_id)
                st.session_state.selected_data_files = [f["name"] for f in data_files]
                st.success(f"已追加: {uploaded.name}")
                st.info("数据已追加，请重新描述分析需求以使用新数据。")
            except Exception as e:
                st.error(f"追加失败: {e}")
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

    # --- 报告导出弹窗 ---
    @st.dialog("📋 导出分析报告")
    def show_report_dialog():
        report_title = st.text_input("报告标题", value=f"{project_name} — 分析报告")

        analysis_state = st.session_state.get("analysis_state", {})
        all_steps = analysis_state.get("steps", [])
        done_steps = [s for s in all_steps if s.get("status") == "done"]

        st.caption("包含内容:")
        include_steps = []
        for i, s in enumerate(done_steps):
            desc = s.get("description", f"步骤{i+1}")[:50]
            if st.checkbox(desc, value=True, key=f"inc_step_{i}"):
                include_steps.append(s)

        include_conclusion = st.checkbox("AI 综合分析结论", value=True, key="inc_conclusion")

        user_notes = st.text_area("工程师补充观点", placeholder="输入你的分析观点，AI 会结合这些生成结论...", height=80,
                                  key="report_user_notes")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("取消", width="stretch", key="report_cancel"):
                st.rerun()
        with col2:
            btn_disabled = len(include_steps) == 0
            if st.button("🤖 AI 结论并预览", type="primary", width="stretch",
                        disabled=btn_disabled, key="report_ai_preview"):
                if include_steps and "agent" in st.session_state:
                    step_data = [{"type": s["type"], "explanation": s.get("llm_explanation", "")}
                               for s in include_steps]
                    with st.spinner("AI 正在汇总..."):
                        conclusion_text = st.write_stream(
                            st.session_state.agent.summarize_conclusions(step_data, user_notes)
                        )
                    st.session_state.conclusion_text = conclusion_text
                st.session_state.report_preview_mode = True
                st.session_state.report_title = report_title
                st.session_state.report_include_steps = include_steps
                st.rerun()
        with col3:
            if st.button("⬇ 导出 HTML", width="stretch", disabled=btn_disabled, key="report_export"):
                sections = []
                for s in include_steps:
                    chart_html = _load_chart_html(pm, project_id, s, all_steps)
                    sections.append(build_section(
                        title=s.get("description", ""),
                        text=s.get("llm_explanation", ""),
                        chart_html=chart_html,
                    ))
                df = st.session_state.get("df", pd.DataFrame())
                html = generate_html_report(
                    title=report_title,
                    sections=sections,
                    conclusion=st.session_state.get("conclusion_text", "分析完成"),
                    data_source=project_name,
                    rows=len(df),
                    cols=len(df.columns),
                )
                report_path = pm.save_report(project_id, html)
                st.success(f"报告已保存: {report_path}")
                with open(report_path, "r", encoding="utf-8") as f:
                    st.download_button(
                        "下载 HTML", f.read(), f"{project_name}_report.html", "text/html",
                        key="report_dl",
                    )

    # --- 工具栏 ---
    col_info, col_data, col_btns = st.columns([2, 3, 2])
    with col_info:
        if st.button(f"📊 {project_name}", key="proj_info_btn", help="点击查看项目信息"):
            show_project_info()
    with col_data:
        try:
            data_files = pm.list_data_files(project_id)
        except Exception:
            data_files = []
        selected = st.session_state.get("selected_data_files", [f["name"] for f in data_files])
        total_rows = sum(f["rows"] for f in data_files if f["name"] in selected)
        st.caption(f"数据: {len(selected)}/{len(data_files)} 个文件 · {total_rows:,} 行")
    with col_btns:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📤 上传新数据", width="stretch", key="toolbar_upload"):
                show_upload_dialog()
        with c2:
            if st.button("📋 导出报告", type="primary", width="stretch", key="toolbar_report"):
                show_report_dialog()

    # --- 检查 show_upload_dialog flag ---
    if st.session_state.get("show_upload_dialog"):
        st.session_state.show_upload_dialog = False
        show_upload_dialog()

    st.divider()

    # --- 报告预览模式 ---
    if st.session_state.get("report_preview_mode"):
        _show_report_preview(pm, project_id)
        return

    # --- 数据加载 ---
    df = st.session_state.get("df")
    if df is None and selected:
        try:
            df = pm.merge_selected_data(project_id, selected)
            st.session_state.df = df
            st.session_state.data_info = get_data_info(df)
        except Exception:
            st.warning("无法加载数据，请在侧边栏「📂 数据列表」中选择数据文件。")
            return

    if df is None:
        st.warning("请在侧边栏「📂 数据列表」中选择至少一个数据文件。")
        return

    data_info = st.session_state.get("data_info", get_data_info(df))

    # --- Agent 初始化 ---
    if "agent" not in st.session_state:
        config = st.session_state.get("config", load_config())
        adapter = LLMAdapter(config.llm)
        st.session_state.agent = AnalysisAgent(adapter)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "analysis_state" not in st.session_state:
        st.session_state.analysis_state = {"steps": [], "current_step": 0}
    if "viewing_step_index" not in st.session_state:
        st.session_state.viewing_step_index = -1

    # --- 三栏布局 ---
    left_col, center_col, right_col = st.columns([0.25, 0.5, 0.25])

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
                st.session_state.viewing_step_index = -1
            st.session_state.agent.set_chat_history(st.session_state.chat_history)
            pm.save_chat_history(project_id, st.session_state.chat_history)
            st.rerun()

    with center_col:
        st.subheader("📈 结果")
        result_container = st.container(height=520)
        with result_container:
            steps = st.session_state.analysis_state.get("steps", [])
            viewing_idx = st.session_state.get("viewing_step_index", -1)

            if viewing_idx >= 0 and viewing_idx < len(steps):
                step = steps[viewing_idx]
                if step.get("llm_explanation"):
                    with st.container(border=True):
                        st.markdown(f"🤖 **AI 解读:** {step['llm_explanation']}")
                if step.get("last_text"):
                    st.markdown(step["last_text"])
                if step.get("last_charts"):
                    for j, chart in enumerate(step["last_charts"]):
                        st.plotly_chart(chart, width="stretch", key=f"hist_chart_{viewing_idx}_{j}")
            elif "last_result" in st.session_state:
                result = st.session_state.last_result
                if result.get("llm_explanation"):
                    with st.container(border=True):
                        st.markdown(f"🤖 **AI 解读:** {result['llm_explanation']}")
                if result.get("text"):
                    st.markdown(result["text"])
                if result.get("charts"):
                    for i, chart in enumerate(result["charts"]):
                        st.plotly_chart(chart, width="stretch", key=f"curr_chart_{i}")
                if result.get("dataframe") is not None:
                    st.dataframe(result["dataframe"], width="stretch")
            else:
                st.info("在对话区描述你的分析需求，Agent 将为你规划步骤。")

    with right_col:
        st.subheader("📋 分析步骤")
        steps_container = st.container(height=520)
        with steps_container:
            steps = st.session_state.analysis_state.get("steps", [])
            if not steps:
                st.info("暂无分析步骤")
            else:
                _render_steps(steps, df, pm)


def _render_steps(steps, df, pm):
    for i, step in enumerate(steps):
        status = step.get("status", "pending")
        status_icon = {"pending": "○", "running": "⟳", "done": "✓", "error": "✗"}
        icon = status_icon.get(status, "○")

        is_viewing = (i == st.session_state.viewing_step_index)
        bg = "#e8f0fe" if is_viewing else "transparent"
        border = "#1a73e8" if is_viewing else "#e0e0e0"

        st.markdown(
            f"<div style='padding:6px 8px;margin:2px 0;border-left:3px solid {border};"
            f"background:{bg};border-radius:4px;font-size:13px;'>"
            f"{icon} <b>步骤 {i+1}</b>: {step['description'][:30]}...</div>",
            unsafe_allow_html=True,
        )

        if status == "done" or status == "pending":
            c_act, c_view = st.columns([1, 1])
            with c_act:
                if status == "pending" and st.button("▶", key=f"run_{i}"):
                    _execute_step(i, step, df, pm)
            with c_view:
                if status == "done" and st.button("查看", key=f"view_{i}"):
                    st.session_state.viewing_step_index = i
                    st.rerun()

    if steps and all(s.get("status") == "done" for s in steps):
        st.success("所有步骤已完成！点击「📋 导出报告」生成报告。")


def _load_chart_html(pm, project_id, step, all_steps):
    """从磁盘加载步骤关联的图表 HTML"""
    try:
        step_idx = all_steps.index(step)
    except (ValueError, IndexError):
        return ""
    chart_html = ""
    chart_dir = os.path.join("projects", project_id, "charts")
    j = 1
    while True:
        chart_path = os.path.join(chart_dir, f"step{step_idx+1}_chart{j}.html")
        if os.path.exists(chart_path):
            with open(chart_path, "r", encoding="utf-8") as f:
                chart_html += f.read()
            j += 1
        else:
            break
    return chart_html


def _show_report_preview(pm, project_id):
    """显示报告预览"""
    st.subheader("📋 报告预览")

    include_steps = st.session_state.get("report_include_steps", [])
    report_title = st.session_state.get("report_title", "分析报告")
    project_name = st.session_state.get("project_name", "")
    conclusion = st.session_state.get("conclusion_text", "")

    sections = []
    all_steps = st.session_state.analysis_state.get("steps", [])
    for s in include_steps:
        chart_html = _load_chart_html(pm, project_id, s, all_steps)
        sections.append(build_section(
            title=s.get("description", ""),
            text=s.get("llm_explanation", ""),
            chart_html=chart_html,
        ))

    df = st.session_state.get("df", pd.DataFrame())
    rows, cols = (len(df), len(df.columns)) if df is not None else (0, 0)
    html = generate_html_report(
        title=report_title, sections=sections, conclusion=conclusion or "分析完成",
        data_source=project_name, rows=rows, cols=cols,
    )

    with st.expander("报告预览", expanded=True):
        st.components.v1.html(html, height=600, scrolling=True)

    c_back, c_dl = st.columns(2)
    with c_back:
        if st.button("← 返回分析", width="stretch"):
            st.session_state.report_preview_mode = False
            st.session_state.pop("preview_report_path", None)
            st.rerun()
    with c_dl:
        if "preview_report_path" not in st.session_state:
            st.session_state.preview_report_path = pm.save_report(project_id, html)
        with open(st.session_state.preview_report_path, "r", encoding="utf-8") as f:
            st.download_button(
                "⬇ 下载 HTML", f.read(), f"{project_name}_report.html",
                "text/html", width="stretch",
            )


def _execute_step(step_index: int, step_def: dict, df, pm):
    """执行分析步骤"""
    step_type = step_def["type"]
    params = step_def.get("params", {})
    text = ""
    charts = []
    result_df = df
    metrics_for_llm = {}

    try:
        result = execute_step(step_type, params, df)
        text = result["text"]
        charts = result["charts"]
        result_df = result["result_df"]
        metrics_for_llm = result["metrics"]

        # LLM 解读
        explanation_text = ""
        if metrics_for_llm and "agent" in st.session_state:
            agent_step = AnalysisStep(id=step_index + 1, type=step_type, description=step_def.get("description", ""))
            try:
                with st.spinner("AI 正在解读结果..."):
                    explanation_text = st.write_stream(
                        st.session_state.agent.explain_result_stream(agent_step, metrics_for_llm)
                    )
            except Exception:
                logger.warning("AI 流式解读失败，尝试同步解读")
            if not explanation_text:
                try:
                    explanation_text = st.session_state.agent.explain_result(agent_step, metrics_for_llm)
                except Exception:
                    logger.warning("AI 解读失败")
                    st.warning("AI 解读暂时不可用，分析结果仍可查看。")

        st.session_state.analysis_state["steps"][step_index]["status"] = "done"
        st.session_state.analysis_state["steps"][step_index]["llm_explanation"] = explanation_text
        st.session_state.analysis_state["steps"][step_index]["last_text"] = text
        st.session_state.analysis_state["steps"][step_index]["last_charts"] = charts
        st.session_state.last_result = {
            "text": text, "charts": charts,
            "dataframe": result_df.head(50) if result_df is not None else None,
            "llm_explanation": explanation_text,
        }
        st.session_state.viewing_step_index = -1

        if "project_id" in st.session_state:
            pm.save_state(st.session_state.project_id, st.session_state.analysis_state)
            for j, chart in enumerate(charts):
                pm.save_chart(st.session_state.project_id, f"step{step_index+1}_chart{j+1}", chart)

    except Exception as e:
        st.session_state.analysis_state["steps"][step_index]["status"] = "error"
        st.session_state.last_result = {"text": f"执行出错: {str(e)}", "charts": [], "dataframe": None, "llm_explanation": ""}

    st.rerun()
