from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from models.bucket_allocation import BucketAllocation
from services.bucket_trim_proposal_service import (
    BucketTrimProposalService,
)


def make_bucket(name, actual_weight, target_weight):
    return BucketAllocation(
        name=name,
        market_value=Decimal("150000"),
        actual_weight=Decimal(actual_weight),
        target_weight=Decimal(target_weight),
        drift=Decimal(actual_weight) - Decimal(target_weight),
        drift_value=Decimal("30000"),
    )


def make_service(
    buckets=None,
    portfolio_value=Decimal("1000000"),
    bucket_tolerance=Decimal("0.02"),
    evaluator=None,
):
    portfolio_service = MagicMock()
    portfolio_service.get_portfolio_value.return_value = portfolio_value
    portfolio_service.get_bucket_allocation.return_value = (
        buckets if buckets is not None else {}
    )

    account = SimpleNamespace(
        name="test_account",
        bucket_tolerance=bucket_tolerance,
    )

    service = BucketTrimProposalService(
        portfolio_service=portfolio_service,
        account=account,
        trim_evaluator=evaluator,
    )

    return service, portfolio_service


def test_creates_proposal_for_overweight_bucket():
    bucket = make_bucket("equity_growth", "0.15", "0.12")
    service, _ = make_service(buckets={"equity_growth": bucket})

    proposals = service.evaluate(snapshot_id=1)

    assert len(proposals) == 1
    proposal = proposals[0]
    assert proposal.bucket_name == "equity_growth"
    assert proposal.actual_weight == Decimal("0.15")
    assert proposal.target_weight == Decimal("0.12")
    assert proposal.upper_boundary == Decimal("0.14")
    assert proposal.trim_amount == Decimal("10000")


@pytest.mark.parametrize("actual_weight", ["0.14", "0.13"])
def test_does_not_propose_trim_at_or_below_boundary(actual_weight):
    bucket = make_bucket("equity_growth", actual_weight, "0.12")
    service, _ = make_service(buckets={"equity_growth": bucket})

    assert service.evaluate(snapshot_id=1) == []


def test_proposes_only_overweight_buckets_in_alphabetical_order():
    buckets = {
        "high_beta": make_bucket("high_beta", "0.15", "0.10"),
        "core_equity": make_bucket("core_equity", "0.20", "0.20"),
        "equity_growth": make_bucket(
            "equity_growth", "0.15", "0.12"
        ),
    }
    service, _ = make_service(buckets=buckets)

    proposals = service.evaluate(snapshot_id=1)

    assert [p.bucket_name for p in proposals] == [
        "equity_growth",
        "high_beta",
    ]
    assert [p.trim_amount for p in proposals] == [
        Decimal("10000"),
        Decimal("30000"),
    ]


@pytest.mark.parametrize("snapshot_id", [0, -1, True, 1.5, "1", None])
def test_rejects_invalid_snapshot_id(snapshot_id):
    service, portfolio_service = make_service()

    with pytest.raises(ValueError):
        service.evaluate(snapshot_id=snapshot_id)

    portfolio_service.get_portfolio_value.assert_not_called()


@pytest.mark.parametrize(
    "portfolio_value",
    [
        Decimal("0"),
        Decimal("-1"),
        Decimal("NaN"),
        Decimal("Infinity"),
        1000000,
    ],
)
def test_rejects_invalid_portfolio_value(portfolio_value):
    service, _ = make_service(portfolio_value=portfolio_value)

    expected_exception = (
        TypeError
        if not isinstance(portfolio_value, Decimal)
        else ValueError
    )

    with pytest.raises(expected_exception):
        service.evaluate(snapshot_id=1)


@pytest.mark.parametrize(
    "bucket_tolerance",
    [
        Decimal("-0.01"),
        Decimal("1.01"),
        Decimal("NaN"),
        Decimal("Infinity"),
        None,
    ],
)
def test_rejects_invalid_bucket_tolerance(bucket_tolerance):
    service, portfolio_service = make_service(
        bucket_tolerance=bucket_tolerance
    )

    with pytest.raises(ValueError):
        service.evaluate(snapshot_id=1)

    portfolio_service.get_bucket_allocation.assert_not_called()


def test_propagates_evaluator_failure():
    bucket = make_bucket("equity_growth", "0.15", "0.12")
    evaluator = MagicMock()
    evaluator.calculate_trim_amount.side_effect = ValueError(
        "Invalid bucket"
    )
    service, _ = make_service(
        buckets={"equity_growth": bucket},
        evaluator=evaluator,
    )

    with pytest.raises(ValueError, match="Invalid bucket"):
        service.evaluate(snapshot_id=1)
