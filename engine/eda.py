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


def correlation_matrix(df: pd.DataFrame, method: str = "pearson", columns: Optional[list] = None) -> tuple:
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
    try:
        fig = px.scatter(df, x=x, y=y, color=color, trendline="ols" if trendline else None,
                         title=f"{x} vs {y}")
    except Exception:
        fig = px.scatter(df, x=x, y=y, color=color, trendline=None,
                         title=f"{x} vs {y}")
    fig.update_layout(height=500)
    return fig


def describe(df: pd.DataFrame, columns: Optional[list] = None) -> str:
    """数值列统计摘要，纯文本不生成图表"""
    targets = [c for c in (columns or df.columns) if pd.api.types.is_numeric_dtype(df[c])]
    if not targets:
        return "无可用数值列"
    stats = df[targets].describe(percentiles=[0.25, 0.5, 0.75])
    lines = ["### 数据统计摘要", f"- 总行数: {len(df)}", f"- 数值列数: {len(targets)}", ""]
    lines.append("| 列名 | 均值 | 标准差 | 最小值 | Q1 | 中位数 | Q3 | 最大值 |")
    lines.append("|------|------|--------|--------|-----|--------|-----|--------|")
    for col in targets:
        s = stats[col]
        lines.append(f"| {col} | {s['mean']:.2f} | {s['std']:.2f} | {s['min']:.2f} | "
                     f"{s['25%']:.2f} | {s['50%']:.2f} | {s['75%']:.2f} | {s['max']:.2f} |")
    return "\n".join(lines)


def line_plot(
    df: pd.DataFrame, x: str, y: str, group_by: Optional[str] = None
) -> go.Figure:
    """折线图，支持按分组列绘制多条折线"""
    if group_by and group_by in df.columns:
        fig = go.Figure()
        for name, group in df.groupby(group_by):
            sorted_group = group.sort_values(x)
            fig.add_trace(go.Scatter(
                x=sorted_group[x], y=sorted_group[y],
                mode="lines+markers", name=str(name),
            ))
        fig.update_layout(title=f"{y} vs {x} (按 {group_by} 分组)", height=500)
    else:
        sorted_df = df.sort_values(x)
        fig = go.Figure(go.Scatter(
            x=sorted_df[x], y=sorted_df[y],
            mode="lines+markers", name=f"{y} vs {x}",
        ))
        fig.update_layout(
            title=f"{y} vs {x}",
            xaxis_title=x, yaxis_title=y, height=500,
        )
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
