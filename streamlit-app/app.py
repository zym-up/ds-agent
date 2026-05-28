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

    page = st.sidebar.radio(
        "导航",
        ["📂 数据上传", "🔬 分析对话", "📋 报告导出", "⚙ 设置", "📁 历史项目"],
    )

    st.sidebar.divider()
    if "project_name" in st.session_state:
        st.sidebar.caption(f"当前项目: {st.session_state.project_name}")

    if page == "📂 数据上传":
        from views import data_upload
        data_upload.show()
    elif page == "🔬 分析对话":
        from views import analysis
        analysis.show()
    elif page == "📋 报告导出":
        from views import report
        report.show()
    elif page == "⚙ 设置":
        from views import settings
        settings.show()
    elif page == "📁 历史项目":
        from views import history
        history.show()


if __name__ == "__main__":
    main()
