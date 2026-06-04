"""数据清洗模块"""
import pandas as pd
import numpy as np
from typing import Optional


def remove_duplicates(df: pd.DataFrame, subset: Optional[list] = None) -> tuple:
    """去重"""
    before = len(df)
    df = df.drop_duplicates(subset=subset).reset_index(drop=True)
    after = len(df)
    summary = {"去重前": before, "去重后": after, "删除重复行数": before - after}
    return df, summary


def drop_missing(
    df: pd.DataFrame, threshold: float = 0.5, axis: str = "row"
) -> tuple:
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
    fill_value=None,
) -> tuple:
    """填充缺失值: strategy: 'mean' | 'median' | 'mode' | 'constant'"""
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
    """检测异常值: method: 'iqr' | 'zscore'"""
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
) -> tuple:
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
