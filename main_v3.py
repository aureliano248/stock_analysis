import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import data_loader
import config
import os
from strategies import create_strategy, get_strategy_params
from main_v2 import run_backtest_v2


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
        params = get_strategy_params(strat_type, config)
        strategy, strategy_name = create_strategy(strat_type, params)
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
    from backtest.summary import print_comparison_summary
    print_comparison_summary(results, start_date, end_date)

if __name__ == "__main__":
    main()
