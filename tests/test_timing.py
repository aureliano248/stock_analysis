"""测试 strategies.base.should_invest 时机判断函数"""

import pytest
import pandas as pd
from strategies.base import should_invest


def _make_history(dates):
    """构造简单的 history DataFrame"""
    return pd.DataFrame({
        'date': [pd.to_datetime(d) for d in dates],
        'close': [100.0] * len(dates),
    })


class TestShouldInvestDaily:
    def test_first_day_always_invest(self):
        df = _make_history(['2024-01-02'])
        assert should_invest(df, pd.to_datetime('2024-01-02'), 'D') is True

    def test_daily_always_true(self):
        df = _make_history(['2024-01-02', '2024-01-03'])
        assert should_invest(df, pd.to_datetime('2024-01-03'), 'D') is True

    def test_empty_df(self):
        df = pd.DataFrame()
        assert should_invest(df, pd.to_datetime('2024-01-02'), 'D') is False


class TestShouldInvestWeekly:
    def test_same_week_no_invest(self):
        """同一周内的第二个交易日不应投资"""
        df = _make_history(['2024-01-08', '2024-01-09'])  # Mon, Tue (same week)
        assert should_invest(df, pd.to_datetime('2024-01-09'), 'W') is False

    def test_new_week_invest(self):
        """新的一周第一个交易日应投资"""
        df = _make_history(['2024-01-05', '2024-01-08'])  # Fri, next Mon
        assert should_invest(df, pd.to_datetime('2024-01-08'), 'W') is True

    def test_first_day_invest(self):
        df = _make_history(['2024-01-08'])
        assert should_invest(df, pd.to_datetime('2024-01-08'), 'W') is True

    def test_cross_year_week(self):
        """跨年的周判断"""
        df = _make_history(['2023-12-29', '2024-01-02'])  # Fri -> next Tue
        assert should_invest(df, pd.to_datetime('2024-01-02'), 'W') is True


class TestShouldInvestMonthly:
    def test_same_month_no_invest(self):
        df = _make_history(['2024-01-02', '2024-01-15'])
        assert should_invest(df, pd.to_datetime('2024-01-15'), 'M') is False

    def test_new_month_invest(self):
        df = _make_history(['2024-01-31', '2024-02-01'])
        assert should_invest(df, pd.to_datetime('2024-02-01'), 'M') is True

    def test_first_day_invest(self):
        df = _make_history(['2024-01-02'])
        assert should_invest(df, pd.to_datetime('2024-01-02'), 'M') is True

    def test_cross_year_month(self):
        """跨年的月判断"""
        df = _make_history(['2023-12-29', '2024-01-02'])
        assert should_invest(df, pd.to_datetime('2024-01-02'), 'M') is True
