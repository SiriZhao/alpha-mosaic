from alphamosaic.mcp.server import _symbols


def test_mcp_symbol_contract_is_bounded_and_normalized() -> None:
    assert _symbols([" aapl ", "MSFT"], minimum=2, maximum=10) == ["AAPL", "MSFT"]
    result = _symbols(["AAPL"], minimum=2, maximum=10)
    assert isinstance(result, dict)
    assert result["status"] == "INVALID_INPUT"
    result = _symbols(["AAPL", "not a ticker"], minimum=1, maximum=5)
    assert isinstance(result, dict)
    assert result["status"] == "INVALID_INPUT"


def test_mcp_symbol_contract_deduplicates_without_expanding_work() -> None:
    assert _symbols(["AAPL", "aapl"], minimum=1, maximum=5) == ["AAPL"]
