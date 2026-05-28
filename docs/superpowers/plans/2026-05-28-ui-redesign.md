# UI 布局美化 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 精简侧边栏导航至 3 项 + 3 个折叠面板，报告导出改为弹窗，支持项目内追加数据和多数据源勾选分析

**Architecture:** 核心改动在 engine/project_manager.py（数据文件管理方法）和 streamlit-app/app.py（侧边栏重写）。各页面视图配合调整：新建项目页替代数据上传页，分析对话页加入工具栏和弹窗，报告页改为从分析页调起的弹窗+预览模式，历史项目页删除。

**Tech Stack:** Python, Streamlit (@st.dialog), Plotly, Pandas

---

## 文件影响

| 文件 | 操作 | 职责 |
|------|------|------|
| `engine/project_manager.py` | 修改 | 新增 add_data, list_data_files, merge_selected_data, list_reports, get_project_info |
| `streamlit-app/app.py` | 重写 | 3 导航 + 3 折叠面板侧边栏 |
| `streamlit-app/views/analysis.py` | 重写 | 工具栏 + 步骤切换 + 上传/报告弹窗 + 报告预览模式 |
| `streamlit-app/views/report.py` | 删除 | 不再独立成页 |
| `streamlit-app/views/data_upload.py` | 重写为 new_project.py | 新建项目页 |
| `streamlit-app/views/history.py` | 删除 | 功能移入侧边栏 |
| `streamlit-app/views/settings.py` | 微调 | 保持现有功能 |

---

### Task 1: engine/project_manager.py — 数据文件管理方法

**Files:** Modify `engine/project_manager.py`

在 ProjectManager 类末尾新增以下方法：

```python
def add_data(self, project_id: str, file_path: str) -> str:
    """向项目追加数据文件，按列名匹配拼接到已有数据末尾。返回存储路径。"""
    import shutil
    pdir = self.projects_dir / project_id / "data"
    existing_files = list(pdir.glob("data_*.csv"))
    new_index = len(existing_files) + 1
    dest = pdir / f"data_{new_index}.csv"
    new_df = pd.read_csv(file_path) if file_path.endswith(".csv") else pd.read_excel(file_path)
    new_df.to_csv(dest, index=False)
    return str(dest)

def list_data_files(self, project_id: str) -> list[dict]:
    """列出项目所有数据文件，返回 [{name, path, rows}]"""
    pdir = self.projects_dir / project_id / "data"
    files = []
    for f in sorted(pdir.glob("data_*.csv")):
        df = pd.read_csv(f)
        files.append({"name": f.name, "path": str(f), "rows": len(df)})
    return files

def merge_selected_data(self, project_id: str, selected_files: list[str]) -> "pd.DataFrame":
    """按勾选文件名列表，合并数据（按列名匹配，按行拼接）"""
    pdir = self.projects_dir / project_id / "data"
    dfs = []
    for fname in selected_files:
        fpath = pdir / fname
        if fpath.exists():
            dfs.append(pd.read_csv(fpath))
    if not dfs:
        raise ValueError("没有找到选中的数据文件")
    return pd.concat(dfs, ignore_index=True)

def list_reports(self, project_id: str) -> list[dict]:
    """列出项目所有报告，返回 [{name, path, created_at}]"""
    pdir = self.projects_dir / project_id / "reports"
    reports = []
    for f in sorted(pdir.glob("report_*.html"), reverse=True):
        stat = f.stat()
        reports.append({
            "name": f.name,
            "path": str(f),
            "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
        })
    return reports

def get_project_info(self, project_id: str) -> dict:
    """获取项目元信息"""
    pdir = self.projects_dir / project_id
    with open(pdir / "meta.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    data_files = self.list_data_files(project_id)
    total_rows = sum(f["rows"] for f in data_files)
    reports = self.list_reports(project_id)
    state_path = pdir / "state.json"
    steps_count = 0
    if state_path.exists():
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
            steps_count = len(state.get("steps", []))
    return {
        "name": meta["name"],
        "created_at": meta["created_at"],
        "data_files_count": len(data_files),
        "total_rows": total_rows,
        "steps_count": steps_count,
        "reports_count": len(reports),
    }
```

- [ ] **Step 1:** 在 `engine/project_manager.py` 末尾添加 5 个方法
- [ ] **Step 2:** `python -c "from engine.project_manager import ProjectManager; print('OK')"`
- [ ] **Step 3:** Commit

---

### Task 2: streamlit-app/app.py — 侧边栏重写

**Files:** 重写 `streamlit-app/app.py`

```python
"""数据科学家 Agent — Streamlit 版"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

st.set_page_config(
    page_title="数据科学家 Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    st.sidebar.title("📊 数据科学家 Agent")

    if "config" not in st.session_state:
        from engine.config import load_config
        st.session_state.config = load_config()

    # --- 主导航 (3 项) ---
    page = st.sidebar.radio(
        "导航",
        ["🆕 新建项目", "🔬 分析对话", "⚙ 设置"],
        label_visibility="collapsed",
    )

    st.sidebar.divider()

    # --- 当前项目 ---
    if "project_name" in st.session_state:
        st.sidebar.caption(f"当前项目: {st.session_state.project_name}")

    # --- 折叠面板: 数据列表 ---
    if "project_id" in st.session_state:
        from engine.project_manager import ProjectManager
        pm = ProjectManager()

        with st.sidebar.expander("📂 数据列表", expanded=False):
            data_files = pm.list_data_files(st.session_state.project_id)
            if not data_files:
                st.caption("暂无数据，请上传")
            else:
                if "selected_data_files" not in st.session_state:
                    st.session_state.selected_data_files = [f["name"] for f in data_files]

                col_all, col_none = st.columns(2)
                with col_all:
                    if st.button("全选", key="select_all", use_container_width=True):
                        st.session_state.selected_data_files = [f["name"] for f in data_files]
                        st.rerun()
                with col_none:
                    if st.button("取消全选", key="select_none", use_container_width=True):
                        st.session_state.selected_data_files = []
                        st.rerun()

                selected = []
                for f in data_files:
                    checked = st.checkbox(
                        f"{f['name']} ({f['rows']:,} 行)",
                        value=f["name"] in st.session_state.selected_data_files,
                        key=f"data_chk_{f['name']}",
                    )
                    if checked:
                        selected.append(f["name"])
                st.session_state.selected_data_files = selected

                if selected:
                    total_rows = sum(f["rows"] for f in data_files if f["name"] in selected)
                    st.caption(f"已选 {len(selected)} 个文件，合计 {total_rows:,} 行")
                else:
                    st.warning("请至少选择一个数据文件")

            if st.button("+ 上传新数据", key="upload_from_sidebar", use_container_width=True):
                st.session_state.show_upload_dialog = True
                st.rerun()

        # --- 折叠面板: 历史项目 ---
        with st.sidebar.expander("📁 历史项目", expanded=False):
            projects = pm.list_projects()
            if not projects:
                st.caption("暂无项目")
            else:
                for proj in projects:
                    is_current = proj["id"] == st.session_state.get("project_id")
                    btn_style = f"**{proj['name']}**" if is_current else proj["name"]
                    if st.button(
                        f"{'📊' if is_current else '📁'} {proj['name']}",
                        key=f"hist_{proj['id']}",
                        use_container_width=True,
                        help=f"创建: {proj['created_at'][:10]}",
                    ):
                        if not is_current:
                            project_data = pm.load_project(proj['id'])
                            st.session_state.project_id = proj['id']
                            st.session_state.project_name = proj['name']
                            st.session_state.df = project_data["dataframe"]
                            st.session_state.chat_history = project_data["chat_history"]
                            st.session_state.analysis_state = project_data["state"]
                            data_files = pm.list_data_files(proj['id'])
                            st.session_state.selected_data_files = [f["name"] for f in data_files]
                            if "conclusion_text" in st.session_state:
                                del st.session_state.conclusion_text
                            st.rerun()

        # --- 折叠面板: 历史报告 ---
        if "project_id" in st.session_state:
            with st.sidebar.expander("📋 历史报告", expanded=False):
                reports = pm.list_reports(st.session_state.project_id)
                if not reports:
                    st.caption("暂无报告")
                else:
                    for r in reports:
                        if st.button(
                            f"📄 {r['name']}",
                            key=f"report_{r['name']}",
                            use_container_width=True,
                            help=r["created_at"],
                        ):
                            import webbrowser
                            webbrowser.open(r["path"])
                            st.success(f"已在浏览器中打开: {r['name']}")

    # --- 页面路由 ---
    if page == "🆕 新建项目":
        from views import new_project
        new_project.show()
    elif page == "🔬 分析对话":
        from views import analysis
        analysis.show()
    elif page == "⚙ 设置":
        from views import settings
        settings.show()


if __name__ == "__main__":
    main()
```

- [ ] **Step 1:** 用以上代码完全替换 `streamlit-app/app.py`
- [ ] **Step 2:** `python -c "compile(open('D:/PythonFile/project1/streamlit-app/app.py', encoding='utf-8').read(), 'app.py', 'exec'); print('Syntax OK')"`
- [ ] **Step 3:** Commit

---

### Task 3: views/data_upload.py → views/new_project.py 重写

**Files:** 创建 `streamlit-app/views/new_project.py`，删除 `streamlit-app/views/data_upload.py`

`new_project.py` 内容:

```python
"""新建项目页面"""
import streamlit as st
import os
from engine.data_loader import load_file, get_data_info
from engine.project_manager import ProjectManager


def show():
    st.title("🆕 新建项目")
    if "project_name" in st.session_state:
        st.info(f"📊 当前项目: **{st.session_state.project_name}**")

    project_name = st.text_input("项目名称", placeholder="输入项目名称...")
    uploaded_file = st.file_uploader(
        "上传数据文件",
        type=["csv", "xlsx", "xls", "json", "tsv"],
        help="支持 CSV、Excel、JSON 格式。必须上传数据才能创建项目。",
    )

    if uploaded_file is not None:
        tmp_path = f"temp_{uploaded_file.name}"
        with open(tmp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        try:
            df = load_file(tmp_path)
            st.subheader("数据预览")
            st.dataframe(df.head(50), use_container_width=True)

            info = get_data_info(df)
            col_a, col_b, col_c, col_d = st.columns(4)
            col_a.metric("行数", info["shape"][0])
            col_b.metric("列数", info["shape"][1])
            col_c.metric("数值列", len(info["numeric_columns"]))
            col_d.metric("分类型列", len(info["categorical_columns"]))

            with st.expander("列详情"):
                for col_name in info["columns"]:
                    dtype = info["dtypes"].get(col_name, "unknown")
                    missing = info["missing_pct"].get(col_name, 0)
                    st.text(f"{col_name} ({dtype}) — 缺失 {missing}%")

            if project_name and st.button("创建并开始分析", type="primary"):
                pm = ProjectManager()
                project_id = pm.create_project(project_name)

                data_path = os.path.join("projects", project_id, "data", "original.csv")
                df.to_csv(data_path, index=False)

                st.session_state.project_id = project_id
                st.session_state.project_name = project_name
                st.session_state.df = df
                st.session_state.data_info = info
                st.session_state.selected_data_files = ["original.csv"]
                st.session_state.chat_history = []
                st.session_state.analysis_state = {"steps": [], "current_step": 0}
                if "conclusion_text" in st.session_state:
                    del st.session_state.conclusion_text
                st.success(f"项目 '{project_name}' 创建成功！正在进入分析对话...")
                st.rerun()

        finally:
            os.unlink(tmp_path)
    else:
        if st.button("创建并开始分析", type="primary", disabled=True):
            pass
        if not uploaded_file:
            st.caption("请先上传数据文件")
```

- [ ] **Step 1:** 创建 `streamlit-app/views/new_project.py`
- [ ] **Step 2:** `python -c "compile(open('D:/PythonFile/project1/streamlit-app/views/new_project.py', encoding='utf-8').read(), 'new_project.py', 'exec'); print('Syntax OK')"`
- [ ] **Step 3:** 删除 `streamlit-app/views/data_upload.py`
- [ ] **Step 4:** Commit

---

### Task 4: views/analysis.py — 重写（工具栏 + 步骤切换 + 弹窗 + 报告预览）

**Files:** 重写 `streamlit-app/views/analysis.py`

这是最复杂的改动。完整代码：

```python
"""分析对话页面"""
import streamlit as st
import json
import os
from engine.data_loader import get_data_info
from engine.config import load_config
from engine.llm_agent import LLMAdapter, AnalysisAgent, AnalysisStep
from engine.data_cleaner import clean_pipeline
from engine.eda import eda_pipeline
from engine.modeler import train_regression, evaluate_regression, split_data, feature_importance, residual_plot
from engine.project_manager import ProjectManager
from engine.reporter import generate_html_report, build_section


def show():
    st.title("🔬 分析对话")

    # --- 未打开项目 ---
    if "project_id" not in st.session_state:
        st.warning("请先新建项目，或从侧边栏「📁 历史项目」中打开已有项目。")
        return

    pm = ProjectManager()
    project_id = st.session_state.project_id

    # --- 项目信息弹窗 ---
    @st.dialog("📋 项目信息")
    def show_project_info():
        info = pm.get_project_info(project_id)
        st.metric("项目名称", info["name"])
        st.metric("创建时间", info["created_at"][:19])
        st.metric("数据文件", f"{info['data_files_count']} 个")
        st.metric("总行数", f"{info['total_rows']:,}")
        st.metric("分析步骤", f"{info['steps_count']} 个")
        st.metric("报告数", f"{info['reports_count']} 个")

    # --- 上传数据弹窗 ---
    @st.dialog("📤 追加数据")
    def show_upload_dialog():
        project_name = st.session_state.get("project_name", "")
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
            finally:
                os.unlink(tmp_path)

    # --- 报告导出弹窗 ---
    @st.dialog("📋 导出分析报告")
    def show_report_dialog():
        project_name = st.session_state.get("project_name", "未命名项目")
        report_title = st.text_input("报告标题", value=f"{project_name} — 分析报告")
        
        analysis_state = st.session_state.get("analysis_state", {})
        done_steps = [s for s in analysis_state.get("steps", []) if s["status"] == "done"]
        st.caption("包含内容:")
        include_steps = []
        for s in done_steps:
            if st.checkbox(f"步骤: {s['description'][:40]}", value=True, key=f"inc_{id(s)}"):
                include_steps.append(s)
        include_conclusion = st.checkbox("AI 综合分析结论", value=True)

        user_notes = st.text_area("工程师补充观点", placeholder="输入你的分析观点...", height=80)

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("取消", use_container_width=True):
                st.rerun()
        with col2:
            if st.button("🤖 AI 结论并预览", type="primary", use_container_width=True,
                        disabled=not include_steps):
                step_data = [{"type": s["type"], "explanation": s.get("llm_explanation", "")}
                           for s in include_steps]
                if "agent" in st.session_state and step_data:
                    conclusion_text = ""
                    for chunk in st.session_state.agent.summarize_conclusions(step_data, user_notes):
                        conclusion_text += chunk
                    st.session_state.conclusion_text = conclusion_text
                st.session_state.report_preview_mode = True
                st.session_state.report_title = report_title
                st.session_state.report_include_steps = include_steps
                st.rerun()
        with col3:
            if st.button("⬇ 导出 HTML", use_container_width=True, disabled=not include_steps):
                sections = []
                for s in include_steps:
                    chart_html = _load_chart_html(pm, project_id, s, done_steps)
                    sections.append(build_section(
                        title=s["description"],
                        text=s.get("llm_explanation", ""),
                        chart_html=chart_html,
                    ))
                html = generate_html_report(
                    title=report_title,
                    sections=sections,
                    conclusion=st.session_state.get("conclusion_text", "分析完成"),
                    data_source=project_name,
                    rows=len(st.session_state.get("df", pd.DataFrame())),
                    cols=len(st.session_state.get("df", pd.DataFrame()).columns) if st.session_state.get("df") is not None else 0,
                )
                report_path = pm.save_report(project_id, html)
                st.success(f"报告已保存: {report_path}")
                with open(report_path, "r", encoding="utf-8") as f:
                    st.download_button("下载 HTML", f.read(), f"{project_name}_report.html", "text/html")

    # --- 工具栏 ---
    col_title, col_info, col_data, col_btns = st.columns([2, 1, 2, 2])
    with col_title:
        pass  # title already at top
    with col_info:
        if st.button(f"📊 {st.session_state.project_name}", key="proj_info_btn"):
            show_project_info()
    with col_data:
        data_files = pm.list_data_files(project_id)
        selected = st.session_state.get("selected_data_files", [f["name"] for f in data_files])
        total_rows = sum(f["rows"] for f in data_files if f["name"] in selected)
        st.caption(f"数据: {len(selected)}/{len(data_files)} 个文件 · {total_rows:,} 行")
    with col_btns:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📤 上传新数据", use_container_width=True):
                show_upload_dialog()
        with c2:
            if st.button("📋 导出报告", type="primary", use_container_width=True):
                show_report_dialog()

    st.divider()

    # --- 报告预览模式 ---
    if st.session_state.get("report_preview_mode"):
        _show_report_preview(pm, project_id)
        return

    # --- 数据加载 ---
    df = st.session_state.get("df")
    if df is None and selected:
        df = pm.merge_selected_data(project_id, selected)
        st.session_state.df = df
        st.session_state.data_info = get_data_info(df)

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
        st.session_state.viewing_step_index = -1  # -1 = 最新结果

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
            st.session_state.agent.chat_history = st.session_state.chat_history
            if "project_id" in st.session_state:
                pm.save_chat_history(st.session_state.project_id, st.session_state.chat_history)
            st.rerun()

    with center_col:
        st.subheader("📈 结果")
        steps = st.session_state.analysis_state.get("steps", [])
        viewing_idx = st.session_state.viewing_step_index

        if viewing_idx >= 0 and viewing_idx < len(steps):
            step = steps[viewing_idx]
            if step.get("llm_explanation"):
                with st.container(border=True):
                    st.markdown(f"🤖 **AI 解读:** {step['llm_explanation']}")
            if step.get("last_text"):
                st.markdown(step["last_text"])
            if step.get("last_charts"):
                for chart in step["last_charts"]:
                    st.plotly_chart(chart, use_container_width=True)
        elif "last_result" in st.session_state:
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
        else:
            st.info("在对话区描述你的分析需求，Agent 将为你规划步骤。")

    with right_col:
        st.subheader("📋 分析步骤")
        steps = st.session_state.analysis_state.get("steps", [])
        if not steps:
            st.info("暂无分析步骤")
            return

        for i, step in enumerate(steps):
            status = step.get("status", "pending")
            status_icon = {"pending": "○", "running": "⟳", "done": "✓", "error": "✗"}
            icon = status_icon.get(status, "○")

            is_viewing = (i == st.session_state.viewing_step_index)
            bg = "#e8f0fe" if is_viewing else "transparent"
            border = "#1a73e8" if is_viewing else "#e0e0e0"

            with st.container():
                st.markdown(
                    f"<div style='padding:6px 8px;margin:2px 0;border-left:3px solid {border};"
                    f"background:{bg};border-radius:4px;font-size:13px;'>"
                    f"{icon} <b>步骤 {i+1}</b>: {step['description'][:30]}...</div>",
                    unsafe_allow_html=True,
                )
                c_act, c_view = st.columns([1, 1])
                with c_act:
                    if status == "pending" and st.button("▶", key=f"run_{i}"):
                        _execute_step(i, step, st.session_state.df, pm)
                with c_view:
                    if status == "done" and st.button("查看", key=f"view_{i}"):
                        st.session_state.viewing_step_index = i
                        st.rerun()

        if steps and all(s.get("status") == "done" for s in steps):
            st.success("所有步骤已完成！点击「📋 导出报告」生成报告。")


def _load_chart_html(pm, project_id, step, all_steps):
    """从磁盘加载步骤关联的图表 HTML"""
    step_idx = all_steps.index(step) if step in all_steps else -1
    if step_idx < 0:
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
    for s in include_steps:
        chart_html = _load_chart_html(pm, project_id, s, 
            st.session_state.analysis_state.get("steps", []))
        sections.append(build_section(
            title=s["description"],
            text=s.get("llm_explanation", ""),
            chart_html=chart_html,
        ))

    df = st.session_state.get("df")
    rows, cols = df.shape if df is not None else (0, 0)
    html = generate_html_report(
        title=report_title, sections=sections, conclusion=conclusion or "分析完成",
        data_source=project_name, rows=rows, cols=cols,
    )

    with st.expander("报告预览", expanded=True):
        st.components.v1.html(html, height=600, scrolling=True)

    c_back, c_dl = st.columns(2)
    with c_back:
        if st.button("← 返回分析", use_container_width=True):
            st.session_state.report_preview_mode = False
            st.rerun()
    with c_dl:
        report_path = pm.save_report(project_id, html)
        with open(report_path, "r", encoding="utf-8") as f:
            st.download_button("⬇ 下载 HTML", f.read(), f"{project_name}_report.html",
                             "text/html", use_container_width=True)


def _execute_step(step_index: int, step_def: dict, df, pm):
    """执行分析步骤（与之前逻辑相同，增加 last_text/last_charts 存储）"""
    import pandas as pd
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
            metrics_for_llm = {"行数": result["row_count"], "列数": result["column_count"], "统计摘要": stats_summary}

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
            text = "报告生成请使用顶部「📋 导出报告」按钮。"
            metrics_for_llm = {}

        # LLM 解读
        explanation_text = ""
        if metrics_for_llm and "agent" in st.session_state:
            agent_step = AnalysisStep(id=step_index + 1, type=step_type, description=step_def["description"])
            try:
                with st.spinner("AI 正在解读结果..."):
                    explanation_text = st.write_stream(
                        st.session_state.agent.explain_result_stream(agent_step, metrics_for_llm)
                    )
            except Exception:
                pass
            if not explanation_text:
                try:
                    explanation_text = st.session_state.agent.explain_result(agent_step, metrics_for_llm)
                except Exception:
                    pass

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
```

- [ ] **Step 1:** 用以上代码替换 `streamlit-app/views/analysis.py`
- [ ] **Step 2:** `python -c "compile(open('D:/PythonFile/project1/streamlit-app/views/analysis.py', encoding='utf-8').read(), 'analysis.py', 'exec'); print('Syntax OK')"`
- [ ] **Step 3:** Commit

---

### Task 5: 清理 + 设置页微调

**Files:** 删除 `views/report.py`, `views/history.py`，微调 `views/settings.py`

- [ ] **Step 1:** 删除 `streamlit-app/views/report.py`
- [ ] **Step 2:** 删除 `streamlit-app/views/history.py`
- [ ] **Step 3:** 在 `views/settings.py` 的 `show()` 中 `st.title()` 后添加项目名显示（如果还没有的话）
- [ ] **Step 4:** 删除 `views/__init__.py` 中的旧导出（如有），确保只有 `new_project`, `analysis`, `settings`
- [ ] **Step 5:** `python -c "compile(open('D:/PythonFile/project1/streamlit-app/views/settings.py', encoding='utf-8').read(), 'settings.py', 'exec'); print('Syntax OK')"`
- [ ] **Step 6:** Commit

---

### Task 6: 全流程验证

- [ ] **Step 1:** 启动 app: `streamlit run streamlit-app/app.py`
- [ ] **Step 2:** 验证: 新建项目 → 创建成功 → 自动跳转分析对话
- [ ] **Step 3:** 验证: 侧边栏数据列表勾选/取消 → 列表面板功能正常
- [ ] **Step 4:** 验证: 侧边栏历史项目 → 点击切换项目
- [ ] **Step 5:** 验证: 分析对话 → 输入需求 → LLM 规划 → 执行步骤 → 流式解读
- [ ] **Step 6:** 验证: 已执行步骤 → 点击「查看」→ 结果区切换显示
- [ ] **Step 7:** 验证: 上传新数据弹窗 → 追加成功
- [ ] **Step 8:** 验证: 报告导出弹窗 → 勾选步骤 → AI 结论预览 → 下载
- [ ] **Step 9:** 验证: 设置页功能正常
- [ ] **Step 10:** Commit
