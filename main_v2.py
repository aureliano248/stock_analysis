import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import data_loader
import strategies
import config
import sys
import os

def run_backtest_v2(symbol, start_date, end_date, strategy, strategy_name="Custom Strategy"):
    # 1. 加载数据
    df = data_loader.load_data(symbol)
    
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
    
    # 记录实际回测开始的日期
    actual_start_date = df_backtest.iloc[0]['date']
    
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
    
    strategy = None
    strategy_name = ""
    
    if strategy_type == 'fixed':
        params = config.FIXED_STRATEGY_PARAMS
        strategy = strategies.FixedInvestment(amount=params['amount'], freq=params['freq'])
        strategy_name = f"Fixed_{params['freq']}_{params['amount']}"
        
    elif strategy_type == 'interval':
        params = config.INTERVAL_STRATEGY_PARAMS
        strategy = strategies.IntervalFixedInvestment(intervals=params)
        strategy_name = "Interval_Custom"
        
    elif strategy_type == 'profit_ratio':
        params = config.PROFIT_RATIO_STRATEGY_PARAMS
        strategy = strategies.ProfitRatioStrategy(base_amount=params['base_amount'], thresholds=params['thresholds'])
        strategy_name = "Profit_Ratio_Dynamic"

    elif strategy_type == 'benchmark_drop':
        params = config.BENCHMARK_DROP_STRATEGY_PARAMS
        strategy = strategies.BenchmarkDropStrategy(
            base_amount=params['base_amount'],
            freq=params['freq'],
            scale_factor=params['scale_factor']
        )
        strategy_name = f"BenchmarkDrop_{params['freq']}_x{params['scale_factor']}"

    elif strategy_type == 'dynamic_benchmark':
        params = config.DYNAMIC_BENCHMARK_STRATEGY_PARAMS
        strategy = strategies.DynamicBenchmarkDropStrategy(
            base_amount=params['base_amount'],
            freq=params['freq'],
            benchmark_type=params['benchmark_type'],
            thresholds=params['thresholds']
        )
        strategy_name = f"DynamicBenchmark_{params['benchmark_type']}"

    elif strategy_type == 'quadratic_ma':
        params = config.QUADRATIC_MA_STRATEGY_PARAMS
        strategy = strategies.QuadraticMAStrategy(
            base_amount=params['base_amount'],
            freq=params['freq'],
            k_factor=params['k_factor'],
            max_multiplier=params['max_multiplier']
        )
        strategy_name = f"QuadraticMA_K{params['k_factor']}"

    else:
        print(f"Error: Unknown strategy type '{strategy_type}' in config.py")
        sys.exit(1)
        
    # Run the backtest v2
    df_results = run_backtest_v2(symbol, start_date, end_date, strategy, strategy_name)
    
    if df_results is None or df_results.empty:
        print("Backtest failed or returned no data.")
        return

    # Plotting
    # 设置 PDF 后端，无需 GUI
    plt.switch_backend('Agg') 
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 绘制收益率曲线
    ax.plot(df_results['date'], df_results['return_rate'], label='Return Rate (%)', color='blue', linewidth=1.5)
    
    ax.set_title(f"Backtest Return Rate: {symbol} ({strategy_name})\n{start_date} to {end_date}")
    ax.set_xlabel("Date (Year-Month)")
    ax.set_ylabel("Return Rate (%)")
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend(loc='upper left')
    
    # 设置 X 轴格式为 年-月
    # 使用 AutoDateLocator 自动选择合适的间隔，但强制格式为 YYYY-MM
    locator = mdates.AutoDateLocator()
    formatter = mdates.DateFormatter('%Y-%m')
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    
    # 旋转日期标签以防重叠
    fig.autofmt_xdate()

    # 生成文件名
    filename = f"result_{symbol}_{strategy_name}.pdf"
    
    # 确保存储目录存在
    figures_dir = os.path.join(os.getcwd(), 'figures')
    os.makedirs(figures_dir, exist_ok=True)
    
    filepath = os.path.join(figures_dir, filename)
    
    # 保存为 PDF
    try:
        plt.savefig(filepath, format='pdf', bbox_inches='tight')
        print(f"\nSuccess! Plot saved to: {filepath}")
    except Exception as e:
        print(f"\nError saving plot: {e}")

if __name__ == "__main__":
    main()
