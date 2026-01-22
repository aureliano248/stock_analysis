import os
import pandas as pd
import akshare as ak
import config
import datetime

def fetch_data_from_akshare(symbol, start_date='19900101', end_date=config.CACHE_END_DATE, adjust='qfq'):
    """
    从 AkShare 获取数据。
    尝试顺序: A股股票 -> 场内ETF -> 场外基金(OTC) -> 指数
    
    :param symbol: 代码, e.g., '000001', '510300', '017641'
    :param adjust: 复权类型, 'qfq' (default), 'hfq', or '' (None)
    :return: DataFrame
    """
    # 清洗 symbol，移除后缀 (如 017641.OF -> 017641)
    clean_symbol = str(symbol).strip().split('.')[0]
    
    print(f"Fetching data for {clean_symbol} from AkShare (adjust={adjust})...")
    df = pd.DataFrame()
    data_source_type = None
    
    # =========================================================
    # 1. 尝试作为 A 股股票获取
    # =========================================================
    try:
        df = ak.stock_zh_a_hist(symbol=clean_symbol, period="daily", start_date=start_date, end_date=end_date, adjust=adjust)
        if not df.empty:
            print(f"Success: Found Stock data for {clean_symbol}")
            data_source_type = 'stock'
    except:
        pass

    # =========================================================
    # 2. 尝试作为 场内ETF 获取 (以 51/15 开头通常为此类)
    # =========================================================
    if df.empty:
        try:
             df = ak.fund_etf_hist_em(symbol=clean_symbol, period="daily", start_date=start_date, end_date=end_date, adjust=adjust)
             if not df.empty:
                print(f"Success: Found ETF data for {clean_symbol}")
                data_source_type = 'etf'
        except:
            pass

    # =========================================================
    # 3. [新增] 尝试作为 场外基金(公募) 获取 (如 017641)
    # =========================================================
    if df.empty:
        try:
            # 接口：开放式基金-历史数据-东方财富
            # 注意：该接口通常返回所有历史数据，不支持直接传 start/end 参数，需手动过滤
            df_fund = ak.fund_open_fund_net_value_em(symbol=clean_symbol)
            
            if not df_fund.empty:
                # 场外基金数据结构不同，需要手动构造成 K线 格式以便兼容回测系统
                # 使用 '累计净值' 作为 '收盘价'，因为它包含了分红收益，类似于复权价
                # 如果 '累计净值' 为空，降级使用 '单位净值'
                if '累计净值' in df_fund.columns:
                    price_col = '累计净值'
                else:
                    price_col = '单位净值'
                
                # 构造标准列名 (模拟 A股接口的中文列名，以便利用下方的统一重命名逻辑)
                df_fund['日期'] = df_fund['净值日期']
                df_fund['收盘'] = df_fund[price_col]
                df_fund['开盘'] = df_fund[price_col] # 基金一天只有一个价
                df_fund['最高'] = df_fund[price_col]
                df_fund['最低'] = df_fund[price_col]
                df_fund['成交量'] = 0                # 场外基金无成交量
                
                # 筛选日期范围
                df_fund['日期'] = pd.to_datetime(df_fund['日期']).dt.strftime('%Y-%m-%d')
                mask = (df_fund['日期'] >= pd.to_datetime(start_date).strftime('%Y-%m-%d')) & \
                       (df_fund['日期'] <= pd.to_datetime(end_date).strftime('%Y-%m-%d'))
                df = df_fund.loc[mask].copy()
                
                if not df.empty:
                    print(f"Success: Found OTC Fund data for {clean_symbol}")
                    data_source_type = 'otc_fund'
        except Exception as e:
            # print(f"Debug: OTC Fund fetch failed: {e}")
            pass

    # =========================================================
    # 4. 尝试作为 指数 获取
    # =========================================================
    if df.empty:
        try:
            df = ak.index_zh_a_hist(symbol=clean_symbol, period="daily", start_date=start_date, end_date=end_date)
            if not df.empty:
                print(f"Success: Found Index data for {clean_symbol}")
                data_source_type = 'index'
        except:
            pass

    # =========================================================
    # 数据校验与清洗
    # =========================================================
    if df.empty:
        print(f"Warning: No data found for {clean_symbol} (checked Stock, ETF, OTC Fund, and Index)")
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
         print(f"Error: Data for {clean_symbol} missing required columns.")
         return None

    df = df[available_cols]
    
    # 确保 date 列是 datetime 类型
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])

    # =========================================================
    # 5. 尝试获取筹码分布数据 (CYQ)
    # =========================================================
    # 仅针对 A 股股票有效
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
    
    # 只有股票才有筹码分布
    if data_source_type == 'stock':
        try:
            df_cyq = ak.stock_cyq_em(symbol=clean_symbol, adjust=adjust)
            if df_cyq is not None and not df_cyq.empty:
                # 统一日期列名
                cyq_date_col = next((col for col in ['date', '日期'] if col in df_cyq.columns), None)
                if cyq_date_col:
                    df_cyq.rename(columns={cyq_date_col: 'date'}, inplace=True)
                    df_cyq['date'] = pd.to_datetime(df_cyq['date'])
                    
                    df_cyq.rename(columns=cyq_map, inplace=True)
                    cols_to_keep = ['date'] + [c for c in cyq_map.values() if c in df_cyq.columns]
                    df_cyq = df_cyq[cols_to_keep]
                    
                    df = pd.merge(df, df_cyq, on='date', how='left')
        except Exception as e:
            print(f"Warning: Failed to fetch/merge CYQ data: {e}")

    # 填充缺失的 CYQ 列，保证 DataFrame 结构一致
    for col in cyq_map.values():
        if col not in df.columns:
            df[col] = pd.NA

    return df

def load_data(symbol, start_date='19900101', end_date=None, adjust='qfq', force_update=False):
    """
    加载数据。如果本地存在则读取，否则从网络获取并保存。
    支持缓存验证和自动更新。
    """
    if end_date is None:
        end_date = config.CACHE_END_DATE

    # 保证缓存文件名为纯数字 (e.g. 017641_qfq.csv)
    clean_symbol = str(symbol).strip().split('.')[0]
    filename = f"{clean_symbol}_{adjust}.csv"
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
                cutoff_time = datetime.time(15, 10) 

                needs_update = False

                # 1. 检查缓存是否过期
                if cached_last_date < request_end_date:
                    if request_end_date <= current_date:
                         # 盘前且缓存是昨天的，无需更新
                         is_pre_market = current_time < datetime.time(9, 15)
                         is_cache_yesterday = (current_date - cached_last_date).days == 1

                         if is_pre_market and is_cache_yesterday:
                             needs_update = False
                         else:
                             print(f"Cache expired (Last: {cached_last_date}). Updating...")
                             needs_update = True
                    elif cached_last_date < current_date:
                        print(f"Cache older than today. Updating...")
                        needs_update = True

                # 2. 盘中强制刷新检查 (如果在交易日且时间未到收盘，且请求日期是今天)
                # 修正：如果本地缓存已经包含今天，但现在是盘中，可能是旧数据，也需要刷新
                start_time = datetime.time(9, 15)
                if current_date == request_end_date and start_time < current_time < cutoff_time:
                     # 只有当请求的是股票/ETF时，盘中更新才有意义
                     # 场外基金通常晚上才更新净值，盘中更新没用，但为了通用性暂且保留
                    print(f"Intraday update triggered. Updating...")
                    needs_update = True

                # 3. 策略字段完整性检查
                if config.STRATEGY_TYPE == 'profit_ratio' and 'profit_ratio' not in df.columns:
                    print(f"Strategy requirement missing (profit_ratio). Updating...")
                    needs_update = True

                if not needs_update:
                    return df
            else:
                 needs_update = True

        except Exception as e:
            print(f"Error reading local file for {clean_symbol}: {e}. Will try to refetch.")
            needs_update = True
    else:
        needs_update = True
    
    if needs_update:
        # Fetch from network (Always use clean_symbol)
        fetch_start_date = '19900101'
        df = fetch_data_from_akshare(clean_symbol, start_date=fetch_start_date, end_date=end_date, adjust=adjust)
        
        if df is not None and not df.empty:
            print(f"Saving data for {clean_symbol} to {file_path}...")
            # 存盘前确保日期格式统一
            df.to_csv(file_path, index=False)
            return df
        else:
            return None
    
    return None