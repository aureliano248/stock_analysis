from .base import BaseStrategy, should_invest


class QuadraticMAStrategy(BaseStrategy):
    """
    均线偏离平方策略：
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

    def get_investment_amount(self, history_df, current_date) -> float:
        if not should_invest(history_df, current_date, self.freq):
            return 0.0

        # 计算 MA250
        close_series = history_df['close']

        if len(close_series) < 250:
            # 数据不足，无法计算 MA250，使用基准金额
            return self.base_amount

        ma250 = close_series.iloc[-250:].mean()
        current_price = history_df.iloc[-1]['close']

        if current_price < ma250:
            d = (ma250 - current_price) / ma250
            multiplier = 1 + self.k_factor * (d ** 2)
            multiplier = min(multiplier, self.max_multiplier)
            return self.base_amount * multiplier
        else:
            return self.base_amount
