# 数据科学家 Agent — 设计文档

**日期**: 2026-05-27
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
| data_loader | 文件解析（CSV/Excel/JSON）、编码检测、Schema 推断 | pandas, openpyxl |
| data_cleaner | 缺失值策略、异常值检测（IQR/Z-score）、类型转换、去重 | pandas, numpy, scipy |
| eda | 描述统计、分布图、相关性矩阵、PCA 降维可视化 | pandas, plotly, scipy |
| feature_engineer | 标准化/归一化、编码、特征选择（方差/相关性/重要性） | sklearn, pandas |
| modeler | 回归/分类/聚类、交叉验证、超参搜索、评估指标 | sklearn, xgboost |
| reporter | HTML/PDF/Markdown 报告生成、图表嵌入 | jinja2, plotly, weasyprint |
| llm_agent | LLM API 调用、意图解析、结果自然语言解释 | httpx |
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
用户输入 → [1. 意图解析] → [2. 步骤展示 & 用户确认]
                ↓
[3. Pipeline 逐步执行] → [4. LLM 结果解释] → [5. 报告导出]
```

- **可解释 > 自动化**：每一步对用户可见、可干预
- **安全执行**：LLM 生成代码在沙箱中运行，只读访问数据文件
- **领域知识注入**：在 system prompt 中融合结构化知识卡片内容

### 4.1 三种交互模式

| 模式 | 触发方式 | 适合场景 |
|------|---------|---------|
| 对话引导 | 输入框自然语言描述 | "帮我分析柔软度和拉伸强度的关系" |
| 手动操作 | 步骤导航直接配置参数 | 已知要做什么，跳过对话 |
| 混合模式 | 对话中指定修改某步 | "第三步换成随机森林，深度设为5" |

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

## 7. 领域知识库（轻量方案）

采用结构化 YAML + TF-IDF 关键词检索，不引入向量数据库。

### 7.1 结构化知识卡片

```yaml
# indicators.yaml
拉伸强度:
  unit: MPa
  desc: 材料断裂前承受的最大拉应力
  typical_range: [5, 50]
  related_perception: 耐久感

柔软度评分:
  type: 主观评分 (1-10)
  desc: 专家触感评价打分
```

### 7.2 分析模板

```yaml
# templates.yaml
座椅面料感知质量:
  steps: [数据清洗, 相关性分析, 回归建模, 残差诊断]
  notes: 注意区分主客观指标
```

### 7.3 参考文档

工程师可上传 PDF/Word，本地分块后通过 TF-IDF 关键词匹配检索，注入 LLM prompt。

### 选择理由

| | 经典 RAG | 本方案 |
|---|---|---|
| 依赖 | 向量数据库 + 嵌入模型 | 无额外依赖 |
| 知识量 | 适合海量文档 | 几十到几百条 |
| 打包 | 需嵌入模型 | 纯文件 |
| 精确度 | 语义近似 | 关键词精确匹配 |

---

## 8. 项目目录结构

```
project1/
├── engine/                    # 共享分析引擎
│   ├── __init__.py
│   ├── data_loader.py
│   ├── data_cleaner.py
│   ├── eda.py
│   ├── feature_engineer.py
│   ├── modeler.py
│   ├── reporter.py
│   ├── llm_agent.py
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
├── knowledge/                 # 领域知识库文件
│   ├── indicators.yaml
│   └── templates.yaml
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
