import json
import sqlite3
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
        source_hash="reviewed-source", benchmark="BBB", fees_assumption={"fee_bps": 10, "slippage_bps": 5},
    )
    assert signal["source_hash"] == "reviewed-source"
    assert store.freeze_signal(
        symbol="AAA", signal_id="frozen-1", issued_at=issued, as_of=issued,
        price_reference=data.bars["AAA"][0].close, signal_direction="BULLISH",
        source_hash="reviewed-source", benchmark="BBB", fees_assumption={"fee_bps": 10, "slippage_bps": 5},
    ) == signal
    with pytest.raises(ValueError, match="immutable"):
        store.freeze_signal(symbol="AAA", signal_id="frozen-1", issued_at=issued, as_of=issued, price_reference=99)
    outcomes = store.evaluate("frozen-1", data.bars["AAA"], data.bars["BBB"])
    assert [item["horizon"] for item in outcomes] == ["T+5", "T+20", "T+60"]
    assert all(item["status"] == "AT_HORIZON" for item in outcomes)
    assert all(item["source_hash"] == "reviewed-source" for item in outcomes)
    assert all(item["net_return"] < item["gross_return"] for item in outcomes)
    assert all(item["source_hash"] == "reviewed-source" for item in store.outcomes("frozen-1"))
    assert store.evaluate("frozen-1", data.bars["AAA"], data.bars["BBB"]) == outcomes


def test_forward_pending_states_are_append_only_until_maturity(tmp_path: Path) -> None:
    data = dataset()
    store = ForwardPaperStore(tmp_path)
    store.initialize()
    issued = data.bars["AAA"][0].observed_at
    store.freeze_signal(
        symbol="AAA", signal_id="evolving-1", issued_at=issued, as_of=issued,
        price_reference=data.bars["AAA"][0].close, signal_direction="BULLISH",
        entry_conditions={"trigger_price": data.bars["AAA"][10].high},
    )
    early = data.bars["AAA"][:4]
    first = store.evaluate("evolving-1", early)
    assert first[0]["status"] == "NOT_TRIGGERED"
    assert store.outcomes("evolving-1") == []
    assert store.observations("evolving-1")

    later = data.bars["AAA"][:25]
    second = store.evaluate("evolving-1", later)
    assert second[0]["status"] == "AT_HORIZON"
    mature = store.outcomes("evolving-1")
    assert len(mature) == 1

    # Repeating the call and reopening the store are idempotent. The matured
    # result remains immutable while pending observations remain append-only.
    reopened = ForwardPaperStore(tmp_path)
    assert reopened.evaluate("evolving-1", later)[0] == second[0]
    assert reopened.outcomes("evolving-1") == mature
    assert len(reopened.observations("evolving-1")) >= 2


def test_forward_late_partial_batches_mature_without_changing_final_result(tmp_path: Path) -> None:
    data = dataset(70)
    store = ForwardPaperStore(tmp_path)
    issued = data.bars["AAA"][0].observed_at
    store.freeze_signal(symbol="AAA", signal_id="late", issued_at=issued, as_of=issued,
                        price_reference=data.bars["AAA"][0].close)
    partial = data.bars["AAA"][1:3] + data.bars["AAA"][4:10]
    first = store.evaluate("late", partial)
    assert all(item["status"] == "INSUFFICIENT_DATA" for item in first)
    assert not store.outcomes()
    count = len(store.observations())
    store.evaluate("late", partial)
    assert len(store.observations()) == count
    second = store.evaluate("late", [data.bars["AAA"][3]])
    assert second[0]["status"] == "AT_HORIZON"
    final = second[0]
    restarted = ForwardPaperStore(tmp_path)
    assert restarted.evaluate("late", data.bars["AAA"][10:65])[0] == final
    assert restarted.evaluate("late", [])[0] == final
    with pytest.raises(ValueError, match="revised"):
        restarted.evaluate("late", [data.bars["AAA"][5].model_copy(update={"close": 99})])


def test_forward_legacy_pending_migration_preserves_original_rows(tmp_path: Path) -> None:
    data = dataset(70)
    store = ForwardPaperStore(tmp_path)
    issued = data.bars["AAA"][0].observed_at
    store.freeze_signal(symbol="AAA", signal_id="legacy", issued_at=issued, as_of=issued,
                        price_reference=data.bars["AAA"][0].close)
    legacy = json.dumps({"signal_id": "legacy", "horizon": "T+5", "status": "HOLDING", "qualified": False})
    with sqlite3.connect(store.path) as connection:
        connection.execute("INSERT INTO outcomes VALUES (?, ?, ?, ?)", ("legacy:5", "legacy", 0, legacy))
    store.initialize()
    assert store.observations()[0]["status"] == "HOLDING"
    assert store.evaluate("legacy", data.bars["AAA"])[0]["status"] == "AT_HORIZON"
    with sqlite3.connect(store.path) as connection:
        assert connection.execute("SELECT payload FROM outcomes WHERE id='legacy:5'").fetchone()[0] == legacy


def test_forward_rejects_future_data_and_wrong_benchmark(tmp_path: Path) -> None:
    data = dataset(70)
    store = ForwardPaperStore(tmp_path)
    issued = data.bars["AAA"][0].observed_at
    store.freeze_signal(symbol="AAA", signal_id="pit", issued_at=issued, as_of=issued,
                        price_reference=data.bars["AAA"][0].close)
    with pytest.raises(ValueError, match="future"):
        store.evaluate("pit", data.bars["AAA"][1:4], cutoff=issued)
    with pytest.raises(ValueError, match="mismatched"):
        store.evaluate("pit", data.bars["AAA"], data.bars["BBB"])
