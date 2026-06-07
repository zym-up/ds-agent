# DS Agent — 数据科学家 Agent

面向汽车研发工程师的智能数据分析工具。用自然语言描述需求，AI 自动规划并执行分析流程。

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-120-passing-brightgreen.svg)](tests/)

## 特性

- **自然语言交互** — 输入"分析拉伸强度和柔软度的关系"，AI 自动规划分析步骤
- **领域知识注入** — 内置汽车面料/传感器领域知识库，分析结果贴合工程语境
- **逐步可解释** — 每个分析步骤独立执行，LLM 解读结果，不是黑盒
- **双前端方案** — Streamlit 版（纯 Python 快速体验）和 FastAPI + Vue 3 版（生产级交互）
- **多轮对话记忆** — 跨步骤保持上下文，支持追问和修改
- **一键打包分发** — PyInstaller 打包，Windows 解压即用

## 快速开始

### 安装依赖

```bash
pip install -r streamlit-app/requirements.txt
```

### 启动方式

**方式一：Streamlit 版（推荐新手）**

```bash
streamlit run streamlit-app/app.py
# 或双击 streamlit-app/run.bat
```

**方式二：FastAPI + Vue 版**

```bash
# 终端 1：启动后端
cd fastapi-app
uvicorn backend.main:app --reload --port 8502

# 终端 2：启动前端
cd fastapi-app/frontend
npm install && npm run dev
# 或双击 fastapi-app/run_backend.bat
```

### 配置 LLM

在 Web 界面设置页填入 API 信息，支持所有兼容 OpenAI API 格式的模型服务（DeepSeek、通义千问、GPT 等）。

## 架构

```
用户自然语言输入
       │
       ▼
┌─────────────────────────────────┐
│  LLM Agent (llm_agent.py)       │
│  场景识别 → 意图解析 → 步骤规划   │
│  + 领域知识库注入                 │
└──────────────┬──────────────────┘
               │ 分析计划 (AnalysisPlan)
               ▼
┌─────────────────────────────────┐
│  Step Executor (step_executor.py)│
│  统一调度：路由到各分析模块        │
└──────────────┬──────────────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
  clean      eda       model
  (清洗)    (探索)    (建模)
    │          │          │
    └──────────┼──────────┘
               ▼
┌─────────────────────────────────┐
│  LLM 结果解读                    │
│  结合领域知识给出工程建议          │
└─────────────────────────────────┘
```

## 项目结构

```
project1/
├── engine/                  # 共享分析引擎
│   ├── llm_agent.py         # LLM 编排（场景识别+步骤规划+结果解读）
│   ├── step_executor.py     # 统一调度层
│   ├── data_loader.py       # 数据加载（CSV/Excel/JSON）
│   ├── data_cleaner.py      # 数据清洗
│   ├── eda.py               # 探索性分析（统计/可视化）
│   ├── feature_engineer.py  # 特征工程
│   ├── modeler.py           # 机器学习建模
│   ├── reporter.py          # 报告生成（HTML/PDF）
│   ├── project_manager.py   # 项目管理
│   ├── sandbox.py           # 安全代码执行
│   └── config.py            # 配置
├── knowledge/               # 领域知识库（YAML）
│   ├── indicators.yaml      # 汽车面料物理指标词典
│   ├── fabric_analysis.yaml # 面料/材料分析决策指南
│   ├── sensor_analysis.yaml # 传感器信号分析决策指南
│   └── titanic_methodology.yaml # 通用表格分析决策指南
├── streamlit-app/           # Streamlit 全栈版
├── fastapi-app/             # FastAPI + Vue 3 版
├── projects/                # 用户项目数据
└── tests/                   # 测试用例（120 个）
```

## 分析能力

| 类别 | 支持的方法 |
|------|-----------|
| 数据清洗 | 去重、缺失值填充（mean/median/mode）、异常值检测（IQR/Z-score）、列删除 |
| 探索分析 | 统计摘要、分布图、相关性矩阵（Pearson/Spearman）、散点图、折线图、配对矩阵 |
| 特征工程 | 标准化/归一化、分类编码（OneHot/Label）、低方差过滤、相关性特征选择 |
| 机器学习 | 随机森林、XGBoost、线性回归、Ridge/Lasso、特征重要性、残差诊断 |
| 报告导出 | HTML/PDF 报告、交互式 Plotly 图表嵌入 |

## 运行测试

```bash
pytest tests/ -v
```

## License

MIT
