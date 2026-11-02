"""Independent hand oracles for typed weekly price features; FIXTURE evidence only.

Originally authored by /root/recovery_boundary_review in the 2026-10-26
read-only independent review. Promoted from runtime/independent_raw_weekly_review_001.py
SHA256 9015bb4397abc91e7665802067f0488b94f9c7a59e3c3a8030f4da93fcc41f8f.
Only attribution, formatting, and static pandas/registry type casts were added;
the six independent numeric/causal oracles are preserved.
"""

from datetime import date, timedelta
from typing import cast

import exchange_calendars as xcals
import pytest

from alphamosaic.backtesting.models import (
    ReplayDataset,
    WeeklyStrategyParameters,
    payment_replay_config,
)
from alphamosaic.backtesting.replay import PaperReplayEngine
from alphamosaic.backtesting.strategies import StrategyRegistry
from alphamosaic.backtesting.weekly_strategy import WeeklyBaselineStrategy
from alphamosaic.core.contracts import CorporateAction, DataQuality, HistoricalBar, SecurityIdentity
from alphamosaic.data.weekly_features import derive_raw_weekly_closes


def data(after=50.0):
    calendar = xcals.get_calendar("XNYS")
    sessions = calendar.sessions_in_range("2024-01-02", "2024-01-26")
    bars = []
    for session in sessions:
        day = session.date()
        value = 100.0 if day < date(2024, 1, 10) else 50.0 if day < date(2024, 1, 17) else after
        stamp = calendar.session_close(session).to_pydatetime()
        bars.append(
            HistoricalBar(
                symbol="AAA",
                session=day,
                open=value,
                high=value,
                low=value,
                close=value,
                volume=1000,
                observed_at=stamp,
                known_at=stamp,
                as_of=stamp,
                source="independent-weekly-fixture",
                source_url="https://example.invalid/fixture",
                currency="USD",
                data_quality=DataQuality.FIXTURE,
                adjustment_policy="RAW",
                provenance={"provider_version": "independent-1"},
                license_scope="test-only",
                pit_status="VERIFIED",
            )
        )
    first = calendar.session_open(cast(date, sessions[0])).to_pydatetime()
    action = CorporateAction(
        symbol="AAA",
        action="SPLIT",
        effective_date=date(2024, 1, 10),
        ratio=2,
        source_action_id="fixture-split-2-for-1",
        source="independent-weekly-fixture",
        source_url="https://example.invalid/fixture",
        observed_at=first - timedelta(days=1),
        known_at=first - timedelta(days=1),
        as_of=first - timedelta(days=1),
        currency="USD",
        data_quality=DataQuality.FIXTURE,
        adjustment_policy="RAW",
        provenance={},
        license_scope="test-only",
        pit_status="VERIFIED",
    )
    identity = SecurityIdentity(
        symbol="AAA",
        exchange="NYSE",
        currency="USD",
        active=True,
        identity_verified=True,
        identity_source="independent-fixture",
        as_of=first,
    )
    return ReplayDataset(
        bars={"AAA": bars},
        identities={"AAA": identity},
        actions=[action],
        cutoff=bars[-1].as_of,
        historical_universe_verified=True,
        corporate_actions_complete=True,
    )


def config():
    return payment_replay_config(
        initial_cash=1000,
        fee_bps=0,
        slippage_bps=0,
        spread_bps=0,
        min_cash_buffer=0,
        max_volume_fraction=1,
        decision_frequency="WEEKLY",
        weekly_feature_policy="RAW_SPLIT_PRICE_ONLY_V1",
        weekly_parameters=WeeklyStrategyParameters(
            lookback_weeks=2, trend_short_weeks=2, trend_long_weeks=3
        ),
    )


@pytest.mark.parametrize("after,eligible", [(50.0, False), (55.0, True), (45.0, False)])
def test_weekly_trend_has_independent_hand_sma_and_next_raw_open_oracle(after, eligible):
    sample = data(after)
    values = derive_raw_weekly_closes(sample, decision_at=sample.cutoff)["AAA"]
    assert [row.close for row in values] == [50.0, 50.0, after, after]
    # At the third week: short=(50+after)/2, long=(50+50+after)/3.
    assert (((50 + after) / 2 > (100 + after) / 3) and after > (100 + after) / 3) is eligible
    result = PaperReplayEngine().run(
        sample, StrategyRegistry().get("weekly_trend"), "weekly_trend", config()
    )
    third = next(
        signal for signal in result.signals if signal.observation_at.date() == date(2024, 1, 19)
    )
    assert third.weights == ({"AAA": 1.0} if eligible else {})
    assert third.feature_evidence and all(
        row.evidence_kind == "DERIVED_FEATURE" for row in third.feature_evidence
    )
    if eligible:
        assert result.fills[0].session == date(2024, 1, 22)
        assert result.fills[0].price == after
    else:
        assert not result.fills


def test_future_announced_split_does_not_change_earlier_values_or_references():
    sample = data(55)
    calendar = xcals.get_calendar("XNYS")
    cutoff = calendar.session_close("2024-01-12").to_pydatetime()
    original = derive_raw_weekly_closes(sample, decision_at=cutoff)
    future = sample.actions[0].model_copy(
        update={
            "effective_date": date(2024, 1, 24),
            "ratio": 7,
            "source_action_id": "fixture-future-split",
        }
    )
    changed = sample.model_copy(
        update={
            "actions": [*sample.actions, future],
            "bars": {
                "AAA": [
                    row.model_copy(
                        update={
                            "as_of": sample.cutoff,
                            "provenance": {
                                **row.provenance,
                                "snapshot_hash": "another-whole-snapshot-with-future-content",
                            },
                        }
                    )
                    for row in sample.bars["AAA"]
                ]
            },
        }
    )
    assert derive_raw_weekly_closes(changed, decision_at=cutoff) == original


def test_applied_split_list_order_does_not_change_features_or_dependencies():
    sample = data(110)
    reverse = sample.actions[0].model_copy(
        update={
            "effective_date": date(2024, 1, 17),
            "ratio": 0.5,
            "source_action_id": "fixture-reverse-split",
        }
    )
    first = sample.model_copy(update={"actions": [sample.actions[0], reverse]})
    second = sample.model_copy(update={"actions": [reverse, sample.actions[0]]})
    left = derive_raw_weekly_closes(first, decision_at=first.cutoff)
    assert [row.close for row in left["AAA"]] == [100, 100, 110, 110]
    assert derive_raw_weekly_closes(second, decision_at=second.cutoff) == left


def test_multi_asset_features_keep_separate_share_units_and_true_equal_weights():
    sample = data(50)
    other = [
        row.model_copy(update={"symbol": "BBB", "open": 200, "high": 200, "low": 200, "close": 200})
        for row in sample.bars["AAA"]
    ]
    sample = sample.model_copy(
        update={
            "bars": {**sample.bars, "BBB": other},
            "identities": {
                **sample.identities,
                "BBB": sample.identities["AAA"].model_copy(update={"symbol": "BBB"}),
            },
        }
    )
    features = derive_raw_weekly_closes(sample, decision_at=sample.cutoff)
    assert [row.close for row in features["AAA"]] == [50] * 4
    assert [row.close for row in features["BBB"]] == [200] * 4
    assert all(not row.applied_splits for row in features["BBB"])
    target = cast(
        WeeklyBaselineStrategy, StrategyRegistry().get("weekly_equal_weight")
    ).allocation_features(features, sample.cutoff, config())
    assert target.weights == {"AAA": 0.5, "BBB": 0.5}
