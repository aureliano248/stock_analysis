import pandas as pd
import strategies
from main import run_backtest
import unittest
from datetime import datetime, timedelta

class TestStockAnalysis(unittest.TestCase):
    
    def create_dummy_data(self, price_pattern='constant', start_date='2020-01-01', days=365):
        dates = [datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=i) for i in range(days)]
        data = []
        
        base_price = 10.0
        
        for i, d in enumerate(dates):
            if price_pattern == 'constant':
                price = base_price
            elif price_pattern == 'linear_up':
                price = base_price + i * 0.1
            elif price_pattern == 'linear_down':
                price = max(0.1, base_price - i * 0.01)
            else:
                price = base_price
                
            data.append({
                'date': d,
                'open': price,
                'close': price,
                'high': price,
                'low': price,
                'volume': 1000
            })
            
        return pd.DataFrame(data)

    def test_constant_price(self):
        """
        测试恒定价格，收益率应为 0
        """
        print("\nRunning Test: Constant Price")
        df = self.create_dummy_data('constant')
        strategy = strategies.FixedInvestment(amount=100, freq='D')
        
        # 只要有一笔交易，就应该能算出结果
        result = run_backtest("TEST_CONSTANT", '2020-01-01', '2020-12-31', strategy, "Daily_100", df=df)
        
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result['return_rate'], 0.0, places=4)
        # 最终市值应该等于总投入（浮点数可能有微小差异）
        self.assertAlmostEqual(result['total_invested'], result['final_value'], places=2)

    def test_linear_up(self):
        """
        测试线性上涨，收益率应大于 0
        """
        print("\nRunning Test: Linear Up")
        df = self.create_dummy_data('linear_up')
        strategy = strategies.FixedInvestment(amount=100, freq='M')
        
        result = run_backtest("TEST_UP", '2020-01-01', '2020-12-31', strategy, "Monthly_100", df=df)
        
        self.assertIsNotNone(result)
        self.assertGreater(result['return_rate'], 0)

    def test_interval_strategy(self):
        """
        测试区间定投策略
        """
        print("\nRunning Test: Interval Strategy")
        df = self.create_dummy_data('constant') # 还是用恒定价格方便验证投入金额
        
        # 2020 全年，前半年投 100，后半年投 200
        intervals = [
            {'start': '2020-01-01', 'end': '2020-06-30', 'amount': 100, 'freq': 'M'},
            {'start': '2020-07-01', 'end': '2020-12-31', 'amount': 200, 'freq': 'M'}
        ]
        strategy = strategies.IntervalFixedInvestment(intervals)
        
        result = run_backtest("TEST_INTERVAL", '2020-01-01', '2020-12-31', strategy, "Interval_Mixed", df=df)
        
        self.assertIsNotNone(result)
        # 验证总投入
        # 1-6月: 6次 * 100 = 600
        # 7-12月: 6次 * 200 = 1200
        # 总计 1800
        # 注意：我们的策略是每月变动时投。
        # 1月1日(或第一个数据日)投。
        # 因为 create_dummy_data 有每日数据，所以每月1号都会投。
        # 1,2,3,4,5,6月各投1次。
        # 7,8,9,10,11,12月各投1次。
        
        self.assertEqual(result['total_invested'], 1800)


if __name__ == '__main__':
    unittest.main()
