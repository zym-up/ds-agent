"""eda 模块测试"""
import pytest
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from engine.eda import (
    describe_numeric, describe_categorical, correlation_matrix,
    distribution_plot, scatter_plot, line_plot, pair_plot,
    describe, eda_pipeline,
)


@pytest.fixture
def sample_df():
    np.random.seed(42)
    return pd.DataFrame({
        "数值A": np.random.randn(50),
        "数值B": np.random.randn(50) * 2 + 5,
        "数值C": np.random.randn(50) + 10,
        "分类列": np.random.choice(["X", "Y", "Z"], 50),
    })


# ── describe_numeric ──
def test_describe_numeric(sample_df):
    result = describe_numeric(sample_df)
    assert "数值A" in result
    assert "skewness" in result["数值A"]
    assert "kurtosis" in result["数值A"]

def test_describe_numeric_empty():
    result = describe_numeric(pd.DataFrame())
    assert result == {}

def test_describe_numeric_specific_columns(sample_df):
    result = describe_numeric(sample_df, columns=["数值A"])
    assert "数值A" in result
    assert "数值B" not in result


# ── describe_categorical ──
def test_describe_categorical(sample_df):
    result = describe_categorical(sample_df)
    assert "分类列" in result
    assert "unique_count" in result["分类列"]
    assert "top_values" in result["分类列"]


# ── correlation_matrix ──
def test_correlation_matrix(sample_df):
    corr, fig = correlation_matrix(sample_df)
    assert corr.shape[0] >= 2
    assert isinstance(fig, go.Figure)

def test_correlation_matrix_spearman(sample_df):
    corr, fig = correlation_matrix(sample_df, method="spearman")
    assert corr.shape[0] >= 2


# ── distribution_plot ──
def test_distribution_plot(sample_df):
    fig = distribution_plot(sample_df, "数值A")
    assert isinstance(fig, go.Figure)

def test_distribution_plot_custom_bins(sample_df):
    fig = distribution_plot(sample_df, "数值A", bins=10)
    assert isinstance(fig, go.Figure)


# ── scatter_plot ──
def test_scatter_plot(sample_df):
    fig = scatter_plot(sample_df, x="数值A", y="数值B")
    assert isinstance(fig, go.Figure)

def test_scatter_plot_no_trendline(sample_df):
    fig = scatter_plot(sample_df, x="数值A", y="数值B", trendline=False)
    assert isinstance(fig, go.Figure)

def test_scatter_plot_with_color(sample_df):
    fig = scatter_plot(sample_df, x="数值A", y="数值B", color="分类列")
    assert isinstance(fig, go.Figure)

def test_scatter_plot_trendline_fallback():
    """非数值 x 列使 OLS 趋势线失败，应降级为无趋势线"""
    df = pd.DataFrame({"cat_x": ["a", "b", "c", "d", "e"],
                        "num_y": [1, 2, 3, 4, 5]})
    fig = scatter_plot(df, x="cat_x", y="num_y", trendline=True)
    assert isinstance(fig, go.Figure)

def test_scatter_plot_nan_values():
    """含 NaN 的数据散点图不应崩溃"""
    df = pd.DataFrame({"x": [1, 2, np.nan, 4, 5], "y": [2, 4, 6, 8, 10]})
    fig = scatter_plot(df, x="x", y="y", trendline=False)
    assert isinstance(fig, go.Figure)


# ── line_plot ──
def test_line_plot(sample_df):
    fig = line_plot(sample_df, x="数值A", y="数值B")
    assert isinstance(fig, go.Figure)

def test_line_plot_with_group(sample_df):
    fig = line_plot(sample_df, x="数值A", y="数值B", group_by="分类列")
    assert isinstance(fig, go.Figure)

def test_line_plot_invalid_group(sample_df):
    fig = line_plot(sample_df, x="数值A", y="数值B", group_by="不存在的列")
    assert isinstance(fig, go.Figure)


# ── pair_plot ──
def test_pair_plot(sample_df):
    fig = pair_plot(sample_df, ["数值A", "数值B"])
    assert isinstance(fig, go.Figure)


# ── describe (text) ──
def test_describe(sample_df):
    text = describe(sample_df)
    assert "统计摘要" in text
    assert "数值A" in text

def test_describe_no_numeric():
    df = pd.DataFrame({"a": ["x", "y", "z"]})
    text = describe(df)
    assert "无可用" in text


# ── eda_pipeline ──
def test_eda_pipeline(sample_df):
    result = eda_pipeline(sample_df)
    assert result["row_count"] == 50
    assert len(result["charts"]) >= 1
    assert "numeric_stats" in result
