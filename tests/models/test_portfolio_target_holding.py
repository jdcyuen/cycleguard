from decimal import Decimal

from models.portfolio_view import PortfolioTargetHolding


def test_portfolio_target_holding():
    target = PortfolioTargetHolding(
        symbol="FTEC",
        bucket="equity_growth",
        target_percentage=Decimal("15.0"),
        account_name="Roth IRA",
    )

    assert target.symbol == "FTEC"
    assert target.bucket == "equity_growth"
    assert target.target_percentage == Decimal("15.0")
    assert target.account_name == "Roth IRA"


def test_portfolio_target_holding_without_account_name():
    target = PortfolioTargetHolding(
        symbol="SOXX",
        bucket="equity_growth",
        target_percentage=Decimal("12.0"),
    )

    assert target.account_name is None