"""data_cleaner 模块测试"""
import pytest
import pandas as pd
import numpy as np
from engine.data_cleaner import (
    remove_duplicates, drop_missing, fill_missing,
    detect_outliers, clean_pipeline,
)


@pytest.fixture
def sample_df():
    np.random.seed(42)
    return pd.DataFrame({
        "数值A": [1.0, 2.0, np.nan, 4.0, 5.0, 100.0],
        "数值B": [10.0, np.nan, 30.0, 40.0, 50.0, 60.0],
        "分类列": ["a", "b", None, "a", "b", "c"],
    })


# ── remove_duplicates ──
def test_remove_duplicates(sample_df):
    df_with_dup = pd.concat([sample_df, sample_df.iloc[:2]]).reset_index(drop=True)
    result_df, info = remove_duplicates(df_with_dup)
    assert info["删除重复行数"] > 0

def test_remove_duplicates_none_found(sample_df):
    result_df, info = remove_duplicates(sample_df)
    assert info["删除重复行数"] == 0

def test_remove_duplicates_with_subset(sample_df):
    df = pd.DataFrame({"a": [1, 1, 2], "b": [1, 2, 3]})
    result_df, info = remove_duplicates(df, subset=["a"])
    assert len(result_df) == 2


# ── drop_missing ──
def test_drop_missing_row(sample_df):
    result_df, info = drop_missing(sample_df, threshold=0.5, axis="row")
    assert result_df is not None

def test_drop_missing_col(sample_df):
    result_df, info = drop_missing(sample_df, threshold=0.5, axis="col")
    assert result_df is not None


# ── fill_missing ──
def test_fill_missing_mean(sample_df):
    result_df, info = fill_missing(sample_df, strategy="mean")
    assert info["策略"] == "mean"
    assert result_df["数值A"].isnull().sum() == 0

def test_fill_missing_median(sample_df):
    result_df, info = fill_missing(sample_df, strategy="median")
    assert result_df["数值A"].isnull().sum() == 0

def test_fill_missing_mode(sample_df):
    result_df, info = fill_missing(sample_df, strategy="mode")
    assert result_df["分类列"].isnull().sum() == 0

def test_fill_missing_constant(sample_df):
    result_df, info = fill_missing(sample_df, strategy="constant", fill_value=-1)
    assert result_df["数值A"].isnull().sum() == 0

def test_fill_missing_specific_columns(sample_df):
    result_df, info = fill_missing(sample_df, strategy="mean", columns=["数值A"])
    assert result_df["数值A"].isnull().sum() == 0

def test_fill_missing_no_missing_cols(sample_df):
    df = pd.DataFrame({"a": [1, 2, 3]})
    result_df, info = fill_missing(df, strategy="mean")
    assert info["填充列"] == {}

def test_fill_missing_non_numeric_mean(sample_df):
    """非数值列用 mean 策略不会被填充"""
    result_df, info = fill_missing(sample_df, strategy="mean", columns=["分类列"])
    assert "分类列" not in info["填充列"]


# ── detect_outliers ──
def test_detect_outliers_iqr(sample_df):
    result = detect_outliers(sample_df, method="iqr")
    assert "数值A" in result
    assert "count" in result["数值A"]

def test_detect_outliers_zscore(sample_df):
    result = detect_outliers(sample_df, method="zscore")
    assert "数值A" in result

def test_detect_outliers_specific_columns(sample_df):
    result = detect_outliers(sample_df, method="iqr", columns=["数值A"])
    assert "数值A" in result
    assert "数值B" not in result

def test_detect_outliers_custom_threshold(sample_df):
    result_strict = detect_outliers(sample_df, method="iqr", threshold=3.0)
    result_loose = detect_outliers(sample_df, method="iqr", threshold=0.5)
    total_strict = sum(v["count"] for v in result_strict.values())
    total_loose = sum(v["count"] for v in result_loose.values())
    assert total_strict <= total_loose

def test_detect_outliers_excludes_non_numeric(sample_df):
    result = detect_outliers(sample_df, method="iqr")
    assert "分类列" not in result


# ── clean_pipeline ──
def test_clean_pipeline(sample_df):
    result_df, summary = clean_pipeline(sample_df)
    assert "去重" in summary
    assert "缺失值填充" in summary
    assert "异常值检测" in summary
