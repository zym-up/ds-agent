# CLAUDE.md

## Project Overview

数据科学家 Agent — 面向汽车研发工程师的数据分析 Web 工具。

包含两个版本：
- streamlit-app/: Streamlit 全栈方案
- fastapi-app/: FastAPI + Vue 3 前后端分离方案
- engine/: 共享分析引擎

## Development Commands

- 安装 Python 依赖: `pip install -r streamlit-app/requirements.txt`
- 启动 Streamlit: `streamlit run streamlit-app/app.py`
- 启动 FastAPI: `uvicorn fastapi-app.backend.main:app --reload --port 8502`
- 启动前端: `cd fastapi-app/frontend && npm run dev`
- 一键启动 (Streamlit): 双击 `streamlit-app/run.bat`
- 一键启动 (FastAPI): 双击 `fastapi-app/run_backend.bat`
- 运行测试: `pytest`

## Architecture

共享引擎模块：
- data_loader: 数据加载 (CSV/Excel/JSON)
- data_cleaner: 数据清洗 (缺失值/异常值)
- eda: 探索性分析 (统计/可视化)
- feature_engineer: 特征工程 (标准化/编码/选择)
- modeler: 建模 (回归/分类/聚类)
- reporter: 报告生成 (HTML/PDF)
- llm_agent: LLM 编排 (OpenAI 兼容 API)
- sandbox: 安全代码执行
- project_manager: 项目管理
- knowledge: 领域知识库

## 语言偏好
请始终使用简体中文与我对话。
