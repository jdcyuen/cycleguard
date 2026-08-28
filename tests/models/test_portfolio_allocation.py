from decimal import Decimal

from models.portfolio_allocation import PortfolioAllocation


def test_portfolio_allocation():
    allocation = PortfolioAllocation(
        portfolio_value=Decimal("150000"),
        buckets={},
    )

    assert allocation.portfolio_value == Decimal("150000")
    assert allocation.buckets == {}