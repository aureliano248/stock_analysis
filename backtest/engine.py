"""
回测引擎：核心回测循环逻辑。

此模块不依赖 config，不依赖 data_loader，仅接收 DataFrame 和策略对象。
数据加载由调用方（main 入口文件）负责。
"""

import pandas as pd


def run_backtest(df, start_date, end_date, strategy, strategy_name="Custom Strategy"):
    """
    对给定数据和策略执行回测，返回逐日记录 DataFrame。

    :param df: 标的的完整历史数据 DataFrame（至少包含 'date', 'close' 列）
    :param start_date: 回测开始日期 (str 或 Timestamp)
    :param end_date: 回测结束日期 (str 或 Timestamp)
    :param strategy: 策略对象（实现 get_investment_amount 方法）
    :param strategy_name: 策略名称（用于日志输出）
    :return: DataFrame，包含逐日的 total_invested, final_value, profit, return_rate 等字段
             如果数据为空或无法回测，返回 None
    """
    if df is None or df.empty:
        print(f"No data provided for backtest ({strategy_name})")
        return None

    # 过滤时间区间
    try:
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
    except Exception as e:
        print(f"Error parsing dates: {e}")
        return None

    mask = (df['date'] >= start_dt) & (df['date'] <= end_dt)
    df_backtest = df.loc[mask].reset_index(drop=True)

    if df_backtest.empty:
        print(f"No data in range {start_date} to {end_date}")
        return None

    # 回测循环
    total_invested = 0.0
    total_shares = 0.0
    daily_records = []

    print(f"Starting backtest ({strategy_name}) from {start_date} to {end_date}...")

    for i in range(len(df_backtest)):
        current_row = df_backtest.iloc[i]
        current_date = current_row['date']
        close_price = current_row['close']

        # 传递历史数据子集
        history_subset = df_backtest.iloc[:i+1]

        amount = strategy.get_investment_amount(history_subset, current_date)

        if amount > 0:
            shares = amount / close_price
            total_shares += shares
            total_invested += amount

        # 记录每日状态
        current_value = total_shares * close_price
        profit = current_value - total_invested
        return_rate = (profit / total_invested * 100) if total_invested > 0 else 0.0

        record = {
            'date': current_date,
            'total_invested': total_invested,
            'final_value': current_value,
            'profit': profit,
            'return_rate': return_rate
        }

        # 保存策略相关列 (如有)
        for col in ['profit_ratio', 'avg_cost']:
            if col in current_row:
                record[col] = current_row[col]

        daily_records.append(record)

    return pd.DataFrame(daily_records)
