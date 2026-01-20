import os
import pandas as pd
import akshare as ak
import config

def fetch_data_from_akshare(symbol, start_date='19900101', end_date=config.CACHE_END_DATE):
    """
    从 AkShare 获取数据。
    尝试顺序: A股股票 -> ETF/基金 -> 指数
    
    :param symbol: 代码, e.g., '000001', '510300', '000300'
    :return: DataFrame
    """
    print(f"Fetching data for {symbol} from AkShare...")
    df = pd.DataFrame()
    
    # 1. 尝试作为 A 股股票获取 (前复权)
    try:
        # adjust='qfq' 前复权
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
        if not df.empty:
            print(f"Success: Found Stock data for {symbol}")
    except:
        pass

    # 2. 如果为空，尝试作为 ETF/基金 获取
    if df.empty:
        try:
             df = ak.fund_etf_hist_em(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
             if not df.empty:
                print(f"Success: Found ETF/Fund data for {symbol}")
        except:
            pass

    # 3. 如果仍为空，尝试作为 指数 获取
    if df.empty:
        try:
            df = ak.index_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date)
            if not df.empty:
                print(f"Success: Found Index data for {symbol}")
        except:
            pass

    if df.empty:
        print(f"Warning: No data found for {symbol} (checked Stock, ETF, and Index)")
        return None
        
    # 重命名列以统一格式
    column_map = {
        "日期": "date",
        "开盘": "open",
        "收盘": "close",
        "最高": "high",
        "最低": "low",
        "成交量": "volume",
        "成交额": "amount",
    }
    df.rename(columns=column_map, inplace=True)
    
    # 过滤并排序需要的列
    needed_cols = ["date", "open", "close", "high", "low", "volume"]
    available_cols = [c for c in needed_cols if c in df.columns]
    
    if not available_cols:
         print(f"Error: Data for {symbol} missing required columns.")
         return None

    df = df[available_cols]
    
    # 确保 date 列是 datetime 类型
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])

    # 4. 尝试获取筹码分布数据 (CYQ) 并合并
    # 仅针对 A 股股票有效，且需要 symbol 是股票代码
    # 注意：这可能会增加网络请求时间
    cyq_map = {
        '获利比例': 'profit_ratio',
        '平均成本': 'avg_cost',
        '90成本-低': 'cost90_low',
        '90成本-高': 'cost90_high',
        '90集中度': 'concentration90',
        '70成本-低': 'cost70_low',
        '70成本-高': 'cost70_high',
        '70集中度': 'concentration70'
    }
    
    try:
        # print(f"Fetching CYQ data for {symbol}...")
        df_cyq = ak.stock_cyq_em(symbol=symbol, adjust="qfq")
        if df_cyq is not None and not df_cyq.empty:
            # 统一日期列名
            cyq_date_col = next((col for col in ['date', '日期'] if col in df_cyq.columns), None)
            if cyq_date_col:
                df_cyq.rename(columns={cyq_date_col: 'date'}, inplace=True)
                df_cyq['date'] = pd.to_datetime(df_cyq['date'])
                
                # 重命名关键列以方便使用
                df_cyq.rename(columns=cyq_map, inplace=True)
                
                # 只保留需要的列
                cols_to_keep = ['date'] + [c for c in cyq_map.values() if c in df_cyq.columns]
                df_cyq = df_cyq[cols_to_keep]
                
                # 合并到主 DataFrame (使用 left join 保留所有行情数据)
                df = pd.merge(df, df_cyq, on='date', how='left')
                # print("Success: Merged CYQ data")
    except Exception as e:
        print(f"Warning: Failed to fetch/merge CYQ data: {e}")

    # 确保关键列存在 (即使没有抓取到，也填充 NaN)，以保证缓存结构的一致性
    # 这避免了因为缺少列而导致 load_data 反复强制更新的问题 (例如针对 ETF 或指数)
    for col in cyq_map.values():
        if col not in df.columns:
            df[col] = pd.NA

    return df

def load_data(symbol, force_update=False):
    """
    加载数据。如果本地存在则读取，否则从网络获取并保存。
    """
    file_path = os.path.join(config.DATA_DIR, f"{symbol}.csv")
    
    if os.path.exists(file_path) and not force_update:
        # print(f"Loading data for {symbol} from local storage...")
        try:
            df = pd.read_csv(file_path, parse_dates=['date'])
            
            # 检查缓存有效性：如果当前策略需要筹码分布数据 ('profit_ratio') 但本地缓存没有
            # 则视为缓存过期，强制刷新
            if config.STRATEGY_TYPE == 'profit_ratio' and 'profit_ratio' not in df.columns:
                print(f"Notice: Strategy '{config.STRATEGY_TYPE}' requires 'profit_ratio' but local cache is missing it. Forcing update...")
                # 不直接 return，让程序继续向下执行网络请求逻辑
            else:
                return df
                
        except Exception as e:
            print(f"Error reading local file for {symbol}: {e}. Will try to refetch.")
    
    # Fetch from network
    df = fetch_data_from_akshare(symbol)
    if df is not None and not df.empty:
        print(f"Saving data for {symbol} to local storage...")
        df.to_csv(file_path, index=False)
        return df
    else:
        return None
