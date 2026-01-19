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
    
    # 1. 尝试作为 A 股股票获取 (后复权)
    try:
        # adjust='hfq' 后复权
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="hfq")
        if not df.empty:
            print(f"Success: Found Stock data for {symbol}")
    except:
        pass

    # 2. 如果为空，尝试作为 ETF/基金 获取
    if df.empty:
        try:
             df = ak.fund_etf_hist_em(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="hfq")
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
