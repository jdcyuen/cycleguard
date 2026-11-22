"""
===============================================================================
CycleGuard Crash Deployment Engine
===============================================================================

PURPOSE
-------
Evaluates market drawdown conditions and calculates proposed crash deployment
amounts according to the configured crash deployment policy.

Crash deployment percentages are calculated against TOTAL PORTFOLIO VALUE,
not the Defensive bucket or available cash.

POLICY
------
Crash levels are defined in:

    src/config/system/crash_deployment.yaml

Example configuration:

    levels:
        level_1:
            drawdown: -0.10
            deploy_pct: 0.03
        level_2:
            drawdown: -0.20
            deploy_pct: 0.05
        level_3:
            drawdown: -0.30
            deploy_pct: 0.08
        level_4:
            drawdown: -0.40
            deploy_pct: 0.09

CALCULATION
-----------
Proposed Deployment = Total Portfolio Value × Deployment Percentage

Example:

    Portfolio Value:       $1,000,000
    Market Drawdown:           -30%
    Applicable Level:       Level 3
    Deployment Percentage:        8%

    Proposed Deployment:      $80,000

LEVEL SELECTION
---------------
The engine selects the deepest applicable configured drawdown level.

Stacking is disabled. Deployment percentages from earlier levels are NOT
added together.

At a 30% drawdown, Level 3 deploys 8%, not 3% + 5% + 8% = 16%.

CAPITAL PROTECTION
------------------
This engine calculates a PROPOSED deployment only.

It does not authorize deployment or execute trades.

The Deployment Orchestration Service and Cash Deployment Policy subsequently
enforce:

    - Available Defensive capital
    - Required Defensive cash reserve
    - Deployment approval limits

The final approved deployment must not exceed available deployable capital.

ARCHITECTURAL RESPONSIBILITIES
------------------------------
Crash Manager:
    Calculates market drawdown.

Crash Deployment Engine:
    Selects crash level and calculates proposed deployment.

Deployment Orchestration Service:
    Prioritizes crash deployment decisions and coordinates approval.

Cash Deployment Policy:
    Enforces available capital and reserve requirements.

Execution Layer:
    Executes approved trades.

DESIGN PRINCIPLES
-----------------
Single Responsibility:
    This engine handles crash-level selection and sizing only.

Open/Closed:
    Crash levels and deployment percentages are configuration-driven.

Dependency Inversion:
    Inherits the deployment engine abstraction and returns the shared
    DeploymentEvaluation model.

Separation of Concerns:
    Cash availability, reserves, approval, and trade execution are handled
    outside this engine.

VALIDATION
----------
Rejects:

    - Non-finite drawdown values
    - Drawdown values outside the valid range of -100% through 0%
    - Negative or non-finite portfolio values
    - Invalid crash policy configuration
    - Invalid deployment percentages
    - Invalid crash thresholds

ERROR HANDLING
--------------
Errors are logged with contextual information.

Unexpected errors are re-raised rather than silently converted to HOLD,
preventing configuration or programming errors from being mistaken for
legitimate market conditions.

===============================================================================
"""

import logging
from decimal import Decimal
from typing import Any

from engine.deployment.base_deployment_engine import BaseDeploymentEngine
from models.deployment_evaluation import DeploymentEvaluation


logger: logging.Logger = logging.getLogger(__name__)


class CrashDeploymentEngine(BaseDeploymentEngine):
    """
    Evaluates crash deployment policy using total portfolio value.

    The engine identifies the deepest crash threshold reached and calculates
    the proposed deployment amount using the configured deployment percentage.

    Defensive capital restrictions are intentionally enforced by downstream
    deployment orchestration and cash deployment policy components.
    """

    def evaluate(
        self,
        drawdown: float,
        total_portfolio_value: Decimal,
    ) -> DeploymentEvaluation:
        """
        Evaluate crash deployment conditions.

        Args:
            drawdown:
                Market drawdown expressed as a negative decimal percentage.
                For example, -0.20 represents a 20% decline.

            total_portfolio_value:
                Total portfolio market value used as the deployment sizing basis.

        Returns:
            DeploymentEvaluation:
                HOLD when no configured crash level has been reached.

                DEPLOY when a crash level has been reached, with the proposed
                deployment amount calculated against total portfolio value.

        Raises:
            TypeError:
                If input types are invalid.

            ValueError:
                If input values or crash policy configuration are invalid.

            Exception:
                Unexpected evaluation errors are logged and re-raised.
        """

        try:
            # ---------------------------------------------------------
            # 1. Validate evaluation inputs
            # ---------------------------------------------------------

            if isinstance(drawdown, bool) or not isinstance(
                drawdown,
                (int, float),
            ):
                raise TypeError(
                    "Drawdown must be an int or float, excluding bool."
                )

            if not isinstance(total_portfolio_value, Decimal):
                raise TypeError(
                    "Total portfolio value must be a Decimal."
                )

            if not total_portfolio_value.is_finite():
                raise ValueError(
                    "Total portfolio value must be finite."
                )

            if total_portfolio_value < Decimal("0"):
                raise ValueError(
                    "Total portfolio value cannot be negative."
                )

            if drawdown != drawdown or drawdown in (
                float("inf"),
                float("-inf"),
            ):
                raise ValueError(
                    "Drawdown must be a finite numeric value."
                )

            if drawdown < -1.0 or drawdown > 0.0:
                raise ValueError(
                    "Drawdown must be between -1.0 and 0.0."
                )

            # ---------------------------------------------------------
            # 2. Validate crash deployment policy
            # ---------------------------------------------------------

            levels: dict[str, Any] = self.deployment_policy.get(
                "levels",
                {},
            )

            if not isinstance(levels, dict) or not levels:
                raise ValueError(
                    "Crash deployment policy must contain a non-empty "
                    "'levels' dictionary."
                )

            validated_levels: list[
                tuple[str, float, Decimal]
            ] = []

            for level_name, level_config in levels.items():

                if not isinstance(level_name, str):
                    raise ValueError(
                        "Crash level names must be strings."
                    )

                if not isinstance(level_config, dict):
                    raise ValueError(
                        f"Configuration for {level_name} must be a dictionary."
                    )

                if "drawdown" not in level_config:
                    raise ValueError(
                        f"Missing drawdown threshold for {level_name}."
                    )

                if "deploy_pct" not in level_config:
                    raise ValueError(
                        f"Missing deploy_pct configuration for {level_name}."
                    )

                raw_drawdown: Any = level_config["drawdown"]

                if isinstance(raw_drawdown, bool) or not isinstance(
                    raw_drawdown,
                    (int, float),
                ):
                    raise ValueError(
                        f"Invalid drawdown threshold for {level_name}."
                    )

                level_drawdown: float = float(raw_drawdown)

                if level_drawdown != level_drawdown or level_drawdown in (
                    float("inf"),
                    float("-inf"),
                ):
                    raise ValueError(
                        f"Drawdown threshold for {level_name} "
                        "must be finite."
                    )

                if level_drawdown < -1.0 or level_drawdown > 0.0:
                    raise ValueError(
                        f"Drawdown threshold for {level_name} must be "
                        "between -1.0 and 0.0."
                    )

                raw_deploy_pct: Any = level_config["deploy_pct"]

                if isinstance(raw_deploy_pct, bool):
                    raise ValueError(
                        f"Invalid deployment percentage for {level_name}."
                    )

                try:
                    deployment_pct: Decimal = Decimal(
                        str(raw_deploy_pct)
                    )
                except (ValueError, TypeError, ArithmeticError) as exc:
                    raise ValueError(
                        f"Invalid deployment percentage for {level_name}."
                    ) from exc

                if not deployment_pct.is_finite():
                    raise ValueError(
                        f"Deployment percentage for {level_name} "
                        "must be finite."
                    )

                if (
                    deployment_pct < Decimal("0")
                    or deployment_pct > Decimal("1")
                ):
                    raise ValueError(
                        f"Deployment percentage for {level_name} "
                        "must be between 0 and 1."
                    )

                validated_levels.append(
                    (
                        level_name,
                        level_drawdown,
                        deployment_pct,
                    )
                )

            # ---------------------------------------------------------
            # 3. Select the deepest applicable crash level
            # ---------------------------------------------------------

            # Drawdown thresholds are sorted ascending:
            # -40%, -30%, -20%, -10%.
            #
            # This ensures the deepest applicable threshold is selected
            # first, preventing deployment stacking.

            validated_levels.sort(
                key=lambda level: level[1],
            )

            selected_level: (
                tuple[str, float, Decimal] | None
            ) = None

            for level_name, level_drawdown, deployment_pct in (
                validated_levels
            ):
                if drawdown <= level_drawdown:
                    selected_level = (
                        level_name,
                        level_drawdown,
                        deployment_pct,
                    )
                    break

            # ---------------------------------------------------------
            # 4. Return HOLD if no crash threshold was reached
            # ---------------------------------------------------------

            if selected_level is None:

                logger.debug(
                    "Crash deployment HOLD. Drawdown=%.4f, "
                    "Portfolio Value=%s. No configured crash level reached.",
                    drawdown,
                    total_portfolio_value,
                )

                return DeploymentEvaluation(
                    action="HOLD",
                    deployment_pct=Decimal("0"),
                    deployment_amount=Decimal("0"),
                    source="crash",
                )

            # ---------------------------------------------------------
            # 5. Calculate proposed deployment using portfolio value
            # ---------------------------------------------------------

            (
                selected_level_name,
                selected_drawdown_threshold,
                deployment_pct,
            ) = selected_level

            deployment_amount: Decimal = (
                total_portfolio_value * deployment_pct
            )

            # ---------------------------------------------------------
            # 6. Log the deployment decision
            # ---------------------------------------------------------

            logger.info(
                "Crash deployment decision: Level=%s, "
                "Drawdown=%.4f, Threshold=%.4f, "
                "Portfolio Value=%s, Deployment Percentage=%s, "
                "Proposed Deployment=%s",
                selected_level_name,
                drawdown,
                selected_drawdown_threshold,
                total_portfolio_value,
                deployment_pct,
                deployment_amount,
            )

            # ---------------------------------------------------------
            # 7. Return deployment evaluation
            # ---------------------------------------------------------

            return DeploymentEvaluation(
                action="DEPLOY",
                deployment_pct=deployment_pct,
                deployment_amount=deployment_amount,
                source="crash",
            )

        except (TypeError, ValueError):
            # Invalid inputs or configuration are logged and propagated.
            logger.exception(
                "Crash deployment evaluation rejected. "
                "Drawdown=%s, Portfolio Value=%s",
                drawdown,
                total_portfolio_value,
            )
            raise

        except Exception:
            # Unexpected failures must not silently become HOLD decisions.
            logger.exception(
                "Unexpected crash deployment engine failure. "
                "Drawdown=%s, Portfolio Value=%s",
                drawdown,
                total_portfolio_value,
            )
            raise