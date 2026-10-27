from decimal import Decimal

import pytest

from engine.allocation.allocation_engine import AllocationEngine
from engine.allocation.current_weight_proportional_strategy import (
    CurrentWeightProportionalStrategy,
)
from models.account_config import PositionLimits


def test_classifies_explicit_and_dynamic_securities():
    engine = AllocationEngine(
        dynamic_allocation_strategy=CurrentWeightProportionalStrategy(),
    )

    explicit, dynamic = engine.classify_securities(
        ["FTEC", "AAPL", "SPMO"],
        {"FTEC": 0.07},
    )

    assert explicit == ["FTEC"]
    assert dynamic == ["AAPL", "SPMO"]


def test_returns_all_dynamic_when_no_explicit_targets():
    engine = AllocationEngine(
        dynamic_allocation_strategy=CurrentWeightProportionalStrategy(),
    )

    explicit, dynamic = engine.classify_securities(
        ["AAPL", "SPMO"],
        {},
    )

    assert explicit == []
    assert dynamic == ["AAPL", "SPMO"]


def test_returns_all_explicit_when_all_have_targets():
    engine = AllocationEngine(
        dynamic_allocation_strategy=CurrentWeightProportionalStrategy(),
    )

    explicit, dynamic = engine.classify_securities(
        ["FTEC", "AAPL"],
        {
            "FTEC": 0.07,
            "AAPL": 0.03,
        },
    )

    assert explicit == ["FTEC", "AAPL"]
    assert dynamic == []

def test_calculates_remaining_dynamic_target():
    engine = AllocationEngine(
        dynamic_allocation_strategy=CurrentWeightProportionalStrategy(),
    )

    result = engine.calculate_remaining_dynamic_target(
        bucket_target=Decimal("0.10"),
        explicit_targets={
            "FTEC": Decimal("0.07"),
        },
    )

    assert result == Decimal("0.03")


def test_returns_full_bucket_target_when_no_explicit_targets():
    engine = AllocationEngine(
        dynamic_allocation_strategy=CurrentWeightProportionalStrategy(),
    )

    result = engine.calculate_remaining_dynamic_target(
        bucket_target=Decimal("0.10"),
        explicit_targets={},
    )

    assert result == Decimal("0.10")


def test_rejects_explicit_targets_above_bucket_target():
    engine = AllocationEngine(
        dynamic_allocation_strategy=CurrentWeightProportionalStrategy(),
    )

    with pytest.raises(
        ValueError,
        match="Explicit security targets cannot exceed bucket target",
    ):
        engine.calculate_remaining_dynamic_target(
            bucket_target=Decimal("0.10"),
            explicit_targets={
                "FTEC": Decimal("0.07"),
                "AAPL": Decimal("0.05"),
            },
        )

def test_calculates_dynamic_targets_using_strategy():
    engine = AllocationEngine(
        dynamic_allocation_strategy=CurrentWeightProportionalStrategy(),
    )

    result = engine.calculate_dynamic_targets(
        bucket_target=Decimal("0.10"),
        explicit_targets={
            "FTEC": Decimal("0.07"),
        },
        dynamic_securities={
            "AAPL": Decimal("6000"),
            "SPMO": Decimal("4000"),
        },
    )

    assert result == {
        "AAPL": Decimal("0.018"),
        "SPMO": Decimal("0.012"),
    }

def test_dynamic_targets_exclude_explicit_targets():
    engine = AllocationEngine(
        dynamic_allocation_strategy=CurrentWeightProportionalStrategy(),
    )

    result = engine.calculate_dynamic_targets(
        bucket_target=Decimal("0.10"),
        explicit_targets={
            "FTEC": Decimal("0.07"),
        },
        dynamic_securities={
            "AAPL": Decimal("5000"),
            "SPMO": Decimal("5000"),
        },
    )

    assert result == {
        "AAPL": Decimal("0.015"),
        "SPMO": Decimal("0.015"),
    }

def test_evaluates_allocation():
    engine = AllocationEngine(
        dynamic_allocation_strategy=CurrentWeightProportionalStrategy(),
    )

    evaluation = engine.evaluate_allocation(
        top_level_targets={
            "equity": Decimal("0.50"),
            "income": Decimal("0.45"),
            "alternatives": Decimal("0.05"),
        },
        bucket_targets={
            "equity_growth": Decimal("0.10"),
        },
        bucket_target=Decimal("0.10"),
        explicit_security_targets={
            "FTEC": Decimal("0.07"),
        },
        dynamic_securities={
            "AAPL": Decimal("6000"),
            "SPMO": Decimal("4000"),
        },
    )

    assert evaluation.top_level_targets == {
        "equity": Decimal("0.50"),
        "income": Decimal("0.45"),
        "alternatives": Decimal("0.05"),
    }

    assert evaluation.bucket_targets == {
        "equity_growth": Decimal("0.10"),
    }

    assert evaluation.security_targets == {
        "FTEC": Decimal("0.07"),
        "AAPL": Decimal("0.018"),
        "SPMO": Decimal("0.012"),
    }

def test_calculates_security_differences():
    engine = AllocationEngine(
        dynamic_allocation_strategy=CurrentWeightProportionalStrategy(),
    )

    differences = engine.calculate_security_differences(
        actual_targets={
            "FTEC": Decimal("0.05"),
            "FZROX": Decimal("0.12"),
        },
        desired_targets={
            "FTEC": Decimal("0.07"),
            "FZROX": Decimal("0.10"),
        },
    )

    assert differences == {
        "FTEC": Decimal("0.02"),
        "FZROX": Decimal("-0.02"),
    }

def test_determines_allocation_status():
    engine = AllocationEngine(
        dynamic_allocation_strategy=CurrentWeightProportionalStrategy(),
    )

    assert (
        engine.determine_allocation_status(
            actual_target=Decimal("0.04"),
            desired_target=Decimal("0.10"),
            tolerance=Decimal("0.05"),
        )
        == "BUY"
    )

    assert (
        engine.determine_allocation_status(
            actual_target=Decimal("0.08"),
            desired_target=Decimal("0.10"),
            tolerance=Decimal("0.05"),
        )
        == "HOLD"
    )

    assert (
        engine.determine_allocation_status(
            actual_target=Decimal("0.16"),
            desired_target=Decimal("0.10"),
            tolerance=Decimal("0.05"),
        )
        == "TRIM"
    )

def test_calculates_security_action_amount():
    engine = AllocationEngine(
        dynamic_allocation_strategy=CurrentWeightProportionalStrategy(),
    )

    assert (
        engine.calculate_security_action_amount(
            symbol="FTEC",
            actual_target=Decimal("0.04"),
            desired_target=Decimal("0.10"),
            tolerance=Decimal("0.05"),
            portfolio_value=Decimal("1000000"),
        )
        == Decimal("10000")
    )

    assert (
        engine.calculate_security_action_amount(
            symbol="AAPL",
            actual_target=Decimal("0.16"),
            desired_target=Decimal("0.10"),
            tolerance=Decimal("0.05"),
            portfolio_value=Decimal("1000000"),
        )
        == Decimal("-10000")
    )

    assert (
        engine.calculate_security_action_amount(
            symbol="SPMO",
            actual_target=Decimal("0.08"),
            desired_target=Decimal("0.10"),
            tolerance=Decimal("0.05"),
            portfolio_value=Decimal("1000000"),
        )
        == Decimal("0")
    )

def test_rejects_invalid_allocation_target():
    engine = AllocationEngine(
        dynamic_allocation_strategy=CurrentWeightProportionalStrategy(),
    )

    with pytest.raises(ValueError, match="Actual target"):
        engine._validate_target(
            Decimal("1.10"),
            "Actual target",
        )


def test_rejects_negative_value():
    engine = AllocationEngine(
        dynamic_allocation_strategy=CurrentWeightProportionalStrategy(),
    )

    with pytest.raises(ValueError, match="Portfolio value"):
        engine._validate_non_negative(
            Decimal("-1000"),
            "Portfolio value",
        )

def test_allocates_deployment_proportionally_across_underweight_securities():
    engine = AllocationEngine(
        dynamic_allocation_strategy=CurrentWeightProportionalStrategy(),
    )

    result = engine.allocate_deployment(
        deployment_amount=Decimal("30000"),
        actual_targets={
            "FTEC": Decimal("0.05"),
            "SOXX": Decimal("0.02"),
            "SPMO": Decimal("0.01"),
        },
        desired_targets={
            "FTEC": Decimal("0.07"),
            "SOXX": Decimal("0.04"),
            "SPMO": Decimal("0.03"),
        },
        portfolio_value=Decimal("1000000"),
        eligible_securities=[
            "FTEC",
            "SOXX",
            "SPMO",
        ],
    )

    assert result == {
        "FTEC": Decimal("10000"),
        "SOXX": Decimal("10000"),
        "SPMO": Decimal("10000"),
    }

    assert sum(result.values(), Decimal("0")) == Decimal("30000")

def test_allocates_only_available_underweight_capacity():
    engine = AllocationEngine(
        dynamic_allocation_strategy=CurrentWeightProportionalStrategy(),
    )

    result = engine.allocate_deployment(
        deployment_amount=Decimal("30000"),
        actual_targets={
            "FTEC": Decimal("0.065"),
            "SOXX": Decimal("0.035"),
            "SPMO": Decimal("0.025"),
        },
        desired_targets={
            "FTEC": Decimal("0.07"),
            "SOXX": Decimal("0.04"),
            "SPMO": Decimal("0.03"),
        },
        portfolio_value=Decimal("1000000"),
        eligible_securities=[
            "FTEC",
            "SOXX",
            "SPMO",
        ],
    )

    assert result == {
        "FTEC": Decimal("5000"),
        "SOXX": Decimal("5000"),
        "SPMO": Decimal("5000"),
    }

    assert sum(result.values(), Decimal("0")) == Decimal("15000")

def test_position_limit_caps_deployment_at_account_default():
    engine = AllocationEngine(
        dynamic_allocation_strategy=CurrentWeightProportionalStrategy(),
    )

    result = engine.allocate_deployment(
        deployment_amount=Decimal("50000"),
        actual_targets={
            "FTEC": Decimal("0.08"),
        },
        desired_targets={
            "FTEC": Decimal("0.15"),
        },
        portfolio_value=Decimal("1000000"),
        eligible_securities=["FTEC"],
        position_limits=PositionLimits(
            max_position_pct=0.10,
            overrides={},
        ),
    )

    # FTEC is at 8%; the 10% cap permits only another $20,000.
    assert result == {
        "FTEC": Decimal("20000"),
    }

def test_position_limit_symbol_override_takes_precedence():
    engine = AllocationEngine(
        dynamic_allocation_strategy=CurrentWeightProportionalStrategy(),
    )

    result = engine.allocate_deployment(
        deployment_amount=Decimal("100000"),
        actual_targets={
            "FTEC": Decimal("0.08"),
        },
        desired_targets={
            "FTEC": Decimal("0.15"),
        },
        portfolio_value=Decimal("1000000"),
        eligible_securities=["FTEC"],
        position_limits=PositionLimits(
            max_position_pct=0.10,
            overrides={"FTEC": 0.20},
        ),
    )

    # The 20% FTEC override permits its full $70,000 target shortfall.
    assert result == {
        "FTEC": Decimal("70000"),
    }

def test_position_at_cap_receives_no_additional_deployment():
    engine = AllocationEngine(
        dynamic_allocation_strategy=CurrentWeightProportionalStrategy(),
    )

    result = engine.allocate_deployment(
        deployment_amount=Decimal("50000"),
        actual_targets={
            "FTEC": Decimal("0.10"),
        },
        desired_targets={
            "FTEC": Decimal("0.15"),
        },
        portfolio_value=Decimal("1000000"),
        eligible_securities=["FTEC"],
        position_limits=PositionLimits(
            max_position_pct=0.10,
            overrides={},
        ),
    )

    assert result == {}
