import os
import pandas as pd
import akshare as ak
import config
import datetime

def fetch_data_from_akshare(symbol, start_date='19900101', end_date=config.CACHE_END_DATE, adjust='qfq'):
    """
    从 AkShare 获取数据。
    
    :param symbol: 代码, e.g., '000001', '510300', '017641', '000300.OF'
    :param adjust: 复权类型, 'qfq' (default), 'hfq', or '' (None)
    :return: DataFrame
    
    查询逻辑:
    1. 如果有 .OF 后缀，删除后缀后只查询场外基金
    2. 如果是其他后缀，报错提醒
    3. 如果没有后缀（纯数字），查询顺序：指数 -> 股票 -> 场内基金 -> 场外基金
    """
    symbol_str = str(symbol).strip()
    
    # 检查是否有后缀
    if '.' in symbol_str:
        parts = symbol_str.split('.')
        clean_symbol = parts[0]
        suffix = parts[1].upper()
        
        # 如果是 .OF 后缀，只查询场外基金
        if suffix == 'OF':
            print(f"Fetching OTC Fund data for {clean_symbol} from AkShare...")
            df = pd.DataFrame()
            try:
                # 使用 fund_open_fund_info_em 接口获取场外基金净值数据
                # 注意：akshare 1.18.14版本中 fund_open_fund_net_value_em 接口已不存在
                df_fund = ak.fund_open_fund_info_em(symbol=clean_symbol, indicator="单位净值走势", period="成立来")
                
                if not df_fund.empty:
                    # 场外基金数据结构: ['净值日期', '单位净值', '日增长率']
                    # 使用 '单位净值' 作为 '收盘价'
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
                    else:
                        print(f"Warning: No OTC Fund data found for {clean_symbol}")
                        return None
                else:
                    print(f"Warning: No OTC Fund data found for {clean_symbol}")
                    return None
            except Exception as e:
                print(f"Error fetching OTC Fund data for {clean_symbol}: {e}")
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
            
            return df
        else:
            # 其他后缀报错
            raise ValueError(f"不支持的代码后缀: {suffix}. 目前只支持 .OF 后缀（场外基金）")
    
    # 没有后缀，纯数字代码
    clean_symbol = symbol_str
    
    print(f"Fetching data for {clean_symbol} from AkShare (adjust={adjust})...")
    df = pd.DataFrame()
    data_source_type = None
    
    # =========================================================
    # 1. 尝试作为 指数 获取
    # =========================================================
    try:
        df = ak.index_zh_a_hist(symbol=clean_symbol, period="daily", start_date=start_date, end_date=end_date)
        if not df.empty:
            print(f"Success: Found Index data for {clean_symbol}")
            data_source_type = 'index'
    except:
        pass
    
    # =========================================================
    # 2. 尝试作为 A 股股票获取
    # =========================================================
    if df.empty:
        try:
            df = ak.stock_zh_a_hist(symbol=clean_symbol, period="daily", start_date=start_date, end_date=end_date, adjust=adjust)
            if not df.empty:
                print(f"Success: Found Stock data for {clean_symbol}")
                data_source_type = 'stock'
        except:
            pass

    # =========================================================
    # 3. 尝试作为 场内ETF 获取 (以 51/15 开头通常为此类)
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
    # 4. 尝试作为 场外基金(公募) 获取 (如 017641)
    # =========================================================
    if df.empty:
        try:
            # 接口：开放式基金-历史数据-东方财富
            # 注意：akshare 1.18.14版本中 fund_open_fund_net_value_em 接口已不存在
            # 使用 fund_open_fund_info_em 接口替代
            # 该接口返回所有历史数据，不支持直接传 start/end 参数，需手动过滤
            df_fund = ak.fund_open_fund_info_em(symbol=clean_symbol, indicator="单位净值走势", period="成立来")
            
            if not df_fund.empty:
                # 场外基金数据结构: ['净值日期', '单位净值', '日增长率']
                # 使用 '单位净值' 作为 '收盘价'
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

    # 缓存文件名保留 .OF 后缀（如果有），其他后缀移除
    symbol_str = str(symbol).strip()
    if '.' in symbol_str:
        parts = symbol_str.split('.')
        clean_symbol = parts[0]
        suffix = parts[1].upper()
        if suffix == 'OF':
            # 保留 .OF 后缀
            filename = f"{clean_symbol}.OF_{adjust}.csv"
        else:
            # 其他后缀移除
            filename = f"{clean_symbol}_{adjust}.csv"
    else:
        clean_symbol = symbol_str
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
                
                # 计算增量更新的开始日期（缓存最后一行日期往前一周）
                cached_last_datetime = df['date'].iloc[-1]
                fetch_start_date = (cached_last_datetime - datetime.timedelta(days=7)).strftime('%Y%m%d')

                # 1. 检查缓存是否过期
                if cached_last_date < request_end_date:
                    # 盘前检查：如果现在是盘前（9:15之前），且缓存是昨天的，则无需更新
                    is_pre_market = current_time < datetime.time(9, 15)
                    is_cache_yesterday = (current_date - cached_last_date).days == 1
                    
                    if is_pre_market and is_cache_yesterday:
                        print(f"Pre-market: Cache is from yesterday ({cached_last_date}), no update needed.")
                        needs_update = False
                    elif cached_last_date < current_date:
                        print(f"Cache older than today (Last: {cached_last_date}). Updating...")
                        needs_update = True
                    else:
                        print(f"Cache expired (Last: {cached_last_date}, Request: {request_end_date}). Updating...")
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
        fetch_start_date = '19900101'  # 首次获取，从1990年开始
    
    if needs_update:
        # Fetch from network (Always use clean_symbol)
        df_new = fetch_data_from_akshare(clean_symbol, start_date=fetch_start_date, end_date=end_date, adjust=adjust)
        
        if df_new is not None and not df_new.empty:
            # 如果是增量更新（fetch_start_date 不是 '19900101'），需要合并旧数据
            if fetch_start_date != '19900101' and os.path.exists(file_path):
                # 读取旧缓存数据
                df_old = pd.read_csv(file_path, parse_dates=['date'])
                # 合并新旧数据并去重（按日期去重，保留新数据）
                df = pd.concat([df_old, df_new], ignore_index=True)
                df = df.drop_duplicates(subset=['date'], keep='last')
                df = df.sort_values('date').reset_index(drop=True)
                print(f"Merged data: {len(df_old)} old + {len(df_new)} new = {len(df)} total rows")
            else:
                df = df_new
            
            print(f"Saving data for {clean_symbol} to {file_path}...")
            # 存盘前确保日期格式统一
            df.to_csv(file_path, index=False)
            return df
        else:
            return None
    
    return None


def get_stock_name(symbol):
    """
    获取股票/ETF/基金/指数的中文名称。
    
    :param symbol: 代码, e.g., '000001', '510300', '017641', '000300.OF'
    :return: 中文名称，如果获取失败则返回 None
    
    查询逻辑:
    1. 如果有 .OF 后缀，删除后缀后只查询场外基金
    2. 如果是其他后缀，报错提醒
    3. 如果没有后缀（纯数字），查询顺序：指数 -> 股票 -> 场内基金 -> 场外基金
    """
    symbol_str = str(symbol).strip()
    
    # 检查是否有后缀
    if '.' in symbol_str:
        parts = symbol_str.split('.')
        clean_symbol = parts[0]
        suffix = parts[1].upper()
        
        # 如果是 .OF 后缀，只查询场外基金
        if suffix == 'OF':
            try:
                # 使用 fund_open_fund_daily_em 获取所有开放式基金列表
                fund_list = ak.fund_open_fund_daily_em()
                if fund_list is not None and not fund_list.empty:
                    match = fund_list[fund_list['基金代码'] == clean_symbol]
                    if not match.empty:
                        return match['基金简称'].iloc[0]
            except:
                pass
            return None
        else:
            # 其他后缀报错
            raise ValueError(f"不支持的代码后缀: {suffix}. 目前只支持 .OF 后缀（场外基金）")
    
    # 没有后缀，纯数字代码，按顺序查询：指数 -> 股票 -> 场内基金 -> 场外基金
    clean_symbol = symbol_str
    
    # 1. 尝试作为 指数 获取名称
    try:
        index_list = ak.index_stock_info()
        if index_list is not None and not index_list.empty:
            match = index_list[index_list['index_code'] == clean_symbol]
            if not match.empty:
                return match['index_name'].iloc[0]
    except:
        pass
    
    # 2. 尝试作为 A 股股票获取名称
    try:
        info = ak.stock_individual_info_em(symbol=clean_symbol)
        if info is not None and not info.empty:
            # 名称通常在 'item' 为 '股票简称' 的行中
            name_row = info[info['item'] == '股票简称']
            if not name_row.empty:
                return name_row['value'].iloc[0]
    except:
        pass
    
    # 3. 尝试作为 场内ETF 获取名称
    try:
        etf_list = ak.fund_etf_spot_em()
        if etf_list is not None and not etf_list.empty:
            match = etf_list[etf_list['代码'] == clean_symbol]
            if not match.empty:
                return match['名称'].iloc[0]
    except:
        pass
    
    # 4. 尝试作为 场外基金 获取名称
    try:
        # 使用 fund_open_fund_daily_em 获取所有开放式基金列表
        fund_list = ak.fund_open_fund_daily_em()
        if fund_list is not None and not fund_list.empty:
            match = fund_list[fund_list['基金代码'] == clean_symbol]
            if not match.empty:
                return match['基金简称'].iloc[0]
    except:
        pass
    
    return None