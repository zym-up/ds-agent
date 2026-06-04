"""modeler 模块测试"""
import pytest
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from engine.modeler import (
    split_data, train_regression, evaluate_regression,
    feature_importance, residual_plot, train_cluster,
)


@pytest.fixture
def sample_df():
    np.random.seed(42)
    n = 100
    X1 = np.random.randn(n)
    X2 = np.random.randn(n)
    y = 3 * X1 + 0.5 * X2 + np.random.randn(n) * 0.5 + 10
    return pd.DataFrame({"特征1": X1, "特征2": X2, "目标": y})


# ── split_data ──
def test_split_data(sample_df):
    X_train, X_test, y_train, y_test = split_data(sample_df, target="目标")
    assert len(X_train) == 80
    assert len(X_test) == 20
    assert len(y_train) == 80
    assert len(y_test) == 20


# ── train_regression ──
def test_train_linear(sample_df):
    X_train, X_test, y_train, y_test = split_data(sample_df, target="目标")
    model, info = train_regression(X_train, y_train, model_type="linear")
    assert model is not None
    assert info["模型"] == "linear"

def test_train_random_forest(sample_df):
    X_train, X_test, y_train, y_test = split_data(sample_df, target="目标")
    model, info = train_regression(X_train, y_train, model_type="random_forest")
    assert model is not None

def test_train_ridge(sample_df):
    X_train, X_test, y_train, y_test = split_data(sample_df, target="目标")
    model, info = train_regression(X_train, y_train, model_type="ridge")
    assert model is not None


# ── evaluate_regression ──
def test_evaluate_regression(sample_df):
    X_train, X_test, y_train, y_test = split_data(sample_df, target="目标")
    model, _ = train_regression(X_train, y_train, model_type="linear")
    metrics = evaluate_regression(model, X_test, y_test)
    assert "R²" in metrics
    assert "RMSE" in metrics
    assert metrics["R²"] > 0


# ── feature_importance ──
def test_feature_importance_linear(sample_df):
    X_train, X_test, y_train, y_test = split_data(sample_df, target="目标")
    model, _ = train_regression(X_train, y_train, model_type="linear")
    df_imp, fig = feature_importance(model, ["特征1", "特征2"])
    assert len(df_imp) == 2
    assert isinstance(fig, go.Figure)

def test_feature_importance_rf(sample_df):
    X_train, X_test, y_train, y_test = split_data(sample_df, target="目标")
    model, _ = train_regression(X_train, y_train, model_type="random_forest")
    df_imp, fig = feature_importance(model, ["特征1", "特征2"])
    assert len(df_imp) == 2


# ── residual_plot ──
def test_residual_plot(sample_df):
    X_train, X_test, y_train, y_test = split_data(sample_df, target="目标")
    model, _ = train_regression(X_train, y_train, model_type="linear")
    y_pred = model.predict(X_test)
    fig = residual_plot(y_test, y_pred)
    assert isinstance(fig, go.Figure)


# ── train_cluster ──
def test_train_cluster(sample_df):
    df_cluster = sample_df[["特征1", "特征2"]].copy()
    result_df, summary, fig = train_cluster(df_cluster, ["特征1", "特征2"], n_clusters=3)
    assert "聚类标签" in result_df.columns
    assert "轮廓系数" in summary
    assert isinstance(fig, go.Figure)

def test_train_cluster_single():
    df = pd.DataFrame({"a": [1, 2, 3, 10, 11, 12], "b": [1, 2, 3, 10, 11, 12]})
    result_df, summary, fig = train_cluster(df, ["a", "b"], n_clusters=1)
    assert summary["轮廓系数"] == 0
