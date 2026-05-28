"""特征工程模块"""
import pandas as pd
import numpy as np
from typing import Optional
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_regression, mutual_info_regression


def scale_features(
    df: pd.DataFrame, columns: list, method: str = "standard"
) -> tuple:
    """特征缩放: method: 'standard' | 'minmax'"""
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
) -> tuple:
    """分类变量编码: method: 'onehot' | 'label'"""
    df = df.copy()
    if method == "onehot":
        df = pd.get_dummies(df, columns=columns, drop_first=True)
        summary = {"方法": "独热编码", "处理列": columns}
    else:
        for col in columns:
            df[col] = LabelEncoder().fit_transform(df[col].astype(str))
        summary = {"方法": "标签编码", "处理列": columns}
    return df, summary


def select_by_variance(df: pd.DataFrame, threshold: float = 0.01) -> tuple:
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
) -> tuple:
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
