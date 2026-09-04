from decimal import Decimal

from engine.deployment.base_deployment_engine import BaseDeploymentEngine
from models.deployment import DeploymentDecision


class RegimeDeploymentEngine(BaseDeploymentEngine):
    """
    Determines portfolio deployment based on the current market regime.

    This engine does not detect the regime and does not calculate
    available capital. It consumes those results and produces a
    DeploymentDecision.
    """

    def __init__(self, deployment_policy=None):
        self.deployment_policy = deployment_policy or {}

        for regime, deployment_pct in self.deployment_policy.items():
            if deployment_pct > Decimal("1"):
                raise ValueError(
                    "Deployment percentage cannot exceed 100%"
                )

            if deployment_pct < Decimal("0"):
                raise ValueError(
                    "Deployment percentage cannot be negative"
                )

    def _get_deployment_pct(self, regime: str) -> Decimal:
        """Return the deployment percentage for a market regime."""
        return self.deployment_policy.get(
            regime,
            Decimal("0"),
        )

    def evaluate(
        self,
        regime_result: dict,
        available_capital: Decimal,
    ) -> DeploymentDecision:
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
        deployment_pct = self._get_deployment_pct(regime)

        deployment_amount = (
            available_capital * deployment_pct
        )

        if deployment_pct == Decimal("0"):
            action = "HOLD" if regime != "RISK_ON" else "DEPLOY"
        else:
            action = "DEPLOY"

        return DeploymentDecision(
            action=action,
            deployment_amount=deployment_amount,
            deployment_pct=deployment_pct,
        )