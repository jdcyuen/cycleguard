from decimal import Decimal

from models.portfolio_allocation_summary import PortfolioAllocationSummary


def test_portfolio_allocation_summary():
    allocation = PortfolioAllocationSummary(
        portfolio_value=Decimal("150000"),
        buckets={},
    )

    assert allocation.portfolio_value == Decimal("150000")
    assert allocation.buckets == {}