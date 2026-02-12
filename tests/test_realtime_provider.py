"""
测试 RealtimeProvider 实时行情获取。

注意：这些是集成测试，需要网络连接访问 AkShare API。
运行方式: pytest tests/test_realtime_provider.py -v
"""

import pytest
from data_loader.realtime_provider import RealtimeProvider


@pytest.fixture
def provider():
    return RealtimeProvider()


def _assert_quote_fields(quote):
    """验证 quote 字典包含必要字段"""
    assert quote is not None, "Quote should not be None"
    assert 'symbol' in quote
    assert 'price' in quote
    assert 'asset_type' in quote
    # price 可能盘前为 None，但字段应该存在
    if quote['price'] is not None:
        assert isinstance(quote['price'], float)


class TestRealtimeStock:
    def test_quote_stock(self, provider):
        """测试 A 股股票实时行情: 600519 (贵州茅台)"""
        quote = provider.get_quote("600519", asset_type='stock')
        _assert_quote_fields(quote)
        assert quote['asset_type'] == 'stock'

    def test_quote_stock_auto_detect(self, provider):
        """测试自动探测获取股票行情"""
        quote = provider.get_quote("600519")
        # 可能被识别为 stock 或 index，只要返回结果就行
        assert quote is not None


class TestRealtimeETF:
    def test_quote_etf(self, provider):
        """测试 ETF 实时行情: 513180 (恒生科技ETF)"""
        quote = provider.get_quote("513180", asset_type='etf')
        _assert_quote_fields(quote)
        assert quote['asset_type'] == 'etf'


class TestRealtimeIndex:
    def test_quote_index(self, provider):
        """测试指数实时行情: 000300 (沪深300)"""
        quote = provider.get_quote("000300", asset_type='index')
        _assert_quote_fields(quote)
        assert quote['asset_type'] == 'index'


class TestRealtimeOTCFund:
    def test_quote_otc_fund(self, provider):
        """测试场外基金实时净值: 013402"""
        quote = provider.get_quote("013402", asset_type='otc_fund')
        _assert_quote_fields(quote)
        assert quote['asset_type'] == 'otc_fund'
