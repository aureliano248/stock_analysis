import pandas as pd
import plotly.graph_objects as go
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

    # 2. Plotting Comparison with Plotly
    print("\nGenerating interactive comparison plot...")

    fig = go.Figure()

    for name, df in results.items():
        if df.empty:
            continue

        first_date = df['date'].iloc[0]

        def calc_annualized(row, _first_date=first_date):
            invested = row['total_invested']
            value = row['final_value']

            if invested <= 0:
                return 0.0

            days_diff = (row['date'] - _first_date).days
            years_diff = days_diff / 365.25

            if years_diff < 0.01:
                return 0.0

            try:
                if value <= 0:
                    return -100.0
                return ((value / invested) ** (1 / years_diff) - 1) * 100
            except Exception:
                return 0.0

        df_plot = df.copy()
        df_plot['annualized_hover'] = df_plot.apply(calc_annualized, axis=1)

        fig.add_trace(go.Scatter(
            x=df_plot['date'],
            y=df_plot['return_rate'],
            mode='lines',
            name=f"{name} (Final: {df_plot.iloc[-1]['return_rate']:.2f}%)",
            customdata=df_plot[['total_invested', 'annualized_hover', 'final_value']],
            hovertemplate=(
                "<b>Return: %{y:.2f}%</b><br>" +
                "Invested: %{customdata[0]:,.0f}<br>" +
                "Value: %{customdata[2]:,.0f}<br>" +
                "Annualized: %{customdata[1]:.2f}%" +
                "<extra></extra>"
            )
        ))

    # Update layout
    fig.update_layout(
        title={
            'text': f"Strategy Comparison: {symbol} ({start_date} to {end_date})<br><sub>Click Legend: Toggle | Double-Click Legend: Isolate | Double-Click Again: Show All</sub>",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_title="Date",
        yaxis_title="Return Rate (%)",
        hovermode="x unified",
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

    # 4. Print Summary Table
    from backtest.summary import print_comparison_summary
    print_comparison_summary(results, start_date, end_date)

if __name__ == "__main__":
    main()
