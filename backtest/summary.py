"""
回测结果摘要：收益率计算、策略对比输出。
"""

import pandas as pd


def calc_annualized_return(total_invested, final_value, days):
    """
    计算年化收益率 (CAGR)。

    :param total_invested: 累计投入金额
    :param final_value: 最终资产价值
    :param days: 投资天数
    :return: 年化收益率 (%)，无法计算时返回 0.0
    """
    if total_invested <= 0 or final_value <= 0 or days <= 0:
        return 0.0
    years = days / 365.25
    if years < 0.01:
        return 0.0
    try:
        return ((final_value / total_invested) ** (1 / years) - 1) * 100
    except Exception:
        return 0.0


def build_comparison_summary(results, start_date, end_date):
    """
    从多策略回测结果构建对比摘要 DataFrame。

    :param results: dict, {strategy_name: df_result}
    :param start_date: 回测起始日期
    :param end_date: 回测结束日期
    :return: DataFrame，包含 Strategy, Total Invested, Final Value, Profit, Return Rate (%), Annualized (%)
    """
    s_dt = pd.to_datetime(start_date)
    e_dt = pd.to_datetime(end_date)
    duration_days = (e_dt - s_dt).days

    summary_data = []
    for name, df in results.items():
        if df is None or df.empty:
            continue
        last_row = df.iloc[-1]
        invested = last_row['total_invested']
        value = last_row['final_value']
        profit = value - invested

        if invested > 0:
            ret_rate = (profit / invested * 100)
            annualized = calc_annualized_return(invested, value, duration_days)
        else:
            ret_rate = 0.0
            annualized = 0.0

        summary_data.append({
            "Strategy": name,
            "Total Invested": invested,
            "Final Value": value,
            "Profit": profit,
            "Return Rate (%)": ret_rate,
            "Annualized (%)": annualized
        })

    summary_df = pd.DataFrame(summary_data)
    if not summary_df.empty:
        summary_df = summary_df.sort_values(by="Return Rate (%)", ascending=False)
    return summary_df


def print_comparison_summary(results, start_date, end_date):
    """
    打印多策略对比摘要表格。

    :param results: dict, {strategy_name: df_result}
    :param start_date: 回测起始日期
    :param end_date: 回测结束日期
    """
    summary_df = build_comparison_summary(results, start_date, end_date)

    print("\n" + "=" * 100)
    print("FINAL STRATEGY COMPARISON")
    print("=" * 100)

    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    pd.set_option('display.float_format', '{:.2f}'.format)

    print(summary_df.to_string(index=False))
    print("=" * 80)
