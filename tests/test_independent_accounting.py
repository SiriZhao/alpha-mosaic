"""Independent FIXTURE ledger reconstruction; no market-performance claim."""

import numpy as np
from test_backtesting import dataset

from alphamosaic.backtesting.models import ReplayConfig
from alphamosaic.backtesting.replay import PaperReplayEngine
from alphamosaic.backtesting.strategies import StrategyRegistry
from alphamosaic.core.contracts import CorporateAction


def test_independent_seeded_fixture_ledger_reconstruction() -> None:
    scenarios = 0
    fills_checked = 0
    for seed in range(8):
        rng = np.random.default_rng(seed)
        data = dataset(100)
        actions = []
        for rows in data.bars.values():
            price = 100.0
            for i, bar in enumerate(rows):
                if i == 40:
                    price /= 2
                if i == 70:
                    price -= 1
                opening = price * float(np.exp(rng.normal(0, 0.01)))
                closing = opening * float(np.exp(rng.normal(0, 0.012)))
                rows[i] = bar.model_copy(
                    update={
                        "open": opening,
                        "close": closing,
                        "high": max(opening, closing) * 1.01,
                        "low": min(opening, closing) * 0.99,
                        "volume": float(rng.integers(10_000, 1_000_000)),
                    }
                )
                price = closing
            evidence = rows[0].model_dump(
                exclude={"session", "open", "high", "low", "close", "volume"}
            )
            actions.extend(
                [
                    CorporateAction(
                        **evidence, action="SPLIT", effective_date=rows[40].session, ratio=2
                    ),
                    CorporateAction(
                        **evidence,
                        action="DIVIDEND",
                        effective_date=rows[70].session,
                        cash_amount=1,
                    ),
                ]
            )
        data = data.model_copy(update={"actions": actions})
        for name in ("equal_weight", "momentum", "volatility_targeting"):
            for delay in (1, 3):
                config = ReplayConfig(
                    rebalance_sessions=5,
                    order_delay_sessions=delay,
                    fee_bps=3 + seed,
                    slippage_bps=5,
                    spread_bps=2,
                    min_cash_buffer=0.05,
                    max_single_weight=0.7,
                )
                result = PaperReplayEngine().run(data, StrategyRegistry().get(name), name, config)
                cash = config.initial_cash
                positions = dict.fromkeys(data.bars, 0.0)
                orders = {order.order_id: order for order in result.orders}
                signals = {signal.signal_id: signal for signal in result.signals}
                for point in result.equity:
                    for action in actions:
                        if action.effective_date == point.session:
                            if action.action == "SPLIT":
                                positions[action.symbol] *= action.ratio
                            else:
                                cash += positions[action.symbol] * action.cash_amount
                    for fill in result.fills:
                        if fill.session == point.session:
                            cash -= fill.quantity * fill.price + fill.fee
                            positions[fill.symbol] += fill.quantity
                            assert positions[fill.symbol] >= 0
                            order = orders[fill.order_id]
                            signal = signals[order.signal_id]
                            assert fill.filled_at is not None
                            assert signal.generated_at <= order.submitted_at < fill.filled_at
                            fills_checked += 1
                    rows = {
                        symbol: next(row for row in bars if row.session == point.session)
                        for symbol, bars in data.bars.items()
                    }
                    expected_nav = cash + sum(positions[s] * rows[s].close for s in positions)
                    assert abs(expected_nav - point.nav) < 1e-6
                    assert abs(cash - point.cash) < 1e-6
                    assert cash >= -1e-7
                    for symbol, quantity in positions.items():
                        assert abs(quantity - point.positions.get(symbol, 0)) < 1e-7
                assert (
                    abs(config.initial_cash + sum(e.amount for e in result.cash_ledger) - cash)
                    < 1e-6
                )
                scenarios += 1
    assert scenarios == 48
    assert fills_checked > 0
