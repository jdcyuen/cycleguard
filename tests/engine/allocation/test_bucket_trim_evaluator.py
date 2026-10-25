
import logging

import pytest
from decimal import Decimal

from models.bucket_allocation import BucketAllocation
from engine.allocation.bucket_trim_evaluator import (
    BucketTrimEvaluator,
)


def test_calculates_minimum_trim_to_upper_tolerance_boundary():
    evaluator = BucketTrimEvaluator()

    bucket = BucketAllocation(
        name="equity_growth",
        market_value=Decimal("150000"),
        actual_weight=Decimal("0.15"),
        target_weight=Decimal("0.12"),
        drift=Decimal("0.03"),
        drift_value=Decimal("30000"),
    )

    result = evaluator.calculate_trim_amount(
        bucket=bucket,
        portfolio_value=Decimal("1000000"),
        tolerance=Decimal("0.02"),
    )

    assert result == Decimal("10000")


def test_returns_zero_when_bucket_is_at_upper_tolerance_boundary():
    evaluator = BucketTrimEvaluator()

    bucket = BucketAllocation(
        name="equity_growth",
        market_value=Decimal("140000"),
        actual_weight=Decimal("0.14"),
        target_weight=Decimal("0.12"),
        drift=Decimal("0.02"),
        drift_value=Decimal("20000"),
    )

    result = evaluator.calculate_trim_amount(
        bucket=bucket,
        portfolio_value=Decimal("1000000"),
        tolerance=Decimal("0.02"),
    )

    assert result == Decimal("0")


def test_returns_zero_when_bucket_is_below_upper_tolerance_boundary():
    evaluator = BucketTrimEvaluator()

    bucket = BucketAllocation(
        name="equity_growth",
        market_value=Decimal("130000"),
        actual_weight=Decimal("0.13"),
        target_weight=Decimal("0.12"),
        drift=Decimal("0.01"),
        drift_value=Decimal("10000"),
    )

    result = evaluator.calculate_trim_amount(
        bucket=bucket,
        portfolio_value=Decimal("1000000"),
        tolerance=Decimal("0.02"),
    )

    assert result == Decimal("0")
	

@pytest.mark.parametrize(
    ("portfolio_value", "tolerance", "exception"),
    [
        (1000000, Decimal("0.02"), TypeError),
        (Decimal("1000000"), 0.02, TypeError),
        (Decimal("0"), Decimal("0.02"), ValueError),
        (Decimal("-1"), Decimal("0.02"), ValueError),
        (Decimal("1000000"), Decimal("-0.01"), ValueError),
        (Decimal("NaN"), Decimal("0.02"), ValueError),
        (Decimal("1000000"), Decimal("Infinity"), ValueError),
    ],
)
def test_rejects_invalid_inputs(
    portfolio_value,
    tolerance,
    exception,
):
    bucket = BucketAllocation(
        name="equity_growth",
        market_value=Decimal("150000"),
        actual_weight=Decimal("0.15"),
        target_weight=Decimal("0.12"),
        drift=Decimal("0.03"),
        drift_value=Decimal("30000"),
    )

    with pytest.raises(exception):
        BucketTrimEvaluator.calculate_trim_amount(
            bucket=bucket,
            portfolio_value=portfolio_value,
            tolerance=tolerance,
        )


def test_logs_warning_for_invalid_input(caplog):
    bucket = BucketAllocation(
        name="equity_growth",
        market_value=Decimal("150000"),
        actual_weight=Decimal("0.15"),
        target_weight=Decimal("0.12"),
        drift=Decimal("0.03"),
        drift_value=Decimal("30000"),
    )

    with caplog.at_level(
        logging.WARNING,
        logger="engine.allocation.bucket_trim_evaluator",
    ):
        with pytest.raises(ValueError):
            BucketTrimEvaluator.calculate_trim_amount(
                bucket=bucket,
                portfolio_value=Decimal("0"),
                tolerance=Decimal("0.02"),
            )

    assert "Invalid input to calculate_trim_amount" in caplog.text

