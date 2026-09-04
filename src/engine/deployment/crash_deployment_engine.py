from decimal import Decimal

from models.deployment import DeploymentDecision
from engine.deployment.base_deployment_engine import BaseDeploymentEngine


# CrashDeploymentEngine takes the drawdown calculated by CrashManager and 
# applies CycleGuard's crash-deployment policy.

class CrashDeploymentEngine(BaseDeploymentEngine):
    """
    CycleGuard crash deployment engine.
    """

    def _get_deployment_pct(self, regime: str) -> Decimal:
        """Return the configured deployment percentage for a regime."""
        return self.deployment_policy.get(
            regime,
            Decimal("0"),
        )

    def evaluate(
        self,
        drawdown: float,
        available_capital: Decimal,
    ) -> DeploymentDecision:

        """
        Evaluate a crash deployment decision based on drawdown.
        """

        if available_capital < Decimal("0"):
            raise ValueError("Available capital cannot be negative")

        level = None

        for level_name, level_config in sorted(
            self.deployment_policy["levels"].items(),
            key=lambda item: item[1]["drawdown"],
            reverse=False,
        ):
            if drawdown <= level_config["drawdown"]:
                level = level_name
                break
        
        if level is None:
            return DeploymentDecision(
                action="HOLD",
                deployment_pct=Decimal("0"),
                deployment_amount=Decimal("0"),
            )

        deployment_pct = Decimal(
            str(self.deployment_policy["levels"][level]["deploy_pct"])
        )

        deployment_amount = available_capital * deployment_pct

        return DeploymentDecision(
            action="DEPLOY",
            deployment_pct=deployment_pct,
            deployment_amount=deployment_amount,
        )