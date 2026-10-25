
"""
Module: regime_deployment_engine.py

Purpose:
    Evaluate market-regime deployment opportunities and return a
    DeploymentEvaluation describing the recommended action, deployment
    percentage, deployment amount, and decision source.

Responsibilities:
    - Validate the regime result and available capital.
    - Delegate deployment percentage calculation to the configured
      RegimeBasedSizingStrategy.
    - Validate the resulting deployment percentage.
    - Construct and return a DeploymentEvaluation.
    - Log initialization, successful evaluations, validation failures,
      and unexpected exceptions.

Design principles:
    - Single Responsibility: evaluate deployment recommendations based
      on an already-determined market regime.
    - Open/Closed: allow alternative sizing strategies to be injected
      without changing the engine.
    - Dependency Inversion: depend on the sizing strategy interface
      rather than embedding sizing rules in this class.

Boundaries:
    This engine does not determine the market regime, calculate
    available capital, enforce the final cash reserve policy, modify
    portfolio holdings, or execute trades. Those responsibilities
    belong to other CycleGuard components.

Error handling:
    Invalid inputs or invalid sizing results raise ValueError.
    Unexpected exceptions are logged with traceback information
    and propagated to the caller.
"""

import logging
from collections.abc import Mapping
from decimal import Decimal

from engine.deployment.base_deployment_engine import BaseDeploymentEngine
from engine.deployment.regime_based_sizing_strategy import (
    RegimeBasedSizingStrategy,
)
from models.deployment_evaluation import DeploymentEvaluation


logger = logging.getLogger(__name__)


class RegimeDeploymentEngine(BaseDeploymentEngine):
    """
    Evaluate regime-based deployment opportunities.

    The engine delegates deployment sizing to a sizing strategy and
    returns a DeploymentEvaluation. It does not execute trades or
    directly modify portfolio holdings.
    """

    def __init__(
        self,
        deployment_policy=None,
        sizing_strategy=None,
    ):
        """Initialize the engine with a policy and sizing strategy."""
        try:
            if deployment_policy is None:
                deployment_policy = {}

            if not isinstance(deployment_policy, Mapping):
                raise ValueError(
                    "Deployment policy must be a mapping"
                )

            for regime, value in deployment_policy.items():
                try:
                    deployment_pct = Decimal(str(value))
                except Exception as exc:
                    raise ValueError(
                        f"Invalid deployment percentage for "
                        f"regime '{regime}': {value!r}"
                    ) from exc

                if (
                    not deployment_pct.is_finite()
                    or deployment_pct < Decimal("0")
                    or deployment_pct > Decimal("1")
                ):
                    raise ValueError(
                        f"Deployment percentage for regime "
                        f"'{regime}' must be between 0 and 1"
                    )

            self.deployment_policy = deployment_policy
            self.sizing_strategy = (
                sizing_strategy
                if sizing_strategy is not None
                else RegimeBasedSizingStrategy(deployment_policy)
            )

            logger.info(
                "RegimeDeploymentEngine initialized: "
                "configured_regimes=%s, sizing_strategy=%s",
                len(deployment_policy),
                type(self.sizing_strategy).__name__,
            )

        except ValueError:
            logger.warning(
                "Invalid configuration initializing "
                "RegimeDeploymentEngine",
                exc_info=True,
            )
            raise

        except Exception:
            logger.exception(
                "Unexpected error initializing RegimeDeploymentEngine"
            )
            raise

    def evaluate(
        self,
        regime_result: dict,
        available_capital: Decimal,
    ) -> DeploymentEvaluation:
        """
        Evaluate a market regime and return a deployment recommendation.

        Args:
            regime_result: Result from the regime engine. Must be a
                dictionary containing the 'regime' key.
            available_capital: Available defensive capital as a
                finite, non-negative Decimal.

        Returns:
            DeploymentEvaluation containing the recommended action,
            deployment percentage, amount, and source.

        Raises:
            ValueError: If inputs or the calculated deployment
                percentage are invalid.
            Exception: Unexpected errors are logged and propagated.
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

            if not isinstance(available_capital, Decimal):
                raise ValueError(
                    "Available capital must be a Decimal"
                )

            if not available_capital.is_finite():
                raise ValueError(
                    "Available capital must be finite"
                )

            if available_capital < Decimal("0"):
                raise ValueError(
                    "Available capital cannot be negative"
                )

            regime = regime_result["regime"]

            logger.info(
                "Evaluating regime deployment: "
                "regime=%s, available_capital=%s",
                regime,
                available_capital,
            )

            deployment_pct = self.sizing_strategy.calculate(
                regime_result,
                available_capital,
            )

            if not isinstance(deployment_pct, Decimal):
                raise ValueError(
                    "Sizing strategy must return a Decimal"
                )

            if not deployment_pct.is_finite():
                raise ValueError(
                    "Deployment percentage must be finite"
                )

            if (
                deployment_pct < Decimal("0")
                or deployment_pct > Decimal("1")
            ):
                raise ValueError(
                    "Deployment percentage must be between 0 and 1"
                )

            deployment_amount = (
                available_capital * deployment_pct
            )

            action = (
                "HOLD"
                if deployment_pct == Decimal("0")
                else "DEPLOY"
            )

            evaluation = DeploymentEvaluation(
                action=action,
                deployment_amount=deployment_amount,
                deployment_pct=deployment_pct,
                source="regime",
            )

            logger.info(
                "Regime deployment evaluation completed: "
                "regime=%s, action=%s, deployment_pct=%s, "
                "deployment_amount=%s",
                regime,
                evaluation.action,
                evaluation.deployment_pct,
                evaluation.deployment_amount,
            )

            return evaluation

        except ValueError:
            logger.warning(
                "Regime deployment evaluation rejected: "
                "regime_result=%r, available_capital=%r",
                regime_result,
                available_capital,
                exc_info=True,
            )
            raise

        except Exception:
            logger.exception(
                "Unexpected error evaluating regime deployment: "
                "regime_result=%r, available_capital=%r",
                regime_result,
                available_capital,
            )
            raise
