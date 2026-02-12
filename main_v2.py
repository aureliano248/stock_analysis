import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import data_loader
import config
import sys
import os
from strategies import create_strategy, get_strategy_params


def run_backtest_v2(symbol, start_date, end_date, strategy, strategy_name="Custom Strategy", df=None):
    """
    运行回测 (v2 版本，返回逐日记录 DataFrame)
    :param symbol: 标的代码
    :param start_date: 开始日期 YYYY-MM-DD
    :param end_date: 结束日期 YYYY-MM-DD
    :param strategy: 策略对象
    :param strategy_name: 策略名称 (用于文件命名)
    :param df: 可选，直接传入 DataFrame，避免重复加载
    """
    # 1. 加载数据
    if df is None:
        result = data_loader.load_data(symbol, data_dir=getattr(config, 'DATA_DIR', None),
                                        end_date=getattr(config, 'CACHE_END_DATE', None),
                                        strategy_type=getattr(config, 'STRATEGY_TYPE', None))
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
    daily_records = []

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

        # 保存策略相关列
        for col in ['profit_ratio', 'avg_cost']:
            if col in current_row:
                record[col] = current_row[col]

        daily_records.append(record)

    return pd.DataFrame(daily_records)


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

    # Run the backtest v2
    df_results = run_backtest_v2(symbol, start_date, end_date, strategy, strategy_name)

    if df_results is None or df_results.empty:
        print("Backtest failed or returned no data.")
        return

    # Plotting
    plt.switch_backend('Agg')

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(df_results['date'], df_results['return_rate'], label='Return Rate (%)', color='blue', linewidth=1.5)

    ax.set_title(f"Backtest Return Rate: {symbol} ({strategy_name})\n{start_date} to {end_date}")
    ax.set_xlabel("Date (Year-Month)")
    ax.set_ylabel("Return Rate (%)")
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend(loc='upper left')

    locator = mdates.AutoDateLocator()
    formatter = mdates.DateFormatter('%Y-%m')
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)

    fig.autofmt_xdate()

    # 生成文件名
    filename = f"result_{symbol}_{strategy_name}.pdf"

    figures_dir = os.path.join(os.getcwd(), 'figures')
    os.makedirs(figures_dir, exist_ok=True)

    filepath = os.path.join(figures_dir, filename)

    try:
        plt.savefig(filepath, format='pdf', bbox_inches='tight')
        print(f"\nSuccess! Plot saved to: {filepath}")
    except Exception as e:
        print(f"\nError saving plot: {e}")

if __name__ == "__main__":
    main()
