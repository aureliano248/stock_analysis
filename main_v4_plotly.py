import pandas as pd
import plotly.graph_objects as go
import data_loader
import strategies
import config
import sys
import os
from main_v2 import run_backtest_v2

def create_strategy(strategy_type):
    """
    根据策略类型创建策略实例 (Copied from main_v3.py)
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

    # 2. Plotting Comparison with Plotly
    print("\nGenerating interactive comparison plot...")
    
    fig = go.Figure()
    
    for name, df in results.items():
        # Pre-calculate annualized return for hover data
        first_date = df['date'].iloc[0]
        
        def calc_annualized(row):
            invested = row['total_invested']
            value = row['final_value']
            
            if invested <= 0:
                return 0.0
                
            days_diff = (row['date'] - first_date).days
            years_diff = days_diff / 365.25
            
            if years_diff < 0.01: # Avoid division by zero or extreme volatility at start
                return 0.0
                
            try:
                if value <= 0: return -100.0
                return ((value / invested) ** (1 / years_diff) - 1) * 100
            except:
                return 0.0

        # Create a copy to avoid SettingWithCopyWarning if slice
        df_plot = df.copy()
        df_plot['annualized_hover'] = df_plot.apply(calc_annualized, axis=1)

        fig.add_trace(go.Scatter(
            x=df_plot['date'],
            y=df_plot['return_rate'],
            mode='lines',
            name=f"{name} (Final: {df_plot.iloc[-1]['return_rate']:.2f}%)",
            # Pass extra data for hover: [Total Invested, Annualized Return, Final Value]
            customdata=df_plot[['total_invested', 'annualized_hover', 'final_value']],
            hovertemplate=(
                "<b>Return: %{y:.2f}%</b><br>" +
                "Invested: %{customdata[0]:,.0f}<br>" +
                "Value: %{customdata[2]:,.0f}<br>" +
                "Annualized: %{customdata[1]:.2f}%" +
                "<extra></extra>" # Hides the trace name in the hover box (optional, often cleaner)
            )
        ))
    
    # Update layout
    fig.update_layout(
        title={
            'text': f"Strategy Comparison: {symbol} ({start_date} to {end_date})<br><sub>Click Legend: Toggle | Double-Click Legend: Isolate | Double-Click Again: Show All</sub>",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_title="Date",
        yaxis_title="Return Rate (%)",
        hovermode="x unified", # Compare values at same x
        legend=dict(
            itemclick="toggle", 
            itemdoubleclick="toggleothers",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255, 255, 255, 0.8)"
        ),
        template="plotly_white"
    )

    # 3. Save to HTML
    filename = f"interactive_comparison_{symbol}_{start_date}_{end_date}.html".replace(' ', '_').replace(':', '')
    figures_dir = os.path.join(os.getcwd(), 'figures')
    os.makedirs(figures_dir, exist_ok=True)
    filepath = os.path.join(figures_dir, filename)
    
    try:
        fig.write_html(filepath)
        print(f"\nSuccess! Interactive plot saved to: {filepath}")
        print(f"You can open this file in any browser: explorer.exe {filepath} (if using WSL)")
    except Exception as e:
        print(f"\nError saving plot: {e}")

    # 4. Print Summary Table (Same as v3)
    print("\n" + "="*100)
    print("FINAL STRATEGY COMPARISON")
    print("="*100)
    
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
    summary_df = summary_df.sort_values(by="Return Rate (%)", ascending=False)
    
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    pd.set_option('display.float_format', '{:.2f}'.format)
    
    print(summary_df.to_string(index=False))
    print("="*80)

if __name__ == "__main__":
    main()
