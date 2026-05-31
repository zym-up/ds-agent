"""共享测试数据和工具函数"""
import sys
import os
import tempfile

# 确保 engine 模块可导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import pytest


@pytest.fixture
def sample_df():
    """一个简单的 DataFrame，供多个测试复用"""
    return pd.DataFrame({
        "车型": ["A", "B", "C", "D"],
        "评分": [8.5, 7.2, 9.0, 6.8],
        "价格": [15, 22, 18, 30],
        "类别": ["SUV", "轿车", "SUV", "轿车"],
    })


def _make_temp(suffix: str) -> str:
    """创建临时文件路径，返回路径。调用者负责写入和清理。"""
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)  # 立即关闭句柄，避免 Windows 锁文件
    return path


@pytest.fixture
def sample_csv(sample_df):
    """把 sample_df 写入临时 CSV 文件，测试完自动删除"""
    path = _make_temp(".csv")
    sample_df.to_csv(path, index=False)
    yield path
    os.unlink(path)


@pytest.fixture
def sample_xlsx(sample_df):
    """把 sample_df 写入临时 Excel 文件，测试完自动删除"""
    path = _make_temp(".xlsx")
    sample_df.to_excel(path, index=False)
    yield path
    os.unlink(path)


@pytest.fixture
def sample_xlsx_multi_sheet(sample_df):
    """多 sheet 的 Excel 文件"""
    path = _make_temp(".xlsx")
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        sample_df.to_excel(writer, sheet_name="Sheet1", index=False)
        pd.DataFrame({"x": [1, 2, 3]}).to_excel(writer, sheet_name="Sheet2", index=False)
    yield path
    os.unlink(path)
