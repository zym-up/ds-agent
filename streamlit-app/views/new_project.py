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
                if "viewing_step_index" in st.session_state:
                    del st.session_state.viewing_step_index
                if "agent" in st.session_state:
                    del st.session_state.agent
                st.success(f"项目 '{project_name}' 创建成功！正在进入分析对话...")
                st.rerun()

        finally:
            os.unlink(tmp_path)
    else:
        if st.button("创建并开始分析", type="primary", disabled=True):
            pass
        st.caption("请先上传数据文件")
