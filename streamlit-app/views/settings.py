"""设置页面"""
import streamlit as st
from engine.config import load_config, save_config, LLM_PRESETS


def show():
    st.title("⚙ 设置")
    if "project_name" in st.session_state:
        st.info(f"📊 当前项目: **{st.session_state.project_name}**")

    config = st.session_state.get("config", load_config())

    tab1, tab2 = st.tabs(["LLM API 配置", "关于"])

    with tab1:
        preset = st.selectbox(
            "选择预设模板",
            list(LLM_PRESETS.keys()),
            format_func=lambda x: f"{LLM_PRESETS[x].name} — {LLM_PRESETS[x].model}",
        )

        if st.button("应用预设"):
            config.llm = LLM_PRESETS[preset]

        st.divider()

        config.llm.name = st.text_input("服务名称", config.llm.name)
        config.llm.base_url = st.text_input("API 地址", config.llm.base_url,
                                             help="例如: https://your-internal-api/v1")
        config.llm.api_key = st.text_input("API Key", config.llm.api_key, type="password")
        config.llm.model = st.text_input("模型名称", config.llm.model)
        config.llm.temperature = st.slider("温度 (Temperature)", 0.0, 1.0, config.llm.temperature, 0.05)
        config.llm.max_tokens = st.slider("最大 Token", 512, 16384, config.llm.max_tokens, 512)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("测试连接"):
                from engine.llm_agent import LLMAdapter
                adapter = LLMAdapter(config.llm)
                ok, msg = adapter.test_connection()
                if ok:
                    st.success(f"连接成功: {msg}")
                else:
                    st.error(f"连接失败: {msg}")

        with col2:
            if st.button("保存配置", type="primary"):
                save_config(config)
                st.session_state.config = config
                st.success("配置已保存")

    with tab2:
        st.markdown("""
        ### 数据科学家 Agent

        面向汽车研发工程师的数据分析助手。

        **支持的分析类型:**
        - 数据清洗与预处理
        - 探索性数据分析 (EDA)
        - 相关性分析
        - 回归建模 (线性回归、岭回归、Lasso、随机森林、XGBoost)
        - 聚类分析
        - 特征工程
        - 报告生成

        **支持的 LLM:**
        - DeepSeek (兼容 OpenAI API)
        - Qwen (通义千问)
        - 自定义服务 (任何兼容 OpenAI API 格式的服务)
        """)
