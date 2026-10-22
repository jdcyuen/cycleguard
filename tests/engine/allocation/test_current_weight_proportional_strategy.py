from decimal import Decimal

import pytest

from engine.allocation.current_weight_proportional_strategy import (
    CurrentWeightProportionalStrategy,
)


def test_allocates_remaining_target_proportionally():
    strategy = CurrentWeightProportionalStrategy()

    result = strategy.allocate(
        Decimal("0.03"),
        {
            "AAPL": Decimal("6000"),
            "SPMO": Decimal("4000"),
        },
    )

    assert result == {
        "AAPL": Decimal("0.018"),
        "SPMO": Decimal("0.012"),
    }


def test_returns_empty_for_no_securities():
    strategy = CurrentWeightProportionalStrategy()

    result = strategy.allocate(
        Decimal("0.03"),
        {},
    )

    assert result == {}


def test_returns_zero_for_zero_total_value():
    strategy = CurrentWeightProportionalStrategy()

    result = strategy.allocate(
        Decimal("0.03"),
        {
            "AAPL": Decimal("0"),
            "SPMO": Decimal("0"),
        },
    )

    assert result == {
        "AAPL": Decimal("0"),
        "SPMO": Decimal("0"),
    }


def test_rejects_negative_available_target():
    strategy = CurrentWeightProportionalStrategy()

    with pytest.raises(ValueError, match="Available target cannot be negative"):
        strategy.allocate(
            Decimal("-0.01"),
            {"AAPL": Decimal("6000")},
        )