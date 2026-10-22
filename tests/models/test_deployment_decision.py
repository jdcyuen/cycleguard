from decimal import Decimal

from models.deployment_decision import DeploymentDecision

def test_deployment_decision_can_be_created():
    decision = DeploymentDecision(
        deployment_decision_id=1,
        account_number="123456789",
        recommended_amount=Decimal("25000"),
        reason="Favorable market regime and excess defensive allocation.",
        )

    assert decision.deployment_decision_id == 1
    assert decision.account_number == "123456789"
    assert decision.recommended_amount == Decimal("25000")
    assert decision.reason == "Favorable market regime and excess defensive allocation."
