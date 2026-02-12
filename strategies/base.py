from abc import ABC, abstractmethod
import pandas as pd


class BaseStrategy(ABC):
    @abstractmethod
    def get_investment_amount(self, history_df, current_date) -> float:
        """
        计算当天的投资金额。

        :param history_df: 截止到 current_date 的历史数据 DataFrame (应包含今天的数据)
        :param current_date: 当前日期 (datetime/Timestamp)
        :return: float (投资金额, 0 表示不投资)
        """
        ...


def should_invest(history_df, current_date, freq='D') -> bool:
    """
    通用的投资时机判断函数。

    根据频率设置判断当天是否应该投资:
    - 'D': 每个交易日都投
    - 'W': 每周第一个交易日投
    - 'M': 每月第一个交易日投

    :param history_df: 截止到 current_date 的历史数据 DataFrame
    :param current_date: 当前日期 (Timestamp)
    :param freq: 投资频率，'D' / 'W' / 'M'
    :return: True 表示今天应该投资
    """
    if history_df.empty:
        return False

    freq = freq.upper()

    # 回测的第一天，总是投资
    if len(history_df) == 1:
        return True

    # 获取上一个交易日的日期
    prev_date = history_df.iloc[-2]['date']
    if not isinstance(prev_date, pd.Timestamp):
        prev_date = pd.to_datetime(prev_date)

    if freq == 'D':
        return True
    elif freq == 'M':
        return (current_date.month != prev_date.month or
                current_date.year != prev_date.year)
    elif freq == 'W':
        return (current_date.isocalendar()[1] != prev_date.isocalendar()[1] or
                current_date.year != prev_date.year)
    else:
        return True
