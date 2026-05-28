# 数据科学家 Agent 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建两个版本的数据科学家 Agent Web 工具，共享分析引擎，面向汽车研发工程师的结构化数据分析。

**Architecture:** 共享 Python 分析引擎（engine/）提供统一数据处理接口，Streamlit 应用（streamlit-app/）提供纯 Python 快速方案，FastAPI + Vue 3 应用（fastapi-app/）提供前后端分离方案。

**Tech Stack:** Python 3.11+, pandas, numpy, scipy, scikit-learn, xgboost, plotly, streamlit, fastapi, vue 3, pinia, vite

**开发顺序:** engine/ → streamlit-app/ → fastapi-app/ → 知识库 → 打包

---

## Phase 0: 项目基础设施

### Task 0.1: 创建目录结构和基础文件

**Files:**
- Create: `engine/__init__.py`
- Create: `engine/config.py`
- Create: `streamlit-app/requirements.txt`
- Create: `fastapi-app/backend/requirements.txt`
- Create: `knowledge/indicators.yaml`
- Create: `knowledge/templates.yaml`

- [ ] **Step 1: 创建所有必要目录**

```bash
mkdir -p engine
mkdir -p streamlit-app/pages
mkdir -p streamlit-app/components
mkdir -p fastapi-app/backend/routers
mkdir -p fastapi-app/backend/models
mkdir -p fastapi-app/frontend/src/views
mkdir -p fastapi-app/frontend/src/components
mkdir -p fastapi-app/frontend/src/api
mkdir -p fastapi-app/frontend/src/stores
mkdir -p knowledge
mkdir -p projects
```

- [ ] **Step 2: 创建 engine/__init__.py**

```python
"""
数据科学家 Agent — 共享分析引擎

提供统一接口的数据处理模块:
- data_loader: 数据加载与解析
- data_cleaner: 数据清洗
- eda: 探索性数据分析
- feature_engineer: 特征工程
- modeler: 模型训练与评估
- reporter: 报告生成
- llm_agent: LLM 编排
- sandbox: 安全代码执行
"""

__version__ = "0.1.0"
```

- [ ] **Step 3: 创建 streamlit-app/requirements.txt**

```
streamlit>=1.28.0
pandas>=2.1.0
numpy>=1.24.0
scipy>=1.11.0
scikit-learn>=1.3.0
xgboost>=2.0.0
plotly>=5.17.0
openpyxl>=3.1.0
jinja2>=3.1.0
httpx>=0.25.0
openai>=1.6.0
pyyaml>=6.0
python-docx>=1.0.0
PyPDF2>=3.0.0
```

- [ ] **Step 4: 创建 fastapi-app/backend/requirements.txt**

```
fastapi>=0.104.0
uvicorn>=0.24.0
python-multipart>=0.0.6
pandas>=2.1.0
numpy>=1.24.0
scipy>=1.11.0
scikit-learn>=1.3.0
xgboost>=2.0.0
plotly>=5.17.0
openpyxl>=3.1.0
jinja2>=3.1.0
httpx>=0.25.0
openai>=1.6.0
pyyaml>=6.0
python-docx>=1.0.0
PyPDF2>=3.0.0
```

- [ ] **Step 5: 创建 knowledge/indicators.yaml**

```yaml
# 汽车座椅面料感知质量 — 物理指标知识库
拉伸强度:
  unit: MPa
  desc: 材料在断裂前能承受的最大拉应力，反映材料的强度特性
  typical_range: [5, 50]
  related_perception: 耐久感、结实感

断裂伸长率:
  unit: "%"
  desc: 材料断裂时的伸长百分比，反映材料的延展性
  typical_range: [10, 300]
  related_perception: 弹性感

撕裂强度:
  unit: N/mm
  desc: 材料抵抗撕裂的能力
  typical_range: [10, 100]
  related_perception: 耐用感

摩擦系数:
  unit: 无量纲
  desc: 表面摩擦力与正压力的比值
  typical_range: [0.2, 1.5]
  related_perception: 滑爽感、柔软感

压缩回弹率:
  unit: "%"
  desc: 压缩后恢复原状的能力
  typical_range: [60, 95]
  related_perception: 蓬松感、厚实感

柔软度评分:
  type: 主观评分 (1-10)
  desc: 专家触感评价打分，分数越高越柔软
  related_indicators: [摩擦系数, 压缩回弹率, 断裂伸长率]
```

- [ ] **Step 6: 创建 knowledge/templates.yaml**

```yaml
座椅面料感知质量:
  description: 分析面料物理性质与用户主观感受之间的关联
  steps:
    - 数据清洗与缺失值处理
    - 各指标描述性统计
    - 物理指标与主观评分相关性分析
    - 多元线性回归建模
    - 残差诊断与异常样本识别
    - 特征重要性排序
  notes: 注意区分客观物理指标和主观评分字段，相关性分析时两种方法都尝试

用户群体满意度分析:
  description: 挖掘不同用户群体对汽车内饰满意度的潜在规律
  steps:
    - 数据清洗与编码
    - 用户群体分层描述统计
    - 各维度满意度分布可视化
    - 分组差异显著性检验
    - 聚类分析识别用户群体
  notes: 关注年龄、性别、车型等分层变量，聚类前需标准化处理
```

- [ ] **Step 7: 提交**

```bash
git add .
git commit -m "chore: 初始化项目目录结构和基础配置文件"
```

---

### Task 0.2: 安装 Python 依赖

- [ ] **Step 1: 创建虚拟环境**

```bash
python -m venv venv
```

- [ ] **Step 2: 安装引擎开发依赖**

```bash
source venv/Scripts/activate  # Windows
pip install pandas numpy scipy scikit-learn xgboost plotly openpyxl jinja2 httpx openai pyyaml python-docx PyPDF2 pytest
```

- [ ] **Step 3: 安装 Streamlit**

```bash
pip install streamlit
```

- [ ] **Step 4: 安装 FastAPI 后端依赖**

```bash
pip install fastapi uvicorn python-multipart
```

---

## Phase 1: 共享分析引擎

### Task 1.1: engine/config.py — 全局配置

**Files:**
- Write: `engine/config.py`

- [ ] **Step 1: 编写配置模块**

```python
"""全局配置管理"""
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from typing import Optional


@dataclass
class LLMConfig:
    name: str = "DeepSeek"
    base_url: str = "https://api.deepseek.com/v1"
    api_key: str = ""
    model: str = "deepseek-chat"
    temperature: float = 0.3
    max_tokens: int = 4096

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "LLMConfig":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class AppConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)
    projects_dir: str = "projects"
    knowledge_dir: str = "knowledge"
    data_dir: str = "data"

    def to_dict(self) -> dict:
        return {
            "llm": self.llm.to_dict(),
            "projects_dir": self.projects_dir,
            "knowledge_dir": self.knowledge_dir,
            "data_dir": self.data_dir,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AppConfig":
        llm = LLMConfig.from_dict(d.get("llm", {}))
        return cls(
            llm=llm,
            projects_dir=d.get("projects_dir", "projects"),
            knowledge_dir=d.get("knowledge_dir", "knowledge"),
            data_dir=d.get("data_dir", "data"),
        )


def load_config(config_path: str = "config.json") -> AppConfig:
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return AppConfig.from_dict(json.load(f))
    return AppConfig()


def save_config(config: AppConfig, config_path: str = "config.json") -> None:
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)


LLM_PRESETS = {
    "deepseek": LLMConfig(
        name="DeepSeek",
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat",
        temperature=0.3,
        max_tokens=4096,
    ),
    "qwen": LLMConfig(
        name="Qwen",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen-plus",
        temperature=0.3,
        max_tokens=4096,
    ),
    "custom": LLMConfig(
        name="自定义",
        base_url="",
        model="",
        temperature=0.3,
        max_tokens=4096,
    ),
}
```

- [ ] **Step 2: 提交**

```bash
git add engine/config.py
git commit -m "feat: 添加全局配置模块 engine/config.py"
```

---

### Task 1.2: engine/data_loader.py — 数据加载

**Files:**
- Write: `engine/data_loader.py`

- [ ] **Step 1: 编写数据加载模块**

```python
"""数据加载与解析模块"""
import pandas as pd
from pathlib import Path
from typing import Optional
import chardet


def detect_encoding(file_path: str, sample_size: int = 10000) -> str:
    """检测文件编码"""
    with open(file_path, "rb") as f:
        raw = f.read(sample_size)
    result = chardet.detect(raw)
    return result.get("encoding", "utf-8")


def load_csv(file_path: str, **kwargs) -> pd.DataFrame:
    """加载 CSV 文件，自动检测编码和分隔符"""
    encoding = kwargs.pop("encoding", detect_encoding(file_path))
    try:
        return pd.read_csv(file_path, encoding=encoding, **kwargs)
    except UnicodeDecodeError:
        return pd.read_csv(file_path, encoding="gbk", **kwargs)


def load_excel(file_path: str, sheet_name: Optional[str] = None, **kwargs) -> pd.DataFrame:
    """加载 Excel 文件"""
    if sheet_name:
        return pd.read_excel(file_path, sheet_name=sheet_name, **kwargs)
    xl = pd.ExcelFile(file_path)
    if len(xl.sheet_names) == 1:
        return pd.read_excel(file_path, **kwargs)
    return pd.read_excel(file_path, sheet_name=xl.sheet_names[0], **kwargs)


def load_json(file_path: str, **kwargs) -> pd.DataFrame:
    """加载 JSON 文件"""
    return pd.read_json(file_path, **kwargs)


def load_file(file_path: str, **kwargs) -> pd.DataFrame:
    """自动识别文件类型并加载"""
    ext = Path(file_path).suffix.lower()
    loaders = {
        ".csv": load_csv,
        ".tsv": lambda p, **kw: load_csv(p, sep="\t", **kw),
        ".xlsx": load_excel,
        ".xls": load_excel,
        ".json": load_json,
    }
    if ext not in loaders:
        raise ValueError(f"不支持的文件格式: {ext}，支持的格式: {list(loaders.keys())}")
    return loaders[ext](file_path, **kwargs)


def get_data_info(df: pd.DataFrame) -> dict:
    """获取 DataFrame 基本信息"""
    return {
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing_count": df.isnull().sum().to_dict(),
        "missing_pct": (df.isnull().sum() / len(df) * 100).round(2).to_dict(),
        "numeric_columns": df.select_dtypes(include=["number"]).columns.tolist(),
        "categorical_columns": df.select_dtypes(include=["object", "category"]).columns.tolist(),
        "preview": df.head(10).to_dict(orient="records"),
    }
```

- [ ] **Step 2: 提交**

```bash
git add engine/data_loader.py
git commit -m "feat: 添加数据加载模块 engine/data_loader.py"
```

---

### Task 1.3: engine/data_cleaner.py — 数据清洗

**Files:**
- Write: `engine/data_cleaner.py`

- [ ] **Step 1: 编写数据清洗模块**

```python
"""数据清洗模块"""
import pandas as pd
import numpy as np
from typing import Optional


def remove_duplicates(df: pd.DataFrame, subset: Optional[list] = None) -> tuple[pd.DataFrame, dict]:
    """去重"""
    before = len(df)
    df = df.drop_duplicates(subset=subset).reset_index(drop=True)
    after = len(df)
    summary = {"去重前": before, "去重后": after, "删除重复行数": before - after}
    return df, summary


def drop_missing(
    df: pd.DataFrame, threshold: float = 0.5, axis: str = "row"
) -> tuple[pd.DataFrame, dict]:
    """删除缺失值过多的行或列"""
    before = df.shape
    if axis == "col":
        df = df.dropna(axis=1, thresh=int(len(df) * (1 - threshold)))
    else:
        df = df.dropna(axis=0, thresh=int(df.shape[1] * (1 - threshold)))
    after = df.shape
    summary = {"处理前": before, "处理后": after}
    return df, summary


def fill_missing(
    df: pd.DataFrame,
    strategy: str = "mean",
    columns: Optional[list] = None,
    fill_value: any = None,
) -> tuple[pd.DataFrame, dict]:
    """填充缺失值

    strategy: 'mean' | 'median' | 'mode' | 'constant'
    """
    targets = columns or df.columns.tolist()
    fills = {}

    for col in targets:
        if col not in df.columns or df[col].isnull().sum() == 0:
            continue
        if strategy == "mean" and pd.api.types.is_numeric_dtype(df[col]):
            fills[col] = df[col].mean()
        elif strategy == "median" and pd.api.types.is_numeric_dtype(df[col]):
            fills[col] = df[col].median()
        elif strategy == "mode":
            mode_vals = df[col].mode()
            fills[col] = mode_vals[0] if len(mode_vals) > 0 else fill_value
        elif strategy == "constant":
            fills[col] = fill_value

    df = df.fillna(fills)
    summary = {"策略": strategy, "填充列": fills}
    return df, summary


def detect_outliers(
    df: pd.DataFrame,
    method: str = "iqr",
    columns: Optional[list] = None,
    threshold: float = 1.5,
) -> dict:
    """检测异常值

    method: 'iqr' | 'zscore'
    """
    targets = [c for c in (columns or df.columns) if pd.api.types.is_numeric_dtype(df[c])]
    outliers = {}

    for col in targets:
        if method == "iqr":
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - threshold * iqr
            upper = q3 + threshold * iqr
            mask = (df[col] < lower) | (df[col] > upper)
        else:
            z = np.abs((df[col] - df[col].mean()) / df[col].std())
            mask = z > threshold
        outliers[col] = {"count": int(mask.sum()), "indices": df[mask].index.tolist()}
    return outliers


def clean_pipeline(
    df: pd.DataFrame,
    drop_dup: bool = True,
    dup_subset: Optional[list] = None,
    fill_strategy: str = "mean",
    fill_columns: Optional[list] = None,
    outlier_method: str = "iqr",
    outlier_columns: Optional[list] = None,
) -> tuple[pd.DataFrame, dict]:
    """清洗流水线：去重 → 填充缺失 → 返回清洗后数据"""
    summary = {}
    if drop_dup:
        df, dup_info = remove_duplicates(df, subset=dup_subset)
        summary["去重"] = dup_info
    df, fill_info = fill_missing(df, strategy=fill_strategy, columns=fill_columns)
    summary["缺失值填充"] = fill_info
    outliers = detect_outliers(df, method=outlier_method, columns=outlier_columns)
    summary["异常值检测"] = outliers
    return df, summary
```

- [ ] **Step 2: 提交**

```bash
git add engine/data_cleaner.py
git commit -m "feat: 添加数据清洗模块 engine/data_cleaner.py"
```

---

### Task 1.4: engine/eda.py — 探索性数据分析

**Files:**
- Write: `engine/eda.py`

- [ ] **Step 1: 编写 EDA 模块**

```python
"""探索性数据分析模块"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Optional


def describe_numeric(df: pd.DataFrame, columns: Optional[list] = None) -> dict:
    """数值型列描述统计"""
    targets = [c for c in (columns or df.columns) if pd.api.types.is_numeric_dtype(df[c])]
    if not targets:
        return {}
    stats = df[targets].describe(percentiles=[0.25, 0.5, 0.75]).to_dict()
    # 追加偏度和峰度
    for col in targets:
        stats[col]["skewness"] = float(df[col].skew())
        stats[col]["kurtosis"] = float(df[col].kurtosis())
    return stats


def describe_categorical(df: pd.DataFrame, columns: Optional[list] = None) -> dict:
    """分类型列统计"""
    targets = [c for c in (columns or df.columns) if not pd.api.types.is_numeric_dtype(df[c])]
    result = {}
    for col in targets:
        value_counts = df[col].value_counts().head(20).to_dict()
        result[col] = {
            "unique_count": int(df[col].nunique()),
            "top_values": value_counts,
            "missing": int(df[col].isnull().sum()),
        }
    return result


def correlation_matrix(df: pd.DataFrame, method: str = "pearson", columns: Optional[list] = None) -> tuple[pd.DataFrame, go.Figure]:
    """计算相关性矩阵并生成热力图"""
    targets = [c for c in (columns or df.columns) if pd.api.types.is_numeric_dtype(df[c])]
    corr = df[targets].corr(method=method)

    fig = go.Figure(
        data=go.Heatmap(
            z=corr.values,
            x=corr.columns.tolist(),
            y=corr.index.tolist(),
            colorscale="RdBu_r",
            zmid=0,
            text=np.round(corr.values, 2),
            texttemplate="%{text}",
            textfont={"size": 10},
        )
    )
    fig.update_layout(
        title=f"{method.upper()} 相关性矩阵",
        xaxis={"tickangle": 45},
        height=600,
    )
    return corr, fig


def distribution_plot(df: pd.DataFrame, column: str, bins: int = 30) -> go.Figure:
    """单变量分布图（直方图 + 箱线图）"""
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.7, 0.3],
        subplot_titles=("分布直方图", "箱线图"),
        specs=[[{"type": "xy"}, {"type": "xy"}]],
    )
    fig.add_trace(go.Histogram(x=df[column], nbinsx=bins, name=column), row=1, col=1)
    fig.add_trace(go.Box(y=df[column], name=column), row=1, col=2)
    fig.update_layout(title=f"{column} 分布分析", showlegend=False, height=400)
    return fig


def scatter_plot(
    df: pd.DataFrame, x: str, y: str, color: Optional[str] = None, trendline: bool = True
) -> go.Figure:
    """散点图，可选趋势线"""
    fig = px.scatter(df, x=x, y=y, color=color, trendline="ols" if trendline else None,
                     title=f"{x} vs {y}")
    fig.update_layout(height=500)
    return fig


def pair_plot(df: pd.DataFrame, columns: list, color: Optional[str] = None) -> go.Figure:
    """多变量配对散点图矩阵"""
    n = len(columns)
    fig = make_subplots(rows=n, cols=n, shared_xaxes=False, shared_yaxes=False)

    for i, col_y in enumerate(columns):
        for j, col_x in enumerate(columns):
            if i == j:
                fig.add_trace(go.Histogram(x=df[col_x], name=col_x), row=i + 1, col=j + 1)
            else:
                fig.add_trace(
                    go.Scatter(x=df[col_x], y=df[col_y], mode="markers",
                               marker=dict(size=3, opacity=0.5), showlegend=False),
                    row=i + 1, col=j + 1,
                )
        fig.update_xaxes(title_text=columns[i], row=n, col=i + 1)
        fig.update_yaxes(title_text=columns[i], row=i + 1, col=1)

    fig.update_layout(height=200 * n, title="配对散点图矩阵")
    return fig


def eda_pipeline(
    df: pd.DataFrame,
    numeric_columns: Optional[list] = None,
    corr_method: str = "pearson",
) -> dict:
    """EDA 流水线"""
    if numeric_columns is None:
        numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()

    numeric_stats = describe_numeric(df, numeric_columns)
    categorical_stats = describe_categorical(df)
    corr_df, corr_fig = correlation_matrix(df, method=corr_method, columns=numeric_columns)

    charts = [corr_fig]
    for col in numeric_columns[:6]:
        charts.append(distribution_plot(df, col))

    return {
        "numeric_stats": numeric_stats,
        "categorical_stats": categorical_stats,
        "correlation_data": corr_df.to_dict(),
        "column_count": len(df.columns),
        "row_count": len(df),
        "charts": charts,
    }
```

- [ ] **Step 2: 提交**

```bash
git add engine/eda.py
git commit -m "feat: 添加探索性数据分析模块 engine/eda.py"
```

---

### Task 1.5: engine/feature_engineer.py — 特征工程

**Files:**
- Write: `engine/feature_engineer.py`

- [ ] **Step 1: 编写特征工程模块**

```python
"""特征工程模块"""
import pandas as pd
import numpy as np
from typing import Optional
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder, OneHotEncoder
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_regression, mutual_info_regression


def scale_features(
    df: pd.DataFrame, columns: list, method: str = "standard"
) -> tuple[pd.DataFrame, dict]:
    """特征缩放

    method: 'standard' | 'minmax'
    """
    scaler = StandardScaler() if method == "standard" else MinMaxScaler()
    df = df.copy()
    df[columns] = scaler.fit_transform(df[columns])
    summary = {
        "方法": "标准化 (Z-score)" if method == "standard" else "归一化 (Min-Max)",
        "处理列": columns,
    }
    return df, summary


def encode_categorical(
    df: pd.DataFrame, columns: list, method: str = "onehot"
) -> tuple[pd.DataFrame, dict]:
    """分类变量编码

    method: 'onehot' | 'label'
    """
    df = df.copy()
    if method == "onehot":
        df = pd.get_dummies(df, columns=columns, drop_first=True)
        summary = {"方法": "独热编码", "处理列": columns}
    else:
        for col in columns:
            df[col] = LabelEncoder().fit_transform(df[col].astype(str))
        summary = {"方法": "标签编码", "处理列": columns}
    return df, summary


def select_by_variance(df: pd.DataFrame, threshold: float = 0.01) -> tuple[pd.DataFrame, dict]:
    """低方差特征过滤"""
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    selector = VarianceThreshold(threshold=threshold)
    selected = selector.fit_transform(df[numeric_cols])
    kept = [numeric_cols[i] for i in range(len(numeric_cols)) if selector.get_support()[i]]
    removed = [c for c in numeric_cols if c not in kept]
    result = df[kept + [c for c in df.columns if c not in numeric_cols]]
    summary = {"保留特征": kept, "移除特征": removed, "阈值": threshold}
    return result, summary


def select_by_correlation(
    df: pd.DataFrame, target: str, k: int = 10, method: str = "f_regression"
) -> tuple[list, dict]:
    """基于目标变量的特征选择"""
    numeric_cols = [c for c in df.select_dtypes(include=["number"]).columns if c != target]
    X = df[numeric_cols].fillna(0)
    y = df[target].fillna(df[target].mean())

    score_func = f_regression if method == "f_regression" else mutual_info_regression
    selector = SelectKBest(score_func=score_func, k=min(k, len(numeric_cols)))
    selector.fit(X, y)

    scores = list(zip(numeric_cols, selector.scores_))
    scores.sort(key=lambda x: x[1], reverse=True)
    selected = [s[0] for s in scores[:k]]
    summary = {"目标变量": target, "方法": method, "特征得分": {s[0]: float(s[1]) for s in scores}}
    return selected, summary
```

- [ ] **Step 2: 提交**

```bash
git add engine/feature_engineer.py
git commit -m "feat: 添加特征工程模块 engine/feature_engineer.py"
```

---

### Task 1.6: engine/modeler.py — 建模与评估

**Files:**
- Write: `engine/modeler.py`

- [ ] **Step 1: 编写建模模块**

```python
"""建模与评估模块"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Optional, Literal
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.metrics import (
    r2_score, mean_squared_error, mean_absolute_error,
    accuracy_score, precision_score, recall_score, f1_score,
    silhouette_score,
)
import xgboost as xgb

ModelType = Literal["linear", "ridge", "lasso", "random_forest", "xgboost"]
TaskType = Literal["regression", "classification", "clustering"]


def split_data(df: pd.DataFrame, target: str, test_size: float = 0.2, random_state: int = 42):
    """划分训练/测试集"""
    X = df.drop(columns=[target])
    y = df[target]
    return train_test_split(X, y, test_size=test_size, random_state=random_state)


def train_regression(
    X_train: pd.DataFrame, y_train: pd.Series, model_type: ModelType = "linear", **kwargs
) -> tuple[object, dict]:
    """训练回归模型"""
    models = {
        "linear": LinearRegression(**kwargs),
        "ridge": Ridge(alpha=kwargs.pop("alpha", 1.0)),
        "lasso": Lasso(alpha=kwargs.pop("alpha", 1.0)),
        "random_forest": RandomForestRegressor(
            n_estimators=kwargs.pop("n_estimators", 100),
            max_depth=kwargs.pop("max_depth", None),
            random_state=42,
        ),
        "xgboost": xgb.XGBRegressor(
            n_estimators=kwargs.pop("n_estimators", 100),
            max_depth=kwargs.pop("max_depth", 6),
            learning_rate=kwargs.pop("learning_rate", 0.1),
            random_state=42,
        ),
    }
    model = models[model_type]
    model.fit(X_train, y_train)
    params = model.get_params() if hasattr(model, "get_params") else {}
    return model, {"模型": model_type, "参数": {k: str(v) for k, v in params.items()}}


def evaluate_regression(model, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    """评估回归模型"""
    y_pred = model.predict(X_test)
    return {
        "R²": round(r2_score(y_test, y_pred), 4),
        "MSE": round(mean_squared_error(y_test, y_pred), 4),
        "RMSE": round(np.sqrt(mean_squared_error(y_test, y_pred)), 4),
        "MAE": round(mean_absolute_error(y_test, y_pred), 4),
    }


def feature_importance(model, feature_names: list) -> tuple[pd.DataFrame, go.Figure]:
    """提取特征重要性"""
    if hasattr(model, "feature_importances_"):
        importance = model.feature_importances_
    elif hasattr(model, "coef_"):
        importance = np.abs(model.coef_)
        if importance.ndim > 1:
            importance = importance.mean(axis=0)
    else:
        return pd.DataFrame(), go.Figure()

    df_imp = pd.DataFrame({"特征": feature_names, "重要性": importance})
    df_imp = df_imp.sort_values("重要性", ascending=True)

    fig = go.Figure(go.Bar(x=df_imp["重要性"], y=df_imp["特征"], orientation="h"))
    fig.update_layout(title="特征重要性", height=400)
    return df_imp, fig


def residual_plot(y_test: pd.Series, y_pred: np.ndarray) -> go.Figure:
    """残差诊断图"""
    residuals = y_test.values - y_pred
    fig = make_subplots(rows=1, cols=2, subplot_titles=("残差分布", "预测值 vs 残差"))

    fig.add_trace(go.Histogram(x=residuals, nbinsx=30, name="残差"), row=1, col=1)
    fig.add_trace(
        go.Scatter(x=y_pred, y=residuals, mode="markers",
                   marker=dict(size=6, opacity=0.5), name="残差"),
        row=1, col=2,
    )
    fig.add_hline(y=0, line_dash="dash", line_color="red", row=1, col=2)
    fig.update_layout(height=400, showlegend=False)
    return fig


def train_cluster(
    df: pd.DataFrame, columns: list, n_clusters: int = 3, random_state: int = 42
) -> tuple[pd.DataFrame, dict, go.Figure]:
    """K-Means 聚类"""
    X = df[columns].fillna(0)
    model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    labels = model.fit_predict(X)

    df = df.copy()
    df["聚类标签"] = labels

    score = silhouette_score(X, labels) if n_clusters > 1 else 0
    summary = {
        "聚类数": n_clusters,
        "轮廓系数": round(score, 4),
        "各类样本数": pd.Series(labels).value_counts().to_dict(),
    }

    # 使用前两个特征绘制散点图
    fig = go.Figure()
    for cluster_id in range(n_clusters):
        mask = labels == cluster_id
        fig.add_trace(
            go.Scatter(
                x=df[mask][columns[0]], y=df[mask][columns[1]],
                mode="markers", name=f"聚类 {cluster_id}",
                marker=dict(size=8, opacity=0.6),
            )
        )
    fig.update_layout(title=f"K-Means 聚类 (k={n_clusters})",
                      xaxis_title=columns[0], yaxis_title=columns[1])
    return df, summary, fig
```

- [ ] **Step 2: 提交**

```bash
git add engine/modeler.py
git commit -m "feat: 添加建模与评估模块 engine/modeler.py"
```

---

### Task 1.7: engine/llm_agent.py — LLM 编排

**Files:**
- Write: `engine/llm_agent.py`

- [ ] **Step 1: 编写 LLM Agent 模块**

```python
"""LLM Agent 编排模块"""
import json
import yaml
import os
from dataclasses import dataclass, field
from typing import Optional
from openai import OpenAI
from engine.config import LLMConfig


@dataclass
class AnalysisStep:
    id: int
    type: str  # 'clean' | 'eda' | 'feature' | 'model' | 'report'
    description: str
    params: dict = field(default_factory=dict)
    status: str = "pending"  # 'pending' | 'running' | 'done' | 'error'
    result_summary: str = ""


@dataclass
class AnalysisPlan:
    steps: list = field(default_factory=list)
    raw_response: str = ""


@dataclass
class ChatMessage:
    role: str  # 'user' | 'assistant' | 'system'
    content: str


class LLMAdapter:
    """兼容 OpenAI API 格式的通用适配器"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = OpenAI(base_url=config.base_url, api_key=config.api_key)

    def chat(self, messages: list[dict]) -> str:
        """发送对话请求"""
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        return response.choices[0].message.content

    def test_connection(self) -> tuple[bool, str]:
        """测试 API 连接"""
        try:
            resp = self.chat([{"role": "user", "content": "你好，请回复'连接成功'"}])
            return True, resp
        except Exception as e:
            return False, str(e)


class AnalysisAgent:
    """数据分析 Agent — 负责理解需求、规划步骤、解释结果"""

    SYSTEM_PROMPT = """你是一个汽车工程数据分析助手。你的用户是汽车研发工程师。

你的职责：
1. 理解工程师的数据分析需求
2. 将需求拆解为具体的分析步骤
3. 用通俗语言解释分析结果

分析步骤类型（type）取值：
- clean: 数据清洗（缺失值、异常值、去重）
- eda: 探索性分析（描述统计、分布图、相关性分析）
- feature: 特征工程（标准化、编码、特征选择）
- model: 建模（回归、分类、聚类）
- report: 报告生成

回复格式（严格 JSON）：
{
  "steps": [
    {"type": "clean", "description": "...", "params": {}},
    {"type": "eda", "description": "...", "params": {"columns": [], "method": ""}},
    {"type": "model", "description": "...", "params": {"target": "", "model_type": ""}}
  ],
  "explanation": "用通俗语言向工程师解释这个分析计划"
}"""

    def __init__(self, llm_adapter: LLMAdapter, knowledge_dir: str = "knowledge"):
        self.llm = llm_adapter
        self.knowledge_dir = knowledge_dir
        self.chat_history: list[dict] = []

    def load_knowledge(self) -> str:
        """加载领域知识"""
        knowledge_parts = []
        for filename in ["indicators.yaml", "templates.yaml"]:
            path = os.path.join(self.knowledge_dir, filename)
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    content = yaml.safe_load(f)
                    knowledge_parts.append(yaml.dump(content, allow_unicode=True))
        return "\n".join(knowledge_parts)

    def build_system_prompt(self) -> str:
        """构建包含领域知识的 system prompt"""
        knowledge = self.load_knowledge()
        if knowledge:
            return self.SYSTEM_PROMPT + f"\n\n## 领域知识\n{knowledge}"
        return self.SYSTEM_PROMPT

    def plan_analysis(self, user_input: str, df_info: dict) -> AnalysisPlan:
        """根据用户输入和数据信息生成分析计划"""
        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": f"""当前数据集信息：
- 行数: {df_info.get('shape', [0, 0])[0]}
- 列数: {df_info.get('shape', [0, 0])[1]}
- 数值列: {df_info.get('numeric_columns', [])}
- 分类型列: {df_info.get('categorical_columns', [])}
- 列名: {df_info.get('columns', [])}

用户的请求: {user_input}

请给出分析计划（JSON 格式）。"""},
        ]

        response = self.llm.chat(messages)
        self.chat_history.append({"role": "user", "content": user_input})
        self.chat_history.append({"role": "assistant", "content": response})

        try:
            # 尝试解析 JSON
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response

            data = json.loads(json_str.strip())
            steps = [
                AnalysisStep(id=i + 1, **s)
                for i, s in enumerate(data.get("steps", []))
            ]
            return AnalysisPlan(steps=steps, raw_response=data.get("explanation", response))
        except (json.JSONDecodeError, KeyError):
            return AnalysisPlan(steps=[], raw_response=response)

    def explain_result(self, step: AnalysisStep, metrics: dict) -> str:
        """用自然语言解释分析结果"""
        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": f"""请用汽车工程师能理解的语言解释以下分析结果：

步骤类型: {step.type}
步骤描述: {step.description}
分析结果: {json.dumps(metrics, ensure_ascii=False)}

请用 3-5 句话解释这些数字的含义，以及它们对工程师意味着什么。"""},
        ]
        explanation = self.llm.chat(messages)
        self.chat_history.append({"role": "assistant", "content": explanation})
        return explanation

    def suggest_name(self, context: str) -> str:
        """根据分析内容建议项目名称"""
        messages = [
            {"role": "user", "content": f"请为以下数据分析项目起一个简短的中文名称（8个字以内）:\n{context}"}
        ]
        return self.llm.chat(messages).strip().strip('"').strip("'")
```

- [ ] **Step 2: 提交**

```bash
git add engine/llm_agent.py
git commit -m "feat: 添加 LLM Agent 编排模块 engine/llm_agent.py"
```

---

### Task 1.8: engine/reporter.py — 报告生成

**Files:**
- Write: `engine/reporter.py`

- [ ] **Step 1: 编写报告生成模块**

```python
"""报告生成模块"""
import os
import json
from datetime import datetime
from typing import Optional
import plotly.graph_objects as go


REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }}</title>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<style>
  body { font-family: 'Microsoft YaHei', sans-serif; max-width: 1100px; margin: 0 auto; padding: 40px 20px; color: #333; }
  h1 { border-bottom: 3px solid #1a73e8; padding-bottom: 10px; }
  h2 { color: #1a73e8; margin-top: 40px; }
  .meta { color: #888; font-size: 14px; margin-bottom: 30px; }
  .chart { margin: 20px 0; border: 1px solid #eee; border-radius: 8px; padding: 10px; }
  table { border-collapse: collapse; width: 100%; margin: 15px 0; }
  th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
  th { background: #f5f5f5; }
  .summary-box { background: #f0f7ff; border-left: 4px solid #1a73e8; padding: 15px 20px; margin: 20px 0; border-radius: 4px; }
  .conclusion { background: #f5fff0; border-left: 4px solid #34a853; padding: 15px 20px; margin: 20px 0; border-radius: 4px; }
</style>
</head>
<body>
<h1>{{ title }}</h1>
<p class="meta">生成时间: {{ created_at }} | 数据: {{ data_source }} ({{ rows }} 行 × {{ cols }} 列)</p>

{% for section in sections %}
<h2>{{ section.title }}</h2>
{% if section.text %}
<div class="summary-box">{{ section.text }}</div>
{% endif %}
{% if section.table %}
{{ section.table }}
{% endif %}
{% if section.chart_html %}
<div class="chart">{{ section.chart_html }}</div>
{% endif %}
{% endfor %}

<div class="conclusion">
<h2>分析结论</h2>
<p>{{ conclusion }}</p>
</div>
</body>
</html>"""


def chart_to_html(fig: go.Figure, chart_id: str) -> str:
    """将 plotly 图表转为可嵌入 HTML 的 div"""
    return fig.to_html(full_html=False, include_plotlyjs=False, div_id=chart_id)


def save_chart(fig: go.Figure, filepath: str) -> str:
    """保存图表为独立 HTML 文件"""
    fig.write_html(filepath)
    return filepath


def dataframe_to_html_table(df_data: list[dict], columns: list = None, max_rows: int = 20) -> str:
    """将字典列表转换为 HTML 表格"""
    if not df_data:
        return "<p>无数据</p>"
    cols = columns or list(df_data[0].keys())
    rows_html = ""
    for row in df_data[:max_rows]:
        cells = "".join(f"<td>{row.get(c, '')}</td>" for c in cols)
        rows_html += f"<tr>{cells}</tr>"
    header = "".join(f"<th>{c}</th>" for c in cols)
    return f"<table><thead><tr>{header}</tr></thead><tbody>{rows_html}</tbody></table>"


def generate_html_report(
    title: str,
    sections: list[dict],
    conclusion: str,
    data_source: str,
    rows: int,
    cols: int,
    charts: Optional[list] = None,
) -> str:
    """生成完整 HTML 报告

    sections = [
        {"title": "描述统计", "text": "...", "table": "<table>...</table>", "chart_html": "..."},
        ...
    ]
    """
    from jinja2 import Template
    template = Template(REPORT_TEMPLATE)
    return template.render(
        title=title,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        data_source=data_source,
        rows=rows,
        cols=cols,
        sections=sections,
        conclusion=conclusion,
    )


def build_section(title: str, text: str = "", table: str = "", chart_html: str = "") -> dict:
    return {"title": title, "text": text, "table": table, "chart_html": chart_html}
```

- [ ] **Step 2: 提交**

```bash
git add engine/reporter.py
git commit -m "feat: 添加报告生成模块 engine/reporter.py"
```

---

### Task 1.9: engine/sandbox.py — 安全执行

**Files:**
- Write: `engine/sandbox.py`

- [ ] **Step 1: 编写安全沙箱模块**

```python
"""安全代码执行沙箱"""
import subprocess
import tempfile
import os
import re
from typing import Optional


FORBIDDEN_IMPORTS = [
    "os", "subprocess", "sys", "shutil", "socket", "requests",
    "urllib", "http", "ftplib", "telnetlib", "smtplib",
    "pickle", "marshal", "ctypes", "multiprocessing",
    "importlib", "__import__", "eval", "exec", "compile",
]

FORBIDDEN_FUNCTIONS = [
    "open(", "exec(", "eval(", "compile(", "__import__(",
    "globals()", "locals()", "getattr(", "setattr(", "delattr(",
]

ALLOWED_IMPORTS = [
    "pandas", "numpy", "scipy", "sklearn", "plotly", "matplotlib",
    "json", "csv", "math", "statistics", "collections", "itertools",
    "functools", "datetime", "typing", "warnings",
]


def validate_code(code: str) -> tuple[bool, Optional[str]]:
    """验证代码安全性"""
    for imp in FORBIDDEN_IMPORTS:
        pattern = rf'\bimport\s+{imp}\b|\bfrom\s+{imp}\b'
        if re.search(pattern, code):
            forbidden = True
            # 检查是否在允许列表中
            if imp not in ALLOWED_IMPORTS:
                return False, f"禁止使用模块: {imp}"

    for func in FORBIDDEN_FUNCTIONS:
        if func in code:
            return False, f"禁止使用函数: {func}"

    return True, None


def run_sandbox(code: str, timeout: int = 30) -> tuple[bool, str, str]:
    """在子进程中安全执行 Python 代码

    返回: (success, stdout, stderr)
    """
    is_safe, error = validate_code(code)
    if not is_safe:
        return False, "", error

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(code)
        tmp_path = f.name

    try:
        result = subprocess.run(
            ["python", tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd(),
            env={
                "PATH": os.environ.get("PATH", ""),
                "PYTHONPATH": os.getcwd(),
            },
        )
        success = result.returncode == 0
        return success, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"代码执行超时 ({timeout}秒)"
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
```

- [ ] **Step 2: 提交**

```bash
git add engine/sandbox.py
git commit -m "feat: 添加安全执行沙箱模块 engine/sandbox.py"
```

---

### Task 1.10: engine/project_manager.py — 项目管理

**Files:**
- Write: `engine/project_manager.py`

- [ ] **Step 1: 编写项目管理模块**

```python
"""分析项目管理模块"""
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
import pandas as pd


class ProjectManager:
    """管理分析项目的创建、保存、加载"""

    def __init__(self, projects_dir: str = "projects"):
        self.projects_dir = Path(projects_dir)
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def create_project(self, name: str, data_file: Optional[str] = None) -> str:
        """创建新项目，返回 project_id"""
        project_id = uuid.uuid4().hex[:12]
        project_path = self.projects_dir / project_id
        project_path.mkdir(parents=True)
        (project_path / "data").mkdir()
        (project_path / "charts").mkdir()
        (project_path / "reports").mkdir()

        meta = {
            "name": name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "data_file": os.path.basename(data_file) if data_file else None,
        }
        with open(project_path / "meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        with open(project_path / "state.json", "w", encoding="utf-8") as f:
            json.dump({"steps": [], "current_step": 0}, f, ensure_ascii=False, indent=2)

        with open(project_path / "chat_history.json", "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

        if data_file and os.path.exists(data_file):
            df = pd.read_csv(data_file) if data_file.endswith(".csv") else pd.read_excel(data_file)
            df.to_csv(project_path / "data" / "original.csv", index=False)

        return project_id

    def list_projects(self) -> list[dict]:
        """列出所有项目"""
        projects = []
        for pdir in self.projects_dir.iterdir():
            if pdir.is_dir():
                meta_path = pdir / "meta.json"
                if meta_path.exists():
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    state_path = pdir / "state.json"
                    steps_count = 0
                    if state_path.exists():
                        with open(state_path, "r", encoding="utf-8") as f:
                            state = json.load(f)
                            steps_count = len(state.get("steps", []))
                    projects.append({
                        "id": pdir.name,
                        **meta,
                        "steps_count": steps_count,
                    })
        projects.sort(key=lambda p: p["created_at"], reverse=True)
        return projects

    def load_project(self, project_id: str) -> dict:
        """加载项目完整数据"""
        pdir = self.projects_dir / project_id
        if not pdir.exists():
            raise FileNotFoundError(f"项目 {project_id} 不存在")

        with open(pdir / "meta.json", "r", encoding="utf-8") as f:
            meta = json.load(f)

        state = {"steps": [], "current_step": 0}
        state_path = pdir / "state.json"
        if state_path.exists():
            with open(state_path, "r", encoding="utf-8") as f:
                state = json.load(f)

        chat_history = []
        chat_path = pdir / "chat_history.json"
        if chat_path.exists():
            with open(chat_path, "r", encoding="utf-8") as f:
                chat_history = json.load(f)

        df = None
        data_path = pdir / "data" / "original.csv"
        if data_path.exists():
            df = pd.read_csv(data_path)

        return {
            "meta": meta,
            "state": state,
            "chat_history": chat_history,
            "dataframe": df,
        }

    def save_state(self, project_id: str, state: dict) -> None:
        """保存分析状态"""
        pdir = self.projects_dir / project_id
        with open(pdir / "state.json", "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2, default=str)

        # 更新 meta 时间
        meta_path = pdir / "meta.json"
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        meta["updated_at"] = datetime.now().isoformat()
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    def save_chat_history(self, project_id: str, chat_history: list) -> None:
        """保存对话历史"""
        pdir = self.projects_dir / project_id
        with open(pdir / "chat_history.json", "w", encoding="utf-8") as f:
            json.dump(chat_history, f, ensure_ascii=False, indent=2)

    def save_chart(self, project_id: str, chart_name: str, fig) -> str:
        """保存图表文件，返回路径"""
        pdir = self.projects_dir / project_id / "charts"
        filepath = pdir / f"{chart_name}.html"
        fig.write_html(str(filepath))
        return str(filepath)

    def save_report(self, project_id: str, html_content: str) -> str:
        """保存报告文件，返回路径"""
        pdir = self.projects_dir / project_id / "reports"
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = pdir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        return str(filepath)

    def delete_project(self, project_id: str) -> None:
        """删除项目"""
        import shutil
        pdir = self.projects_dir / project_id
        if pdir.exists():
            shutil.rmtree(pdir)

    def rename_project(self, project_id: str, new_name: str) -> None:
        """重命名项目"""
        pdir = self.projects_dir / project_id
        meta_path = pdir / "meta.json"
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        meta["name"] = new_name
        meta["updated_at"] = datetime.now().isoformat()
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
```

- [ ] **Step 2: 提交**

```bash
git add engine/project_manager.py
git commit -m "feat: 添加项目管理模块 engine/project_manager.py"
```

---

### Task 1.11: engine/knowledge.py — 知识库管理

**Files:**
- Write: `engine/knowledge.py`

- [ ] **Step 1: 编写知识库模块**

```python
"""领域知识库管理模块"""
import os
import yaml
import re
from typing import Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class KnowledgeBase:
    """轻量领域知识库 — YAML + TF-IDF 检索"""

    def __init__(self, knowledge_dir: str = "knowledge"):
        self.knowledge_dir = knowledge_dir
        self._indicators: dict = {}
        self._templates: dict = {}
        self._documents: list[dict] = []
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._doc_vectors = None
        self.load()

    def load(self) -> None:
        """加载所有知识库文件"""
        # 加载指标知识
        indicators_path = os.path.join(self.knowledge_dir, "indicators.yaml")
        if os.path.exists(indicators_path):
            with open(indicators_path, "r", encoding="utf-8") as f:
                self._indicators = yaml.safe_load(f) or {}

        # 加载分析模板
        templates_path = os.path.join(self.knowledge_dir, "templates.yaml")
        if os.path.exists(templates_path):
            with open(templates_path, "r", encoding="utf-8") as f:
                self._templates = yaml.safe_load(f) or {}

        # 加载参考文档（TXT 文件）
        ref_dir = os.path.join(self.knowledge_dir, "references")
        if os.path.exists(ref_dir):
            self._documents = []
            texts = []
            for filename in os.listdir(ref_dir):
                if filename.endswith((".txt", ".md")):
                    path = os.path.join(ref_dir, filename)
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    # 按段落分块
                    chunks = [c.strip() for c in content.split("\n\n") if c.strip()]
                    for chunk in chunks:
                        if len(chunk) > 20:
                            self._documents.append({"source": filename, "content": chunk})
                            texts.append(chunk)

            if texts:
                self._vectorizer = TfidfVectorizer(max_features=500)
                self._doc_vectors = self._vectorizer.fit_transform(texts)

    def get_indicator_info(self, name: str) -> Optional[dict]:
        """查询指标信息"""
        return self._indicators.get(name)

    def get_template(self, name: str) -> Optional[dict]:
        """查询分析模板"""
        return self._templates.get(name)

    def search_indicators(self, keyword: str) -> list[dict]:
        """关键词搜索指标"""
        results = []
        for name, info in self._indicators.items():
            if keyword in name or keyword in info.get("desc", ""):
                results.append({"name": name, **info})
        return results

    def search_documents(self, query: str, top_k: int = 5) -> list[dict]:
        """TF-IDF 检索参考文档"""
        if self._vectorizer is None:
            return []
        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._doc_vectors)[0]
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            if scores[idx] > 0.05:  # 最低相似度阈值
                results.append({
                    **self._documents[idx],
                    "score": float(scores[idx]),
                })
        return results

    def list_indicators(self) -> list[str]:
        """列出所有指标名称"""
        return list(self._indicators.keys())

    def list_templates(self) -> list[str]:
        """列出所有模板名称"""
        return list(self._templates.keys())

    def get_context_for_llm(self, query: str = "") -> str:
        """生成注入 LLM prompt 的知识上下文"""
        parts = []

        if self._indicators:
            parts.append("## 领域指标知识\n")
            for name, info in self._indicators.items():
                parts.append(f"- {name}: {info.get('desc', '')} (单位: {info.get('unit', 'N/A')})")

        if self._templates:
            parts.append("\n## 分析模板\n")
            for name, tmpl in self._templates.items():
                parts.append(f"- {name}: {'→'.join(tmpl.get('steps', []))}")

        if query:
            docs = self.search_documents(query)
            if docs:
                parts.append("\n## 相关参考文档\n")
                for doc in docs[:3]:
                    parts.append(doc["content"])

        return "\n".join(parts)
```

- [ ] **Step 2: 提交**

```bash
git add engine/knowledge.py
git commit -m "feat: 添加知识库管理模块 engine/knowledge.py"
```

---

## Phase 2: Streamlit 应用

### Task 2.1: streamlit-app/app.py — 应用入口

**Files:**
- Write: `streamlit-app/app.py`

- [ ] **Step 1: 编写 Streamlit 入口**

```python
"""数据科学家 Agent — Streamlit 版"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from engine.config import load_config, save_config, LLM_PRESETS

st.set_page_config(
    page_title="数据科学家 Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    st.sidebar.title("📊 数据科学家 Agent")

    # 加载配置
    if "config" not in st.session_state:
        st.session_state.config = load_config()

    # 侧边栏导航
    page = st.sidebar.radio(
        "导航",
        ["📂 数据上传", "🔬 分析对话", "📋 报告导出", "⚙ 设置", "📁 历史项目"],
    )

    st.sidebar.divider()
    if "project_name" in st.session_state:
        st.sidebar.caption(f"当前项目: {st.session_state.project_name}")

    # 路由到各页面
    if page == "📂 数据上传":
        from pages import data_upload
        data_upload.show()
    elif page == "🔬 分析对话":
        from pages import analysis
        analysis.show()
    elif page == "📋 报告导出":
        from pages import report
        report.show()
    elif page == "⚙ 设置":
        from pages import settings
        settings.show()
    elif page == "📁 历史项目":
        from pages import history
        history.show()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 提交**

```bash
git add streamlit-app/app.py
git commit -m "feat: 添加 Streamlit 应用入口"
```

---

### Task 2.2: streamlit-app/pages/ — 页面模块

**Files:**
- Write: `streamlit-app/pages/data_upload.py`
- Write: `streamlit-app/pages/settings.py`
- Write: `streamlit-app/pages/history.py`

- [ ] **Step 1: 编写数据上传页**

```python
"""数据上传页面"""
import streamlit as st
import pandas as pd
import os
from engine.data_loader import load_file, get_data_info
from engine.project_manager import ProjectManager


def show():
    st.title("📂 数据上传")

    col1, col2 = st.columns([1, 1])
    with col1:
        uploaded_file = st.file_uploader(
            "上传数据文件",
            type=["csv", "xlsx", "xls", "json", "tsv"],
            help="支持 CSV、Excel、JSON 格式",
        )

    if uploaded_file is not None:
        # 保存临时文件
        tmp_path = f"temp_{uploaded_file.name}"
        with open(tmp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        try:
            df = load_file(tmp_path)
            st.session_state.df = df
            st.session_state.data_info = get_data_info(df)

            # 数据预览
            st.subheader("数据预览")
            st.dataframe(df.head(50), use_container_width=True)

            # 基本信息
            info = st.session_state.data_info
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

            # 创建项目
            project_name = st.text_input(
                "项目名称",
                value=uploaded_file.name.rsplit(".", 1)[0],
            )
            if st.button("创建分析项目", type="primary"):
                pm = ProjectManager()
                project_id = pm.create_project(project_name)

                # 保存数据
                data_path = os.path.join("projects", project_id, "data", "original.csv")
                df.to_csv(data_path, index=False)

                st.session_state.project_id = project_id
                st.session_state.project_name = project_name
                st.success(f"项目 '{project_name}' 创建成功！请切换到「分析对话」页面开始分析。")

        finally:
            os.unlink(tmp_path)
```

- [ ] **Step 2: 编写设置页**

```python
"""设置页面"""
import streamlit as st
from engine.config import load_config, save_config, LLMConfig, LLM_PRESETS


def show():
    st.title("⚙ 设置")

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
```

- [ ] **Step 3: 编写历史项目页**

```python
"""历史项目页面"""
import streamlit as st
from engine.project_manager import ProjectManager


def show():
    st.title("📁 历史项目")

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
                    report_dir = f"projects/{proj['id']}/reports"
                    st.info(f"报告目录: {report_dir}")
            with col4:
                if st.button("删除", key=f"del_{proj['id']}", type="secondary"):
                    pm.delete_project(proj['id'])
                    st.rerun()
        st.divider()
```

- [ ] **Step 4: 提交**

```bash
git add streamlit-app/pages/
git commit -m "feat: 添加 Streamlit 数据上传、设置、历史项目页面"
```

---

### Task 2.3: streamlit-app/pages/analysis.py — 分析对话页

**Files:**
- Write: `streamlit-app/pages/analysis.py`

- [ ] **Step 1: 编写分析对话页**

```python
"""分析对话页面"""
import streamlit as st
import pandas as pd
import json
from engine.data_loader import get_data_info
from engine.config import load_config
from engine.llm_agent import LLMAdapter, AnalysisAgent, AnalysisStep
from engine.data_cleaner import clean_pipeline
from engine.eda import eda_pipeline, correlation_matrix, scatter_plot
from engine.modeler import train_regression, evaluate_regression, split_data, feature_importance, residual_plot
from engine.reporter import chart_to_html, build_section
from engine.project_manager import ProjectManager
import plotly.graph_objects as go


def show():
    st.title("🔬 分析对话")

    if "df" not in st.session_state:
        st.warning("请先在「数据上传」页面上传数据并创建项目。")
        return

    df = st.session_state.df
    data_info = st.session_state.data_info

    # 初始化 agent
    if "agent" not in st.session_state:
        config = st.session_state.get("config", load_config())
        adapter = LLMAdapter(config.llm)
        st.session_state.agent = AnalysisAgent(adapter)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "analysis_state" not in st.session_state:
        st.session_state.analysis_state = {"steps": [], "current_step": 0}

    # 三栏布局
    left_col, center_col, right_col = st.columns([2, 3, 1.5])

    # === 左侧: 对话区 ===
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

            # LLM 生成分析计划
            agent = st.session_state.agent
            plan = agent.plan_analysis(user_input, data_info)
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

            # 同步到 agent
            st.session_state.agent.chat_history = st.session_state.chat_history

            # 保存对话历史
            if "project_id" in st.session_state:
                pm = ProjectManager()
                pm.save_chat_history(st.session_state.project_id,
                                     st.session_state.chat_history)

            st.rerun()

    # === 中间: 结果展示区 ===
    with center_col:
        st.subheader("📈 结果")

        if "last_result" in st.session_state:
            result = st.session_state.last_result
            if result.get("text"):
                st.markdown(result["text"])
            if result.get("charts"):
                for chart in result["charts"]:
                    st.plotly_chart(chart, use_container_width=True)
            if result.get("dataframe") is not None:
                st.dataframe(result["dataframe"], use_container_width=True)

    # === 右侧: 步骤导航 ===
    with right_col:
        st.subheader("📋 分析步骤")

        steps = st.session_state.analysis_state.get("steps", [])
        if not steps:
            st.info("在对话区描述你的分析需求，Agent 将为你规划步骤。")
            return

        for i, step in enumerate(steps):
            status_icon = {"pending": "○", "running": "⟳", "done": "✓", "error": "✗"}
            icon = status_icon.get(step.get("status", "pending"), "○")

            col_s, col_b = st.columns([4, 1])
            with col_s:
                st.markdown(f"{icon} **步骤 {i+1}**: {step['description'][:30]}...")
            with col_b:
                if step["status"] == "pending" and st.button("▶", key=f"run_{i}"):
                    execute_step(i, step, df)

        if steps and all(s.get("status") == "done" for s in steps):
            st.success("所有步骤已完成！前往「报告导出」生成报告。")


def execute_step(step_index: int, step_def: dict, df: pd.DataFrame):
    """执行单个分析步骤"""
    step_type = step_def["type"]
    params = step_def.get("params", {})
    text = ""
    charts = []
    result_df = df

    try:
        if step_type == "clean":
            result_df, summary = clean_pipeline(df, **params)
            text = f"### 数据清洗完成\n```json\n{json.dumps(summary, ensure_ascii=False, indent=2)}\n```"

        elif step_type == "eda":
            numeric_cols = params.get("columns") or df.select_dtypes(include=["number"]).columns.tolist()
            result = eda_pipeline(df, numeric_columns=numeric_cols)
            charts = result["charts"]
            text = f"### 探索性分析\n- 行数: {result['row_count']}\n- 列数: {result['column_count']}"

        elif step_type == "model":
            target = params.get("target", "")
            model_type = params.get("model_type", "linear")

            # 准备数据
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

        elif step_type == "report":
            text = "报告生成请前往「报告导出」页面。"

        st.session_state.analysis_state["steps"][step_index]["status"] = "done"
        st.session_state.last_result = {
            "text": text, "charts": charts, "dataframe": result_df.head(50)
        }

        # 保存状态
        if "project_id" in st.session_state:
            pm = ProjectManager()
            pm.save_state(st.session_state.project_id, st.session_state.analysis_state)

            # 保存图表
            for j, chart in enumerate(charts):
                pm.save_chart(st.session_state.project_id,
                              f"step{step_index+1}_chart{j+1}", chart)

    except Exception as e:
        st.session_state.analysis_state["steps"][step_index]["status"] = "error"
        st.session_state.last_result = {"text": f"执行出错: {str(e)}", "charts": [], "dataframe": None}

    st.rerun()
```

- [ ] **Step 2: 编写报告导出页**

```python
"""报告导出页面"""
import streamlit as st
from engine.reporter import generate_html_report, build_section, chart_to_html
from engine.project_manager import ProjectManager
import json
import os


def show():
    st.title("📋 报告导出")

    if "project_id" not in st.session_state:
        st.warning("请先创建分析项目。")
        return

    st.markdown("### 报告内容")

    # 基础信息
    df = st.session_state.get("df")
    project_name = st.session_state.get("project_name", "未命名项目")
    project_id = st.session_state.get("project_id")

    report_title = st.text_input("报告标题", value=f"{project_name} — 分析报告")

    # 收集分析步骤结果
    sections = []
    analysis_state = st.session_state.get("analysis_state", {})
    for step in analysis_state.get("steps", []):
        if step["status"] == "done":
            sections.append(build_section(
                title=step["description"],
                text=f"步骤类型: {step['type']}",
            ))

    # 如果有清除结果
    if "last_result" in st.session_state and st.session_state.last_result.get("text"):
        sections.append(build_section(
            title="详细结果",
            text=st.session_state.last_result["text"],
        ))

    conclusion = st.text_area("分析结论", placeholder="请在此填写或让 Agent 总结分析结论...",
                              height=150)

    if st.button("生成报告", type="primary"):
        rows, cols = df.shape if df is not None else (0, 0)
        html = generate_html_report(
            title=report_title,
            sections=sections,
            conclusion=conclusion or "分析完成",
            data_source=project_name,
            rows=rows,
            cols=cols,
        )

        pm = ProjectManager()
        report_path = pm.save_report(project_id, html)
        st.success(f"报告已生成: {report_path}")

        # 预览和下载
        with st.expander("报告预览"):
            st.components.v1.html(html, height=600, scrolling=True)

        with open(report_path, "r", encoding="utf-8") as f:
            st.download_button(
                "下载报告 (HTML)",
                data=f.read(),
                file_name=f"{project_name}_report.html",
                mime="text/html",
            )
```

- [ ] **Step 3: 提交**

```bash
git add streamlit-app/pages/
git commit -m "feat: 添加 Streamlit 分析对话和报告导出页面"
```

---

## Phase 3: FastAPI + Vue 3 应用

### Task 3.1: fastapi-app/backend/main.py — FastAPI 入口

**Files:**
- Write: `fastapi-app/backend/main.py`
- Write: `fastapi-app/backend/models/schemas.py`

- [ ] **Step 1: 编写数据模型**

```python
"""Pydantic 数据模型"""
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class LLMConfigSchema(BaseModel):
    name: str = "DeepSeek"
    base_url: str = ""
    api_key: str = ""
    model: str = ""
    temperature: float = 0.3
    max_tokens: int = 4096


class ProjectMeta(BaseModel):
    id: str
    name: str
    created_at: str
    updated_at: str
    data_file: Optional[str] = None
    steps_count: int = 0


class AnalysisStepSchema(BaseModel):
    type: str
    description: str
    params: dict = {}
    status: str = "pending"


class AnalysisRequest(BaseModel):
    project_id: str
    user_input: str


class StepExecuteRequest(BaseModel):
    project_id: str
    step_index: int


class GenerateReportRequest(BaseModel):
    project_id: str
    title: str
    conclusion: str = ""


class ChatMessage(BaseModel):
    role: str
    content: str
```

- [ ] **Step 2: 编写 FastAPI 入口**

```python
"""FastAPI 应用入口"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import json
import tempfile
import shutil

from engine.data_loader import load_file, get_data_info
from engine.config import load_config, save_config, LLMConfig
from engine.llm_agent import LLMAdapter, AnalysisAgent
from engine.project_manager import ProjectManager
from engine.data_cleaner import clean_pipeline
from engine.eda import eda_pipeline
from engine.modeler import train_regression, evaluate_regression, split_data, feature_importance, residual_plot
from engine.reporter import generate_html_report, build_section

from models.schemas import (
    LLMConfigSchema, AnalysisRequest, StepExecuteRequest,
    GenerateReportRequest, ChatMessage,
)

app = FastAPI(title="数据科学家 Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局状态（生产环境应使用 Redis 或数据库）
sessions: dict = {}
pm = ProjectManager()


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# === 配置 ===
@app.get("/api/config")
async def get_config():
    return load_config().to_dict()


@app.post("/api/config")
async def update_config(config: LLMConfigSchema):
    app_config = load_config()
    app_config.llm = LLMConfig(**config.model_dump())
    save_config(app_config)
    return {"status": "ok"}


@app.post("/api/config/test")
async def test_connection(config: LLMConfigSchema):
    adapter = LLMAdapter(LLMConfig(**config.model_dump()))
    ok, msg = adapter.test_connection()
    return {"success": ok, "message": msg}


# === 数据上传 ===
@app.post("/api/data/upload")
async def upload_data(file: UploadFile = File(...)):
    tmp_path = f"temp_{file.filename}"
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        df = load_file(tmp_path)
        info = get_data_info(df)
        return {"columns": info["columns"], "dtypes": info["dtypes"],
                "shape": list(info["shape"]), "preview": df.head(10).to_dict(orient="records")}
    finally:
        os.unlink(tmp_path)


# === 项目管理 ===
@app.get("/api/projects")
async def list_projects():
    return pm.list_projects()


@app.post("/api/projects")
async def create_project(name: str, file: Optional[UploadFile] = File(None)):
    data_path = None
    if file:
        tmp_path = f"temp_{file.filename}"
        with open(tmp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        data_path = tmp_path

    project_id = pm.create_project(name, data_path)

    if data_path:
        os.unlink(data_path)

    return {"project_id": project_id}


@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    data = pm.load_project(project_id)
    meta = data["meta"]
    state = data["state"]
    chat = data["chat_history"]

    preview = None
    if data["dataframe"] is not None:
        preview = data["dataframe"].head(10).to_dict(orient="records")

    return {
        "meta": meta,
        "state": state,
        "chat_history": chat,
        "preview": preview,
        "data_info": get_data_info(data["dataframe"]) if data["dataframe"] is not None else {},
    }


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    pm.delete_project(project_id)
    return {"status": "ok"}


# === 分析 ===
@app.post("/api/analysis/plan")
async def plan_analysis(req: AnalysisRequest):
    config = load_config()
    adapter = LLMAdapter(config.llm)
    agent = AnalysisAgent(adapter)

    data = pm.load_project(req.project_id)
    df = data["dataframe"]
    if df is None:
        raise HTTPException(400, "项目无数据")

    info = get_data_info(df)
    plan = agent.plan_analysis(req.user_input, info)

    # 更新项目状态
    state = data["state"]
    state["steps"] = [{"type": s.type, "description": s.description,
                        "params": s.params, "status": "pending"} for s in plan.steps]
    pm.save_state(req.project_id, state)

    pm.save_chat_history(req.project_id, agent.chat_history)

    return {
        "explanation": plan.raw_response,
        "steps": state["steps"],
    }


@app.post("/api/analysis/execute")
async def execute_step(req: StepExecuteRequest):
    data = pm.load_project(req.project_id)
    df = data["dataframe"]
    state = data["state"]
    step = state["steps"][req.step_index]

    try:
        result_text = ""
        charts = []

        if step["type"] == "clean":
            df, summary = clean_pipeline(df, **step.get("params", {}))
            result_text = json.dumps(summary, ensure_ascii=False)

        elif step["type"] == "eda":
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            result = eda_pipeline(df, numeric_columns=numeric_cols)
            result_text = f"行数: {result['row_count']}, 列数: {result['column_count']}"

        elif step["type"] == "model":
            target = step["params"].get("target", "")
            model_type = step["params"].get("model_type", "linear")
            numeric_cols = [c for c in df.select_dtypes(include=["number"]).columns if c != target]
            model_df = df[numeric_cols + [target]].dropna()
            X_train, X_test, y_train, y_test = split_data(model_df, target)
            model, _ = train_regression(X_train, y_train, model_type)
            metrics = evaluate_regression(model, X_test, y_test)
            result_text = json.dumps(metrics, ensure_ascii=False)

        state["steps"][req.step_index]["status"] = "done"
        pm.save_state(req.project_id, state)

        # 更新原始数据
        data_path = os.path.join("projects", req.project_id, "data", "original.csv")
        df.to_csv(data_path, index=False)

        return {"status": "done", "result": result_text}

    except Exception as e:
        state["steps"][req.step_index]["status"] = "error"
        pm.save_state(req.project_id, state)
        return {"status": "error", "result": str(e)}


# === 报告 ===
@app.post("/api/report/generate")
async def generate_report(req: GenerateReportRequest):
    data = pm.load_project(req.project_id)
    df = data["dataframe"]
    state = data["state"]

    sections = []
    for step in state.get("steps", []):
        if step["status"] == "done":
            sections.append(build_section(title=step["description"]))

    rows, cols = df.shape if df is not None else (0, 0)
    html = generate_html_report(
        title=req.title, sections=sections, conclusion=req.conclusion,
        data_source=data["meta"]["name"], rows=rows, cols=cols,
    )

    report_path = pm.save_report(req.project_id, html)
    return {"path": report_path}


@app.get("/api/report/download/{project_id}")
async def download_report(project_id: str):
    reports_dir = os.path.join("projects", project_id, "reports")
    if not os.path.exists(reports_dir):
        raise HTTPException(404, "无报告")
    files = sorted(os.listdir(reports_dir), reverse=True)
    if not files:
        raise HTTPException(404, "无报告")
    return FileResponse(os.path.join(reports_dir, files[0]))


# 静态文件 (前端构建产物)
if os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8502)
```

- [ ] **Step 3: 提交**

```bash
git add fastapi-app/backend/
git commit -m "feat: 添加 FastAPI 后端入口和数据模型"
```

---

### Task 3.2: fastapi-app/frontend/ — Vue 3 前端基础

**Files:**
- Create: `fastapi-app/frontend/package.json`
- Create: `fastapi-app/frontend/vite.config.js`
- Create: `fastapi-app/frontend/index.html`
- Create: `fastapi-app/frontend/src/main.js`
- Create: `fastapi-app/frontend/src/App.vue`
- Create: `fastapi-app/frontend/src/api/index.js`
- Create: `fastapi-app/frontend/src/stores/project.js`

- [ ] **Step 1: 初始化前端项目配置文件**

`package.json`:
```json
{
  "name": "ds-agent-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.3.0",
    "pinia": "^2.1.0",
    "axios": "^1.6.0",
    "plotly.js-dist-min": "^2.29.0",
    "element-plus": "^2.5.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "vite": "^5.1.0"
  }
}
```

`vite.config.js`:
```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8502',
        changeOrigin: true,
      }
    }
  }
})
```

`index.html`:
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>数据科学家 Agent</title>
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/src/main.js"></script>
</body>
</html>
```

`src/main.js`:
```javascript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'

const routes = [
  { path: '/', name: 'upload', component: () => import('./views/DataUpload.vue') },
  { path: '/analysis', name: 'analysis', component: () => import('./views/Analysis.vue') },
  { path: '/report', name: 'report', component: () => import('./views/Report.vue') },
  { path: '/settings', name: 'settings', component: () => import('./views/Settings.vue') },
  { path: '/history', name: 'history', component: () => import('./views/History.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.mount('#app')
```

`src/App.vue`:
```vue
<template>
  <el-container style="height: 100vh">
    <el-aside width="220px" style="background: #fafafa; border-right: 1px solid #eee">
      <div style="padding: 20px; font-size: 18px; font-weight: bold; color: #1a73e8">
        📊 数据科学家 Agent
      </div>
      <el-menu :default-active="currentRoute" router>
        <el-menu-item index="/">
          <span>📂 数据上传</span>
        </el-menu-item>
        <el-menu-item index="/analysis">
          <span>🔬 分析对话</span>
        </el-menu-item>
        <el-menu-item index="/report">
          <span>📋 报告导出</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <span>⚙ 设置</span>
        </el-menu-item>
        <el-menu-item index="/history">
          <span>📁 历史项目</span>
        </el-menu-item>
      </el-menu>
      <div style="padding: 10px 20px; color: #999; font-size: 12px; position: absolute; bottom: 10px">
        <span v-if="projectStore.currentName">当前: {{ projectStore.currentName }}</span>
      </div>
    </el-aside>

    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectStore } from './stores/project'

const route = useRoute()
const projectStore = useProjectStore()
const currentRoute = computed(() => route.path)
</script>
```

`src/api/index.js`:
```javascript
import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const uploadData = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/data/upload', form)
}

export const getConfig = () => api.get('/config')
export const saveConfig = (config) => api.post('/config', config)
export const testConnection = (config) => api.post('/config/test', config)

export const listProjects = () => api.get('/projects')
export const createProject = (name, file) => {
  const form = new FormData()
  form.append('name', name)
  if (file) form.append('file', file)
  return api.post('/projects', form)
}
export const getProject = (id) => api.get(`/projects/${id}`)
export const deleteProject = (id) => api.delete(`/projects/${id}`)

export const planAnalysis = (projectId, userInput) =>
  api.post('/analysis/plan', { project_id: projectId, user_input: userInput })

export const executeStep = (projectId, stepIndex) =>
  api.post('/analysis/execute', { project_id: projectId, step_index: stepIndex })

export const generateReport = (projectId, title, conclusion) =>
  api.post('/report/generate', { project_id: projectId, title, conclusion })
```

`src/stores/project.js`:
```javascript
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useProjectStore = defineStore('project', () => {
  const currentId = ref(null)
  const currentName = ref('')
  const dataColumns = ref([])
  const dataShape = ref([0, 0])
  const steps = ref([])
  const chatHistory = ref([])

  function setProject(id, name, info) {
    currentId.value = id
    currentName.value = name
    if (info) {
      dataColumns.value = info.columns || []
      dataShape.value = info.shape || [0, 0]
    }
  }

  function setSteps(newSteps) {
    steps.value = newSteps
  }

  function addChatMessage(msg) {
    chatHistory.value.push(msg)
  }

  function clearProject() {
    currentId.value = null
    currentName.value = ''
    dataColumns.value = []
    dataShape.value = [0, 0]
    steps.value = []
    chatHistory.value = []
  }

  return { currentId, currentName, dataColumns, dataShape, steps, chatHistory,
           setProject, setSteps, addChatMessage, clearProject }
})
```

- [ ] **Step 2: 提交**

```bash
git add fastapi-app/frontend/
git commit -m "feat: 添加 Vue 3 前端基础框架"
```

---

### Task 3.3: fastapi-app/frontend/src/views/ — Vue 页面组件

**Files:**
- Write: `fastapi-app/frontend/src/views/DataUpload.vue`
- Write: `fastapi-app/frontend/src/views/Analysis.vue`
- Write: `fastapi-app/frontend/src/views/Settings.vue`
- Write: `fastapi-app/frontend/src/views/History.vue`
- Write: `fastapi-app/frontend/src/views/Report.vue`

- [ ] **Step 1: 编写 DataUpload.vue**

```vue
<template>
  <div>
    <h2>📂 数据上传</h2>
    <el-upload
      drag
      :auto-upload="false"
      :on-change="handleFileChange"
      accept=".csv,.xlsx,.xls,.json,.tsv"
      :limit="1"
    >
      <div class="el-upload__text">拖拽文件到此处或 <em>点击上传</em></div>
      <div class="el-upload__tip">支持 CSV、Excel、JSON 格式</div>
    </el-upload>

    <div v-if="uploadResult" style="margin-top: 20px">
      <h3>数据预览</h3>
      <el-table :data="uploadResult.preview" border stripe max-height="400" style="width: 100%">
        <el-table-column
          v-for="col in uploadResult.columns" :key="col" :prop="col" :label="col"
          min-width="120"
        />
      </el-table>

      <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="6">
          <el-statistic title="行数" :value="uploadResult.shape[0]" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="列数" :value="uploadResult.shape[1]" />
        </el-col>
      </el-row>

      <div style="margin-top: 20px">
        <el-input v-model="projectName" placeholder="项目名称" style="width: 300px" />
        <el-button type="primary" @click="createProject" style="margin-left: 10px"
                   :loading="creating">
          创建分析项目
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { uploadData, createProject as apiCreateProject } from '../api'
import { useProjectStore } from '../stores/project'
import { ElMessage } from 'element-plus'

const router = useRouter()
const projectStore = useProjectStore()

const selectedFile = ref(null)
const uploadResult = ref(null)
const projectName = ref('')
const creating = ref(false)

const handleFileChange = async (file) => {
  selectedFile.value = file.raw
  const res = await uploadData(file.raw)
  uploadResult.value = res.data
  projectName.value = file.name.replace(/\.[^.]+$/, '')
}

const createProject = async () => {
  creating.value = true
  try {
    const res = await apiCreateProject(projectName.value, selectedFile.value)
    projectStore.setProject(res.data.project_id, projectName.value, uploadResult.value)
    ElMessage.success('项目创建成功')
    router.push('/analysis')
  } catch (e) {
    ElMessage.error('创建失败: ' + e.message)
  } finally {
    creating.value = false
  }
}
</script>
```

- [ ] **Step 2: 编写 Analysis.vue**

```vue
<template>
  <div>
    <h2>🔬 分析对话</h2>

    <div v-if="!projectStore.currentId">
      <el-empty description="请先上传数据并创建项目" />
    </div>

    <div v-else style="display: flex; gap: 20px; height: calc(100vh - 150px)">
      <!-- 对话区 -->
      <div style="flex: 1; display: flex; flex-direction: column">
        <div style="flex: 1; overflow-y: auto; border: 1px solid #eee; border-radius: 8px; padding: 15px; margin-bottom: 10px">
          <div v-for="(msg, i) in chatHistory" :key="i" style="margin-bottom: 15px">
            <div v-if="msg.role === 'user'" style="text-align: right">
              <el-tag>👤 你</el-tag>
              <div style="background: #e3f2fd; padding: 10px; border-radius: 8px; margin-top: 5px; display: inline-block; text-align: left; max-width: 80%">
                {{ msg.content }}
              </div>
            </div>
            <div v-else>
              <el-tag type="success">🤖 Agent</el-tag>
              <div style="background: #f5f5f5; padding: 10px; border-radius: 8px; margin-top: 5px; max-width: 80%">
                {{ msg.content }}
              </div>
            </div>
          </div>
        </div>

        <div style="display: flex; gap: 10px">
          <el-input v-model="userInput" placeholder="描述你的分析需求..." @keyup.enter="sendMessage" />
          <el-button type="primary" @click="sendMessage" :loading="sending">发送</el-button>
        </div>
      </div>

      <!-- 步骤导航 -->
      <div style="width: 250px; border: 1px solid #eee; border-radius: 8px; padding: 15px">
        <h3>📋 分析步骤</h3>
        <div v-if="!steps.length" style="color: #999; font-size: 13px; margin-top: 20px">
          在对话区描述需求，Agent 将自动规划步骤
        </div>
        <div v-for="(step, i) in steps" :key="i" style="margin: 10px 0; padding: 8px; background: #fafafa; border-radius: 4px">
          <div style="display: flex; justify-content: space-between; align-items: center">
            <span>
              <span v-if="step.status === 'done'">✓</span>
              <span v-else-if="step.status === 'running'">⟳</span>
              <span v-else>○</span>
              步骤 {{ i + 1 }}
            </span>
            <el-button v-if="step.status === 'pending'" size="small" @click="runStep(i)">▶</el-button>
          </div>
          <div style="font-size: 12px; color: #666; margin-top: 4px">{{ step.description }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { planAnalysis, executeStep } from '../api'
import { useProjectStore } from '../stores/project'
import { ElMessage } from 'element-plus'

const projectStore = useProjectStore()
const userInput = ref('')
const sending = ref(false)
const chatHistory = ref([])
const steps = ref([])

const sendMessage = async () => {
  if (!userInput.value.trim()) return
  const msg = userInput.value
  userInput.value = ''
  chatHistory.value.push({ role: 'user', content: msg })

  sending.value = true
  try {
    const res = await planAnalysis(projectStore.currentId, msg)
    chatHistory.value.push({ role: 'assistant', content: res.data.explanation })
    steps.value = res.data.steps || []
  } catch (e) {
    ElMessage.error('请求失败: ' + e.message)
  } finally {
    sending.value = false
  }
}

const runStep = async (index) => {
  steps.value[index].status = 'running'
  try {
    const res = await executeStep(projectStore.currentId, index)
    steps.value[index].status = res.data.status
  } catch (e) {
    steps.value[index].status = 'error'
    ElMessage.error('执行失败: ' + e.message)
  }
}
</script>
```

- [ ] **Step 3: 编写 Settings.vue**

```vue
<template>
  <div>
    <h2>⚙ 设置</h2>
    <el-card style="max-width: 600px">
      <el-form :model="config" label-width="120px">
        <el-form-item label="预设模板">
          <el-select v-model="preset" @change="applyPreset">
            <el-option label="DeepSeek — deepseek-chat" value="deepseek" />
            <el-option label="Qwen — qwen-plus" value="qwen" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="服务名称">
          <el-input v-model="config.name" />
        </el-form-item>
        <el-form-item label="API 地址">
          <el-input v-model="config.base_url" placeholder="https://your-internal-api/v1" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="config.api_key" type="password" />
        </el-form-item>
        <el-form-item label="模型名称">
          <el-input v-model="config.model" />
        </el-form-item>
        <el-form-item label="温度">
          <el-slider v-model="config.temperature" :min="0" :max="1" :step="0.05" show-input />
        </el-form-item>
        <el-form-item label="最大 Token">
          <el-input-number v-model="config.max_tokens" :min="512" :max="16384" :step="512" />
        </el-form-item>
        <el-form-item>
          <el-button @click="testConnection">测试连接</el-button>
          <el-button type="primary" @click="saveSettings">保存配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getConfig, saveConfig, testConnection as apiTest } from '../api'
import { ElMessage } from 'element-plus'

const config = ref({
  name: '', base_url: '', api_key: '', model: '',
  temperature: 0.3, max_tokens: 4096
})
const preset = ref('deepseek')

const presets = {
  deepseek: { name: 'DeepSeek', base_url: 'https://api.deepseek.com/v1', model: 'deepseek-chat' },
  qwen: { name: 'Qwen', base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1', model: 'qwen-plus' },
  custom: { name: '自定义', base_url: '', model: '' },
}

onMounted(async () => {
  try {
    const res = await getConfig()
    Object.assign(config.value, res.data.llm)
  } catch (e) { /* use defaults */ }
})

const applyPreset = () => {
  Object.assign(config.value, presets[preset.value])
}

const testConnection = async () => {
  try {
    const res = await apiTest(config.value)
    if (res.data.success) ElMessage.success('连接成功: ' + res.data.message)
    else ElMessage.error('连接失败: ' + res.data.message)
  } catch (e) { ElMessage.error('连接失败: ' + e.message) }
}

const saveSettings = async () => {
  try {
    await saveConfig(config.value)
    ElMessage.success('配置已保存')
  } catch (e) { ElMessage.error('保存失败: ' + e.message) }
}
</script>
```

- [ ] **Step 4: 编写 History.vue 和 Report.vue**

```vue
<!-- History.vue -->
<template>
  <div>
    <h2>📁 历史项目</h2>
    <el-input v-model="search" placeholder="搜索项目..." style="width: 300px; margin-bottom: 20px" clearable />

    <div v-if="!filteredProjects.length" style="color: #999">暂无项目</div>

    <el-card v-for="p in filteredProjects" :key="p.id" style="margin-bottom: 15px">
      <div style="display: flex; justify-content: space-between; align-items: center">
        <div>
          <h3 style="margin: 0">📊 {{ p.name }}</h3>
          <div style="color: #999; font-size: 13px; margin-top: 5px">
            创建: {{ p.created_at?.slice(0, 10) }} | {{ p.steps_count }} 个步骤
            <span v-if="p.data_file"> | 数据: {{ p.data_file }}</span>
          </div>
        </div>
        <div>
          <el-button @click="openProject(p)">打开</el-button>
          <el-button type="danger" plain @click="removeProject(p.id)">删除</el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listProjects, getProject, deleteProject } from '../api'
import { useProjectStore } from '../stores/project'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const projectStore = useProjectStore()
const projects = ref([])
const search = ref('')

onMounted(async () => {
  const res = await listProjects()
  projects.value = res.data
})

const filteredProjects = computed(() =>
  search.value
    ? projects.value.filter(p => p.name.includes(search.value))
    : projects.value
)

const openProject = async (p) => {
  const res = await getProject(p.id)
  projectStore.setProject(p.id, p.name, res.data.data_info)
  router.push('/analysis')
}

const removeProject = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除此项目？', '确认', { type: 'warning' })
    await deleteProject(id)
    projects.value = projects.value.filter(p => p.id !== id)
    ElMessage.success('已删除')
  } catch (e) { /* cancelled */ }
}
</script>
```

```vue
<!-- Report.vue -->
<template>
  <div>
    <h2>📋 报告导出</h2>

    <div v-if="!projectStore.currentId">
      <el-empty description="请先创建分析项目" />
    </div>

    <div v-else>
      <el-input v-model="title" placeholder="报告标题" style="width: 400px; margin-bottom: 15px" />
      <el-input v-model="conclusion" type="textarea" :rows="5" placeholder="分析结论（可选）"
                style="margin-bottom: 15px" />

      <el-button type="primary" @click="genReport" :loading="generating">生成报告</el-button>

      <div v-if="reportHtml" style="margin-top: 20px; border: 1px solid #eee; border-radius: 8px; padding: 20px">
        <div v-html="reportHtml"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { generateReport } from '../api'
import { useProjectStore } from '../stores/project'
import { ElMessage } from 'element-plus'

const projectStore = useProjectStore()
const title = ref(projectStore.currentName + ' — 分析报告')
const conclusion = ref('')
const reportHtml = ref('')
const generating = ref(false)

const genReport = async () => {
  generating.value = true
  try {
    const res = await generateReport(projectStore.currentId, title.value, conclusion.value)
    ElMessage.success('报告已生成: ' + res.data.path)
  } catch (e) {
    ElMessage.error('生成失败: ' + e.message)
  } finally {
    generating.value = false
  }
}
</script>
```

- [ ] **Step 5: 提交**

```bash
git add fastapi-app/frontend/src/views/
git commit -m "feat: 添加 Vue 3 全部页面组件"
```

---

## Phase 4: 知识库 & 启动脚本

### Task 4.1: 完成知识库 & 打包脚本

**Files:**
- Create: `streamlit-app/run.bat`
- Create: `fastapi-app/run_backend.bat`
- Create: `fastapi-app/run_frontend.bat`
- Create: `knowledge/references/README.txt`

- [ ] **Step 1: 编写启动脚本**

`streamlit-app/run.bat`:
```bat
@echo off
chcp 65001 >nul
echo ==========================================
echo   数据科学家 Agent - Streamlit 版
echo ==========================================
echo.
cd /d "%~dp0\.."
call venv\Scripts\activate.bat
streamlit run streamlit-app/app.py --server.port 8501
pause
```

`fastapi-app/run_backend.bat`:
```bat
@echo off
chcp 65001 >nul
echo ==========================================
echo   数据科学家 Agent - FastAPI 后端
echo ==========================================
echo.
cd /d "%~dp0\.."
call venv\Scripts\activate.bat
cd fastapi-app\backend
uvicorn main:app --host 0.0.0.0 --port 8502 --reload
pause
```

`fastapi-app/run_frontend.bat`:
```bat
@echo off
chcp 65001 >nul
echo ==========================================
echo   数据科学家 Agent - Vue 前端
echo ==========================================
echo.
cd /d "%~dp0"
cd frontend
npm run dev
pause
```

- [ ] **Step 2: 知识库参考文档说明**

`knowledge/references/README.txt`:
```
此目录用于存放汽车工程领域的参考文档。

支持格式: .txt, .md

文档将被自动分块并通过 TF-IDF 关键词检索，在分析时注入 LLM 上下文。

建议放入:
- 行业标准参数说明
- 面料测试方法文档
- 常规分析流程 SOP
- 过往分析案例的关键发现

添加文档后重启应用即可生效。
```

- [ ] **Step 3: 更新 CLAUDE.md**

将 `CLAUDE.md` 更新为反映当前项目状态：

```markdown
# CLAUDE.md

## Project Overview

数据科学家 Agent — 面向汽车研发工程师的数据分析 Web 工具。

包含两个版本：
- streamlit-app/: Streamlit 全栈方案
- fastapi-app/: FastAPI + Vue 3 前后端分离方案
- engine/: 共享分析引擎

## Development Commands

- 安装依赖: `pip install -r streamlit-app/requirements.txt`
- 启动 Streamlit: `streamlit run streamlit-app/app.py`
- 启动 FastAPI: `uvicorn fastapi-app.backend.main:app --reload --port 8502`
- 启动前端: `cd fastapi-app/frontend && npm run dev`
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
```

- [ ] **Step 4: 提交**

```bash
git add .
git commit -m "feat: 添加启动脚本、知识库说明和更新项目文档"
```

---

## Plan Self-Review

### Spec Coverage
- [x] 共享引擎 (8 个模块) → Tasks 1.1-1.11
- [x] LLM 配置适配器 → Task 1.1 (config) + Task 1.7 (llm_agent)
- [x] LLM Agent 编排流程 (5 步) → Task 1.7 (llm_agent.py)
- [x] 用户交互界面 (三栏布局) → Task 2.3 (Streamlit) + Task 3.3 (Vue)
- [x] 历史项目管理 → Task 1.10 + Task 2.2 (Streamlit) + Task 3.3 (Vue)
- [x] 领域知识库 → Task 1.11 + Task 4.1
- [x] Web 设置页 LLM 配置 → Task 2.2 (Streamlit) + Task 3.3 (Vue Settings)
- [x] 打包分发 → Task 4.1 (启动脚本)
- [x] 项目目录结构 → Task 0.1

### Placeholder Check
- 无 TBD / TODO / 占位符
- 所有代码步骤均包含具体实现

### Type Consistency
- LLMConfig 在 config.py (Task 1.1) 和 schemas.py (Task 3.1) 中字段一致
- AnalysisPlan/AnalysisStep 在 llm_agent.py (Task 1.7) 中定义
- ProjectManager 接口在各页面中一致调用
