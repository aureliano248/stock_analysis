
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from data_loader.data_provider import DataProvider

@pytest.fixture
def provider():
    return DataProvider()

def test_standardize(provider):
    df = pd.DataFrame({
        "日期": ["2024-01-01"],
        "收盘": [100.0],
        "无关列": [0]
    })
    std_df = provider._standardize(df)
    assert "date" in std_df.columns
    assert "close" in std_df.columns
    assert "无关列" not in std_df.columns
    assert std_df["date"].dtype == 'datetime64[ns]'

def test_standardize_empty(provider):
    assert provider._standardize(pd.DataFrame()).empty
    assert provider._standardize(None).empty

def test_standardize_english_columns(provider):
    """测试已经是英文列名的 DataFrame（如 Sina 接口返回的）"""
    df = pd.DataFrame({
        "date": ["2024-01-01"],
        "close": [100.0],
        "open": [99.0],
        "high": [101.0],
        "low": [98.0],
        "volume": [1000]
    })
    std_df = provider._standardize(df)
    assert len(std_df.columns) == 6
    assert "date" in std_df.columns

@patch("akshare.index_zh_a_hist")
def test_fetch_index(mock_ak, provider):
    mock_df = pd.DataFrame({"日期": ["2024-01-01"], "收盘": [3000]})
    mock_ak.return_value = mock_df
    df, t = provider.fetch_index("000300", "20240101", "20240101")
    assert not df.empty
    assert t == 'index'

@patch("akshare.stock_zh_a_hist")
def test_fetch_stock(mock_ak, provider):
    mock_df = pd.DataFrame({"日期": ["2024-01-01"], "收盘": [10.0]})
    mock_ak.return_value = mock_df
    df, t = provider.fetch_stock("600519", "20240101", "20240101", "qfq")
    assert not df.empty
    assert t == 'stock'

@patch("akshare.fund_etf_hist_sina")
def test_fetch_etf_sina(mock_ak, provider):
    mock_df = pd.DataFrame({
        "date": ["2024-01-01", "2024-01-02"],
        "close": [1.5, 1.6],
        "open": [1.4, 1.5],
        "high": [1.6, 1.7],
        "low": [1.3, 1.4],
        "volume": [100, 200]
    })
    mock_ak.return_value = mock_df
    df, t = provider.fetch_etf("513180", "20240101", "20240102", "qfq")
    assert not df.empty
    assert t == 'etf'

@patch("akshare.fund_open_fund_info_em")
def test_fetch_otc_fund(mock_ak, provider):
    mock_df = pd.DataFrame({
        "净值日期": ["2024-01-01", "2024-01-02"],
        "单位净值": [1.5, 1.6],
        "累计净值": [1.5, 1.6],
        "日增长率": [0.5, 0.3]
    })
    mock_ak.return_value = mock_df
    df, t = provider.fetch_otc_fund("013402", "20240101", "20240102")
    assert not df.empty
    assert t == 'otc_fund'
    assert "close" in df.columns
