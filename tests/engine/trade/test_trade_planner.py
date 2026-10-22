import pytest
from decimal import Decimal

from models.trade_plan import TradePlan
from engine.trade.trade_planner import TradePlanner


def test_creates_trade_plan_with_buy():
    planner = TradePlanner()

    plan = planner.create_plan(
        deployment_amount=Decimal("100.00"),
        buys={
            "FZROX": Decimal("100.00"),
        },
        sells={},
        reason="Level 1",
    )

    assert isinstance(plan, TradePlan)
    assert plan.deployment_amount == Decimal("100.00")
    assert plan.buys[0].symbol == "FZROX"
    assert plan.buys[0].action == "BUY"
    assert plan.buys[0].amount == Decimal("100.00")
    assert plan.sells == ()
    assert plan.reason == "Level 1"

def test_creates_trade_plan_with_sell():
    planner = TradePlanner()

    plan = planner.create_plan(
        deployment_amount=Decimal("100.00"),
        buys={},
        sells={
            "SGOV": Decimal("100.00"),
        },
        reason="Level 1",
    )

    assert plan.sells[0].symbol == "SGOV"
    assert plan.sells[0].action == "SELL"
    assert plan.sells[0].amount == Decimal("100.00")
    assert plan.buys == ()

def test_rejects_negative_deployment_amount():
    planner = TradePlanner()

    with pytest.raises(ValueError, match="Invalid trade plan inputs"):
        planner.create_plan(
            deployment_amount=Decimal("-100.00"),
            buys={},
            sells={},
            reason="Level 1",
        )

def test_rejects_non_dictionary_buys():
    planner = TradePlanner()

    with pytest.raises(ValueError, match="Invalid trade plan inputs"):
        planner.create_plan(
            deployment_amount=Decimal("100.00"),
            buys=[],
            sells={},
            reason="Level 1",
        )

def test_rejects_non_dictionary_sells():
    planner = TradePlanner()

    with pytest.raises(ValueError, match="Invalid trade plan inputs"):
        planner.create_plan(
            deployment_amount=Decimal("100.00"),
            buys={},
            sells=[],
            reason="Level 1",
        )

def test_rejects_non_string_reason():
    planner = TradePlanner()

    with pytest.raises(ValueError, match="Invalid trade plan inputs"):
        planner.create_plan(
            deployment_amount=Decimal("100.00"),
            buys={},
            sells={},
            reason=None,
        )

def test_rejects_negative_trade_amount():
    planner = TradePlanner()

    with pytest.raises(ValueError, match="Invalid trade plan inputs"):
        planner.create_plan(
            deployment_amount=Decimal("100.00"),
            buys={"FZROX": Decimal("-50.00")},
            sells={},
            reason="Level 1",
        )

def test_rejects_zero_trade_amount():
    planner = TradePlanner()

    with pytest.raises(ValueError, match="Invalid trade plan inputs"):
        planner.create_plan(
            deployment_amount=Decimal("100.00"),
            buys={"FZROX": Decimal("0")},
            sells={},
            reason="Level 1",
        )

def test_rejects_empty_trade_symbol():
    planner = TradePlanner()

    with pytest.raises(ValueError, match="Invalid trade plan inputs"):
        planner.create_plan(
            deployment_amount=Decimal("100.00"),
            buys={"": Decimal("100.00")},
            sells={},
            reason="Level 1",
        )

def test_rejects_whitespace_trade_symbol():
    planner = TradePlanner()

    with pytest.raises(ValueError, match="Invalid trade plan inputs"):
        planner.create_plan(
            deployment_amount=Decimal("100.00"),
            buys={"   ": Decimal("100.00")},
            sells={},
            reason="Level 1",
        )

def test_rejects_buy_and_sell_for_same_symbol():
    planner = TradePlanner()

    with pytest.raises(ValueError, match="Invalid trade plan inputs"):
        planner.create_plan(
            deployment_amount=Decimal("100.00"),
            buys={"FZROX": Decimal("100.00")},
            sells={"FZROX": Decimal("50.00")},
            reason="Level 1",
        )

def test_rejects_buy_total_different_from_deployment_amount():
    planner = TradePlanner()

    with pytest.raises(ValueError, match="Invalid trade plan inputs"):
        planner.create_plan(
            deployment_amount=Decimal("100.00"),
            buys={
                "FZROX": Decimal("75.00"),
            },
            sells={},
            reason="Level 1",
        )

def test_creates_trade_plan_with_sells_and_buys():
    planner = TradePlanner()

    plan = planner.create_plan(
        deployment_amount=Decimal("100.00"),
        buys={
            "FZROX": Decimal("100.00"),
        },
        sells={
            "SGOV": Decimal("50.00"),
        },
        reason="Level 1",
    )

    assert plan.deployment_amount == Decimal("100.00")
    assert plan.buys[0].symbol == "FZROX"
    assert plan.buys[0].amount == Decimal("100.00")
    assert plan.sells[0].symbol == "SGOV"
    assert plan.sells[0].amount == Decimal("50.00")

def test_rejects_zero_deployment_amount_with_buys():
    planner = TradePlanner()

    with pytest.raises(ValueError, match="Invalid trade plan inputs"):
        planner.create_plan(
            deployment_amount=Decimal("0"),
            buys={
                "FZROX": Decimal("100.00"),
            },
            sells={},
            reason="Level 1",
        )

def test_rejects_empty_reason():
    planner = TradePlanner()

    with pytest.raises(ValueError, match="Invalid trade plan inputs"):
        planner.create_plan(
            deployment_amount=Decimal("100.00"),
            buys={
                "FZROX": Decimal("100.00"),
            },
            sells={},
            reason="",
        )

def test_creates_trade_plan_with_multiple_buys_and_sells():
    planner = TradePlanner()

    plan = planner.create_plan(
        deployment_amount=Decimal("300.00"),
        buys={
            "FZROX": Decimal("100.00"),
            "FTEC": Decimal("200.00"),
        },
        sells={
            "SGOV": Decimal("50.00"),
            "BINC": Decimal("75.00"),
        },
        reason="Level 1 deployment",
    )

    assert len(plan.buys) == 2
    assert len(plan.sells) == 2

    assert plan.buys[0].symbol == "FZROX"
    assert plan.buys[0].amount == Decimal("100.00")
    assert plan.buys[1].symbol == "FTEC"
    assert plan.buys[1].amount == Decimal("200.00")

    assert plan.sells[0].symbol == "SGOV"
    assert plan.sells[0].amount == Decimal("50.00")
    assert plan.sells[1].symbol == "BINC"
    assert plan.sells[1].amount == Decimal("75.00")

def test_trade_plan_assigns_correct_trade_actions():
    planner = TradePlanner()

    plan = planner.create_plan(
        deployment_amount=Decimal("100.00"),
        buys={"FZROX": Decimal("100.00")},
        sells={"SGOV": Decimal("50.00")},
        reason="Level 1 deployment",
    )

    assert plan.buys[0].action == "BUY"
    assert plan.sells[0].action == "SELL"

def test_creates_sell_only_plan_with_zero_deployment():
    planner = TradePlanner()

    plan = planner.create_plan(
        deployment_amount=Decimal("0"),
        buys={},
        sells={
            "SGOV": Decimal("50.00"),
        },
        reason="Raise cash",
    )

    assert plan.deployment_amount == Decimal("0")
    assert len(plan.buys) == 0
    assert len(plan.sells) == 1
    assert plan.sells[0].symbol == "SGOV"
    assert plan.sells[0].action == "SELL"
    assert plan.sells[0].amount == Decimal("50.00")

def test_creates_empty_trade_plan_with_zero_deployment():
    planner = TradePlanner()

    plan = planner.create_plan(
        deployment_amount=Decimal("0"),
        buys={},
        sells={},
        reason="No trades required",
    )

    assert plan.deployment_amount == Decimal("0")
    assert plan.buys == ()
    assert plan.sells == ()
    assert plan.reason == "No trades required"

def test_rejects_non_finite_deployment_amount():
    planner = TradePlanner()

    with pytest.raises(ValueError, match="Invalid trade plan inputs"):
        planner.create_plan(
            deployment_amount=Decimal("NaN"),
            buys={},
            sells={},
            reason="Invalid deployment",
        )
