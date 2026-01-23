import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import data_loader
import config
import os

def main():
    print("Loading configuration from config.py...")
    symbol = config.SYMBOL
    
    # 1. 加载所有数据 (不进行时间过滤，以查看完整数据情况，或者根据需求过滤？)
    # 既然是 "检查拉取到的数据"，通常指检查本地缓存或新拉取的数据文件整体。
    # data_loader.load_data 现在返回 (DataFrame, stock_name) 元组
    result = data_loader.load_data(symbol)
    if result is not None:
        df, stock_name = result
    else:
        df = None
    
    if df is None or df.empty:
        print(f"Failed to load data for {symbol}")
        return

    print(f"Data loaded. Rows: {len(df)}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Price range: {df['close'].min()} to {df['close'].max()}")

    # 2. 绘图
    plt.switch_backend('Agg') 
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(df['date'], df['close'], label='Close Price', color='green', linewidth=1)
    
    ax.set_title(f"Original Close Price: {symbol}\n({df['date'].min().date()} to {df['date'].max().date()})")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='upper left')
    
    # Format X axis
    locator = mdates.AutoDateLocator()
    formatter = mdates.DateFormatter('%Y-%m')
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    
    fig.autofmt_xdate()
    
    # 3. 保存
    figures_dir = os.path.join(os.getcwd(), 'figures')
    os.makedirs(figures_dir, exist_ok=True)
    
    filename = f"original_close_{symbol}.pdf"
    filepath = os.path.join(figures_dir, filename)
    
    try:
        plt.savefig(filepath, format='pdf', bbox_inches='tight')
        print(f"\nSuccess! Close price plot saved to: {filepath}")
    except Exception as e:
        print(f"\nError saving plot: {e}")

if __name__ == "__main__":
    main()
