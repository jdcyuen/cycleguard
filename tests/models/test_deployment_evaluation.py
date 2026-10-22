from decimal import Decimal

from models.deployment_evaluation import DeploymentEvaluation


def test_deployment_evaluation_can_be_created():
    decision = DeploymentEvaluation(
        action="HOLD",
        deployment_pct=Decimal("0"),
        deployment_amount=Decimal("0"),
    )

    assert decision.action == "HOLD"
    assert decision.deployment_amount == Decimal("0")
    assert decision.deployment_pct == Decimal("0")