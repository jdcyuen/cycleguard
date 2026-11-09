from decimal import Decimal

from models.portfolio_view import (
    PortfolioBucketAllocation,
    PortfolioHolding,
    PortfolioTargetHolding,
)
from models.position import Position


def test_portfolio_bucket_allocation_with_actual_holding():
    position = Position(
        symbol="FZROX",
        current_value=Decimal("25000"),
        percent_of_account=Decimal("25.0"),
    )

    holding = PortfolioHolding(
        position=position,
        bucket="core_equity",
        account_name="Roth IRA",
    )

    allocation = PortfolioBucketAllocation(
        bucket="core_equity",
        percentage=Decimal("25.0"),
        market_value=Decimal("25000"),
        holdings=[holding],
    )

    assert allocation.bucket == "core_equity"
    assert allocation.percentage == Decimal("25.0")
    assert allocation.market_value == Decimal("25000")
    assert len(allocation.holdings) == 1
    assert allocation.holdings[0].position.symbol == "FZROX"
    assert allocation.target_holdings == []


def test_portfolio_bucket_allocation_with_target_holding():
    target = PortfolioTargetHolding(
        symbol="FTEC",
        bucket="equity_growth",
        target_percentage=Decimal("15.0"),
        account_name="Roth IRA",
    )

    allocation = PortfolioBucketAllocation(
        bucket="equity_growth",
        percentage=Decimal("40.0"),
        target_holdings=[target],
    )

    assert allocation.bucket == "equity_growth"
    assert allocation.percentage == Decimal("40.0")
    assert allocation.market_value is None
    assert allocation.holdings == []
    assert len(allocation.target_holdings) == 1
    assert allocation.target_holdings[0].symbol == "FTEC"


def test_portfolio_bucket_allocation_defaults_preserve_compatibility():
    allocation = PortfolioBucketAllocation(
        bucket="fixed_income",
        percentage=Decimal("0"),
    )

    assert allocation.market_value is None
    assert allocation.holdings == []
    assert allocation.target_holdings == []