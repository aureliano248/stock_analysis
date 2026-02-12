import pandas as pd
from .base import BaseStrategy


class ProfitRatioStrategy(BaseStrategy):
    """
    获利比例策略：
    基于每日获利比例 (profit_ratio) 调整定投金额。
    默认执行频率为每日（即每天都会检查并可能买入）。
    """

    def __init__(self, base_amount, thresholds=None):
        """
        :param base_amount: 基准定投金额 (1倍)
        :param thresholds: 列表，每个元素为 (ratio_limit, multiplier)
                           例如 [(0.05, 2), (0.01, 10)]
                           表示 < 5% 时 2倍，< 1% 时 10倍。
        """
        self.base_amount = base_amount
        if thresholds is None:
            self.thresholds = [
                (0.01, 10),  # < 1% -> 10x
                (0.05, 2)    # < 5% -> 2x
            ]
        else:
            # 按 ratio 从小到大排序，以便优先匹配更极端的条件
            self.thresholds = sorted(thresholds, key=lambda x: x[0])

    def get_investment_amount(self, history_df, current_date) -> float:
        if history_df.empty:
            return 0.0

        today_row = history_df.iloc[-1]

        if 'profit_ratio' not in today_row:
            return self.base_amount

        profit_ratio = today_row['profit_ratio']

        if pd.isna(profit_ratio):
            return self.base_amount

        multiplier = 1.0
        for limit, mult in self.thresholds:
            if profit_ratio < limit:
                multiplier = mult
                break

        return self.base_amount * multiplier
