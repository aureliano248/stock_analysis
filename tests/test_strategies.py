"""测试各策略的 get_investment_amount 纯计算逻辑"""

import pytest
import pandas as pd
from strategies import (
    FixedInvestment,
    IntervalFixedInvestment,
    ProfitRatioStrategy,
    BenchmarkDropStrategy,
    DynamicBenchmarkDropStrategy,
    QuadraticMAStrategy,
    create_strategy,
    get_strategy_params,
)


def _make_history(prices, start_date='2024-01-02'):
    """构造带有递增交易日的 history DataFrame"""
    dates = pd.bdate_range(start=start_date, periods=len(prices))
    return pd.DataFrame({
        'date': dates,
        'close': prices,
    })


# ============================
# FixedInvestment
# ============================
class TestFixedInvestment:
    def test_daily_invest(self):
        strategy = FixedInvestment(amount=100, freq='D')
        df = _make_history([10.0, 11.0])
        assert strategy.get_investment_amount(df, df.iloc[-1]['date']) == 100.0

    def test_monthly_first_day(self):
        strategy = FixedInvestment(amount=500, freq='M')
        df = _make_history([10.0])
        assert strategy.get_investment_amount(df, df.iloc[0]['date']) == 500.0

    def test_monthly_same_month_no_invest(self):
        strategy = FixedInvestment(amount=500, freq='M')
        df = _make_history([10.0, 11.0])  # 都在同一月
        assert strategy.get_investment_amount(df, df.iloc[-1]['date']) == 0.0

    def test_weekly_new_week_invest(self):
        strategy = FixedInvestment(amount=200, freq='W')
        # 周五 -> 下周一
        dates = [pd.to_datetime('2024-01-05'), pd.to_datetime('2024-01-08')]
        df = pd.DataFrame({'date': dates, 'close': [10.0, 11.0]})
        assert strategy.get_investment_amount(df, df.iloc[-1]['date']) == 200.0

    def test_empty_df(self):
        strategy = FixedInvestment(amount=100, freq='D')
        assert strategy.get_investment_amount(pd.DataFrame(), pd.to_datetime('2024-01-02')) == 0.0


# ============================
# IntervalFixedInvestment
# ============================
class TestIntervalFixedInvestment:
    def test_within_interval(self):
        intervals = [
            {'start': '2024-01-01', 'end': '2024-06-30', 'amount': 1000, 'freq': 'D'},
        ]
        strategy = IntervalFixedInvestment(intervals=intervals)
        df = _make_history([10.0])
        assert strategy.get_investment_amount(df, df.iloc[0]['date']) == 1000.0

    def test_outside_interval(self):
        intervals = [
            {'start': '2024-07-01', 'end': '2024-12-31', 'amount': 1000, 'freq': 'D'},
        ]
        strategy = IntervalFixedInvestment(intervals=intervals)
        df = _make_history([10.0])
        assert strategy.get_investment_amount(df, df.iloc[0]['date']) == 0.0


# ============================
# ProfitRatioStrategy
# ============================
class TestProfitRatioStrategy:
    def test_low_profit_ratio_high_multiplier(self):
        strategy = ProfitRatioStrategy(base_amount=100, thresholds=[(0.01, 10), (0.05, 2)])
        df = pd.DataFrame({
            'date': [pd.to_datetime('2024-01-02')],
            'close': [10.0],
            'profit_ratio': [0.005],  # < 1%
        })
        assert strategy.get_investment_amount(df, df.iloc[0]['date']) == 1000.0

    def test_medium_profit_ratio(self):
        strategy = ProfitRatioStrategy(base_amount=100, thresholds=[(0.01, 10), (0.05, 2)])
        df = pd.DataFrame({
            'date': [pd.to_datetime('2024-01-02')],
            'close': [10.0],
            'profit_ratio': [0.03],  # < 5% but > 1%
        })
        assert strategy.get_investment_amount(df, df.iloc[0]['date']) == 200.0

    def test_high_profit_ratio_base_amount(self):
        strategy = ProfitRatioStrategy(base_amount=100, thresholds=[(0.01, 10), (0.05, 2)])
        df = pd.DataFrame({
            'date': [pd.to_datetime('2024-01-02')],
            'close': [10.0],
            'profit_ratio': [0.50],  # > 5%
        })
        assert strategy.get_investment_amount(df, df.iloc[0]['date']) == 100.0

    def test_nan_profit_ratio_falls_back(self):
        strategy = ProfitRatioStrategy(base_amount=100)
        df = pd.DataFrame({
            'date': [pd.to_datetime('2024-01-02')],
            'close': [10.0],
            'profit_ratio': [pd.NA],
        })
        assert strategy.get_investment_amount(df, df.iloc[0]['date']) == 100.0

    def test_missing_profit_ratio_column(self):
        strategy = ProfitRatioStrategy(base_amount=100)
        df = pd.DataFrame({
            'date': [pd.to_datetime('2024-01-02')],
            'close': [10.0],
        })
        assert strategy.get_investment_amount(df, df.iloc[0]['date']) == 100.0


# ============================
# BenchmarkDropStrategy
# ============================
class TestBenchmarkDropStrategy:
    def test_no_drop_base_amount(self):
        strategy = BenchmarkDropStrategy(base_amount=100, freq='D', scale_factor=1.0)
        df = _make_history([10.0, 11.0])  # price up
        assert strategy.get_investment_amount(df, df.iloc[-1]['date']) == 100.0

    def test_drop_increases_amount(self):
        strategy = BenchmarkDropStrategy(base_amount=100, freq='D', scale_factor=1.0)
        df = _make_history([10.0, 8.0])  # 20% drop
        amount = strategy.get_investment_amount(df, df.iloc[-1]['date'])
        # Expected: 100 * (1 + 0.2) = 120
        assert abs(amount - 120.0) < 0.01

    def test_scale_factor(self):
        strategy = BenchmarkDropStrategy(base_amount=100, freq='D', scale_factor=2.0)
        df = _make_history([10.0, 8.0])  # 20% drop, 2x scale
        amount = strategy.get_investment_amount(df, df.iloc[-1]['date'])
        # Expected: 100 * (1 + 0.2 * 2.0) = 140
        assert abs(amount - 140.0) < 0.01


# ============================
# DynamicBenchmarkDropStrategy
# ============================
class TestDynamicBenchmarkDropStrategy:
    def test_max60_no_drop(self):
        """价格未跌破 max60 标杆"""
        strategy = DynamicBenchmarkDropStrategy(
            base_amount=100, freq='D', benchmark_type='max60',
            thresholds=[(0.10, 2.0), (0.05, 1.5)]
        )
        prices = [10.0] * 5 + [10.5]  # 价格上升
        df = _make_history(prices)
        assert strategy.get_investment_amount(df, df.iloc[-1]['date']) == 100.0

    def test_max60_with_drop(self):
        """价格跌破 max60 标杆超过 10%"""
        strategy = DynamicBenchmarkDropStrategy(
            base_amount=100, freq='D', benchmark_type='max60',
            thresholds=[(0.10, 2.0), (0.05, 1.5)]
        )
        prices = [10.0] * 5 + [8.5]  # 15% drop from max
        df = _make_history(prices)
        amount = strategy.get_investment_amount(df, df.iloc[-1]['date'])
        assert amount == 200.0  # > 10% threshold -> 2.0x

    def test_ma250_insufficient_data(self):
        """MA250 数据不足时返回基准金额"""
        strategy = DynamicBenchmarkDropStrategy(
            base_amount=100, freq='D', benchmark_type='ma250',
            thresholds=[(0.10, 2.0)]
        )
        prices = [10.0] * 10
        df = _make_history(prices)
        assert strategy.get_investment_amount(df, df.iloc[-1]['date']) == 100.0


# ============================
# QuadraticMAStrategy
# ============================
class TestQuadraticMAStrategy:
    def test_above_ma250_base_amount(self):
        strategy = QuadraticMAStrategy(base_amount=100, freq='D', k_factor=30.0, max_multiplier=5.0)
        # 250 天价格 10，今天价格 12 (> MA250)
        prices = [10.0] * 250 + [12.0]
        df = _make_history(prices)
        assert strategy.get_investment_amount(df, df.iloc[-1]['date']) == 100.0

    def test_below_ma250_quadratic(self):
        strategy = QuadraticMAStrategy(base_amount=100, freq='D', k_factor=30.0, max_multiplier=5.0)
        # MA250 = 10.0, 今天 = 8.0, D = 0.2, multiplier = 1 + 30*0.04 = 2.2
        prices = [10.0] * 250 + [8.0]
        df = _make_history(prices)
        amount = strategy.get_investment_amount(df, df.iloc[-1]['date'])
        assert abs(amount - 220.0) < 1.0

    def test_max_multiplier_cap(self):
        strategy = QuadraticMAStrategy(base_amount=100, freq='D', k_factor=30.0, max_multiplier=3.0)
        # MA250 = 10.0, 今天 = 5.0, D = 0.5, multiplier = 1 + 30*0.25 = 8.5 -> capped at 3.0
        prices = [10.0] * 250 + [5.0]
        df = _make_history(prices)
        amount = strategy.get_investment_amount(df, df.iloc[-1]['date'])
        assert amount == 300.0

    def test_insufficient_data(self):
        strategy = QuadraticMAStrategy(base_amount=100, freq='D', k_factor=30.0, max_multiplier=5.0)
        prices = [10.0] * 10
        df = _make_history(prices)
        assert strategy.get_investment_amount(df, df.iloc[-1]['date']) == 100.0


# ============================
# create_strategy 工厂函数
# ============================
class TestCreateStrategy:
    def test_fixed(self):
        strategy, name = create_strategy('fixed', {'amount': 200, 'freq': 'W'})
        assert strategy is not None
        assert 'Fixed' in name

    def test_benchmark_drop(self):
        strategy, name = create_strategy('benchmark_drop', {'base_amount': 100, 'freq': 'D', 'scale_factor': 1.5})
        assert isinstance(strategy, BenchmarkDropStrategy)

    def test_quadratic_ma(self):
        strategy, name = create_strategy('quadratic_ma', {'base_amount': 100, 'freq': 'D', 'k_factor': 20.0, 'max_multiplier': 4.0})
        assert isinstance(strategy, QuadraticMAStrategy)

    def test_unknown_type(self):
        strategy, name = create_strategy('nonexistent')
        assert strategy is None
        assert name is None

    def test_default_params(self):
        """即使 params 为空也应该能创建（使用默认值）"""
        strategy, name = create_strategy('fixed')
        assert strategy is not None

    def test_interval_params_as_list(self):
        intervals = [{'start': '2024-01-01', 'end': '2024-12-31', 'amount': 100, 'freq': 'M'}]
        strategy, name = create_strategy('interval', intervals)
        assert isinstance(strategy, IntervalFixedInvestment)
