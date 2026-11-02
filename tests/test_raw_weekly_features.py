"""Hand numeric oracles for the opt-in price hypothesis and daily accounting boundary."""

from datetime import date, timedelta

import exchange_calendars as xcals
import pytest
from test_independent_dividend_payment import payment_config
from test_weekly_research import data_between

from alphamosaic.backtesting.models import ReplayConfig, ReplayDataset, WeeklyStrategyParameters
from alphamosaic.backtesting.replay import PaperReplayEngine
from alphamosaic.backtesting.strategies import StrategyRegistry
from alphamosaic.core.contracts import CorporateAction, HistoricalBar
from alphamosaic.data.weekly import WeeklyBar, aggregate_weekly
from alphamosaic.data.weekly_features import derive_raw_weekly_closes

POLICY = "RAW_SPLIT_PRICE_ONLY_V1"


def action(data, day, kind="SPLIT", ratio: float = 2, **changes):
    known = xcals.get_calendar("XNYS").session_open(data.bars["AAA"][0].session).to_pydatetime() - timedelta(days=1)
    fields = data.bars["AAA"][0].model_dump(exclude={"session", "open", "high", "low", "close", "volume"})
    fields.update(observed_at=known, known_at=known, as_of=known)
    terms = dict(ratio=ratio) if kind == "SPLIT" else dict(cash_amount=1,
        effective_date_role="EX_DATE", dividend_type="ORDINARY_CASH", payment_date=date(2024, 1, 23),
        cash_amount_basis="EX_DATE_SHARES", source_action_id="declared-dividend-1")
    return CorporateAction.model_validate({**fields, "action": kind, "effective_date": day, **terms, **changes})


def prices(data, schedule):
    return data.model_copy(update={"bars": {"AAA": [bar.model_copy(update={field:
        next(price for day, price in reversed(schedule) if bar.session >= day)
        for field in ("open", "high", "low", "close")}) for bar in data.bars["AAA"]]}})


def features(data, at=None):
    return derive_raw_weekly_closes(data, decision_at=at or data.cutoff)["AAA"]


def replay(data, name="weekly_momentum", **changes):
    config = payment_config(decision_frequency="WEEKLY", weekly_feature_policy=POLICY,
        weekly_parameters=WeeklyStrategyParameters(lookback_weeks=2, trend_short_weeks=2, trend_long_weeks=3), **changes)
    return PaperReplayEngine().run(data, StrategyRegistry().get(name), name, config)


@pytest.mark.parametrize("ratio,after", [(2, 50), (0.5, 200)])
def test_hand_split_and_reverse_split_remove_only_unit_jump(ratio, after):
    data = data_between("2024-01-02", "2024-01-26")
    day = date(2024, 1, 10)
    data = prices(data, [(date.min, 100), (day, after)]).model_copy(update={"actions": [action(data, day, ratio=ratio)]})
    rows = features(data)
    assert [row.close for row in rows] == [after] * 4
    assert rows[0].unit_anchor == date(2024, 1, 26)
    assert rows[0].applied_splits[0].ratio == ratio
    assert rows[0].applied_splits[0].source_action_id is None  # hash is not a provider ID
    assert rows[0].evidence_kind == "DERIVED_FEATURE" and rows[0].pit_status == "NOT_APPLICABLE"
    assert rows[0].parent_pit_status == "VERIFIED"
    result = replay(data)
    assert not result.fills and all(not signal.weights for signal in result.signals)
    assert any(signal.feature_evidence for signal in result.signals)


def test_multi_split_product_and_price_hypothesis_hand_return():
    data = data_between("2024-01-02", "2024-01-26")
    split, reverse = date(2024, 1, 10), date(2024, 1, 17)
    data = prices(data, [(date.min, 100), (split, 50), (reverse, 110)]).model_copy(update={"actions": [
        action(data, split, ratio=2), action(data, reverse, ratio=0.5)]})
    rows = features(data)
    assert [row.close for row in rows] == [100, 100, 110, 110]
    assert rows[-1].close / rows[0].close - 1 == pytest.approx(0.1)
    assert len(rows[0].applied_splits) == 2
    result = replay(data)
    assert result.fills and result.fills[0].price == 110  # unadjusted observed execution


def test_no_action_parity_and_old_config_defaults():
    data = data_between("2024-01-02", "2024-02-02")
    assert [row.close for row in features(data)] == [row.close for row in aggregate_weekly(data).bars["AAA"]]
    config = payment_config(decision_frequency="WEEKLY", weekly_parameters=WeeklyStrategyParameters(lookback_weeks=2))
    old = PaperReplayEngine().run(data, StrategyRegistry().get("weekly_momentum"), "weekly_momentum", config)
    new = replay(data)
    assert old.fills == new.fills and old.equity == new.equity
    assert ReplayConfig.model_validate({}).weekly_feature_policy == "LEGACY_REJECT_RAW_ACTIONS"
    with pytest.raises(ValueError, match="requires WEEKLY"):
        ReplayConfig(weekly_feature_policy=POLICY)


def test_dividend_price_drop_fixed_receivable_nav_and_payment_independence():
    data = data_between("2024-01-02", "2024-01-26")
    ex = date(2024, 1, 10)
    data = prices(data, [(date.min, 100), (ex, 99)]).model_copy(update={"actions": [action(data, ex, "DIVIDEND")]})
    rows = features(data)
    assert rows[1].close / rows[0].close - 1 == pytest.approx(-0.01)
    changed = data.model_copy(update={"actions": [data.actions[0].model_copy(update={"payment_date": date(2024, 1, 12)})]})
    assert features(changed) == rows
    left, right = replay(data, "weekly_equal_weight"), replay(changed, "weekly_equal_weight")
    assert left.signals == right.signals
    assert left.equity[-1].nav == right.equity[-1].nav == 1000
    assert left.dividend_entitlements[0].amount == 10
    assert sum(payment.amount for payment in left.dividend_payments) == 10
    ex_point = next(point for point in left.equity if point.session == ex)
    assert ex_point.market_values == {"AAA": 990} and sum(ex_point.receivables.values()) == 10
    assert left.dividend_payments[0].at != right.dividend_payments[0].at


def test_split_dividend_reverse_split_keep_fixed_dollar_rights():
    data = data_between("2024-01-02", "2024-02-02")
    split, ex, reverse = date(2024, 1, 9), date(2024, 1, 11), date(2024, 1, 17)
    data = prices(data, [(date.min, 100), (split, 50), (ex, 49), (reverse, 98)]).model_copy(update={"actions": [
        action(data, split), action(data, ex, "DIVIDEND"), action(data, reverse, ratio=0.5)]})
    assert [row.close for row in features(data)] == [100, 98, 98, 98, 98]
    result = replay(data, "weekly_equal_weight")
    claim = result.dividend_entitlements[0]
    assert claim.entitled_quantity == 20 and claim.amount == 20
    assert result.dividend_payments[0].amount == 20 and result.equity[-1].nav == 1000
    assert len(result.dividend_payments) == 1


def test_future_rows_actions_snapshot_hashes_do_not_enter_earlier_dependencies():
    data = data_between("2024-01-02", "2024-02-02")
    boundary = date(2024, 1, 19)
    at = xcals.get_calendar("XNYS").session_close(boundary).to_pydatetime()
    changed = prices(data, [(date.min, 100), (date(2024, 1, 22), 999)])
    original = prices(data, [(date.min, 100)])
    changed = changed.model_copy(update={"bars": {"AAA": [bar.model_copy(update={"provenance": {
        **bar.provenance, "snapshot_hash": "new-global-future-snapshot"}}) for bar in changed.bars["AAA"]]},
        "actions": [action(data, date(2024, 1, 24), ratio=7)]})
    assert features(original, at) == features(changed, at)
    left, right = replay(original), replay(changed)
    assert [s for s in left.signals if s.observation_at.date() <= boundary] == [s for s in right.signals if s.observation_at.date() <= boundary]
    assert [f for f in left.fills if f.session <= boundary] == [f for f in right.fills if f.session <= boundary]


def test_partial_current_week_split_does_not_reanchor_prior_complete_week():
    data = data_between("2024-01-02", "2024-01-17")
    data = prices(data, [(date.min, 100), (date(2024, 1, 17), 50)]).model_copy(update={"actions": [action(data, date(2024, 1, 17))]})
    rows = features(data)
    assert [row.close for row in rows] == [100, 100]
    assert all(row.unit_anchor == date(2024, 1, 12) and not row.applied_splits for row in rows)


@pytest.mark.parametrize("changes,match", [
    ({"ratio": None}, "ratio missing"),
    ({"pit_status": "RECONSTRUCTED"}, "not certified PIT"),
    ({"currency": "GBP"}, "invalid"),
])
def test_invalid_split_terms_fail_closed(changes, match):
    data = data_between()
    data = data.model_copy(update={"actions": [action(data, date(2024, 1, 10), **changes)]})
    with pytest.raises(ValueError, match=match):
        features(data)


@pytest.mark.parametrize("mode", ["STRICT_PIT", "RECONSTRUCTED_DIAGNOSTIC"])
def test_late_action_disclosure_refused_even_in_diagnostics(mode):
    data = data_between()
    late = xcals.get_calendar("XNYS").session_close(date(2024, 1, 10)).to_pydatetime()
    data = data.model_copy(update={"mode": mode, "actions": [action(data, date(2024, 1, 10), observed_at=late, known_at=late, as_of=late)]})
    with pytest.raises(ValueError, match="unavailable"):
        features(data)


@pytest.mark.parametrize("kind", ["SPECIAL_CASH", "DUE_BILL", "UNKNOWN"])
def test_unsupported_dividend_terms_rejected(kind):
    data = data_between()
    data = data.model_copy(update={"actions": [action(data, date(2024, 1, 10), "DIVIDEND", dividend_type=kind)]})
    with pytest.raises(ValueError, match="qualified ordinary"):
        features(data)


def test_duplicate_unsupported_same_day_and_missing_payment_terms_refused():
    data = data_between()
    split = action(data, date(2024, 1, 10))
    dividend = action(data, date(2024, 1, 10), "DIVIDEND")
    for actions in ([split, split], [split, dividend], [dividend.model_copy(update={"payment_date": None})],
                    [split.model_copy(update={"action": "DELISTING"})]):
        with pytest.raises(ValueError):
            features(data.model_copy(update={"actions": actions}))


def test_missing_late_and_misaligned_sessions_and_holiday_anchor():
    data = data_between()
    rows = data.bars["AAA"]
    with pytest.raises(ValueError, match="complete chronological"):
        features(data.model_copy(update={"bars": {"AAA": rows[:6] + rows[7:]}}))
    late = rows[-1].model_copy(update={"known_at": data.cutoff + timedelta(days=1), "as_of": data.cutoff + timedelta(days=1)})
    altered = data.model_copy(update={"bars": {"AAA": [*rows[:-1], late]}})
    assert features(altered)[-1].unit_anchor == date(2024, 1, 26)
    holiday = data_between("2024-03-25", "2024-03-28")
    assert features(holiday)[0].unit_anchor == date(2024, 3, 28)
    other = [row.model_copy(update={"symbol": "BBB"}) for row in [*rows[:-1], late]]
    misaligned = data.model_copy(update={"bars": {"AAA": rows, "BBB": other}, "identities": {
        **data.identities, "BBB": data.identities["AAA"].model_copy(update={"symbol": "BBB"})}})
    with pytest.raises(ValueError, match="unaligned"):
        features(misaligned)


@pytest.mark.parametrize("ratio", [1e308, 1e-308])
def test_unrepresentable_split_products_fail_explicitly(ratio):
    data = data_between()
    data = data.model_copy(update={"actions": [action(data, date(2024, 1, 10), ratio=ratio),
        action(data, date(2024, 1, 17), ratio=ratio)]})
    with pytest.raises(ValueError, match="unrepresentable"):
        features(data)


def test_derived_features_cannot_enter_daily_or_weekly_observation_contracts():
    data = data_between()
    row = features(data)[0]
    for contract in (HistoricalBar, WeeklyBar):
        with pytest.raises(ValueError):
            contract.model_validate(row.model_dump())
    with pytest.raises(ValueError):
        ReplayDataset.model_validate({**data.model_dump(), "bars": {"AAA": [row.model_dump()]}})


def test_passive_benchmark_does_not_claim_feature_consumption():
    result = replay(data_between(), "buy_and_hold")
    assert result.fills and all(not signal.feature_evidence for signal in result.signals)
    assert not any("DERIVED_FEATURE" in flag for flag in result.diagnostics)
