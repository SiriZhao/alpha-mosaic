from pathlib import Path

import pytest
from test_backtesting import dataset

from alphamosaic.backtesting.models import ReplayConfig
from alphamosaic.evaluation.engine_comparison import compare_engine_paths
from alphamosaic.integrations.frameworks import FrameworkIntegrationMatrix
from alphamosaic.portfolio.forward import ForwardPaperStore


def test_framework_matrix_separates_capabilities() -> None:
    records = {item.name: item for item in FrameworkIntegrationMatrix().records()}
    assert {"QuantConnect LEAN", "QuantStats", "VectorBT", "FinRL-X", "Backtrader"} <= records.keys()
    assert records["QuantStats"].adapter_present is True
    assert records["QuantStats"].engine_started is False
    assert records["QuantStats"].computation_succeeded is False
    assert records["FinRL-X"].status == "BLOCKED"
    assert records["Backtrader"].status == "LICENSE_BLOCKED"


def test_engine_comparison_keeps_execution_and_statistics_distinct() -> None:
    result = compare_engine_paths(dataset(), "momentum", ReplayConfig(fee_bps=20, slippage_bps=10))
    assert result["status"] == "COMPUTED"
    assert result["independent_execution_engine"] is False
    assert result["same_sessions"] is True
    assert result["same_fills"] is True
    assert result["fees"] > 0
    assert result["validation"] == "NO_ALPHA_CERTIFICATION"


def test_forward_signal_is_immutable_and_evaluates_costed_horizons(tmp_path: Path) -> None:
    data = dataset()
    store = ForwardPaperStore(tmp_path)
    store.initialize()
    issued = data.bars["AAA"][0].observed_at
    signal = store.freeze_signal(
        symbol="AAA", signal_id="frozen-1", issued_at=issued, as_of=issued,
        price_reference=data.bars["AAA"][0].close, signal_direction="BULLISH",
        source_hash="reviewed-source", fees_assumption={"fee_bps": 10, "slippage_bps": 5},
    )
    assert signal["source_hash"] == "reviewed-source"
    assert store.freeze_signal(
        symbol="AAA", signal_id="frozen-1", issued_at=issued, as_of=issued,
        price_reference=data.bars["AAA"][0].close, signal_direction="BULLISH",
        source_hash="reviewed-source", fees_assumption={"fee_bps": 10, "slippage_bps": 5},
    ) == signal
    with pytest.raises(ValueError, match="immutable"):
        store.freeze_signal(symbol="AAA", signal_id="frozen-1", issued_at=issued, as_of=issued, price_reference=99)
    outcomes = store.evaluate("frozen-1", data.bars["AAA"], data.bars["BBB"])
    assert [item["horizon"] for item in outcomes] == ["T+5", "T+20", "T+60"]
    assert all(item["status"] == "AT_HORIZON" for item in outcomes)
    assert all(item["source_hash"] == "reviewed-source" for item in outcomes)
    assert all(item["net_return"] < item["gross_return"] for item in outcomes)
    assert store.evaluate("frozen-1", data.bars["AAA"], data.bars["BBB"]) == outcomes
