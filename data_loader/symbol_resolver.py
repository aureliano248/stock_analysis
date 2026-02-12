
import akshare as ak
import os
import json

class SymbolResolver:
    @staticmethod
    def resolve(symbol):
        """
        解析代码类型。
        返回: (clean_symbol, suffix, asset_type)
        """
        symbol_str = str(symbol).strip()
        if '.' in symbol_str:
            parts = symbol_str.split('.')
            clean_symbol = parts[0]
            suffix = parts[1].upper()
            if suffix == 'OF':
                return clean_symbol, suffix, 'otc_fund'
            else:
                raise ValueError(f"不支持的代码后缀: {suffix}")
        
        return symbol_str, None, None # 类型由 Provider 探测确定

    @staticmethod
    def get_stock_name(symbol, data_dir):
        """获取资产中文名称"""
        symbol_str = str(symbol).strip()
        
        # 0. 优先从本地映射文件读取
        name_cache_file = os.path.join(data_dir, 'stock_names.json')
        if os.path.exists(name_cache_file):
            try:
                with open(name_cache_file, 'r', encoding='utf-8') as f:
                    name_map = json.load(f)
                    if symbol_str in name_map:
                        return name_map[symbol_str]
            except:
                pass
        
        # 检查是否有后缀
        if '.' in symbol_str:
            parts = symbol_str.split('.')
            clean_symbol = parts[0]
            suffix = parts[1].upper()
            if suffix == 'OF':
                try:
                    fund_list = ak.fund_open_fund_daily_em()
                    if fund_list is not None and not fund_list.empty:
                        match = fund_list[fund_list['基金代码'] == clean_symbol]
                        if not match.empty:
                            return match['基金简称'].iloc[0]
                except: pass
                return None
            else:
                raise ValueError(f"不支持的代码后缀: {suffix}")

        clean_symbol = symbol_str
        # 1. 指数
        try:
            index_list = ak.index_stock_info()
            if index_list is not None and not index_list.empty:
                match = index_list[index_list['index_code'] == clean_symbol]
                if not match.empty: return match['index_name'].iloc[0]
        except: pass

        # 2. 股票
        try:
            info = ak.stock_individual_info_em(symbol=clean_symbol)
            if info is not None and not info.empty:
                name_row = info[info['item'] == '股票简称']
                if not name_row.empty: return name_row['value'].iloc[0]
        except: pass

        # 3. ETF
        try:
            etf_list = ak.fund_etf_spot_em()
            if etf_list is not None and not etf_list.empty:
                match = etf_list[etf_list['代码'] == clean_symbol]
                if not match.empty: return match['名称'].iloc[0]
        except: pass

        # 4. 场外基金
        try:
            fund_list = ak.fund_open_fund_daily_em()
            if fund_list is not None and not fund_list.empty:
                match = fund_list[fund_list['基金代码'] == clean_symbol]
                if not match.empty: return match['基金简称'].iloc[0]
        except: pass

        return None
