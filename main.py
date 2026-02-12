import pandas as pd
import data_loader
import config
import os
import sys
from strategies import create_strategy, get_strategy_params


def run_backtest(symbol, start_date, end_date, strategy, strategy_name="Custom Strategy", df=None):
    """
    运行回测 (v1 版本，文本输出)
    :param symbol: 标的代码
    :param start_date: 开始日期 YYYY-MM-DD
    :param end_date: 结束日期 YYYY-MM-DD
    :param strategy: 策略对象
    :param strategy_name: 策略名称 (用于文件命名)
    :param df: 可选，直接传入 DataFrame，用于测试
    """
    # 1. 加载数据
    if df is None:
        result = data_loader.load_data(symbol, data_dir=config.DATA_DIR,
                                        end_date=config.CACHE_END_DATE,
                                        strategy_type=config.STRATEGY_TYPE)
        if result is not None:
            df, stock_name = result
        else:
            df = None

    if df is None:
        print(f"Failed to load data for {symbol}")
        return None

    # 2. 过滤时间区间
    try:
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
    except Exception as e:
        print(f"Error parsing dates: {e}")
        return None

    mask = (df['date'] >= start_dt) & (df['date'] <= end_dt)
    df_backtest = df.loc[mask].reset_index(drop=True)

    if df_backtest.empty:
        print(f"No data in range {start_date} to {end_date} for {symbol}")
        return None

    # 3. 回测循环
    total_invested = 0.0
    total_shares = 0.0
    logs = []

    print(f"Starting backtest for {symbol} ({strategy_name}) from {start_date} to {end_date}...")

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
            log_item = {
                'date': current_date,
                'price': close_price,
                'invest_amount': amount,
                'shares_bought': shares,
                'total_shares': total_shares,
                'total_invested': total_invested
            }

            for col in ['profit_ratio', 'avg_cost', 'cost90_low', 'cost90_high', 'concentration90']:
                if col in current_row:
                    log_item[col] = current_row[col]

            logs.append(log_item)

    # 4. 结算
    if total_shares == 0:
        print("No investment made during this period.")
        return {
            'total_invested': 0,
            'final_value': 0,
            'profit': 0,
            'return_rate': 0
        }

    final_price = df_backtest.iloc[-1]['close']
    final_value = total_shares * final_price
    profit = final_value - total_invested
    return_rate = (profit / total_invested) * 100

    days = (df_backtest.iloc[-1]['date'] - df_backtest.iloc[0]['date']).days
    months = days / 30.0

    annualized_return = 0.0
    if days > 0:
        years = days / 365.0
        if total_invested > 0 and final_value > 0:
            try:
                annualized_return = ((final_value / total_invested) ** (1 / years) - 1) * 100
            except Exception:
                annualized_return = 0.0

    # 5. 输出结果
    result_str = f"""
==================================================
Backtest Result for {symbol}
Strategy: {strategy_name}
--------------------------------------------------
Start Date: {df_backtest.iloc[0]['date'].strftime('%Y-%m-%d')}
End Date:   {df_backtest.iloc[-1]['date'].strftime('%Y-%m-%d')}
Duration:   {months:.1f} months
Start Price: {df_backtest.iloc[0]['close']:.2f}
End Price:   {final_price:.2f}
--------------------------------------------------
Total Invested: {total_invested:.2f}
Final Value:    {final_value:.2f}
Profit:         {profit:.2f}
Return Rate:    {return_rate:.2f}%
Annualized:     {annualized_return:.2f}% (CAGR)
==================================================
"""
    print(result_str)

    # 保存结果到文件
    filename = f"{symbol}_{strategy_name}_{start_date}_{end_date}.txt".replace(' ', '_').replace(':', '')
    filepath = os.path.join(config.RESULTS_DIR, filename)
    with open(filepath, 'w') as f:
        f.write(result_str)

    print(f"Result saved to {filepath}")

    # 保存详细交易日志
    log_df = pd.DataFrame(logs)
    if not log_df.empty:
        log_path = os.path.join(config.RESULTS_DIR, filename.replace('.txt', '_details.csv'))
        log_df.to_csv(log_path, index=False)
        print(f"Details saved to {log_path}")

    return {
        'total_invested': total_invested,
        'final_value': final_value,
        'profit': profit,
        'return_rate': return_rate,
        'annualized_return': annualized_return
    }


def main():
    print("Loading configuration from config.py...")

    symbol = config.SYMBOL
    start_date = config.START_DATE
    end_date = config.END_DATE
    strategy_type = config.STRATEGY_TYPE

    params = get_strategy_params(strategy_type, config)
    strategy, strategy_name = create_strategy(strategy_type, params)

    if strategy is None:
        print(f"Error: Unknown strategy type '{strategy_type}' in config.py")
        sys.exit(1)

    run_backtest(symbol, start_date, end_date, strategy, strategy_name)

if __name__ == "__main__":
    main()
