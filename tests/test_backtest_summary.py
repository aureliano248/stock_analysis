"""测试 backtest.summary 摘要计算逻辑"""

import pytest
import pandas as pd
from backtest.summary import calc_annualized_return, build_comparison_summary


class TestCalcAnnualizedReturn:
    def test_positive_return(self):
        # 投入 1000, 1年后变成 1100, CAGR = 10%
        result = calc_annualized_return(1000, 1100, 365)
        assert abs(result - 10.0) < 0.5

    def test_zero_invested(self):
        assert calc_annualized_return(0, 100, 365) == 0.0

    def test_zero_value(self):
        assert calc_annualized_return(100, 0, 365) == 0.0

    def test_zero_days(self):
        assert calc_annualized_return(100, 110, 0) == 0.0

    def test_negative_invested(self):
        assert calc_annualized_return(-100, 110, 365) == 0.0

    def test_multi_year(self):
        # 投入 1000, 2年后变成 1210, CAGR ~ 10%
        result = calc_annualized_return(1000, 1210, 730)
        assert abs(result - 10.0) < 1.0

    def test_very_short_period(self):
        # 极短时间（< 0.01年 ≈ 3.65天）
        result = calc_annualized_return(1000, 1100, 1)
        assert result == 0.0


class TestBuildComparisonSummary:
    def test_basic_summary(self):
        results = {
            'Strategy_A': pd.DataFrame({
                'date': [pd.to_datetime('2024-01-31')],
                'total_invested': [1000.0],
                'final_value': [1100.0],
                'profit': [100.0],
                'return_rate': [10.0],
            }),
            'Strategy_B': pd.DataFrame({
                'date': [pd.to_datetime('2024-01-31')],
                'total_invested': [2000.0],
                'final_value': [2400.0],
                'profit': [400.0],
                'return_rate': [20.0],
            }),
        }
        summary = build_comparison_summary(results, '2024-01-01', '2024-01-31')
        assert len(summary) == 2
        assert 'Strategy' in summary.columns
        assert 'Annualized (%)' in summary.columns
        # B 排第一（return rate 更高）
        assert summary.iloc[0]['Strategy'] == 'Strategy_B'

    def test_empty_results(self):
        summary = build_comparison_summary({}, '2024-01-01', '2024-01-31')
        assert summary.empty

    def test_with_none_result(self):
        results = {
            'Strategy_A': None,
            'Strategy_B': pd.DataFrame({
                'date': [pd.to_datetime('2024-01-31')],
                'total_invested': [1000.0],
                'final_value': [1100.0],
                'profit': [100.0],
                'return_rate': [10.0],
            }),
        }
        summary = build_comparison_summary(results, '2024-01-01', '2024-01-31')
        assert len(summary) == 1
