from decimal import Decimal

from models.portfolio_bucket import PortfolioBucket


def test_portfolio_bucket():
    bucket = PortfolioBucket(
        name="core_equity",
        market_value=Decimal("141300.38"),
        weight=Decimal("0.1413"),
    )

    assert bucket.name == "core_equity"
    assert bucket.market_value == Decimal("141300.38")
    assert bucket.weight == Decimal("0.1413")