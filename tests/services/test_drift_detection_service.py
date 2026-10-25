
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from models.bucket_allocation import BucketAllocation
from models.position import Position
from services.drift_detection_service import DriftDetectionService


def make_position(symbol, current_value):
    return Position(
        symbol=symbol,
        current_value=Decimal(current_value),
    )


def make_bucket(name, market_value, actual_weight, target_weight):
    actual = Decimal(actual_weight)
    target = Decimal(target_weight)

    return BucketAllocation(
        name=name,
        market_value=Decimal(market_value),
        actual_weight=actual,
        target_weight=target,
        drift=actual - target,
        drift_value=(actual - target) * Decimal("1000000"),
    )


def make_service(
    positions=None,
    buckets=None,
    portfolio_value=Decimal("1000000"),
    security_targets=None,
    bucket_mapping=None,
    position_tolerance=Decimal("0.05"),
    bucket_tolerance=Decimal("0.02"),
    trim_proposals=None,
):
    portfolio_service = MagicMock()
    portfolio_service.get_positions.return_value = (
        positions if positions is not None else []
    )
    portfolio_service.get_bucket_allocation.return_value = (
        buckets if buckets is not None else {}
    )
    portfolio_service.get_portfolio_value.return_value = portfolio_value

    account = SimpleNamespace(
        security_targets=(
            security_targets if security_targets is not None else {}
        ),
        bucket_mapping=(
            bucket_mapping if bucket_mapping is not None else {}
        ),
        tolerance=position_tolerance,
        bucket_tolerance=bucket_tolerance,
        config_path="test_account.yaml",
    )

    trim_service = MagicMock()
    trim_service.evaluate.return_value = (
        trim_proposals if trim_proposals is not None else []
    )

    service = DriftDetectionService(
        portfolio_service=portfolio_service,
        account=account,
        bucket_trim_service=trim_service,
    )

    return service, portfolio_service, trim_service


def test_calculates_overweight_position_drift():
    service, _, _ = make_service(
        positions=[make_position("FTEC", "100000")],
        security_targets={"FTEC": "0.05"},
        bucket_mapping={"FTEC": "equity_growth"},
		position_tolerance=Decimal("0.02"),
    )

    rows = service.evaluate(snapshot_id=1)

    position = next(row for row in rows if row["Row Type"] == "Position")

    assert position["Actual %"] == Decimal("0.1")
    assert position["Target %"] == Decimal("0.05")
    assert position["Drift %"] == Decimal("0.05")
    assert position["Drift $"] == Decimal("50000")
    assert position["Status"] == "Overweight"


def test_position_without_target_is_not_assigned_drift():
    service, _, _ = make_service(
        positions=[make_position("FTEC", "100000")],
        bucket_mapping={"FTEC": "equity_growth"},
    )

    rows = service.evaluate(snapshot_id=1)

    position = next(row for row in rows if row["Row Type"] == "Position")

    assert position["Target %"] is None
    assert position["Drift %"] is None
    assert position["Drift $"] is None
    assert position["Status"] == "No target configured"
    assert position["Proposed Action"] is None
    assert position["Proposed Amount"] is None


def test_bucket_trim_proposal_appears_only_on_bucket_row():
    bucket = make_bucket(
        "equity_growth",
        "150000",
        "0.15",
        "0.12",
    )
    proposal = SimpleNamespace(
        bucket_name="equity_growth",
        trim_amount=Decimal("10000"),
    )

    service, _, trim_service = make_service(
        positions=[make_position("FTEC", "150000")],
        buckets={"equity_growth": bucket},
        security_targets={"FTEC": "0.15"},
        bucket_mapping={"FTEC": "equity_growth"},
        trim_proposals=[proposal],
    )

    rows = service.evaluate(snapshot_id=1)

    position_rows = [
        row for row in rows if row["Row Type"] == "Position"
    ]
    bucket_rows = [
        row for row in rows if row["Row Type"] == "Bucket"
    ]

    assert len(position_rows) == 1
    assert len(bucket_rows) == 1
    assert position_rows[0]["Proposed Amount"] is None
    assert bucket_rows[0]["Proposed Action"] == "Trim bucket"
    assert bucket_rows[0]["Proposed Amount"] == Decimal("10000")
    trim_service.evaluate.assert_called_once_with(1)


@pytest.mark.parametrize(
    "snapshot_id",
    [0, -1, True, 1.5, "1", None],
)
def test_rejects_invalid_snapshot_id(snapshot_id):
    service, portfolio_service, trim_service = make_service()

    with pytest.raises(ValueError, match="snapshot_id"):
        service.evaluate(snapshot_id=snapshot_id)

    portfolio_service.get_positions.assert_not_called()
    trim_service.evaluate.assert_not_called()


def test_rejects_non_positive_portfolio_value():
    service, _, _ = make_service(
        portfolio_value=Decimal("0"),
    )

    with pytest.raises(ValueError, match="Portfolio value"):
        service.evaluate(snapshot_id=1)


def test_missing_bucket_mapping_raises_actionable_error():
    service, _, trim_service = make_service(
        positions=[make_position("FTEC", "100000")],
        bucket_mapping={},
    )

    with pytest.raises(ValueError, match="FTEC"):
        service.evaluate(snapshot_id=1)

    trim_service.evaluate.assert_not_called()


def test_unexpected_dependency_failure_is_logged_and_reraised(caplog):
    service, portfolio_service, _ = make_service()
    portfolio_service.get_positions.side_effect = RuntimeError(
        "test repository failure"
    )

    with caplog.at_level("ERROR"):
        with pytest.raises(
            RuntimeError,
            match="test repository failure",
        ):
            service.evaluate(snapshot_id=1)

    assert "Unexpected drift evaluation failure" in caplog.text
