# 数据科学家 Agent — 设计文档

**日期**: 2026-05-27　**更新**: 2026-06-02（知识库扩展、方法原子化、场景识别、上下文记忆）
**目标用户**: 汽车研发工程师（有理论基础，不一定有编程基础）
**部署方式**: 单机 Web 工具，打包为可移植工具

---

## 1. 项目概述

开发两个版本的数据科学家 Agent 工具，服务于汽车研发工程师对内网数据的分析需求：

- **项目 A (streamlit-app)**: Streamlit 全栈方案，纯 Python，快速可用
- **项目 B (fastapi-app)**: FastAPI + Vue 3 分离方案，交互更灵活
- **共享引擎 (engine/)**: 两个项目共享同一套分析引擎

典型场景：座椅面料感知质量调查、用户内饰满意度数据挖掘、物理性质与主观感受关联分析等。

---

## 2. 架构总览

```
项目 A: streamlit-app/          项目 B: fastapi-app/

┌── Streamlit UI ──┐           ┌─ Vue 3 SPA UI ─┐
│  页面路由 & 组件   │           │  交互式页面     │
└──────┬───────────┘           └──────┬─────────┘
       │                              │ HTTP/SSE
┌──────┴───────────┐           ┌──────┴─────────┐
│   (内嵌)         │           │  FastAPI REST  │
└──────┬───────────┘           └──────┬─────────┘
       │                              │
       └──────────┬───────────────────┘
                  │
     ┌────────────┴──────────────┐
     │   共享分析引擎 (engine/)   │
     │  · step_executor          │ ← 统一调度层
     │  · data_loader            │
     │  · data_cleaner           │
     │  · eda                    │
     │  · feature_engineer       │
     │  · modeler                │
     │  · reporter               │
     │  · llm_agent              │
     │  · sandbox                │
     └───────────────────────────┘
```

---

## 3. 共享引擎模块

### 3.1 模块列表

| 模块 | 职责 | 关键依赖 |
|------|------|---------|
| step_executor | 统一调度层：接收 step_type+method → 路由到领域模块，返回标准化 {charts, text, metrics, result_df} | 以下所有模块 |
| data_loader | 文件解析（CSV/Excel/JSON）、编码检测、Schema 推断 | pandas, openpyxl |
| data_cleaner | 缺失值策略、异常值检测（IQR/Z-score）、类型转换、去重 | pandas, numpy, scipy |
| eda | 描述统计、分布图、相关性矩阵、散点图、折线图、配对矩阵 | pandas, plotly, scipy |
| feature_engineer | 标准化/归一化、编码、特征选择（方差/相关性/重要性） | sklearn, pandas |
| modeler | 回归/分类/聚类、交叉验证、超参搜索、评估指标 | sklearn, xgboost |
| reporter | HTML/PDF/Markdown 报告生成、图表嵌入 | jinja2, plotly, weasyprint |
| llm_agent | LLM API 调用、场景识别、意图解析、步骤规划、结果自然语言解释 | httpx, openai, yaml |
| sandbox | LLM 生成代码的安全执行环境 | 内置 subprocess |

每个模块统一接口：输入 `pd.DataFrame` + 配置字典，输出处理后的 DataFrame + 结果描述 + 图表列表。

### 3.2 LLM 配置适配器

```python
@dataclass
class LLMConfig:
    name: str           # 服务名称
    base_url: str       # 内网 API 地址
    api_key: str        # 认证密钥
    model: str          # 模型名称
    temperature: float  # 0.0-1.0
    max_tokens: int     # 最大输出长度

class LLMAdapter:
    """兼容 OpenAI API 格式的通用适配器"""
    def __init__(self, config: LLMConfig): ...
    def chat(self, messages: list) -> str: ...
    def analyze_intent(self, user_input: str) -> AnalysisPlan: ...
    def explain_results(self, data: dict) -> str: ...
```

支持预设模板：DeepSeek、Qwen、自定义，用户可在 Web 设置页配置和切换。

---

## 4. LLM Agent 编排流程

```
用户输入 → [0. 场景识别] → [1. 意图解析] → [2. 方法选择] → [3. 步骤组合] → [4. 验证计划]
                                      ↓
[5. Pipeline 逐步执行] → [6. LLM 结果解释] → [7. 报告导出]
```

### 4.1 分析规划流程（五步法）

| 步骤 | 名称 | 说明 |
|------|------|------|
| 第零步 | 场景识别 | 根据数据特征和用户表述判断场景类型（通用表格/面料物理指标/传感器信号），不同场景有不同分析策略 |
| 第一步 | 意图识别 | 判断用户意图：数据概览/分布探索/变量关系/多变量探索/寻找关键因素/预测建模/数据清洗/特征构造 |
| 第二步 | 方法选择 | 根据意图+场景选择最合适的原子方法（method），优先原子方法而非全量流水线 |
| 第三步 | 步骤组合 | 按逻辑顺序组合多个步骤（如 correlation→importance 互补验证），步骤数控制在 1-6 个 |
| 第四步 | 验证计划 | 检查列名存在性、步骤依赖关系、方法-数据类型匹配 |

### 4.2 分析方法原子化

分析步骤不再捆绑执行，而是通过 `method` 参数指定原子操作：

| step_type | 可用 method | 不填 method 行为 |
|-----------|------------|-----------------|
| clean | dedup / fill_missing / detect_outliers / drop_columns | 全量清洗流水线 |
| eda | correlation / distribution / scatter / line / pairplot / describe | 全量 EDA 流水线 |
| feature | scale / encode / variance_filter / correlation_select | 按 params 子参数执行 |
| model | train / importance / residual | 全量建模流水线 |

`step_executor.py` 作为统一调度层，两个前端（Streamlit / FastAPI）共享同一份路由逻辑。

### 4.3 三种场景分析策略

| 场景 | 触发信号 | 分析特点 | 知识库 |
|------|---------|---------|--------|
| 通用表格分析 | CSV/Excel 表格，行=样本列=变量 | 常规分析全流程 | titanic_methodology.yaml |
| 面料/材料分析 | 物理指标（拉伸强度、摩擦系数等）+ 主观评分 | 小样本、Spearman 相关、非线性映射 | fabric_analysis.yaml |
| 传感器信号分析 | 长时间序列（>1000行）、采样频率固定 | 需先特征提取（时域/频域）再分析 | sensor_analysis.yaml |

- **可解释 > 自动化**：每一步对用户可见、可干预
- **安全执行**：LLM 生成代码在沙箱中运行，只读访问数据文件
- **领域知识注入**：在 system prompt 中融合结构化决策指南

### 4.4 三种交互模式

| 模式 | 触发方式 | 适合场景 |
|------|---------|---------|
| 对话引导 | 输入框自然语言描述 | "帮我分析柔软度和拉伸强度的关系" |
| 手动操作 | 步骤导航直接配置参数 | 已知要做什么，跳过对话 |
| 混合模式 | 对话中指定修改某步 | "第三步换成随机森林，深度设为5" |

### 4.5 上下文记忆

LLM 调用时自动注入对话历史，支持跨步骤连续对话：

```
LLM messages 结构:
┌─────────────────────────────┐
│  system prompt（含领域知识）  │
├─────────────────────────────┤
│  最近 10 轮对话历史           │  ← 从 chat_history.json 恢复
│  user: "帮我分析..."         │
│  assistant: "好的，计划..."   │
│  user: "换成 Spearman"       │
│  assistant: "已修改..."      │
├─────────────────────────────┤
│  当前任务消息                 │
└─────────────────────────────┘
```

- `_build_messages_with_context()` 统一构造：system + 历史 + 当前任务
- `plan_analysis`、`explain_result`、`summarize_conclusions` 三个调用点共用
- 最多保留 20 条（10 轮），防止 token 溢出
- 项目保存 → `chat_history.json`；重新打开 → `set_chat_history()` 恢复
- 用户可以跨步骤引用之前的分析结果，如"把上面的相关性分析换成 Spearman"

---

## 5. 用户交互界面

主分析页分为三栏：

```
┌──────────────────────────────────────────────────────────┐
│  📊 项目名称                      [设置] [历史项目] [保存] │
├──────────┬──────────────────────────────┬─────────────────┤
│ 对话区    │ 结果展示区                    │ 步骤导航         │
│ Agent:   │ ┌──────────────────────────┐│ ○ 数据清洗 ✓    │
│ 已规划...│ │ [图表]     [数据表]       ││ ● 相关性分析 ⟳ │
│          │ └──────────────────────────┘│ ○ 回归建模      │
│ 你: 改成 │                              │                 │
│ Spearman│                              │                 │
├──────────┴──────────────────────────────┴─────────────────┤
│ [输入框: 帮我加上控制变量: 面料厚度              ] [发送] │
└──────────────────────────────────────────────────────────┘
```

---

## 6. 历史项目管理

```
每个项目目录结构:
projects/{project_id}/
├── meta.json             # 项目名称、创建时间、描述
├── data/original.csv     # 原始数据（只读保留）
├── state.json            # 分析步骤状态快照
├── charts/               # 交互式图表（HTML格式）
├── reports/              # 导出报告
└── chat_history.json     # LLM 对话记录
```

- 项目名由 LLM 根据内容自动建议
- 保存参数引用，重开可重新执行任意步骤
- chat_history 恢复对话上下文

---

## 7. 领域知识库

采用结构化 YAML 分析决策指南，注入 LLM system prompt，教 LLM 如何根据场景和意图选择分析方法。

### 7.1 知识库文件清单

| 文件 | 类型 | 内容 |
|------|------|------|
| `indicators.yaml` | 领域词典 | 汽车座椅面料物理指标（拉伸强度、摩擦系数等）及其与感官的关联 |
| `templates.yaml` | 分析模板 | 座椅面料感知质量、用户满意度分析的步骤模板 |
| `titanic_methodology.yaml` | 分析决策指南 | 泰坦尼克生存预测案例 — 通用表格数据分析的完整推理框架 |
| `fabric_analysis.yaml` | 分析决策指南 | 面料/材料物理指标分析 — 基于 KES 川端评价系统方法论 |
| `sensor_analysis.yaml` | 分析决策指南 | 传感器/信号数据分析 — 基于 CWRU 轴承故障诊断方法论 |

### 7.2 决策指南结构

每个决策指南包含五个部分：

| 部分 | 内容 | 作用 |
|------|------|------|
| 场景识别 | 触发信号（数据特征+用户表述） | 帮 LLM 判断当前数据属于哪种分析场景 |
| 领域知识 | 专属概念（物理指标含义、信号特征类型） | 注入领域术语和背景 |
| 意图识别映射 | 用户表述 → 分析目标 → 推荐步骤 | 教 LLM 从用户措辞推断分析意图 |
| 步骤组合模式 | 常用步骤链路及组合理由 | 教 LLM 为何这样组合、何时变体 |
| 常见陷阱 | 该领域的典型错误和注意事项 | 减少分析失误 |

### 7.3 选择理由

| | 经典 RAG | 本方案 |
|---|---|---|
| 依赖 | 向量数据库 + 嵌入模型 | 无额外依赖 |
| 知识量 | 适合海量文档 | 几十到几百条 |
| 打包 | 需嵌入模型 | 纯文件 |
| 精确度 | 语义近似 | LLM 推理 + 结构化引导 |
| 优势 | 自动检索 | 推理过程可控、可解释 |

---

## 8. 项目目录结构

```
project1/
├── engine/                    # 共享分析引擎
│   ├── __init__.py
│   ├── step_executor.py       # 统一调度层（method 路由）
│   ├── data_loader.py
│   ├── data_cleaner.py
│   ├── eda.py
│   ├── feature_engineer.py
│   ├── modeler.py
│   ├── reporter.py
│   ├── llm_agent.py           # LLM 编排（场景识别+意图解析+步骤规划）
│   ├── sandbox.py
│   └── config.py
│
├── streamlit-app/             # 项目 A
│   ├── app.py
│   ├── pages/
│   │   ├── data_upload.py
│   │   ├── analysis.py
│   │   └── report.py
│   ├── components/
│   │   ├── data_table.py
│   │   ├── chart_panel.py
│   │   └── step_stepper.py
│   └── requirements.txt
│
├── fastapi-app/               # 项目 B
│   ├── backend/
│   │   ├── main.py
│   │   ├── routers/
│   │   │   ├── data.py
│   │   │   ├── analysis.py
│   │   │   └── report.py
│   │   ├── models/schemas.py
│   │   └── requirements.txt
│   └── frontend/
│       ├── src/
│       │   ├── views/
│       │   ├── components/
│       │   ├── api/
│       │   └── stores/
│       └── package.json
│
├── projects/                  # 用户分析项目存储
├── knowledge/                 # 领域知识库（分析决策指南）
│   ├── indicators.yaml        # 汽车面料物理指标词典
│   ├── templates.yaml         # 分析模板
│   ├── titanic_methodology.yaml  # 通用表格分析决策指南
│   ├── fabric_analysis.yaml   # 面料/材料分析决策指南
│   └── sensor_analysis.yaml   # 传感器信号分析决策指南
└── docs/
```

---

## 9. 打包分发

- **项目 A**: PyInstaller 打包 + 一键 bat 启动脚本
- **项目 B**: 后端 PyInstaller 打包，前端 npm build 后嵌入后端静态文件服务
- 两个项目最终都提供免安装解压即用的体验，面向 Windows 工程师

---

## 10. 技术栈总结

| 层 | 项目 A | 项目 B |
|----|--------|--------|
| UI | Streamlit | Vue 3 + Pinia |
| 后端 | 无（Streamlit 内嵌） | FastAPI |
| 分析引擎 | engine/ (共享) | engine/ (共享) |
| 数据处理 | pandas, numpy, scipy | 同左 |
| 可视化 | plotly | plotly（后端生成）+ 前端渲染 |
| 机器学习 | sklearn, xgboost | 同左 |
| LLM 对接 | httpx + OpenAI SDK | 同左 |
| 打包 | PyInstaller | PyInstaller + Vite build |
