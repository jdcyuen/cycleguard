import logging
from decimal import Decimal

from engine.deployment.deployment_sizing_strategy import (
    DeploymentSizingStrategy,
)

logger = logging.getLogger(__name__)

class SignalAdjustedSizingStrategy(DeploymentSizingStrategy):
    """
    Determines deployment size using the market regime and
    individual signal results.
    """

    def __init__(
        self, 
        deployment_policy: dict | None = None,
        adjustments: dict | None = None,
    ):
        self.deployment_policy = deployment_policy or {}
        self.adjustments = adjustments or {}

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
        Return the base deployment percentage for the current regime.

        Signal adjustments will be added incrementally.
        """

        try:
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
            deployment_pct = self.deployment_policy.get(
                regime,
                Decimal("0"),
            )

            signals = regime_result.get("signals", {})

            for signal_name, signal_config in self.adjustments.items():
                signal_result = signals.get(signal_name)

                if not signal_result:
                    continue

                status = signal_result.get("status")
                adjustment = signal_config.get(status)

                if adjustment is not None:
                    deployment_pct += adjustment

            deployment_pct = max(
                deployment_pct,
                Decimal("0"),
            )

            deployment_pct = min(
                deployment_pct,
                Decimal("1"),
            )

            logger.debug(
                "Signal-adjusted sizing calculated: "
                "regime=%s, deployment_pct=%s, available_capital=%s",
                regime,
                deployment_pct,
                available_capital,
            )

            return deployment_pct

        except (ValueError, TypeError):
            logger.exception(
                "Invalid input to signal-adjusted sizing strategy"
            )
            raise

        except Exception:
            logger.exception(
                "Unexpected error in signal-adjusted sizing strategy"
            )
            raise