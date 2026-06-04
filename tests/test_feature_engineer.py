"""feature_engineer 模块测试"""
import pytest
import pandas as pd
import numpy as np
from engine.feature_engineer import (
    scale_features, encode_categorical, select_by_variance, select_by_correlation,
)


@pytest.fixture
def sample_df():
    np.random.seed(42)
    return pd.DataFrame({
        "数值A": np.random.randn(100),
        "数值B": np.random.randn(100) * 2 + 5,
        "分类列": np.random.choice(["X", "Y", "Z"], 100),
        "目标列": np.random.randn(100) * 3 + 20,
    })


# ── scale_features ──
def test_scale_standard(sample_df):
    result_df, summary = scale_features(sample_df, ["数值A", "数值B"], method="standard")
    assert abs(result_df["数值A"].mean()) < 1e-10
    assert abs(result_df["数值A"].std() - 1.0) < 0.1

def test_scale_minmax(sample_df):
    result_df, summary = scale_features(sample_df, ["数值A", "数值B"], method="minmax")
    assert result_df["数值A"].min() >= 0
    assert result_df["数值A"].max() <= 1


# ── encode_categorical ──
def test_encode_onehot(sample_df):
    result_df, summary = encode_categorical(sample_df, ["分类列"], method="onehot")
    assert "分类列" not in result_df.columns
    assert any(c.startswith("分类列_") for c in result_df.columns)

def test_encode_label(sample_df):
    result_df, summary = encode_categorical(sample_df, ["分类列"], method="label")
    assert "分类列" in result_df.columns
    assert pd.api.types.is_numeric_dtype(result_df["分类列"])


# ── select_by_variance ──
def test_select_by_variance(sample_df):
    result_df, summary = select_by_variance(sample_df, threshold=0.01)
    assert isinstance(result_df, pd.DataFrame)

def test_select_by_variance_high_threshold():
    df = pd.DataFrame({"a": [1, 1, 1, 1, 1], "b": [1, 2, 3, 4, 5]})  # a 方差为 0
    result_df, summary = select_by_variance(df, threshold=0.01)
    assert "a" in summary["移除特征"]


# ── select_by_correlation ──
def test_select_by_correlation(sample_df):
    selected, summary = select_by_correlation(sample_df, target="目标列", k=2)
    assert len(selected) <= 2
    assert "目标列" in summary["目标变量"]

def test_select_by_correlation_missing_target(sample_df):
    """目标列不存在时应报错"""
    with pytest.raises(KeyError):
        select_by_correlation(sample_df, target="不存在的列")
