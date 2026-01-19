from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):
    @abstractmethod
    def get_investment_amount(self, history_df, current_date):
        """
        计算当天的投资金额
        :param history_df: 截止到 current_date 的历史数据 DataFrame (应包含今天的数据)
        :param current_date: 当前日期 (datetime/Timestamp)
        :return: float (投资金额, 0 表示不投资)
        """
        pass

class FixedInvestment(BaseStrategy):
    """
    定期定额投资策略
    """
    def __init__(self, amount, freq='M'):
        """
        :param amount: 每次定投金额
        :param freq: 定投频率, 'D' (日), 'W' (周), 'M' (月)
        """
        self.amount = amount
        self.freq = freq.upper()

    def get_investment_amount(self, history_df, current_date):
        # 必须确保 history_df 按时间排序且非空
        if history_df.empty:
            return 0.0
            
        # 如果只有一行数据（今天），说明是回测的第一天，执行投资
        if len(history_df) == 1:
            return self.amount

        # 获取上一个交易日的日期
        # history_df 的最后一行应该是今天 (current_date)
        # 倒数第二行是上一个交易日
        prev_date = history_df.iloc[-2]['date']
        
        # 确保 prev_date 是 timestamp 类型
        if not isinstance(prev_date, pd.Timestamp):
            prev_date = pd.to_datetime(prev_date)

        should_invest = False
        if self.freq == 'M':
            # 如果月份变化，说明进入新的一月
            if current_date.month != prev_date.month or current_date.year != prev_date.year:
                should_invest = True
        elif self.freq == 'W':
            # 如果周数变化 (注意跨年时的周数)
            if current_date.isocalendar()[1] != prev_date.isocalendar()[1] or current_date.year != prev_date.year:
                 should_invest = True
        elif self.freq == 'D':
            should_invest = True
            
        return self.amount if should_invest else 0.0

class IntervalFixedInvestment(BaseStrategy):
    """
    区间定投策略：根据时间区间设定不同的定投参数
    """
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

    def get_investment_amount(self, history_df, current_date):
        # 找到 current_date 所在的区间
        for item in self.interval_strategies:
            if item['start'] <= current_date <= item['end']:
                return item['strategy'].get_investment_amount(history_df, current_date)
        return 0.0
