"""报告导出页面"""
import os
import streamlit as st
from engine.reporter import generate_html_report, build_section
from engine.project_manager import ProjectManager


def show():
    st.title("📋 报告导出")
    if "project_name" in st.session_state:
        st.info(f"📊 当前项目: **{st.session_state.project_name}**")

    if "project_id" not in st.session_state:
        st.warning("请先创建分析项目。")
        return

    df = st.session_state.get("df")
    project_name = st.session_state.get("project_name", "未命名项目")
    project_id = st.session_state.get("project_id")

    report_title = st.text_input("报告标题", value=f"{project_name} — 分析报告")

    pm = ProjectManager()
    sections = []
    analysis_state = st.session_state.get("analysis_state", {})
    for i, step in enumerate(analysis_state.get("steps", [])):
        if step["status"] == "done":
            explanation = step.get("llm_explanation", "")
            if not explanation:
                explanation = f"步骤类型: {step['type']}"

            # 从磁盘加载该步骤的图表
            chart_html = ""
            chart_dir = os.path.join("projects", project_id, "charts")
            j = 1
            while True:
                chart_path = os.path.join(chart_dir, f"step{i+1}_chart{j}.html")
                if os.path.exists(chart_path):
                    with open(chart_path, "r", encoding="utf-8") as f:
                        chart_html += f.read()
                    j += 1
                else:
                    break

            sections.append(build_section(
                title=step["description"],
                text=explanation,
                chart_html=chart_html,
            ))

    if "last_result" in st.session_state and st.session_state.last_result.get("llm_explanation"):
        last_exp = st.session_state.last_result["llm_explanation"]
        already_included = any(
            s.get("llm_explanation") == last_exp
            for s in analysis_state.get("steps", [])
        )
        if not already_included:
            sections.append(build_section(
                title="最新结果解读",
                text=last_exp,
            ))

    # --- AI 自动汇总结论 ---
    if "conclusion_text" not in st.session_state:
        st.session_state.conclusion_text = ""

    st.subheader("🤖 AI 综合结论")

    col_ai, col_user = st.columns([2, 1])
    with col_user:
        user_notes = st.text_area(
            "工程师补充观点",
            placeholder="输入你的分析观点，AI 会结合这些生成结论...",
            height=120,
            key="user_notes_input",
        )

    with col_ai:
        done_steps = [
            {"type": s["type"], "explanation": s.get("llm_explanation", "")}
            for s in analysis_state.get("steps", [])
            if s["status"] == "done"
        ]
        if st.button("生成 AI 结论", type="primary", disabled=not done_steps):
            if "agent" in st.session_state and done_steps:
                with st.spinner("AI 正在汇总分析结论..."):
                    conclusion_text = st.write_stream(
                        st.session_state.agent.summarize_conclusions(done_steps, user_notes)
                    )
                    st.session_state.conclusion_text = conclusion_text
            else:
                st.warning("请先完成至少一个分析步骤。")

    conclusion = st.text_area(
        "分析结论",
        value=st.session_state.conclusion_text,
        placeholder="点击「生成 AI 结论」自动生成，或手动填写...",
        height=150,
        key="conclusion_editor",
    )
    # --- 结论区域结束 ---

    if st.button("生成报告", type="primary"):
        rows, cols = df.shape if df is not None else (0, 0)
        html = generate_html_report(
            title=report_title,
            sections=sections,
            conclusion=conclusion or "分析完成",
            data_source=project_name,
            rows=rows,
            cols=cols,
        )

        report_path = pm.save_report(project_id, html)
        st.success(f"报告已生成: {report_path}")

        with st.expander("报告预览"):
            st.components.v1.html(html, height=600, scrolling=True)

        with open(report_path, "r", encoding="utf-8") as f:
            st.download_button(
                "下载报告 (HTML)",
                data=f.read(),
                file_name=f"{project_name}_report.html",
                mime="text/html",
            )
