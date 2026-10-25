from decimal import Decimal

from models.deployment_evaluation import DeploymentEvaluation
from engine.deployment.base_deployment_engine import BaseDeploymentEngine


# CrashDeploymentEngine takes the drawdown calculated by CrashManager and 
# applies CycleGuard's crash-deployment policy.
#	1. Reads configured crash drawdown levels.
#	2. Selects a matching level based on the drawdown.
#	3. Calculates the proposed deployment as available_capital × deploy_pct.
#	4. Returns a DeploymentEvaluation with source="crash".
#	5. Returns HOLD when no configured level matches.


class CrashDeploymentEngine(BaseDeploymentEngine):
    """
    CycleGuard crash deployment engine.
    """

    def evaluate(
        self,
        drawdown: float,
        available_capital: Decimal,
    ) -> DeploymentEvaluation:

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
            return DeploymentEvaluation(
                action="HOLD",
                deployment_pct=Decimal("0"),
                deployment_amount=Decimal("0"),
				source="crash",
            )

        deployment_pct = Decimal(
            str(self.deployment_policy["levels"][level]["deploy_pct"])
        )

        deployment_amount = available_capital * deployment_pct

        return DeploymentEvaluation(
            action="DEPLOY",
            deployment_pct=deployment_pct,
            deployment_amount=deployment_amount,
			source="crash",
        )