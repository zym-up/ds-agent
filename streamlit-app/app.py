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
            try:
                data_files = pm.list_data_files(st.session_state.project_id)
            except Exception:
                data_files = []

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
                            if "viewing_step_index" in st.session_state:
                                del st.session_state.viewing_step_index
                            if "report_preview_mode" in st.session_state:
                                del st.session_state.report_preview_mode
                            if "agent" in st.session_state:
                                del st.session_state.agent
                            st.rerun()

        # --- 折叠面板: 历史报告 ---
        with st.sidebar.expander("📋 历史报告", expanded=False):
            try:
                reports = pm.list_reports(st.session_state.project_id)
            except Exception:
                reports = []
            if not reports:
                st.caption("暂无报告")
            else:
                for r in reports:
                    col_rpt, _ = st.columns([4, 1])
                    with col_rpt:
                        st.markdown(f"📄 [{r['name']}]({r['path']})")
                        st.caption(r["created_at"])

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
