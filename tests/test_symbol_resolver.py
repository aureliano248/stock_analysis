
import pytest
from data_loader.symbol_resolver import SymbolResolver

def test_resolve_of_suffix():
    resolver = SymbolResolver()
    symbol, suffix, asset_type = resolver.resolve("000300.OF")
    assert symbol == "000300"
    assert suffix == "OF"
    assert asset_type == "otc_fund"

def test_resolve_no_suffix():
    resolver = SymbolResolver()
    symbol, suffix, asset_type = resolver.resolve("600519")
    assert symbol == "600519"
    assert suffix is None
    assert asset_type is None

def test_resolve_unsupported_suffix():
    resolver = SymbolResolver()
    with pytest.raises(ValueError, match="不支持的代码后缀"):
        resolver.resolve("600519.SH")
