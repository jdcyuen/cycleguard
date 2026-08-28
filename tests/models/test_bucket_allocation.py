from decimal import Decimal

from models.bucket_allocation import BucketAllocation


def test_bucket_allocation():
    allocation = BucketAllocation(
        name="core_equity",
        market_value=Decimal("141300.38"),
        actual_weight=Decimal("0.1413"),
        target_weight=Decimal("0.20"),
        drift=Decimal("-0.0587"),
        drift_value=Decimal("-58700"),
    )

    assert allocation.name == "core_equity"
    assert allocation.market_value == Decimal("141300.38")
    assert allocation.actual_weight == Decimal("0.1413")
    assert allocation.target_weight == Decimal("0.20")
    assert allocation.drift == Decimal("-0.0587")
    assert allocation.drift_value == Decimal("-58700")