from decimal import Decimal

from engine.deployment.base_deployment_engine import BaseDeploymentEngine
from models.deployment_evaluation import DeploymentEvaluation
from engine.deployment.regime_based_sizing_strategy import (
    RegimeBasedSizingStrategy,
)


class RegimeDeploymentEngine(BaseDeploymentEngine):
    """
    Determines portfolio deployment based on the current market regime.

    This engine does not detect the regime and does not calculate
    available capital. It consumes those results and produces a
    DeploymentEvaluation.
    """

    def __init__(
        self, 
        deployment_policy=None,
        sizing_strategy=None,
    ):
        self.deployment_policy = deployment_policy or {}
        self.sizing_strategy = (
            sizing_strategy
            or RegimeBasedSizingStrategy(self.deployment_policy)
        )

        for regime, deployment_pct in self.deployment_policy.items():
            if deployment_pct > Decimal("1"):
                raise ValueError(
                    "Deployment percentage cannot exceed 100%"
                )

            if deployment_pct < Decimal("0"):
                raise ValueError(
                    "Deployment percentage cannot be negative"
                )

    def evaluate(
        self,
        regime_result: dict,
        available_capital: Decimal,
    ) -> DeploymentEvaluation:
        """
        Convert a market regime and available capital into a
        deployment decision.
        """

        if not isinstance(regime_result, dict):
            raise ValueError(
                "Regime result must be a dictionary"
            )

        if "regime" not in regime_result:
            raise ValueError(
                "Regime result must contain a regime"
            )

        if available_capital < Decimal("0"):
            raise ValueError(
                "Available capital cannot be negative"
            )

        regime = regime_result["regime"]
        deployment_pct = self.sizing_strategy.calculate(
            regime_result,
            available_capital,
        )

        deployment_amount = (
            available_capital * deployment_pct
        )

        if deployment_pct == Decimal("0"):
            action = "HOLD"
        else:
            action = "DEPLOY"

        return DeploymentEvaluation(
            action=action,
            deployment_amount=deployment_amount,
            deployment_pct=deployment_pct,
			source="regime",
        )