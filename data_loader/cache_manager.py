
import os
import pandas as pd
import datetime

class CacheManager:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def get_file_path(self, symbol, suffix, adjust):
        if suffix == 'OF':
            filename = f"{symbol}.OF_{adjust}.csv"
        else:
            filename = f"{symbol}_{adjust}.csv"
        return os.path.join(self.data_dir, filename)

    def get_name_cache_path(self, symbol):
        return os.path.join(self.data_dir, f"{symbol}.name")

    def load_local_cache(self, file_path):
        if os.path.exists(file_path):
            try:
                return pd.read_csv(file_path, parse_dates=['date'])
            except Exception as e:
                print(f"Error reading cache {file_path}: {e}")
        return pd.DataFrame()

    def save_cache(self, df, file_path):
        if df is not None and not df.empty:
            df.to_csv(file_path, index=False)
            return True
        return False

    def check_needs_update(self, df, request_end_date, strategy_type=None):
        """
        判断是否需要更新。
        返回: (needs_update, fetch_start_date)
        """
        if df.empty:
            return True, '19900101'
        
        last_date = df['date'].iloc[-1].date()
        request_date = pd.to_datetime(request_end_date).date()
        current_dt = datetime.datetime.now()
        current_date = current_dt.date()
        current_time = current_dt.time()
        
        if request_date > current_date:
            request_date = current_date

        fetch_start = (df['date'].iloc[-1] - datetime.timedelta(days=7)).strftime('%Y%m%d')

        # 1. 盘前检查
        is_pre_market = current_time < datetime.time(9, 15)
        if is_pre_market and (current_date - last_date).days <= 1:
            return False, fetch_start

        # 2. 周末检查
        if current_date.weekday() >= 5:
            days_to_subtract = current_date.weekday() - 4
            friday_date = current_date - datetime.timedelta(days=days_to_subtract)
            if last_date >= friday_date:
                return False, fetch_start

        # 3. 日期落后检查
        if last_date < request_date:
            return True, fetch_start

        # 4. 盘中刷新 (9:15 - 15:10)
        cutoff_time = datetime.time(15, 10)
        if datetime.time(9, 15) < current_time < cutoff_time and last_date == current_date:
            # 这里原逻辑是即使最后一天是今天，盘中也可能需要刷新
            return True, fetch_start

        # 5. 策略字段完整性
        if strategy_type == 'profit_ratio' and 'profit_ratio' not in df.columns:
            return True, fetch_start

        return False, fetch_start

    def merge_data(self, old_df, new_df):
        if old_df.empty: return new_df
        if new_df.empty: return old_df
        
        combined = pd.concat([old_df, new_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=['date'], keep='last')
        return combined.sort_values('date').reset_index(drop=True)
