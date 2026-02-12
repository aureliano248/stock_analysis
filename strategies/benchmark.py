import pandas as pd
from .base import BaseStrategy, should_invest


class BenchmarkDropStrategy(BaseStrategy):
    """
    标杆跌幅策略：
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

    def get_investment_amount(self, history_df, current_date) -> float:
        if not should_invest(history_df, current_date, self.freq):
            return 0.0

        benchmark_price = history_df.iloc[0]['close']
        current_price = history_df.iloc[-1]['close']

        if current_price < benchmark_price:
            drop_ratio = (benchmark_price - current_price) / benchmark_price
            increase_ratio = drop_ratio * self.scale_factor
            return self.base_amount * (1 + increase_ratio)
        else:
            return self.base_amount


class DynamicBenchmarkDropStrategy(BaseStrategy):
    """
    动态标杆回撤策略：
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
        # 确保阈值按跌幅从大到小排序
        if thresholds is None:
            self.thresholds = []
        else:
            self.thresholds = sorted(thresholds, key=lambda x: x[0], reverse=True)

    def get_investment_amount(self, history_df, current_date) -> float:
        if not should_invest(history_df, current_date, self.freq):
            return 0.0

        close_series = history_df['close']

        # 计算标杆价格
        benchmark_price = self._calc_benchmark(close_series)
        if benchmark_price is None or pd.isna(benchmark_price):
            return self.base_amount

        current_price = history_df.iloc[-1]['close']

        if current_price >= benchmark_price:
            return self.base_amount

        # 跌幅匹配档位
        drop_ratio = (benchmark_price - current_price) / benchmark_price

        multiplier = 1.0
        for limit, mult in self.thresholds:
            if drop_ratio > limit:
                multiplier = mult
                break

        return self.base_amount * multiplier

    def _calc_benchmark(self, close_series):
        """计算标杆价格"""
        if self.benchmark_type == 'ma250':
            if len(close_series) >= 250:
                return close_series.iloc[-250:].mean()
            else:
                return None  # 数据不足
        elif self.benchmark_type == 'max60':
            if len(close_series) >= 1:
                window = min(len(close_series), 60)
                return close_series.iloc[-window:].max()
            else:
                return None
        else:
            return None
