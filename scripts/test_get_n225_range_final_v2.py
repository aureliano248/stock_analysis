import akshare as ak

def get_n225_history_final_final(start_date, end_date):
    """
    使用 index_global_hist_em 获取日经225历史行情
    这是目前 akshare 最推荐的全球指数历史接口
    """
    # 之前报错 KeyError: 'N225' 是因为 symbol 映射表里可能没有 N225
    # 但是 akshare 的接口通常也支持直接传入东方财富的 secid
    # 我们可以通过 index_global_spot_em 找到 secid
    
    print(f"查询区间: {start_date} 到 {end_date}")
    
    # 1. 获取日经225的代码
    df_spot = ak.index_global_spot_em()
    n225_info = df_spot[df_spot['名称'] == '日经225']
    if n225_info.empty:
        print("未找到日经225")
        return None
    
    symbol_code = n225_info.iloc[0]['代码']
    print(f"找到代码: {symbol_code}")
    
    # 2. 尝试使用 stock_zh_index_daily_em 获取历史数据
    # 这个接口虽然名字带 zh，但实际上能获取全球指数的历史
    try:
        # 注意：这里需要传入完整代码，例如 100.N225
        # 如果 symbol_code 是 N225，可能需要前缀 100.
        full_code = f"100.{symbol_code}" if "." not in symbol_code else symbol_code
        print(f"请求接口 stock_zh_index_daily_em(symbol='{full_code}')")
        df_hist = ak.stock_zh_index_daily_em(symbol=full_code)
        
        if df_hist is not None and not df_hist.empty:
            # 格式化日期并过滤
            df_hist['date'] = df_hist['date'].astype(str)
            # 兼容处理输入日期格式
            s = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}" if len(start_date) == 8 else start_date
            e = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}" if len(end_date) == 8 else end_date
            
            mask = (df_hist['date'] >= s) & (df_hist['date'] <= e)
            return df_hist.loc[mask]
    except Exception as ex:
        print(f"接口调用异常: {ex}")
        
    return None

if __name__ == "__main__":
    start = "20230101"
    end = "20231231"
    df = get_n225_history_final_final(start, end)
    
    if df is not None and not df.empty:
        print(df.head())
        print(f"成功获取 {len(df)} 条数据")
    else:
        print("尝试失败，可能是接口变动或网络问题。")
        # 打印一下 index_global_spot_em 的结果以便调试
        print("当前 spot 数据:")
        print(ak.index_global_spot_em()[['代码', '名称']].head(20))
