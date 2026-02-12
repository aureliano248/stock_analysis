import akshare as ak

if __name__ == "__main__":

    fund_etf_category_sina_df = ak.fund_etf_category_sina(symbol="封闭式基金")
    print(fund_etf_category_sina_df)

    fund_etf_category_sina_df = ak.fund_etf_category_sina(symbol="ETF基金")
    print(fund_etf_category_sina_df)

    fund_etf_category_sina_df = ak.fund_etf_category_sina(symbol="LOF基金")
    print(fund_etf_category_sina_df)

    fund_etf_hist_hfq_em_df = ak.fund_etf_hist_sina(
        symbol="sh513180"
    )
    print(fund_etf_hist_hfq_em_df)
