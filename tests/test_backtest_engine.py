"""测试 backtest.engine.run_backtest 回测引擎"""

import pytest
import pandas as pd
from backtest.engine import run_backtest
from strategies import FixedInvestment


def _make_price_data(prices, start_date='2024-01-02'):
    """构造标准格式的价格数据"""
    dates = pd.bdate_range(start=start_date, periods=len(prices))
    return pd.DataFrame({
        'date': dates,
        'open': prices,
        'close': prices,
        'high': prices,
        'low': prices,
        'volume': [1000] * len(prices),
    })


class TestRunBacktest:
    def test_basic_backtest(self):
        """基本回测：固定价格每日定投"""
        df = _make_price_data([10.0] * 10)
        strategy = FixedInvestment(amount=100, freq='D')
        result = run_backtest(df, '2024-01-02', '2024-01-15', strategy)
        assert result is not None
        assert not result.empty
        assert 'date' in result.columns
        assert 'total_invested' in result.columns
        assert 'return_rate' in result.columns

    def test_no_data_returns_none(self):
        result = run_backtest(None, '2024-01-02', '2024-01-15', FixedInvestment(100))
        assert result is None

    def test_empty_df_returns_none(self):
        result = run_backtest(pd.DataFrame(), '2024-01-02', '2024-01-15', FixedInvestment(100))
        assert result is None

    def test_date_range_out_of_data(self):
        """请求的日期范围不在数据范围内"""
        df = _make_price_data([10.0] * 5, start_date='2024-01-02')
        strategy = FixedInvestment(amount=100, freq='D')
        result = run_backtest(df, '2025-01-01', '2025-12-31', strategy)
        assert result is None

    def test_constant_price_no_profit(self):
        """固定价格下的收益率应该为 0%"""
        df = _make_price_data([10.0] * 10)
        strategy = FixedInvestment(amount=100, freq='D')
        result = run_backtest(df, '2024-01-02', '2024-01-15', strategy)
        assert result is not None
        last = result.iloc[-1]
        assert abs(last['return_rate']) < 0.01

    def test_price_increase_positive_return(self):
        """价格从 10 涨到 20，收益率应该为正"""
        prices = [10.0 + i for i in range(11)]  # 10, 11, ..., 20
        df = _make_price_data(prices)
        strategy = FixedInvestment(amount=100, freq='D')
        result = run_backtest(df, '2024-01-02', '2024-01-16', strategy)
        assert result is not None
        last = result.iloc[-1]
        assert last['return_rate'] > 0

    def test_price_decrease_negative_return(self):
        """价格从 20 跌到 10，收益率应该为负"""
        prices = [20.0 - i for i in range(11)]  # 20, 19, ..., 10
        df = _make_price_data(prices)
        strategy = FixedInvestment(amount=100, freq='D')
        result = run_backtest(df, '2024-01-02', '2024-01-16', strategy)
        assert result is not None
        last = result.iloc[-1]
        assert last['return_rate'] < 0

    def test_total_invested_accumulates(self):
        """累计投入应该逐日增长"""
        df = _make_price_data([10.0] * 5)
        strategy = FixedInvestment(amount=100, freq='D')
        result = run_backtest(df, '2024-01-02', '2024-01-08', strategy)
        assert result is not None
        invested = result['total_invested'].tolist()
        # 应该是递增的
        for i in range(1, len(invested)):
            assert invested[i] >= invested[i-1]

    def test_result_row_count_matches_trading_days(self):
        """结果行数应该与回测区间内的交易日数一致"""
        df = _make_price_data([10.0] * 20)
        strategy = FixedInvestment(amount=100, freq='D')
        result = run_backtest(df, '2024-01-02', '2024-01-29', strategy)
        assert result is not None
        assert len(result) == 20
