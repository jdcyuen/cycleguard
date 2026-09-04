from decimal import Decimal

from models.trade import Trade
from models.trade_plan import TradePlan


def test_trade_plan_creation():
    sell = Trade(
        symbol="SGOV",
        action="SELL",
        amount=Decimal("100.00"),
    )

    buy = Trade(
        symbol="FZROX",
        action="BUY",
        amount=Decimal("50.00"),
    )

    plan = TradePlan(
        deployment_amount=Decimal("100.00"),
        sells=(sell,),
        buys=(buy,),
        reason="Level 1",
    )

    assert plan.deployment_amount == Decimal("100.00")
    assert plan.sells == (sell,)
    assert plan.buys == (buy,)
    assert plan.reason == "Level 1"


def test_trade_plan_is_immutable():
    plan = TradePlan(
        deployment_amount=Decimal("100.00"),
        sells=(),
        buys=(),
        reason="Level 1",
    )

    try:
        plan.reason = "Level 2"
        assert False, "TradePlan should be immutable"
    except AttributeError:
        pass