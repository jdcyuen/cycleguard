from decimal import Decimal

from engine.deployment.deployment_sizing_strategy import (
    DeploymentSizingStrategy,
)


class RegimeBasedSizingStrategy(DeploymentSizingStrategy):
    """
    Determines the base deployment percentage from the market regime.
    """

    def __init__(self, deployment_policy: dict | None = None):
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

    def calculate(
        self,
        regime_result: dict,
        available_capital: Decimal,
    ) -> Decimal:
        """
        Return the deployment percentage for the current regime.
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

        return self.deployment_policy.get(
            regime_result["regime"],
            Decimal("0"),
        )