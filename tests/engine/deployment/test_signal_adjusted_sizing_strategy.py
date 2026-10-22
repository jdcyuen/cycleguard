import pytest
from decimal import Decimal

from engine.deployment.signal_adjusted_sizing_strategy import (
    SignalAdjustedSizingStrategy,
)


def test_signal_adjusted_sizing_strategy_returns_base_regime_percentage():
    strategy = SignalAdjustedSizingStrategy(
        {
            "RISK_ON": Decimal("0.50"),
            "TRANSITION": Decimal("0"),
        }
    )

    result = strategy.calculate(
        {
            "regime": "RISK_ON",
            "signals": {
                "trend": {"status": "bullish"},
                "breadth": {"status": "strong"},
            },
        },
        Decimal("10000"),
    )

    assert result == Decimal("0.50")

def test_signal_adjusted_sizing_strategy_rejects_invalid_regime_result():
    strategy = SignalAdjustedSizingStrategy(
        {
            "RISK_ON": Decimal("0.50"),
        }
    )

    with pytest.raises(
        ValueError,
        match="Regime result must contain a regime",
    ):
        strategy.calculate(
            {
                "signals": {},
            },
            Decimal("10000"),
        )

def test_signal_adjusted_sizing_strategy_receives_individual_signals():
    strategy = SignalAdjustedSizingStrategy(
        {
            "RISK_ON": Decimal("0.50"),
        }
    )

    regime_result = {
        "regime": "RISK_ON",
        "signals": {
            "trend": {"status": "bullish"},
            "breadth": {"status": "strong"},
            "volatility": {"status": "calm"},
            "leadership": {"status": "Strong"},
            "credit": {"status": "Healthy"},
            "cape": {"status": "Neutral"},
        },
    }

    result = strategy.calculate(
        regime_result,
        Decimal("10000"),
    )

    assert result == Decimal("0.50")
    assert len(regime_result["signals"]) == 6
    assert "trend" in regime_result["signals"]
    assert "breadth" in regime_result["signals"]
    assert "volatility" in regime_result["signals"]
    assert "leadership" in regime_result["signals"]
    assert "credit" in regime_result["signals"]
    assert "cape" in regime_result["signals"]

def test_signal_adjusted_sizing_strategy_applies_trend_adjustment():
    strategy = SignalAdjustedSizingStrategy(
        deployment_policy={
            "RISK_ON": Decimal("0.50"),
        },
        adjustments={
            "trend": {
                "bullish": Decimal("0.05"),
            },
        },
    )

    result = strategy.calculate(
        {
            "regime": "RISK_ON",
            "signals": {
                "trend": {"status": "bullish"},
            },
        },
        Decimal("10000"),
    )

    assert result == Decimal("0.55")

def test_signal_adjusted_sizing_strategy_caps_deployment_at_100_percent():
    strategy = SignalAdjustedSizingStrategy(
        deployment_policy={
            "RISK_ON": Decimal("0.90"),
        },
        adjustments={
            "trend": {
                "bullish": Decimal("0.10"),
            },
            "breadth": {
                "strong": Decimal("0.10"),
            },
        },
    )

    result = strategy.calculate(
        {
            "regime": "RISK_ON",
            "signals": {
                "trend": {"status": "bullish"},
                "breadth": {"status": "strong"},
            },
        },
        Decimal("10000"),
    )

    assert result == Decimal("1.00")

def test_signal_adjusted_sizing_strategy_ignores_unknown_signal_status():
    strategy = SignalAdjustedSizingStrategy(
        deployment_policy={
            "RISK_ON": Decimal("0.50"),
        },
        adjustments={
            "trend": {
                "bullish": Decimal("0.10"),
            },
        },
    )

    result = strategy.calculate(
        {
            "regime": "RISK_ON",
            "signals": {
                "trend": {"status": "unknown"},
            },
        },
        Decimal("10000"),
    )

    assert result == Decimal("0.50")

def test_signal_adjusted_sizing_strategy_ignores_missing_signal():
    strategy = SignalAdjustedSizingStrategy(
        deployment_policy={
            "RISK_ON": Decimal("0.50"),
        },
        adjustments={
            "trend": {
                "bullish": Decimal("0.10"),
            },
        },
    )

    result = strategy.calculate(
        {
            "regime": "RISK_ON",
            "signals": {},
        },
        Decimal("10000"),
    )

    assert result == Decimal("0.50")

def test_signal_adjusted_sizing_strategy_caps_deployment_at_zero_percent():
    strategy = SignalAdjustedSizingStrategy(
        deployment_policy={
            "RISK_ON": Decimal("0.05"),
        },
        adjustments={
            "trend": {
                "bearish": Decimal("-0.10"),
            },
        },
    )

    result = strategy.calculate(
        {
            "regime": "RISK_ON",
            "signals": {
                "trend": {"status": "bearish"},
            },
        },
        Decimal("10000"),
    )

    assert result == Decimal("0")


def test_signal_adjusted_sizing_strategy_combines_multiple_signal_adjustments():
    strategy = SignalAdjustedSizingStrategy(
        deployment_policy={
            "RISK_ON": Decimal("0.50"),
        },
        adjustments={
            "trend": {
                "bullish": Decimal("0.10"),
            },
            "breadth": {
                "strong": Decimal("0.05"),
            },
            "volatility": {
                "elevated": Decimal("-0.10"),
            },
        },
    )

    result = strategy.calculate(
        {
            "regime": "RISK_ON",
            "signals": {
                "trend": {"status": "bullish"},
                "breadth": {"status": "strong"},
                "volatility": {"status": "elevated"},
            },
        },
        Decimal("10000"),
    )

    assert result == Decimal("0.55")

def test_signal_adjusted_sizing_strategy_applies_available_adjustments_when_other_signals_are_missing():
    strategy = SignalAdjustedSizingStrategy(
        deployment_policy={
            "RISK_ON": Decimal("0.50"),
        },
        adjustments={
            "trend": {
                "bullish": Decimal("0.10"),
            },
            "breadth": {
                "strong": Decimal("0.05"),
            },
        },
    )

    result = strategy.calculate(
        {
            "regime": "RISK_ON",
            "signals": {
                "trend": {"status": "bullish"},
            },
        },
        Decimal("10000"),
    )

    assert result == Decimal("0.60")