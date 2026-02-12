
import pytest
import pandas as pd
from data_loader.data_provider import DataProvider

@pytest.fixture
def provider():
    return DataProvider()

def test_fetch_index(provider):
    """测试指数: 000300 (沪深300)"""
    df, asset_type = provider.fetch_index("000300", "20240101", "20240110")
    assert not df.empty, "指数数据拉取失败"
    assert asset_type == "index"
    assert "date" in df.columns
    assert "close" in df.columns

def test_fetch_stock(provider):
    """测试股票: 600519 (贵州茅台)"""
    df, asset_type = provider.fetch_stock("600519", "20240101", "20240110", "qfq")
    assert not df.empty, "股票数据拉取失败"
    assert asset_type == "stock"
    assert "date" in df.columns

def test_fetch_etf(provider):
    """测试 ETF: 513180 (纳指ETF)"""
    df, asset_type = provider.fetch_etf("513180", "20240101", "20260215", "qfq")
    assert not df.empty, "ETF数据拉取失败"
    assert asset_type == "etf"

def test_fetch_otc_fund(provider):
    """测试场外基金: 013402 (阿波罗基金)"""
    # 注意：DataProvider.fetch_otc_fund 接收的是去掉后缀的纯代码
    df, asset_type = provider.fetch_otc_fund("013402", "20240101", "20240110")
    assert not df.empty, "场外基金数据拉取失败"
    assert asset_type == "otc_fund"
