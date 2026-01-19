import os
import datetime

# ==========================================
# 1. 路径与环境配置
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
RESULTS_DIR = os.path.join(BASE_DIR, 'results')

# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# 缓存数据的结束日期，格式 YYYYMMDD
# 默认设置为今天，确保拉取到最新数据
CACHE_END_DATE = datetime.date.today().strftime('%Y%m%d')
# CACHE_END_DATE = '20251231' # 固定截止日期示例


# ==========================================
# 2. 回测参数配置 (Backtest Configuration)
# ==========================================

# 2.1 标的与时间
# 标的代码
# 支持: A股股票 (如 "600519"), ETF/基金 (如 "510300"), 指数 (如 "000300")
# SYMBOL = "600519"
# SYMBOL = "000300" # 沪深300指数
SYMBOL = "513180" #恒生科技指数ETF 

# 回测开始日期 (YYYY-MM-DD)
START_DATE = "2021-11-26"

# 回测结束日期 (YYYY-MM-DD)
END_DATE = "2023-07-01"
# END_DATE = "2023-07-28"
# END_DATE = "2024-10-10"
# END_DATE = "2026-01-01"


# 2.2 策略选择
# 选项: 'fixed' (普通定投), 'interval' (区间定投)
STRATEGY_TYPE = "fixed" 


# 2.3 策略详情配置

# [配置 A] 普通定投参数 (当 STRATEGY_TYPE = 'fixed' 时生效)
FIXED_STRATEGY_PARAMS = {
    "amount": 100,    # 每次定投金额
    "freq": "D"        # 定投频率: 'D' (日), 'W' (周), 'M' (月)
}

# [配置 B] 区间定投参数 (当 STRATEGY_TYPE = 'interval' 时生效)
# 列表中的每个字典代表一个时间段的定投计划
INTERVAL_STRATEGY_PARAMS = [
    {
        'start': '2020-01-01', 
        'end': '2021-12-31', 
        'amount': 1000, 
        'freq': 'M'
    },
    {
        'start': '2022-01-01', 
        'end': '2023-12-31', 
        'amount': 2000, 
        'freq': 'M'
    }
]
