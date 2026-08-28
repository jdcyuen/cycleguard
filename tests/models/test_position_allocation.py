from decimal import Decimal

from models.position_allocation import PositionAllocation


def test_position_allocation():
    allocation = PositionAllocation(
        symbol="FZROX",
        bucket="core_equity",
        market_value=Decimal("100000"),
        weight=Decimal("0.6666666666666666666666666667"),
    )

    assert allocation.symbol == "FZROX"
    assert allocation.bucket == "core_equity"
    assert allocation.market_value == Decimal("100000")
    assert allocation.weight == Decimal(
        "0.6666666666666666666666666667"
    )