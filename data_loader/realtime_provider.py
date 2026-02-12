
import akshare as ak
import pandas as pd


class RealtimeProvider:
    """获取标的的实时行情数据（当前最新报价）"""

    def get_quote(self, symbol, asset_type=None):
        """
        获取给定标的的实时行情。

        :param symbol: 标的代码（纯数字，如 "513180", "600519", "000300"）
        :param asset_type: 资产类型提示，可选值: 'index', 'stock', 'etf', 'otc_fund', None (自动探测)
        :return: dict，包含标准化字段:
                 {
                     'symbol': str,
                     'name': str,
                     'price': float,       # 最新价
                     'change': float,       # 涨跌额
                     'change_pct': float,   # 涨跌幅 (%)
                     'open': float,
                     'high': float,
                     'low': float,
                     'pre_close': float,    # 昨收
                     'volume': float,       # 成交量
                     'amount': float,       # 成交额
                     'timestamp': str,      # 数据时间
                     'asset_type': str,     # 资产类型
                 }
                 获取失败返回 None
        """
        clean_symbol = str(symbol).strip()
        if '.' in clean_symbol:
            clean_symbol = clean_symbol.split('.')[0]

        # 如果指定了类型，直接调用对应方法
        if asset_type:
            dispatch = {
                'stock': self._quote_stock,
                'etf': self._quote_etf,
                'index': self._quote_index,
                'otc_fund': self._quote_otc_fund,
            }
            func = dispatch.get(asset_type)
            if func:
                return func(clean_symbol)

        # 自动探测：按优先级尝试
        for func in [self._quote_index, self._quote_stock, self._quote_etf, self._quote_otc_fund]:
            result = func(clean_symbol)
            if result is not None:
                return result

        return None

    def _quote_stock(self, symbol):
        """获取 A 股股票实时行情"""
        try:
            df = ak.stock_zh_a_spot_em()
            if df is None or df.empty:
                return None
            row = df[df['代码'] == symbol]
            if row.empty:
                return None
            row = row.iloc[0]
            return self._build_quote(row, symbol, 'stock', name_col='名称',
                                     price_col='最新价', change_col='涨跌额',
                                     pct_col='涨跌幅', open_col='今开',
                                     high_col='最高', low_col='最低',
                                     pre_close_col='昨收', volume_col='成交量',
                                     amount_col='成交额')
        except Exception:
            return None

    def _quote_etf(self, symbol):
        """获取 ETF 实时行情"""
        try:
            df = ak.fund_etf_spot_em()
            if df is None or df.empty:
                return None
            row = df[df['代码'] == symbol]
            if row.empty:
                return None
            row = row.iloc[0]
            return self._build_quote(row, symbol, 'etf', name_col='名称',
                                     price_col='最新价', change_col='涨跌额',
                                     pct_col='涨跌幅', open_col='今开',
                                     high_col='最高', low_col='最低',
                                     pre_close_col='昨收', volume_col='成交量',
                                     amount_col='成交额')
        except Exception:
            return None

    def _quote_index(self, symbol):
        """获取指数实时行情"""
        try:
            df = ak.stock_zh_index_spot_em()
            if df is None or df.empty:
                return None
            row = df[df['代码'] == symbol]
            if row.empty:
                return None
            row = row.iloc[0]
            return self._build_quote(row, symbol, 'index', name_col='名称',
                                     price_col='最新价', change_col='涨跌额',
                                     pct_col='涨跌幅', open_col='今开',
                                     high_col='最高', low_col='最低',
                                     pre_close_col='昨收', volume_col='成交量',
                                     amount_col='成交额')
        except Exception:
            return None

    def _quote_otc_fund(self, symbol):
        """获取场外基金实时净值"""
        try:
            df = ak.fund_open_fund_daily_em()
            if df is None or df.empty:
                return None
            row = df[df['基金代码'] == symbol]
            if row.empty:
                return None
            row = row.iloc[0]
            nav = self._safe_float(row.get('单位净值'))
            prev_nav = self._safe_float(row.get('累计净值'))  # 场外基金可能无昨收
            change = None
            change_pct = self._safe_float(row.get('日增长率'))

            return {
                'symbol': symbol,
                'name': str(row.get('基金简称', '')),
                'price': nav,
                'change': change,
                'change_pct': change_pct,
                'open': nav,
                'high': nav,
                'low': nav,
                'pre_close': prev_nav,
                'volume': None,
                'amount': None,
                'timestamp': str(row.get('净值日期', '')),
                'asset_type': 'otc_fund',
            }
        except Exception:
            return None

    @staticmethod
    def _safe_float(value):
        """安全转换为 float，失败返回 None"""
        if value is None:
            return None
        try:
            result = float(value)
            if pd.isna(result):
                return None
            return result
        except (ValueError, TypeError):
            return None

    def _build_quote(self, row, symbol, asset_type, *, name_col, price_col,
                     change_col, pct_col, open_col, high_col, low_col,
                     pre_close_col, volume_col, amount_col):
        """从 AkShare 返回的行构建标准化 quote 字典"""
        return {
            'symbol': symbol,
            'name': str(row.get(name_col, '')),
            'price': self._safe_float(row.get(price_col)),
            'change': self._safe_float(row.get(change_col)),
            'change_pct': self._safe_float(row.get(pct_col)),
            'open': self._safe_float(row.get(open_col)),
            'high': self._safe_float(row.get(high_col)),
            'low': self._safe_float(row.get(low_col)),
            'pre_close': self._safe_float(row.get(pre_close_col)),
            'volume': self._safe_float(row.get(volume_col)),
            'amount': self._safe_float(row.get(amount_col)),
            'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            'asset_type': asset_type,
        }
