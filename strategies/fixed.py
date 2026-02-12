import pandas as pd
from .base import BaseStrategy, should_invest


class FixedInvestment(BaseStrategy):
    """定期定额投资策略"""

    def __init__(self, amount, freq='M'):
        """
        :param amount: 每次定投金额
        :param freq: 定投频率, 'D' (日), 'W' (周), 'M' (月)
        """
        self.amount = amount
        self.freq = freq.upper()

    def get_investment_amount(self, history_df, current_date) -> float:
        if not should_invest(history_df, current_date, self.freq):
            return 0.0
        return self.amount


class IntervalFixedInvestment(BaseStrategy):
    """区间定投策略：根据时间区间设定不同的定投参数"""

    def __init__(self, intervals):
        """
        :param intervals: 列表，每个元素为 dict
                          {'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD', 'amount': float, 'freq': 'M'}
        """
        self.interval_strategies = []
        for item in intervals:
            self.interval_strategies.append({
                'start': pd.to_datetime(item['start']),
                'end': pd.to_datetime(item['end']),
                'strategy': FixedInvestment(item['amount'], item['freq'])
            })

    def get_investment_amount(self, history_df, current_date) -> float:
        for item in self.interval_strategies:
            if item['start'] <= current_date <= item['end']:
                return item['strategy'].get_investment_amount(history_df, current_date)
        return 0.0
