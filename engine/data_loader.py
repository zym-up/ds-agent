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
    """加载 CSV 文件,自动检测编码和分隔符"""
    encoding = kwargs.pop("encoding", detect_encoding(file_path))
    try:
        return pd.read_csv(file_path, encoding=encoding, **kwargs)
    except UnicodeDecodeError:
        return pd.read_csv(file_path, encoding="gbk", **kwargs)


def load_excel(file_path: str, sheet_name: Optional[str] = None, **kwargs) -> pd.DataFrame:
    """加载 Excel 文件"""
    if sheet_name:
        return pd.read_excel(file_path, sheet_name=sheet_name, **kwargs)
    with pd.ExcelFile(file_path) as xl:
        sheets = xl.sheet_names
    if len(sheets) == 1:
        return pd.read_excel(file_path, **kwargs)
    return pd.read_excel(file_path, sheet_name=sheets[0], **kwargs)


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
