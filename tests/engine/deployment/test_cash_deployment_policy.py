
import pytest
from decimal import Decimal

from engine.deployment.cash_deployment_policy import CashDeploymentPolicy


def test_approval_respects_reserve_and_event_cap():
    policy = CashDeploymentPolicy(
        required_reserve=Decimal("50000"),
        max_deployment_per_event=Decimal("0.15"),
    )

    approved = policy.approve(
        proposed_amount=Decimal("200000"),
        available_defensive_capital=Decimal("120000"),
        portfolio_value=Decimal("1000000"),
    )

    assert approved == Decimal("70000")


def test_approval_is_zero_when_cash_is_below_required_reserve():
    policy = CashDeploymentPolicy(
        required_reserve=Decimal("50000"),
        max_deployment_per_event=Decimal("0.15"),
    )

    approved = policy.approve(
        proposed_amount=Decimal("20000"),
        available_defensive_capital=Decimal("30000"),
        portfolio_value=Decimal("1000000"),
    )

    assert approved == Decimal("0")


def test_approval_is_limited_by_event_cap():
    policy = CashDeploymentPolicy(
        required_reserve=Decimal("10000"),
        max_deployment_per_event=Decimal("0.15"),
    )

    approved = policy.approve(
        proposed_amount=Decimal("300000"),
        available_defensive_capital=Decimal("500000"),
        portfolio_value=Decimal("1000000"),
    )

    assert approved == Decimal("150000")


def test_approval_rejects_negative_proposed_amount():
    policy = CashDeploymentPolicy(
        required_reserve=Decimal("50000"),
        max_deployment_per_event=Decimal("0.15"),
    )

    with pytest.raises(ValueError, match="proposed_amount cannot be negative"):
        policy.approve(
            proposed_amount=Decimal("-1000"),
            available_defensive_capital=Decimal("100000"),
            portfolio_value=Decimal("1000000"),
        )


def test_approval_rejects_non_finite_proposed_amount():
    policy = CashDeploymentPolicy(
        required_reserve=Decimal("50000"),
        max_deployment_per_event=Decimal("0.15"),
    )

    with pytest.raises(ValueError, match="proposed_amount must be a finite Decimal"):
        policy.approve(
            proposed_amount=Decimal("NaN"),
            available_defensive_capital=Decimal("100000"),
            portfolio_value=Decimal("1000000"),
        )
