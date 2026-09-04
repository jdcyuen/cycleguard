import pytest
from decimal import Decimal

from engine.deployment.regime_deployment_engine import RegimeDeploymentEngine
from models.deployment import DeploymentDecision

def test_deployment_engine_returns_deployment_decision():

    engine = RegimeDeploymentEngine(
        {
            "TRANSITION": Decimal("0"),
        }
    )

    regime_result = {
        "signals": {},
        "regime": "TRANSITION",
    }

    decision = engine.evaluate(
        regime_result,
        Decimal("10000"),
    )

    assert isinstance(decision, DeploymentDecision)
    assert decision.action == "HOLD"
    assert decision.deployment_amount == Decimal("0")


def test_deployment_engine_deploys_when_regime_is_risk_on():
    engine = RegimeDeploymentEngine(
        {
            "RISK_ON": Decimal("1.00"),
        }
    )

    regime_result = {
        "signals": {},
        "regime": "RISK_ON",
    }

    decision = engine.evaluate(
        regime_result,
        Decimal("10000"),
    )

    assert decision.action == "DEPLOY"
    assert decision.deployment_amount == Decimal("10000")
    assert decision.deployment_pct == Decimal("1.0")


def test_deployment_engine_holds_when_regime_is_risk_off():

    engine = RegimeDeploymentEngine(
        {
            "RISK_OFF": Decimal("0"),
        }
    )

    regime_result = {
        "signals": {},
        "regime": "RISK_OFF",
    }

    decision = engine.evaluate(
        regime_result,
        Decimal("10000"),
    )

    assert decision.action == "HOLD"
    assert decision.deployment_amount == Decimal("0")
    assert decision.deployment_pct == Decimal("0")

def test_deployment_engine_supports_partial_deployment():
    engine = RegimeDeploymentEngine(
        {
            "RISK_ON": Decimal("0.50"),
        }
    )

    regime_result = {
        "signals": {},
        "regime": "RISK_ON",
    }

    decision = engine.evaluate(
        regime_result,
        Decimal("10000"),
    )

    assert decision.action == "DEPLOY"
    assert decision.deployment_pct == Decimal("0.50")
    assert decision.deployment_amount == Decimal("5000")

def test_deployment_engine_calculates_fractional_deployment():
    engine = RegimeDeploymentEngine(
        {
            "RISK_ON": Decimal("0.3333"),
        }
    )

    regime_result = {
        "signals": {},
        "regime": "RISK_ON",
    }

    decision = engine.evaluate(
        regime_result,
        Decimal("10000"),
    )

    assert decision.action == "DEPLOY"
    assert decision.deployment_pct == Decimal("0.3333")
    assert decision.deployment_amount == Decimal("3333.0000")

def test_deployment_engine_rejects_deployment_pct_above_one():
    with pytest.raises(
        ValueError,
        match="Deployment percentage cannot exceed 100%",
    ):
        RegimeDeploymentEngine(
            {
                "RISK_ON": Decimal("1.50"),
            }
        )

def test_deployment_engine_rejects_negative_deployment_pct():
    with pytest.raises(
        ValueError,
        match="Deployment percentage cannot be negative",
    ):
        RegimeDeploymentEngine(
            {
                "RISK_ON": Decimal("-0.10"),
            }
        )

def test_deployment_engine_rejects_negative_available_capital():
    engine = RegimeDeploymentEngine(
        {
            "RISK_ON": Decimal("0.50"),
        }
    )

    regime_result = {
        "signals": {},
        "regime": "RISK_ON",
    }

    with pytest.raises(
        ValueError,
        match="Available capital cannot be negative",
    ):
        engine.evaluate(
            regime_result,
            Decimal("-10000"),
        )

def test_deployment_engine_allows_zero_percent_deployment():
    engine = RegimeDeploymentEngine(
        {
            "RISK_ON": Decimal("0"),
        }
    )

    regime_result = {
        "signals": {},
        "regime": "RISK_ON",
    }

    decision = engine.evaluate(
        regime_result,
        Decimal("10000"),
    )

    assert decision.action == "DEPLOY"
    assert decision.deployment_pct == Decimal("0")
    assert decision.deployment_amount == Decimal("0")

def test_deployment_engine_allows_100_percent_deployment():
    engine = RegimeDeploymentEngine(
        {
            "RISK_ON": Decimal("1.00"),
        }
    )

    regime_result = {
        "signals": {},
        "regime": "RISK_ON",
    }

    decision = engine.evaluate(
        regime_result,
        Decimal("10000"),
    )

    assert decision.action == "DEPLOY"
    assert decision.deployment_pct == Decimal("1.00")
    assert decision.deployment_amount == Decimal("10000")

def test_deployment_engine_rejects_missing_regime():
    engine = RegimeDeploymentEngine()

    regime_result = {
        "signals": {},
    }

    with pytest.raises(
        ValueError,
        match="Regime result must contain a regime",
    ):
        engine.evaluate(
            regime_result,
            Decimal("10000"),
        )

def test_deployment_engine_rejects_non_dict_regime_result():
    engine = RegimeDeploymentEngine()

    with pytest.raises(
        ValueError,
        match="Regime result must be a dictionary",
    ):
        engine.evaluate(
            None,
            Decimal("10000"),
        )

def test_deployment_engine_accepts_regime_deployment_policy():
    deployment_policy = {
        "RISK_ON": Decimal("1.00"),
        "TRANSITION": Decimal("0.50"),
        "RISK_OFF": Decimal("0.00"),
    }

    engine = RegimeDeploymentEngine(deployment_policy)

    assert engine.deployment_policy == deployment_policy

def test_deployment_engine_gets_deployment_pct_for_regime():
    deployment_policy = {
        "RISK_ON": Decimal("1.00"),
        "TRANSITION": Decimal("0.50"),
        "RISK_OFF": Decimal("0.00"),
    }

    engine = RegimeDeploymentEngine(deployment_policy)

    assert engine._get_deployment_pct("RISK_ON") == Decimal("1.00")
    assert engine._get_deployment_pct("TRANSITION") == Decimal("0.50")
    assert engine._get_deployment_pct("RISK_OFF") == Decimal("0.00")

def test_deployment_engine_defaults_to_zero_for_unknown_regime():
    engine = RegimeDeploymentEngine(
        {
            "RISK_ON": Decimal("1.00"),
            "TRANSITION": Decimal("0.50"),
            "RISK_OFF": Decimal("0.00"),
        }
    )

    assert engine._get_deployment_pct("UNKNOWN") == Decimal("0")

def test_deployment_engine_defaults_to_zero_for_unknown_regime():
    engine = RegimeDeploymentEngine(
        {
            "RISK_ON": Decimal("1.00"),
            "TRANSITION": Decimal("0.50"),
            "RISK_OFF": Decimal("0.00"),
        }
    )

    assert engine._get_deployment_pct("UNKNOWN") == Decimal("0")

def test_deployment_engine_partially_deploys_in_transition():
    engine = RegimeDeploymentEngine(
        {
            "RISK_ON": Decimal("1.00"),
            "TRANSITION": Decimal("0.50"),
            "RISK_OFF": Decimal("0.00"),
        }
    )

    regime_result = {
        "signals": {},
        "regime": "TRANSITION",
    }

    decision = engine.evaluate(
        regime_result,
        Decimal("10000"),
    )

    assert decision.action == "DEPLOY"
    assert decision.deployment_pct == Decimal("0.50")
    assert decision.deployment_amount == Decimal("5000")

def test_deployment_engine_holds_for_unknown_regime():
    engine = RegimeDeploymentEngine(
        {
            "RISK_ON": Decimal("1.00"),
            "TRANSITION": Decimal("0.50"),
            "RISK_OFF": Decimal("0.00"),
        }
    )

    regime_result = {
        "signals": {},
        "regime": "UNKNOWN",
    }

    decision = engine.evaluate(
        regime_result,
        Decimal("10000"),
    )

    assert decision.action == "HOLD"
    assert decision.deployment_pct == Decimal("0")
    assert decision.deployment_amount == Decimal("0")