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

class ProfitRatioStrategy(BaseStrategy):
    """
    获利比例策略：
    基于每日获利比例 (profit_ratio) 调整定投金额。
    默认执行频率为每日 (即每天都会检查并可能买入)。
    """
    def __init__(self, base_amount, thresholds=None):
        """
        :param base_amount: 基准定投金额 (1倍)
        :param thresholds: 列表，每个元素为 (ratio_limit, multiplier)
                           例如 [(0.05, 2), (0.01, 10)]
                           表示 < 5% 时 2倍，< 1% 时 10倍。
        """
        self.base_amount = base_amount
        # 默认阈值配置
        if thresholds is None:
            self.thresholds = [
                (0.01, 10), # < 1% -> 10x
                (0.05, 2)   # < 5% -> 2x
            ]
        else:
            # 确保按 ratio 从小到大排序，以便优先匹配更极端的条件 (更小的比例)
            self.thresholds = sorted(thresholds, key=lambda x: x[0])

    def get_investment_amount(self, history_df, current_date):
        if history_df.empty:
            return 0.0
            
        # 获取当天的行
        today_row = history_df.iloc[-1]
        
        # 检查是否有 'profit_ratio' 列
        if 'profit_ratio' not in today_row:
            # 如果没有数据，回退到基准定投
            return self.base_amount
            
        profit_ratio = today_row['profit_ratio']
        
        # 处理 NaN
        if pd.isna(profit_ratio):
            return self.base_amount
            
        # 检查阈值
        multiplier = 1.0
        for limit, mult in self.thresholds:
            if profit_ratio < limit:
                multiplier = mult
                break # 找到满足的最极端条件，应用对应倍数并停止
                
        return self.base_amount * multiplier

class QuadraticMAStrategy(BaseStrategy):
    """
    策略6: 均线偏离平方策略
    以 MA250 为标杆。
    当 现价 < MA250 时触发。
    跌幅 D = (MA250 - 现价) / MA250
    买入金额 = Base * (1 + K * D^2)
    设置最大倍数上限。
    """
    def __init__(self, base_amount, freq='D', k_factor=30.0, max_multiplier=5.0):
        """
        :param base_amount: 基准投资金额
        :param freq: 投资频率
        :param k_factor: 系数 K
        :param max_multiplier: 最大倍数上限
        """
        self.base_amount = base_amount
        self.freq = freq
        self.k_factor = k_factor
        self.max_multiplier = max_multiplier
        self.timing_strategy = FixedInvestment(amount=0, freq=freq)

    def get_investment_amount(self, history_df, current_date):
        if history_df.empty:
            return 0.0
            
        # 1. 时机判断
        should_invest = False
        if len(history_df) == 1:
            should_invest = True
        else:
            prev_date = history_df.iloc[-2]['date']
            if not isinstance(prev_date, pd.Timestamp):
                prev_date = pd.to_datetime(prev_date)
            
            if self.freq == 'D':
                should_invest = True
            elif self.freq == 'M':
                if current_date.month != prev_date.month or current_date.year != prev_date.year:
                    should_invest = True
            elif self.freq == 'W':
                if current_date.isocalendar()[1] != prev_date.isocalendar()[1] or current_date.year != prev_date.year:
                    should_invest = True
        
        if not should_invest:
            return 0.0

        # 2. 计算 MA250
        close_series = history_df['close']
        ma250 = None
        
        if len(close_series) >= 250:
            ma250 = close_series.iloc[-250:].mean()
        else:
            # 数据不足，无法计算 MA250，使用基准金额
            return self.base_amount

        current_price = history_df.iloc[-1]['close']
        
        # 3. 计算买入金额
        if current_price < ma250:
            d = (ma250 - current_price) / ma250
            multiplier = 1 + self.k_factor * (d ** 2)
            # 应用上限
            multiplier = min(multiplier, self.max_multiplier)
            return self.base_amount * multiplier
        else:
            # 现价 >= MA250，维持基准定投
            return self.base_amount

class BenchmarkDropStrategy(BaseStrategy):
    """
    策略4: 标杆跌幅策略
    以回测区间第一天的价格作为标杆。
    如果某天价格低于标杆，则买入金额增加对应的跌幅比例。
    Invest = Base * (1 + (Benchmark - Current) / Benchmark * ScaleFactor)
    """
    def __init__(self, base_amount, freq='D', scale_factor=1.0):
        """
        :param base_amount: 基准投资金额
        :param freq: 投资频率 ('D', 'W', 'M')
        :param scale_factor: 跌幅放大系数，默认 1.0 (跌多少加多少)
        """
        self.base_amount = base_amount
        self.freq = freq
        self.scale_factor = scale_factor
        # 复用 FixedInvestment 的时机判断逻辑
        self.timing_strategy = FixedInvestment(amount=0, freq=freq)

    def get_investment_amount(self, history_df, current_date):
        if history_df.empty:
            return 0.0
            
        # 1. 判断是否是定投日
        # 利用 FixedInvestment 的逻辑，传入 dummy amount 0，只看是否返回 0
        # 但 FixedInvestment 返回 amount 或 0。
        # 这里为了避免重复代码，我简单重写一遍时机判断逻辑
        
        should_invest = False
        if len(history_df) == 1:
            should_invest = True
        else:
            prev_date = history_df.iloc[-2]['date']
            if not isinstance(prev_date, pd.Timestamp):
                prev_date = pd.to_datetime(prev_date)
            
            if self.freq == 'D':
                should_invest = True
            elif self.freq == 'M':
                if current_date.month != prev_date.month or current_date.year != prev_date.year:
                    should_invest = True
            elif self.freq == 'W':
                if current_date.isocalendar()[1] != prev_date.isocalendar()[1] or current_date.year != prev_date.year:
                    should_invest = True
        
        if not should_invest:
            return 0.0

        # 2. 计算金额
        # 标杆价格: 第一天的收盘价
        benchmark_price = history_df.iloc[0]['close']
        current_price = history_df.iloc[-1]['close']
        
        if current_price < benchmark_price:
            drop_ratio = (benchmark_price - current_price) / benchmark_price
            # 增加比例 = 跌幅 * 系数
            increase_ratio = drop_ratio * self.scale_factor
            investment = self.base_amount * (1 + increase_ratio)
        else:
            # 高于或等于标杆，保持基准投入
            investment = self.base_amount
            
        return investment

class DynamicBenchmarkDropStrategy(BaseStrategy):
    """
    策略5: 动态标杆回撤策略
    以 MA250 或 近60日最高点 为标杆。
    根据价格跌破标杆的幅度，分档位增加买入金额。
    """
    def __init__(self, base_amount, freq='D', benchmark_type='ma250', thresholds=None):
        """
        :param base_amount: 基准投资金额
        :param freq: 投资频率
        :param benchmark_type: 'ma250' 或 'max60'
        :param thresholds: list of (drop_ratio, multiplier). e.g. [(0.05, 1.5), ...]
        """
        self.base_amount = base_amount
        self.freq = freq
        self.benchmark_type = benchmark_type.lower()
        # 确保阈值按跌幅从大到小排序 (e.g. 0.5, 0.3, 0.15, 0.05)
        # 这样我们可以依次检查：如果跌幅 > 0.5，则匹配。否则检查 > 0.3...
        if thresholds is None:
            self.thresholds = []
        else:
            self.thresholds = sorted(thresholds, key=lambda x: x[0], reverse=True)
            
        self.timing_strategy = FixedInvestment(amount=0, freq=freq)

    def get_investment_amount(self, history_df, current_date):
        if history_df.empty:
            return 0.0
            
        # 1. 时机判断 (复用 FixedInvestment 逻辑的简化版)
        should_invest = False
        if len(history_df) == 1:
            should_invest = True
        else:
            prev_date = history_df.iloc[-2]['date']
            if not isinstance(prev_date, pd.Timestamp):
                prev_date = pd.to_datetime(prev_date)
            
            if self.freq == 'D':
                should_invest = True
            elif self.freq == 'M':
                if current_date.month != prev_date.month or current_date.year != prev_date.year:
                    should_invest = True
            elif self.freq == 'W':
                if current_date.isocalendar()[1] != prev_date.isocalendar()[1] or current_date.year != prev_date.year:
                    should_invest = True
        
        if not should_invest:
            return 0.0

        # 2. 计算标杆
        benchmark_price = None
        close_series = history_df['close']
        
        if self.benchmark_type == 'ma250':
            if len(close_series) >= 250:
                benchmark_price = close_series.iloc[-250:].mean()
            else:
                # 数据不足，无法计算 MA250，回退到基准金额
                return self.base_amount
                
        elif self.benchmark_type == 'max60':
            if len(close_series) >= 1: # 只要有数据就能算 max
                window = min(len(close_series), 60)
                benchmark_price = close_series.iloc[-window:].max()
            else:
                return self.base_amount
        else:
            # 未知类型
            return self.base_amount

        if benchmark_price is None or pd.isna(benchmark_price):
             return self.base_amount

        # 3. 计算跌幅并匹配档位
        current_price = history_df.iloc[-1]['close']
        
        if current_price >= benchmark_price:
            return self.base_amount
            
        # 跌幅 (正数表示跌了多少)
        drop_ratio = (benchmark_price - current_price) / benchmark_price
        
        multiplier = 1.0
        # thresholds 是从大到小排序的 (e.g. 0.5, 0.3, 0.15, 0.05)
        for limit, mult in self.thresholds:
            if drop_ratio > limit: # 例如 跌幅 0.6 > 0.5
                multiplier = mult
                break
        
        return self.base_amount * multiplier
