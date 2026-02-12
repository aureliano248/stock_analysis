"""
策略模块：提供各种定投策略实现和策略工厂函数。

使用示例:
    from strategies import create_strategy, FixedInvestment

    # 方式 1: 直接实例化
    strategy = FixedInvestment(amount=100, freq='D')

    # 方式 2: 通过工厂函数（接收策略类型 + 参数字典）
    strategy, name = create_strategy('fixed', {'amount': 100, 'freq': 'D'})
"""

from .base import BaseStrategy, should_invest
from .fixed import FixedInvestment, IntervalFixedInvestment
from .profit_ratio import ProfitRatioStrategy
from .benchmark import BenchmarkDropStrategy, DynamicBenchmarkDropStrategy
from .quadratic_ma import QuadraticMAStrategy

__all__ = [
    'BaseStrategy',
    'should_invest',
    'FixedInvestment',
    'IntervalFixedInvestment',
    'ProfitRatioStrategy',
    'BenchmarkDropStrategy',
    'DynamicBenchmarkDropStrategy',
    'QuadraticMAStrategy',
    'create_strategy',
]


def create_strategy(strategy_type, params=None):
    """
    策略工厂函数：根据策略类型和参数创建策略实例。

    :param strategy_type: 策略类型字符串
        'fixed', 'interval', 'profit_ratio', 'benchmark_drop', 'dynamic_benchmark', 'quadratic_ma'
    :param params: 参数字典，各策略所需参数不同：
        - fixed: {'amount': float, 'freq': str}
        - interval: [{'start': str, 'end': str, 'amount': float, 'freq': str}, ...]
        - profit_ratio: {'base_amount': float, 'thresholds': list}
        - benchmark_drop: {'base_amount': float, 'freq': str, 'scale_factor': float}
        - dynamic_benchmark: {'base_amount': float, 'freq': str, 'benchmark_type': str, 'thresholds': list}
        - quadratic_ma: {'base_amount': float, 'freq': str, 'k_factor': float, 'max_multiplier': float}
    :return: (strategy_instance, strategy_name) 元组，未知类型返回 (None, None)
    """
    if params is None:
        params = {}

    if strategy_type == 'fixed':
        strategy = FixedInvestment(
            amount=params.get('amount', 100),
            freq=params.get('freq', 'D')
        )
        name = f"Fixed_{params.get('freq', 'D')}_{params.get('amount', 100)}"

    elif strategy_type == 'interval':
        # params 本身就是区间列表
        intervals = params if isinstance(params, list) else params.get('intervals', [])
        strategy = IntervalFixedInvestment(intervals=intervals)
        name = "Interval_Custom"

    elif strategy_type == 'profit_ratio':
        strategy = ProfitRatioStrategy(
            base_amount=params.get('base_amount', 100),
            thresholds=params.get('thresholds')
        )
        name = "Profit_Ratio_Dynamic"

    elif strategy_type == 'benchmark_drop':
        strategy = BenchmarkDropStrategy(
            base_amount=params.get('base_amount', 100),
            freq=params.get('freq', 'D'),
            scale_factor=params.get('scale_factor', 1.0)
        )
        name = f"BenchmarkDrop_{params.get('freq', 'D')}_x{params.get('scale_factor', 1.0)}"

    elif strategy_type == 'dynamic_benchmark':
        strategy = DynamicBenchmarkDropStrategy(
            base_amount=params.get('base_amount', 100),
            freq=params.get('freq', 'D'),
            benchmark_type=params.get('benchmark_type', 'ma250'),
            thresholds=params.get('thresholds')
        )
        name = f"DynamicBenchmark_{params.get('benchmark_type', 'ma250')}"

    elif strategy_type == 'quadratic_ma':
        strategy = QuadraticMAStrategy(
            base_amount=params.get('base_amount', 100),
            freq=params.get('freq', 'D'),
            k_factor=params.get('k_factor', 30.0),
            max_multiplier=params.get('max_multiplier', 5.0)
        )
        name = f"QuadraticMA_K{params.get('k_factor', 30.0)}"

    else:
        print(f"Warning: Unknown strategy type '{strategy_type}'")
        return None, None

    return strategy, name


def get_strategy_params(strategy_type, config_module):
    """
    从 config 模块中读取对应策略的参数字典。
    这是连接旧 config 模块和新 create_strategy 的桥梁函数。

    :param strategy_type: 策略类型字符串
    :param config_module: config 模块（或任何有相同属性的对象）
    :return: 参数字典
    """
    mapping = {
        'fixed': 'FIXED_STRATEGY_PARAMS',
        'interval': 'INTERVAL_STRATEGY_PARAMS',
        'profit_ratio': 'PROFIT_RATIO_STRATEGY_PARAMS',
        'benchmark_drop': 'BENCHMARK_DROP_STRATEGY_PARAMS',
        'dynamic_benchmark': 'DYNAMIC_BENCHMARK_STRATEGY_PARAMS',
        'quadratic_ma': 'QUADRATIC_MA_STRATEGY_PARAMS',
    }
    attr_name = mapping.get(strategy_type)
    if attr_name and hasattr(config_module, attr_name):
        return getattr(config_module, attr_name)
    return {}
