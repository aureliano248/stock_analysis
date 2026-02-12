
import akshare as ak
import pandas as pd

class DataProvider:
    def __init__(self):
        self.column_map = {
            "日期": "date", 
            "开盘": "open", 
            "收盘": "close",
            "最高": "high", 
            "最低": "low", 
            "成交量": "volume",
            "成交额": "amount"
        }

    def _standardize(self, df):
        if df is None or df.empty:
            return pd.DataFrame()
        
        # 统一重命名逻辑：先检查是否需要从中文重命名
        df = df.rename(columns=self.column_map)
        
        # 定义标准列名
        needed_cols = ["date", "open", "close", "high", "low", "volume"]
        
        # 处理可能已经存在的英文列名 (如 Sina 接口返回的)
        available_cols = [c for c in needed_cols if c in df.columns]
        
        df = df[available_cols].copy()
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        return df

    def fetch_index(self, symbol, start, end):
        # 探测顺序：原始代码 -> sh/sz 前缀补全
        symbols_to_try = [symbol]
        if len(symbol) == 6 and symbol.isdigit():
            if symbol.startswith(('6', '000')):
                symbols_to_try.append("sh" + symbol)
            else:
                symbols_to_try.append("sz" + symbol)
        
        # 1. 尝试 EM 接口
        for s in symbols_to_try:
            try:
                df = ak.index_zh_a_hist(symbol=s, period="daily", start_date=start, end_date=end)
                if df is not None and not df.empty:
                    return self._standardize(df), 'index'
            except:
                continue
        
        # 2. 尝试 Sina 接口 (作为备选，应对网络/代理问题)
        for s in symbols_to_try:
            if not s.startswith(('sh', 'sz')): continue # Sina 必须有前缀
            try:
                df = ak.stock_zh_index_daily(symbol=s)
                if df is not None and not df.empty:
                    df['date'] = pd.to_datetime(df['date'])
                    # 过滤日期
                    start_dt = pd.to_datetime(start)
                    end_dt = pd.to_datetime(end)
                    df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]
                    return self._standardize(df), 'index'
            except:
                continue

        return pd.DataFrame(), None

    def fetch_stock(self, symbol, start, end, adjust):
        # 1. 尝试 EM 接口
        try:
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start, end_date=end, adjust=adjust)
            if df is not None and not df.empty:
                return self._standardize(df), 'stock'
        except:
            pass
        
        # 2. 尝试 Sina 接口
        try:
            full_symbol = ("sh" + symbol) if symbol.startswith(('6', '000', '688')) else ("sz" + symbol)
            df = ak.stock_zh_a_daily(symbol=full_symbol, start_date=start, end_date=end, adjust=adjust)
            if df is not None and not df.empty:
                return self._standardize(df), 'stock'
        except:
            pass
            
        return pd.DataFrame(), None

    def fetch_etf(self, symbol, start, end, adjust):
        # 1. 优先尝试 Sina 接口 (根据用户规则补全前缀，稳定性更高)
        try:
            exchange = 'sh' if symbol.startswith('5') else 'sz'
            full_symbol = exchange + symbol
            df = ak.fund_etf_hist_sina(symbol=full_symbol)
            if df is not None and not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                # 过滤日期
                start_dt = pd.to_datetime(start)
                end_dt = pd.to_datetime(end)
                df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]
                return self._standardize(df), 'etf'
            
        except:
            pass

        # 2. 备选尝试 EM 接口
        try:
            df = ak.fund_etf_hist_em(symbol=symbol, period="daily", start_date=start, end_date=end, adjust=adjust)
            if df is not None and not df.empty:
                return self._standardize(df), 'etf'
        except:
            pass
            
        return pd.DataFrame(), None

    def fetch_otc_fund(self, symbol, start, end):
        try:
            df = ak.fund_open_fund_info_em(symbol=symbol, indicator="单位净值走势", period="成立来")
            if df is None or df.empty:
                return pd.DataFrame(), None
            
            # 场外基金模拟 OHLC
            df['日期'] = df['净值日期']
            df['收盘'] = df['单位净值']
            df['开盘'] = df['单位净值']
            df['最高'] = df['单位净值']
            df['最低'] = df['单位净值']
            df['成交量'] = 0
            
            # 日期过滤
            df['日期'] = pd.to_datetime(df['日期'])
            start_dt = pd.to_datetime(start)
            end_dt = pd.to_datetime(end)
            df = df[(df['日期'] >= start_dt) & (df['日期'] <= end_dt)]
            
            return self._standardize(df), 'otc_fund'
        except Exception as e:
            return pd.DataFrame(), None

    def fetch_cyq(self, symbol, adjust):
        """获取筹码分布数据"""
        cyq_map = {
            '获利比例': 'profit_ratio', '平均成本': 'avg_cost',
            '90成本-低': 'cost90_low', '90成本-高': 'cost90_high',
            '90集中度': 'concentration90', '70成本-低': 'cost70_low',
            '70成本-高': 'cost70_high', '70集中度': 'concentration70'
        }
        try:
            df_cyq = ak.stock_cyq_em(symbol=symbol, adjust=adjust)
            if df_cyq is not None and not df_cyq.empty:
                date_col = next((col for col in ['date', '日期'] if col in df_cyq.columns), None)
                if date_col:
                    df_cyq = df_cyq.rename(columns={date_col: 'date'})
                    df_cyq['date'] = pd.to_datetime(df_cyq['date'])
                    df_cyq = df_cyq.rename(columns=cyq_map)
                    cols = ['date'] + [c for c in cyq_map.values() if c in df_cyq.columns]
                    return df_cyq[cols]
        except:
            pass
        return pd.DataFrame()
