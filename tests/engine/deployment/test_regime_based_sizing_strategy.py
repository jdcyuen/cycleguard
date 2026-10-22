from decimal import Decimal

from engine.deployment.regime_based_sizing_strategy import (
    RegimeBasedSizingStrategy,
)


def test_regime_based_sizing_strategy_returns_regime_deployment_percentage():
    strategy = RegimeBasedSizingStrategy(
        {
            "RISK_ON": Decimal("0.50"),
            "TRANSITION": Decimal("0"),
        }
    )

    result = strategy.calculate(
        {
            "regime": "RISK_ON",
            "signals": {},
        },
        Decimal("10000"),
    )

    assert result == Decimal("0.50")