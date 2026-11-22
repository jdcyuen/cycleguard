from decimal import Decimal

import pytest

from engine.deployment.cash_deployment_policy import CashDeploymentPolicy


def test_approval_respects_required_reserve() -> None:
    policy: CashDeploymentPolicy = CashDeploymentPolicy(
        required_reserve=Decimal("50000"),
    )

    approved: Decimal = policy.approve(
        proposed_amount=Decimal("200000"),
        available_defensive_capital=Decimal("120000"),
    )

    assert approved == Decimal("70000")


def test_approval_is_zero_when_cash_is_below_required_reserve() -> None:
    policy: CashDeploymentPolicy = CashDeploymentPolicy(
        required_reserve=Decimal("50000"),
    )

    approved: Decimal = policy.approve(
        proposed_amount=Decimal("20000"),
        available_defensive_capital=Decimal("30000"),
    )

    assert approved == Decimal("0")


def test_approval_is_not_limited_by_portfolio_percentage() -> None:
    policy: CashDeploymentPolicy = CashDeploymentPolicy(
        required_reserve=Decimal("10000"),
    )

    approved: Decimal = policy.approve(
        proposed_amount=Decimal("300000"),
        available_defensive_capital=Decimal("500000"),
    )

    assert approved == Decimal("300000")


def test_approval_does_not_exceed_proposed_amount() -> None:
    policy: CashDeploymentPolicy = CashDeploymentPolicy(
        required_reserve=Decimal("10000"),
    )

    approved: Decimal = policy.approve(
        proposed_amount=Decimal("50000"),
        available_defensive_capital=Decimal("500000"),
    )

    assert approved == Decimal("50000")


def test_approval_rejects_negative_proposed_amount() -> None:
    policy: CashDeploymentPolicy = CashDeploymentPolicy(
        required_reserve=Decimal("50000"),
    )

    with pytest.raises(
        ValueError,
        match="proposed_amount cannot be negative",
    ):
        policy.approve(
            proposed_amount=Decimal("-1000"),
            available_defensive_capital=Decimal("100000"),
        )


def test_approval_rejects_non_finite_proposed_amount() -> None:
    policy: CashDeploymentPolicy = CashDeploymentPolicy(
        required_reserve=Decimal("50000"),
    )

    with pytest.raises(
        ValueError,
        match="proposed_amount must be finite",
    ):
        policy.approve(
            proposed_amount=Decimal("NaN"),
            available_defensive_capital=Decimal("100000"),
        )


def test_approval_rejects_non_decimal_proposed_amount() -> None:
    policy: CashDeploymentPolicy = CashDeploymentPolicy(
        required_reserve=Decimal("50000"),
    )

    with pytest.raises(
        TypeError,
        match="proposed_amount must be a Decimal",
    ):
        policy.approve(
            proposed_amount=1000,  # type: ignore[arg-type]
            available_defensive_capital=Decimal("100000"),
        )