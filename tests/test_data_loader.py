"""data_loader 模块测试"""
import pytest
import pandas as pd
from engine.data_loader import load_file, load_csv, load_excel, load_json, get_data_info


class TestLoadCsv:
    def test_basic(self, sample_csv):
        df = load_csv(sample_csv)
        assert isinstance(df, pd.DataFrame)
        assert df.shape == (4, 4)

    def test_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            load_csv("不存在的文件.csv")


class TestLoadExcel:
    def test_basic(self, sample_xlsx):
        df = load_excel(sample_xlsx)
        assert isinstance(df, pd.DataFrame)
        assert df.shape == (4, 4)

    def test_multi_sheet(self, sample_xlsx_multi_sheet):
        """多 sheet 时应该读第一个 sheet"""
        df = load_excel(sample_xlsx_multi_sheet)
        assert isinstance(df, pd.DataFrame)
        assert df.shape == (4, 4)  # Sheet1 是 4 行

    def test_specific_sheet(self, sample_xlsx_multi_sheet):
        """指定 sheet_name 时读指定 sheet"""
        df = load_excel(sample_xlsx_multi_sheet, sheet_name="Sheet2")
        assert df.shape == (3, 1)
        assert "x" in df.columns


class TestLoadFile:
    def test_csv_auto_detect(self, sample_csv):
        df = load_file(sample_csv)
        assert isinstance(df, pd.DataFrame)

    def test_xlsx_auto_detect(self, sample_xlsx):
        df = load_file(sample_xlsx)
        assert isinstance(df, pd.DataFrame)

    def test_unsupported_format(self):
        with pytest.raises(ValueError, match="不支持的文件格式"):
            load_file("data.xyz")


class TestGetDataInfo:
    def test_basic_info(self, sample_df):
        info = get_data_info(sample_df)
        assert info["shape"] == (4, 4)
        assert len(info["numeric_columns"]) == 2  # 评分, 价格
        assert len(info["categorical_columns"]) == 2  # 车型, 类别

    def test_missing_percentage(self):
        import numpy as np
        df = pd.DataFrame({"a": [1, np.nan, 3, np.nan]})
        info = get_data_info(df)
        assert info["missing_pct"]["a"] == 50.0
