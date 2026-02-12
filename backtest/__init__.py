"""
回测模块：提供回测引擎和结果摘要功能。
"""

from .engine import run_backtest
from .summary import calc_annualized_return, print_comparison_summary

__all__ = [
    'run_backtest',
    'calc_annualized_return',
    'print_comparison_summary',
]
