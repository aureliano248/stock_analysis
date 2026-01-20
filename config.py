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
# SYMBOL = "512890" #红利低波ETF 

# 回测开始日期 (YYYY-MM-DD)
START_DATE = "2019-01-18"
# START_DATE = "2021-09-10"
# START_DATE = "2021-11-26"
# START_DATE = "2024-05-24"

# 回测结束日期 (YYYY-MM-DD)
# END_DATE = "2022-07-01"
# END_DATE = "2023-02-5"
# END_DATE = "2023-07-28"
# END_DATE = "2024-10-13"
# END_DATE = "2025-07-16"
END_DATE = "2026-01-16"


# 2.2 策略选择
# 选项: 'fixed' (普通定投), 'interval' (区间定投), 'profit_ratio' (获利比例策略), 'benchmark_drop' (标杆跌幅策略)
# 动态标杆回撤策略参数 (当 STRATEGY_TYPE = 'dynamic_benchmark' 时生效)
# 均线偏离平方策略参数 (当 STRATEGY_TYPE = 'quadratic_ma' 时生效)
# STRATEGY_TYPE = "fixed"
# STRATEGY_TYPE = "profit_ratio"
# STRATEGY_TYPE = "benchmark_drop"
# STRATEGY_TYPE = "dynamic_benchmark"
STRATEGY_TYPE = "quadratic_ma"


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

# [配置 C] 获利比例策略参数 (当 STRATEGY_TYPE = 'profit_ratio' 时生效)
PROFIT_RATIO_STRATEGY_PARAMS = {
    "base_amount": 100,  # 基准定投金额 (每日)
    "thresholds": [      # 阈值配置: [(比例, 倍数)]
        (0.01, 10),      # 获利比例 < 1% -> 10倍买入
        (0.05, 2)        # 获利比例 < 5% -> 2倍买入
    ]
}

# [配置 D] 标杆跌幅策略参数 (当 STRATEGY_TYPE = 'benchmark_drop' 时生效)
# 逻辑: 以第一天价格为标杆，低于标杆多少百分比，买入金额就增加多少百分比
BENCHMARK_DROP_STRATEGY_PARAMS = {
    'base_amount': 100,      # 基准定投金额
    'freq': 'D',              # 定投频率
    'scale_factor': 1.0       # 放大系数 (1.0 表示 跌10%加10%)
}

# [配置 E] 动态标杆回撤策略参数 (当 STRATEGY_TYPE = 'dynamic_benchmark' 时生效)
# 逻辑: 以 MA250 或 MAX60 为标杆，跌破指定阈值时分档加仓
DYNAMIC_BENCHMARK_STRATEGY_PARAMS = {
    'base_amount': 100,       # 基准定投金额
    'freq': 'D',              # 定投频率
    # 'benchmark_type': 'ma250', # 'ma250' (年线) 或 'max60' (近60日最高)
    'benchmark_type': 'max60', # 'ma250' (年线) 或 'max60' (近60日最高)
    'thresholds': [           # 跌幅阈值配置 (跌幅, 倍数)
        (0.05, 1.05),          # 跌破 5% -> 1.05倍
        (0.15, 1.3),
        (0.20, 1.5),
        (0.30, 2.0),
        (0.35, 3.0),
        (0.40, 4.0),
        (0.45, 5.0),
        (0.50, 10.0)
    ]
}

# [配置 F] 均线偏离平方策略参数 (当 STRATEGY_TYPE = 'quadratic_ma' 时生效)
# 逻辑: 现价 < MA250 时, 买入 = Base * (1 + k * D^2)
QUADRATIC_MA_STRATEGY_PARAMS = {
    'base_amount': 100,       # 基准定投金额
    'freq': 'D',              # 定投频率
    'k_factor': 30.0,         # 系数 k (微调为30)
    'max_multiplier': 5.0     # 最大倍数限制 (5倍)
}

# [配置 G] 策略对比绘图列表 (main_v3.py 使用)
# 指定要在同一张图中对比的策略类型
DRAW_STRATEGY_LIST = [
    'fixed',
    # 'profit_ratio',
    'benchmark_drop',
    'dynamic_benchmark',
    'quadratic_ma'
]
