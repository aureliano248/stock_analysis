
import pytest
import pandas as pd
import datetime
import os
import shutil
from data_loader.cache_manager import CacheManager

@pytest.fixture
def temp_cache_mgr():
    test_dir = "./test_data_tmp"
    mgr = CacheManager(test_dir)
    yield mgr
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

def test_check_needs_update_empty_df(temp_cache_mgr):
    needs_update, fetch_start = temp_cache_mgr.check_needs_update(pd.DataFrame(), "20240101")
    assert needs_update is True
    assert fetch_start == '19900101'

def test_merge_data(temp_cache_mgr):
    df_old = pd.DataFrame({'date': [pd.to_datetime('2024-01-01')], 'close': [100]})
    df_new = pd.DataFrame({'date': [pd.to_datetime('2024-01-01'), pd.to_datetime('2024-01-02')], 'close': [105, 110]})
    merged = temp_cache_mgr.merge_data(df_old, df_new)
    assert len(merged) == 2
    # 检查去重逻辑是否保留了 new 中的 105
    assert merged[merged['date'] == '2024-01-01']['close'].values[0] == 105

def test_get_file_path(temp_cache_mgr):
    path = temp_cache_mgr.get_file_path("600519", None, "qfq")
    assert path.endswith("600519_qfq.csv")
    
    path_of = temp_cache_mgr.get_file_path("000300", "OF", "qfq")
    assert path_of.endswith("000300.OF_qfq.csv")
