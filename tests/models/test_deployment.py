from decimal import Decimal

from models.deployment import DeploymentDecision


def test_deployment_decision_can_be_created():
    decision = DeploymentDecision(
        action="HOLD",
        deployment_pct=Decimal("0"),
        deployment_amount=Decimal("0"),
    )

    assert decision.action == "HOLD"
    assert decision.deployment_amount == Decimal("0")
    assert decision.deployment_pct == Decimal("0")