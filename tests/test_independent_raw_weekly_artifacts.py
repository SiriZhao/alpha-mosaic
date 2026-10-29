"""Independent integration oracles promoted from recovery_boundary_review; synthetic evidence only."""

import csv
import json
from datetime import date
from pathlib import Path

import pytest
from test_raw_weekly_features import action, prices
from test_weekly_research import data_between

from alphamosaic.backtesting.models import WeeklyStrategyParameters, payment_replay_config
from alphamosaic.core.service import ApplicationService
from alphamosaic.experiments.runner import canonical, digest
from alphamosaic.reporting.research import weekly_feature_evidence

POLICY = 'RAW_SPLIT_PRICE_ONLY_V1'


def register(home, dividend=False):
    service = ApplicationService(home)
    sample = data_between('2024-01-02', '2024-02-02')
    if dividend:
        ex = date(2024, 1, 10)
        sample = prices(sample, [(date.min, 100), (ex, 99)])
        sample = sample.model_copy(update={'actions': [action(sample, ex, 'DIVIDEND')]})
    else:
        split = date(2024, 1, 10)
        sample = prices(sample, [(date.min, 100), (split, 50), (date(2024, 1, 17), 55)])
        sample = sample.model_copy(update={'actions': [action(sample, split)]})
    manifest = service.experiment_runner().datasets.save(sample)
    return service, sample, manifest['dataset_id']


def execute(service, dataset_id, strategy='weekly_momentum', policy=POLICY):
    replay = payment_replay_config(initial_cash=1000, fee_bps=0, slippage_bps=0, spread_bps=0,
        min_cash_buffer=0, max_volume_fraction=1, decision_frequency='WEEKLY',
        weekly_feature_policy=policy, weekly_parameters=WeeklyStrategyParameters(lookback_weeks=2,
            trend_short_weeks=2, trend_long_weeks=3))
    item = service.research_experiment({'dataset_id': dataset_id, 'strategy': strategy,
        'symbols': ['AAA'], 'benchmark': 'AAA', 'replay': replay.model_dump(mode='json')})
    assert item['status'] == 'COMPLETED', item.get('error')
    return item


def test_dividend_income_never_becomes_price_feature_or_second_payment_return(tmp_path):
    service, sample, dataset_id = register(tmp_path, dividend=True)
    item = execute(service, dataset_id, 'weekly_equal_weight')
    values = [row for signal in item['result']['signals'] for row in signal['feature_evidence']]
    assert values and all(row['return_basis'] == 'PRICE_ONLY_EXCLUDES_DIVIDENDS' for row in values)
    assert {row['close'] for row in values} == {100, 99}
    result = item['result']
    assert result['dividend_entitlements'][0]['amount'] == 10
    assert sum(row['amount'] for row in result['dividend_payments']) == 10
    assert all(point['nav'] == 1000 for point in result['equity'])
    raw = {row.session.isoformat(): row.close for row in sample.bars['AAA']}
    for point in result['equity']:
        assert point['market_values'] == {symbol: quantity * raw[point['session']]
            for symbol, quantity in point['positions'].items()}
    assert all(not signal['feature_evidence'] for signal in item['benchmark_result']['signals'])
    disclosure = weekly_feature_evidence(item)
    assert disclosure['portfolio_return_basis'] == 'RAW_WITH_CASH_ACTIONS'
    assert disclosure['feature_pit_status'] == 'NOT_APPLICABLE'


def test_csv_close_values_have_independent_share_unit_and_signal_time_oracle(tmp_path):
    service, sample, dataset_id = register(tmp_path)
    item = execute(service, dataset_id)
    folder = service.experiment_runner().store.path(item['experiment_id'])
    with (folder / 'weekly_price_features.csv').open(newline='', encoding='utf-8') as stream:
        exported = list(csv.DictReader(stream))
    signals = {signal['signal_id']: signal for signal in item['result']['signals']}
    assert exported and item['artifact_schema_version'] == 4
    raw = {row.session: row.close for row in sample.bars['AAA']}
    for row in exported:
        end, anchor = date.fromisoformat(row['last_session']), date.fromisoformat(row['unit_anchor'])
        ratio = 2 if end < date(2024, 1, 10) <= anchor else 1
        assert float(row['close']) == raw[end] / ratio
        assert row['signal_generated_at'] == row['decision_at'] == signals[row['signal_id']]['generated_at']
        assert row['evidence_kind'] == 'DERIVED_FEATURE' and row['pit_status'] == 'NOT_APPLICABLE'
    assert item['result']['fills'][0]['price'] == 55
    assert item['result']['fills'][0]['session'] == '2024-01-22'
    # A changed export must be detected even though the primary JSON is intact.
    (folder / 'weekly_price_features.csv').write_text('corrupt-independent-fixture', encoding='utf-8')
    with pytest.raises(ValueError, match='integrity'):
        service.research_result(item['experiment_id'])


def test_requested_passive_policy_does_not_claim_feature_consumption(tmp_path):
    service, _, dataset_id = register(tmp_path)
    item = execute(service, dataset_id, 'buy_and_hold')
    disclosure = weekly_feature_evidence(item)
    assert item['artifact_schema_version'] == 4 and disclosure['requested_policy'] == POLICY
    assert disclosure['recorded_feature_rows'] == disclosure['signals_with_features'] == 0
    assert disclosure['feature_return_basis'] == disclosure['feature_pit_status'] == 'NOT_RECORDED'
    path = service.experiment_runner().store.path(item['experiment_id']) / 'weekly_price_features.csv'
    with path.open(newline='', encoding='utf-8') as stream:
        assert list(csv.DictReader(stream)) == []


def test_legacy_schema_three_missing_policy_and_features_is_read_without_rewrite(tmp_path):
    service = ApplicationService(tmp_path)
    sample = data_between()
    manifest = service.experiment_runner().datasets.save(sample)
    item = execute(service, manifest['dataset_id'], 'buy_and_hold', 'LEGACY_REJECT_RAW_ACTIONS')
    folder = service.experiment_runner().store.path(item['experiment_id'])
    assert item['artifact_schema_version'] == 3 and not (folder / 'weekly_price_features.csv').exists()
    # Model a sealed old-schema fixture without fields introduced by the new source.
    item['config']['replay'].pop('weekly_feature_policy')
    for result in [item['result'], item['benchmark_result']]:
        result['config'].pop('weekly_feature_policy')
        for signal in result['signals']:
            signal.pop('feature_evidence')
    (folder / 'experiment.json').write_bytes(canonical(item))
    (folder / 'config.json').write_bytes(canonical(item['config']))
    checksums = json.loads((folder / 'checksums.json').read_bytes())
    for name in ['experiment.json', 'config.json']:
        checksums[name] = digest((folder / name).read_bytes())
    (folder / 'checksums.json').write_bytes(canonical(checksums))
    before = {path.name: path.read_bytes() for path in folder.iterdir()}
    saved = service.research_result(item['experiment_id'])
    assert saved == item and weekly_feature_evidence(saved)['recorded_feature_rows'] == 0
    assert {path.name: path.read_bytes() for path in folder.iterdir()} == before


def test_strategy_lab_submits_selected_raw_policy_to_real_job(tmp_path, monkeypatch):
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    monkeypatch.setenv('ALPHAMOSAIC_HOME', str(tmp_path))
    st.cache_resource.clear()
    try:
        register(tmp_path)
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'src/alphamosaic/ui/app.py'), default_timeout=30).run()
        app.sidebar.radio[0].set_value('Strategy Lab').run()
        next(select for select in app.selectbox if select.label == 'Strategy').set_value('weekly_momentum').run()
        next(select for select in app.selectbox if select.label == 'Weekly signal price policy').set_value(POLICY)
        next(select for select in app.selectbox if select.label == 'Cost scenario').set_value('zero')
        next(widget for widget in app.number_input if widget.label == 'Lookback weeks').set_value(2)
        next(widget for widget in app.date_input if widget.label.startswith('Evaluation start')).set_value(date(2024, 1, 2))
        next(button for button in app.button if button.label == 'Run local experiment').click().run()
        assert not app.exception
        result = app.session_state['job'].result(timeout=30)
        assert result['status'] == 'COMPLETED', result.get('error')
        assert result['config']['replay']['weekly_feature_policy'] == POLICY
        assert result['artifact_schema_version'] == 4
        assert weekly_feature_evidence(result)['recorded_feature_rows'] > 0
        assert result['result']['fills'][0]['price'] == 55
        assert ApplicationService(tmp_path).research_result(result['experiment_id'])['result'] == result['result']
    finally:
        st.cache_resource.clear()
