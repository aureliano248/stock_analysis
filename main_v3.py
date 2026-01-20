import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import data_loader
import strategies
import config
import sys
import os
from main_v2 import run_backtest_v2

def create_strategy(strategy_type):
    """
    根据策略类型创建策略实例
    """
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
        print(f"Warning: Unknown strategy type '{strategy_type}' in DRAW_STRATEGY_LIST")
        return None, None
        
    return strategy, strategy_name

def main():
    print("Loading configuration from config.py...")
    
    symbol = config.SYMBOL
    start_date = config.START_DATE
    end_date = config.END_DATE
    draw_list = config.DRAW_STRATEGY_LIST
    
    if not draw_list:
        print("Error: DRAW_STRATEGY_LIST is empty in config.py")
        return

    print(f"Comparing strategies for {symbol}: {draw_list}")
    
    results = {}
    
    # 1. Run Backtests
    for strat_type in draw_list:
        strategy, strategy_name = create_strategy(strat_type)
        if strategy is None:
            continue
            
        print(f"\n--- Running Strategy: {strategy_name} ---")
        df_result = run_backtest_v2(symbol, start_date, end_date, strategy, strategy_name)
        
        if df_result is not None and not df_result.empty:
            results[strategy_name] = df_result
        else:
            print(f"Strategy {strategy_name} returned no results.")

    if not results:
        print("No results to plot.")
        return

    # 2. Plotting Comparison
    print("\nGenerating comparison plot...")
    plt.switch_backend('Agg') 
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Plot each strategy
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'cyan', 'magenta']
    color_idx = 0
    
    for name, df in results.items():
        color = colors[color_idx % len(colors)]
        ax.plot(df['date'], df['return_rate'], label=f"{name} (Final: {df.iloc[-1]['return_rate']:.2f}%)", color=color, linewidth=1.5)
        color_idx += 1
        
    ax.set_title(f"Strategy Comparison: {symbol}\n{start_date} to {end_date}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Return Rate (%)")
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend(loc='upper left')
    
    # Formatting
    locator = mdates.AutoDateLocator()
    formatter = mdates.DateFormatter('%Y-%m')
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    fig.autofmt_xdate()
    
    # Save
    filename = f"comparison_{symbol}_{start_date}_{end_date}.pdf".replace(' ', '_').replace(':', '')
    figures_dir = os.path.join(os.getcwd(), 'figures')
    os.makedirs(figures_dir, exist_ok=True)
    filepath = os.path.join(figures_dir, filename)
    
    try:
        plt.savefig(filepath, format='pdf', bbox_inches='tight')
        print(f"\nSuccess! Comparison plot saved to: {filepath}")
    except Exception as e:
        print(f"\nError saving plot: {e}")

    # 3. Print Summary Table
    print("\n" + "="*100)
    print("FINAL STRATEGY COMPARISON")
    print("="*100)
    
    # Calculate duration in years for annualization
    s_dt = pd.to_datetime(start_date)
    e_dt = pd.to_datetime(end_date)
    duration_days = (e_dt - s_dt).days
    years = duration_days / 365.25
    
    summary_data = []
    for name, df in results.items():
        last_row = df.iloc[-1]
        invested = last_row['total_invested']
        value = last_row['final_value']
        profit = value - invested
        
        if invested > 0:
            ret_rate = (profit / invested * 100)
            # CAGR formula: (End_Value / Start_Value) ^ (1/n) - 1
            # Note: This treats total_invested as initial lump sum (Conservative for SIP)
            if years > 0 and value > 0:
                annualized = ((value / invested) ** (1 / years) - 1) * 100
            else:
                annualized = 0.0
        else:
            ret_rate = 0
            annualized = 0
        
        summary_data.append({
            "Strategy": name,
            "Total Invested": invested,
            "Final Value": value,
            "Profit": profit,
            "Return Rate (%)": ret_rate,
            "Annualized (%)": annualized
        })
        
    summary_df = pd.DataFrame(summary_data)
    # Sort by Return Rate descending
    summary_df = summary_df.sort_values(by="Return Rate (%)", ascending=False)
    
    # Format for pretty printing
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    pd.set_option('display.float_format', '{:.2f}'.format)
    
    # Use to_string to ensure it prints nicely even if it's large
    print(summary_df.to_string(index=False))
    print("="*80)

if __name__ == "__main__":
    main()
