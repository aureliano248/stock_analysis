
import pytest
import pandas as pd
from data_loader.data_provider import DataProvider


if __name__ == "__main__":
    """直接运行以执行测试"""
    """测试 ETF: 513180 (纳指ETF)"""
    df, asset_type = DataProvider().fetch_etf("513180", "20240101", "20260215", "qfq")
    print(df.size)
    print(df)
    full_count=0
    temp_count=0
    for date, close in zip(df['date'], df['close']):
        if date >= pd.to_datetime("2025-07-01") and date <= pd.to_datetime("2026-01-19"):
            print(f"Date: {date}, Close: {close}")
            full_count+=1
            if close > 0.708:
                temp_count+=1
    print(f"Total entries from 2025-07-01: {full_count}, Close > 0.708: {temp_count}")



    



