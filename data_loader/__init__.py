
import pandas as pd
import os
import datetime
from .symbol_resolver import SymbolResolver
from .data_provider import DataProvider
from .cache_manager import CacheManager
from .realtime_provider import RealtimeProvider

# 默认数据目录
_DEFAULT_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

# 全局组件（延迟初始化，支持自定义 data_dir）
_resolver = SymbolResolver()
_provider = DataProvider()
_realtime = RealtimeProvider()
_cache_mgr = None
_cache_mgr_dir = None


def _get_cache_mgr(data_dir=None):
    """获取或创建 CacheManager 实例（按 data_dir 缓存）"""
    global _cache_mgr, _cache_mgr_dir
    if data_dir is None:
        data_dir = _DEFAULT_DATA_DIR
    if _cache_mgr is None or _cache_mgr_dir != data_dir:
        _cache_mgr = CacheManager(data_dir)
        _cache_mgr_dir = data_dir
    return _cache_mgr


def load_data(symbol, start_date='19900101', end_date=None, adjust='qfq',
              force_update=False, data_dir=None, strategy_type=None):
    """
    统一的数据加载入口。

    :param symbol: 标的代码，如 "513180", "000300.OF"
    :param start_date: 数据起始日期，格式 YYYYMMDD
    :param end_date: 数据截止日期，格式 YYYYMMDD，默认为今天
    :param adjust: 复权方式，'qfq' (前复权), 'hfq' (后复权), '' (不复权)
    :param force_update: 是否强制全量更新
    :param data_dir: 数据缓存目录，默认为项目下的 data/ 目录
    :param strategy_type: 策略类型（影响缓存更新判断，如 'profit_ratio' 需要筹码数据）
    :return: (DataFrame, stock_name) 元组
    """
    if end_date is None:
        end_date = datetime.date.today().strftime('%Y%m%d')
    if data_dir is None:
        data_dir = _DEFAULT_DATA_DIR

    cache_mgr = _get_cache_mgr(data_dir)

    clean_symbol, suffix, asset_type = _resolver.resolve(symbol)
    file_path = cache_mgr.get_file_path(clean_symbol, suffix, adjust)

    # 1. 读取缓存
    df = cache_mgr.load_local_cache(file_path)

    # 2. 检查更新需求
    needs_update, fetch_start = cache_mgr.check_needs_update(df, end_date, strategy_type)
    if force_update:
        needs_update = True
        fetch_start = '19900101'

    # 3. 执行更新
    if needs_update:
        print(f"Updating data for {symbol} (start={fetch_start})...")
        df_new, detected_type = _fetch_raw_data(clean_symbol, suffix, asset_type, fetch_start, end_date, adjust)

        if not df_new.empty:
            df = cache_mgr.merge_data(df, df_new)

            # 针对股票的特殊逻辑：筹码分布
            if detected_type == 'stock':
                df_cyq = _provider.fetch_cyq(clean_symbol, adjust)
                if not df_cyq.empty:
                    df = pd.merge(df, df_cyq, on='date', how='left')

            # 填充缺失列以保持结构一致 (CYQ 相关列)
            cyq_cols = ['profit_ratio', 'avg_cost', 'cost90_low', 'cost90_high',
                        'concentration90', 'cost70_low', 'cost70_high', 'concentration70']
            for col in cyq_cols:
                if col not in df.columns:
                    df[col] = pd.NA

            cache_mgr.save_cache(df, file_path)
        else:
            print(f"Warning: No new data fetched for {symbol}")

    stock_name = _resolver.get_stock_name(symbol, data_dir)
    return df, stock_name


def _fetch_raw_data(symbol, suffix, asset_type, start, end, adjust):
    """内部探测逻辑"""
    if asset_type == 'otc_fund' or suffix == 'OF':
        return _provider.fetch_otc_fund(symbol, start, end)

    # 按优先级探测
    # 指数
    df, t = _provider.fetch_index(symbol, start, end)
    if not df.empty:
        return df, t

    # 股票
    df, t = _provider.fetch_stock(symbol, start, end, adjust)
    if not df.empty:
        return df, t

    # ETF
    df, t = _provider.fetch_etf(symbol, start, end, adjust)
    if not df.empty:
        return df, t

    # 场外基金 (不带后缀的情况)
    df, t = _provider.fetch_otc_fund(symbol, start, end)
    if not df.empty:
        return df, t

    return pd.DataFrame(), None


def get_stock_name(symbol, data_dir=None):
    """获取资产中文名称"""
    if data_dir is None:
        data_dir = _DEFAULT_DATA_DIR
    return _resolver.get_stock_name(symbol, data_dir)


def get_realtime_quote(symbol, asset_type=None):
    """
    获取给定标的的实时行情。

    :param symbol: 标的代码，如 "513180", "600519", "000300.OF"
    :param asset_type: 资产类型提示 ('index', 'stock', 'etf', 'otc_fund')，None 时自动探测
    :return: dict 包含标准化行情字段 (price, change, change_pct, open, high, low, ...)
             获取失败返回 None
    """
    clean_symbol = str(symbol).strip()
    # 如果有 .OF 后缀，自动识别为场外基金
    if '.' in clean_symbol:
        parts = clean_symbol.split('.')
        clean_symbol = parts[0]
        if parts[1].upper() == 'OF':
            asset_type = 'otc_fund'
    return _realtime.get_quote(clean_symbol, asset_type=asset_type)
