import akshare as ak

def check_available_indices():
    df_spot = ak.index_global_spot_em()
    n225_info = df_spot[df_spot['名称'].str.contains('日经', na=False)]
    print("找到的相关指数:")
    print(n225_info)
    return n225_info

if __name__ == "__main__":
    check_available_indices()
