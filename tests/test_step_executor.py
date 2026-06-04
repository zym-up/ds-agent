"""step_executor 边界测试 — 测试缺失参数、非法输入等边界情况"""
import pytest
import pandas as pd
import numpy as np
from engine.step_executor import execute_step


@pytest.fixture
def sample_df():
    np.random.seed(42)
    return pd.DataFrame({
        "数值A": np.random.randn(100),
        "数值B": np.random.randn(100) * 2 + 5,
        "数值C": np.random.randn(100) + 10,
        "分类列": np.random.choice(["X", "Y", "Z"], 100),
        "目标列": np.random.randn(100) * 3 + 20,
    })


# ── EDA scatter 缺参数 ──
def test_scatter_missing_x(sample_df):
    result = execute_step("eda", {"method": "scatter", "y": "数值B"}, sample_df)
    assert "错误" in result["text"]

def test_scatter_missing_y(sample_df):
    result = execute_step("eda", {"method": "scatter", "x": "数值A"}, sample_df)
    assert "错误" in result["text"]

def test_scatter_both_missing(sample_df):
    result = execute_step("eda", {"method": "scatter"}, sample_df)
    assert "错误" in result["text"]

def test_scatter_ok(sample_df):
    result = execute_step("eda", {"method": "scatter", "x": "数值A", "y": "数值B"}, sample_df)
    assert "错误" not in result["text"]
    assert len(result["charts"]) == 1


# ── EDA line 缺参数 ──
def test_line_missing_x(sample_df):
    result = execute_step("eda", {"method": "line", "y": "数值B"}, sample_df)
    assert "错误" in result["text"]

def test_line_missing_y(sample_df):
    result = execute_step("eda", {"method": "line", "x": "数值A"}, sample_df)
    assert "错误" in result["text"]

def test_line_ok(sample_df):
    result = execute_step("eda", {"method": "line", "x": "数值A", "y": "数值B"}, sample_df)
    assert "错误" not in result["text"]
    assert len(result["charts"]) == 1


# ── EDA 其他方法 ──
def test_correlation(sample_df):
    result = execute_step("eda", {"method": "correlation", "columns": ["数值A", "数值B"]}, sample_df)
    assert "错误" not in result["text"]
    assert len(result["charts"]) == 1

def test_correlation_method_spearman(sample_df):
    result = execute_step("eda", {"method": "correlation", "corr_method": "spearman"}, sample_df)
    assert "spearman" in result["text"].lower()

def test_distribution(sample_df):
    result = execute_step("eda", {"method": "distribution", "columns": ["数值A", "数值B"]}, sample_df)
    assert len(result["charts"]) >= 1

def test_describe(sample_df):
    result = execute_step("eda", {"method": "describe"}, sample_df)
    assert "统计摘要" in result["text"]

def test_pairplot(sample_df):
    result = execute_step("eda", {"method": "pairplot", "columns": ["数值A", "数值B", "数值C"]}, sample_df)
    assert len(result["charts"]) == 1


# ── EDA 默认流水线 ──
def test_eda_no_method(sample_df):
    result = execute_step("eda", {}, sample_df)
    assert "错误" not in result["text"]
    assert len(result["charts"]) >= 1


# ── EDA 非法列名 ──
def test_scatter_invalid_column(sample_df):
    result = execute_step("eda", {"method": "scatter", "x": "不存在的列", "y": "数值B"}, sample_df)
    assert result["charts"] == [] or "错误" in result["text"]


# ── EDA scatter trendline 降级 (非数值列) ──
def test_scatter_trendline_fallback(sample_df):
    result = execute_step("eda", {"method": "scatter", "x": "分类列", "y": "数值B", "trendline": True}, sample_df)
    assert len(result["charts"]) == 1


# ── clean 各种 method ──
def test_clean_dedup(sample_df):
    result = execute_step("clean", {"method": "dedup"}, sample_df)
    assert "去重完成" in result["text"]

def test_clean_fill_missing(sample_df):
    df_with_na = sample_df.copy()
    df_with_na.loc[0, "数值A"] = np.nan
    result = execute_step("clean", {"method": "fill_missing", "strategy": "mean"}, df_with_na)
    assert "缺失值填充" in result["text"]

def test_clean_detect_outliers(sample_df):
    result = execute_step("clean", {"method": "detect_outliers", "outlier_method": "iqr"}, sample_df)
    assert "异常值检测" in result["text"]

def test_clean_drop_columns(sample_df):
    result = execute_step("clean", {"method": "drop_columns", "columns": ["分类列"]}, sample_df)
    assert "删除列" in result["text"]
    assert "分类列" not in result["result_df"].columns

def test_clean_unknown_method_falls_back_to_pipeline(sample_df):
    result = execute_step("clean", {"method": "不存在的_方法"}, sample_df)
    assert result["result_df"] is not None


# ── clean 默认流水线 ──
def test_clean_no_method(sample_df):
    result = execute_step("clean", {}, sample_df)
    assert "数据清洗完成" in result["text"]
    assert result["result_df"] is not None


# ── model 缺 target ──
def test_model_missing_target(sample_df):
    result = execute_step("model", {"model_type": "linear"}, sample_df)
    assert "错误" in result["text"]


# ── feature scale 缺 columns ──
def test_feature_scale_missing_columns(sample_df):
    result = execute_step("feature", {"method": "scale"}, sample_df)
    assert "错误" in result["text"]


# ── feature encode 缺 columns ──
def test_feature_encode_missing_columns(sample_df):
    result = execute_step("feature", {"method": "encode"}, sample_df)
    assert "错误" in result["text"]


# ── 非法 step_type ──
def test_unknown_step_type(sample_df):
    result = execute_step("unknown_type", {}, sample_df)
    assert len(result["charts"]) == 0
    assert result["text"] == ""


# ── report 类型 ──
def test_report_step(sample_df):
    result = execute_step("report", {}, sample_df)
    assert "报告" in result["text"]


# ── 空 DataFrame ──
def test_empty_dataframe():
    df = pd.DataFrame()
    result = execute_step("eda", {"method": "describe"}, df)
    assert "无可用" in result["text"]
