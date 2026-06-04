"""建模与评估模块"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional, Literal
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.metrics import (
    r2_score, mean_squared_error, mean_absolute_error, silhouette_score,
)
import xgboost as xgb

ModelType = Literal["linear", "ridge", "lasso", "random_forest", "xgboost"]


def split_data(df: pd.DataFrame, target: str, test_size: float = 0.2, random_state: int = 42):
    """划分训练/测试集"""
    X = df.drop(columns=[target])
    y = df[target]
    return train_test_split(X, y, test_size=test_size, random_state=random_state)


def _build_regression_model(model_type: str, **kwargs) -> tuple:
    """按类型构造单个回归模型（避免 dict literal 一次性构造所有模型）"""
    if model_type == "linear":
        return LinearRegression(**kwargs)
    elif model_type == "ridge":
        return Ridge(alpha=kwargs.pop("alpha", 1.0))
    elif model_type == "lasso":
        return Lasso(alpha=kwargs.pop("alpha", 1.0))
    elif model_type == "random_forest":
        return RandomForestRegressor(
            n_estimators=kwargs.pop("n_estimators", 100),
            max_depth=kwargs.pop("max_depth", None),
            random_state=42,
        )
    elif model_type == "xgboost":
        return xgb.XGBRegressor(
            n_estimators=kwargs.pop("n_estimators", 100),
            max_depth=kwargs.pop("max_depth", 6),
            learning_rate=kwargs.pop("learning_rate", 0.1),
            random_state=42,
        )
    else:
        raise ValueError(f"不支持的模型类型: {model_type}")


def train_regression(
    X_train: pd.DataFrame, y_train: pd.Series, model_type: ModelType = "linear", **kwargs
) -> tuple:
    """训练回归模型"""
    model = _build_regression_model(model_type, **kwargs)
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


def feature_importance(model, feature_names: list) -> tuple:
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
) -> tuple:
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
