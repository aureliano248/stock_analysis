import yfinance as yf
import pandas as pd

# 下载日经225历史数据
# 注意：国内访问可能需要代理
# 如果本地运行了 Clash，默认端口通常是 7890
proxy = "http://172.27.48.1:7897"

n225 = yf.download("^N225", start="2023-01-01", end="2025-01-24", proxy=proxy)

# 如果是 MultiIndex，将其简化
if not n225.empty and isinstance(n225.columns, pd.MultiIndex):
    n225.columns = n225.columns.get_level_values(0)

print(n225)