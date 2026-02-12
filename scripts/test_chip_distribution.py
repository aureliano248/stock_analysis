import akshare as ak
import pandas as pd
import datetime

# 配置
symbol = "600519"
start_date = "2026-01-01"
# 使用当前日期作为结束日期，或者足够远的日期
end_date = datetime.date.today().strftime("%Y-%m-%d")

print(f"Fetching data for {symbol} from {start_date} to {end_date} (Adjust: qfq)...")

def get_combined_data():
    try:
        # 1. 获取行情数据 (Price)
        # 格式化日期为 YYYYMMDD
        start_str = start_date.replace("-", "")
        end_str = end_date.replace("-", "")
        
        print("Fetching price data...")
        df_price = ak.stock_zh_a_hist(
            symbol=symbol, 
            period="daily", 
            start_date=start_str, 
            end_date=end_str, 
            adjust="qfq"
        )
        
        if df_price is None or df_price.empty:
            print("No price data found.")
            return

        # 统一日期列名为 'date' 并转换为 datetime
        df_price.rename(columns={'日期': 'date', '开盘': 'open', '收盘': 'close', 
                               '最高': 'high', '最低': 'low', '成交量': 'volume'}, inplace=True)
        df_price['date'] = pd.to_datetime(df_price['date'])
        
        # 2. 获取筹码分布数据 (CYQ)
        print("Fetching CYQ data...")
        df_cyq = ak.stock_cyq_em(symbol=symbol, adjust="qfq")
        
        if df_cyq is None or df_cyq.empty:
            print("No CYQ data found.")
            return

        # 统一日期列
        cyq_date_col = next((col for col in ['date', '日期'] if col in df_cyq.columns), None)
        if not cyq_date_col:
            print("CYQ date column not found.")
            return
            
        df_cyq.rename(columns={cyq_date_col: 'date'}, inplace=True)
        df_cyq['date'] = pd.to_datetime(df_cyq['date'])
        
        # 过滤时间段
        df_cyq = df_cyq[df_cyq['date'] >= pd.to_datetime(start_date)]
        
        # 3. 合并数据
        # 使用 inner join 确保两天都有数据
        df_merge = pd.merge(df_price, df_cyq, on='date', how='inner')
        
        # 4. 整理输出列
        # 选择我们关注的列
        cols = [
            'date', 
            'close', 
            '平均成本', 
            '获利比例', 
            '90成本-低', '90成本-高', '90集中度',
            '70成本-低', '70成本-高', '70集中度'
        ]
        
        # 检查列是否存在
        available_cols = [c for c in cols if c in df_merge.columns]
        final_df = df_merge[available_cols].copy()
        
        # 格式化输出
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        pd.set_option('display.max_rows', None)

        print("\n=== Combined Data (2026-01-01 to Present) ===")
        print(final_df.to_string(index=False))
        
        # 保存到 CSV 方便用户查看
        output_file = "result_2026_jan_qfq.csv"
        final_df.to_csv(output_file, index=False)
        print(f"\nData saved to {output_file}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    get_combined_data()
