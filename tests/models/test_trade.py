from decimal import Decimal

from models.trade import Trade


def test_trade_creation():
    trade = Trade(
        symbol="FZROX",
        action="BUY",
        amount=Decimal("50.00"),
    )

    assert trade.symbol == "FZROX"
    assert trade.action == "BUY"
    assert trade.amount == Decimal("50.00")


def test_trade_is_immutable():
    trade = Trade(
        symbol="FZROX",
        action="BUY",
        amount=Decimal("50.00"),
    )

    try:
        trade.amount = Decimal("100.00")
        assert False, "Trade should be immutable"
    except AttributeError:
        pass