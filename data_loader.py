import os
import pandas as pd
import akshare as ak
import config
import datetime

def fetch_data_from_akshare(symbol, start_date='19900101', end_date=config.CACHE_END_DATE, adjust='qfq'):
    """
    从 AkShare 获取数据。
    尝试顺序: A股股票 -> ETF/基金 -> 指数
    
    :param symbol: 代码, e.g., '000001', '510300', '000300'
    :param adjust: 复权类型, 'qfq' (default), 'hfq', or '' (None)
    :return: DataFrame
    """
    print(f"Fetching data for {symbol} from AkShare (adjust={adjust})...")
    df = pd.DataFrame()
    data_source_type = None
    
    # 1. 尝试作为 A 股股票获取
    try:
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust=adjust)
        if not df.empty:
            print(f"Success: Found Stock data for {symbol}")
            data_source_type = 'stock'
    except:
        pass

    # 2. 如果为空，尝试作为 ETF/基金 获取
    if df.empty:
        try:
             df = ak.fund_etf_hist_em(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust=adjust)
             if not df.empty:
                print(f"Success: Found ETF/Fund data for {symbol}")
                data_source_type = 'etf'
        except:
            pass

    # 3. 如果仍为空，尝试作为 指数 获取
    # 指数接口通常没有 adjust 参数，或者逻辑不同，暂保持原样
    if df.empty:
        try:
            df = ak.index_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date)
            if not df.empty:
                print(f"Success: Found Index data for {symbol}")
                data_source_type = 'index'
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
    
    # 仅当数据源为 'stock' 时才尝试获取 CYQ 数据
    if data_source_type == 'stock':
        try:
            # print(f"Fetching CYQ data for {symbol}...")
            # CYQ data adjustment should match the main data adjustment if possible
            df_cyq = ak.stock_cyq_em(symbol=symbol, adjust=adjust)
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

def load_data(symbol, start_date='19900101', end_date=None, adjust='qfq', force_update=False):
    """
    加载数据。如果本地存在则读取，否则从网络获取并保存。
    支持缓存验证和自动更新。
    
    :param symbol: 代码
    :param start_date: 开始日期 YYYYMMDD
    :param end_date: 结束日期 YYYYMMDD (default: config.CACHE_END_DATE)
    :param adjust: 复权类型 'qfq', 'hfq'
    :param force_update: 强制刷新
    """
    if end_date is None:
        end_date = config.CACHE_END_DATE

    # Construct filename with adjustment type
    filename = f"{symbol}_{adjust}.csv"
    file_path = os.path.join(config.DATA_DIR, filename)
    
    # Check if cache exists
    if os.path.exists(file_path) and not force_update:
        try:
            df = pd.read_csv(file_path, parse_dates=['date'])
            
            # --- Cache Validation Logic ---
            if not df.empty and 'date' in df.columns:
                cached_last_date = df['date'].iloc[-1].date()
                request_end_date = pd.to_datetime(end_date).date()
                
                # Current time check for intraday updates
                current_dt = datetime.datetime.now()
                current_date = current_dt.date()
                current_time = current_dt.time()
                cutoff_time = datetime.time(15, 10) # 15:10

                needs_update = False

                # 1. Check if cache is old (last date in cache < requested end date)
                if cached_last_date < request_end_date:
                    # But verify if the requested end date is actually in the future compared to "now"
                    # If request_end_date is today, and cache is yesterday, we need update.
                    # If request_end_date is yesterday, and cache is yesterday, we are good.
                    
                    # Special case: If today is a trading day, we might not have data for it yet until after market close.
                    # Simple rule: if cache < request, we *try* to update.
                    # But to avoid unnecessary fetches if market hasn't closed or data isn't out:
                    # If request > cache, proceed to fetch.
                    # However, if request > current_date (future), we can only fetch up to current_date.
                    
                    # Logic: If the user *wants* data up to end_date, and we have less than that,
                    # AND it is possible to get more data (i.e. end_date <= current_date), then update.
                    if request_end_date <= current_date:
                         # 优化：如果在开盘前 (e.g. 09:15)，且缓存已经是昨天的数据，则不需要更新
                         # 因为此时 API 还没有今天的数据，获取也是白费
                         is_pre_market = current_time < datetime.time(9, 15)
                         is_cache_yesterday = (current_date - cached_last_date).days == 1

                         if is_pre_market and is_cache_yesterday:
                             print(f"Pre-market time ({current_time}), cache up to yesterday ({cached_last_date}). Skipping update.")
                             needs_update = False
                         else:
                             print(f"Cache expired (Last: {cached_last_date}, Requested: {request_end_date}). Updating...")
                             needs_update = True
                    elif cached_last_date < current_date:
                        # Requested future, but cache is older than today. Try to get up to today.
                        print(f"Cache older than today (Last: {cached_last_date}). Updating...")
                        needs_update = True

                # 2. Intraday update check
                # If current_date == end_date and current_time < 15:10, force update
                # even if cache has data for today (it might be partial or previous check)
                # Actually, if cache *has* data for today, it means we already fetched it today.
                # If current_time < 15:10, that data might be incomplete (if fetched during trading).
                # So we force re-fetch to get latest snapshot.
                # Optimized: Only check intraday if market is open (after 09:15)
                start_time = datetime.time(9, 15)
                if current_date == request_end_date and start_time < current_time < cutoff_time:
                    print(f"Intraday update triggered (Time: {current_time} < {cutoff_time}). Updating...")
                    needs_update = True

                # 3. Strategy requirement check
                if config.STRATEGY_TYPE == 'profit_ratio' and 'profit_ratio' not in df.columns:
                    print(f"Strategy requirement missing (profit_ratio). Updating...")
                    needs_update = True

                if not needs_update:
                    return df
            else:
                 # Empty dataframe or invalid structure
                 needs_update = True

        except Exception as e:
            print(f"Error reading local file for {symbol}: {e}. Will try to refetch.")
            needs_update = True
    else:
        needs_update = True
    
    if needs_update:
        # Fetch from network
        # Always fetch from '19900101' to ensure full coverage as requested
        fetch_start_date = '19900101'
        df = fetch_data_from_akshare(symbol, start_date=fetch_start_date, end_date=end_date, adjust=adjust)
        
        if df is not None and not df.empty:
            print(f"Saving data for {symbol} to {file_path}...")
            df.to_csv(file_path, index=False)
            return df
        else:
            return None
    
    return None
