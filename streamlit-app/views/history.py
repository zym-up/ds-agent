"""历史项目页面"""
import streamlit as st
from engine.project_manager import ProjectManager


def show():
    st.title("📁 历史项目")
    if "project_name" in st.session_state:
        st.info(f"📊 当前项目: **{st.session_state.project_name}**")

    pm = ProjectManager()
    projects = pm.list_projects()

    if not projects:
        st.info("暂无历史项目。请先上传数据创建项目。")
        return

    search = st.text_input("搜索项目", placeholder="输入项目名称...")

    filtered = projects
    if search:
        filtered = [p for p in projects if search.lower() in p["name"].lower()]

    for proj in filtered:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.subheader(f"📊 {proj['name']}")
                st.caption(f"创建: {proj['created_at'][:10]} | {proj['steps_count']} 个分析步骤")
                if proj.get("data_file"):
                    st.caption(f"数据: {proj['data_file']}")
            with col2:
                if st.button("打开", key=f"open_{proj['id']}"):
                    project_data = pm.load_project(proj['id'])
                    st.session_state.project_id = proj['id']
                    st.session_state.project_name = proj['name']
                    st.session_state.df = project_data["dataframe"]
                    st.session_state.chat_history = project_data["chat_history"]
                    st.session_state.analysis_state = project_data["state"]
                    st.success(f"已打开项目: {proj['name']}")
                    st.rerun()
            with col3:
                if st.button("导出报告", key=f"report_{proj['id']}"):
                    st.info(f"报告目录: projects/{proj['id']}/reports")
            with col4:
                if st.button("删除", key=f"del_{proj['id']}", type="secondary"):
                    pm.delete_project(proj['id'])
                    st.rerun()
        st.divider()
