import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


def _validate_non_negative_decimal(
    name: str,
    value: Decimal,
) -> None:
    """
    Validate that a monetary input is a finite, non-negative Decimal.

    Raises:
        TypeError: If the value is not a Decimal.
        ValueError: If the value is non-finite or negative.
    """

    if not isinstance(value, Decimal):
        logger.warning(
            "Invalid cash deployment input: %s must be a Decimal; received %s",
            name,
            type(value).__name__,
        )
        raise TypeError(f"{name} must be a Decimal")

    if not value.is_finite():
        logger.warning(
            "Invalid cash deployment input: %s must be finite; received %s",
            name,
            value,
        )
        raise ValueError(f"{name} must be finite")

    if value < Decimal("0"):
        logger.warning(
            "Invalid cash deployment input: %s cannot be negative; received %s",
            name,
            value,
        )
        raise ValueError(f"{name} cannot be negative")


class CashDeploymentPolicy:
    """
    Cash Deployment Policy

    Controls how much Defensive bucket capital may be released when
    a deployment engine recommends investing.

    Approval is constrained by two independent limits:

    1. Proposed amount:
       The dollar amount recommended by the deployment engine.

    2. Releasable Defensive capital:
       The Defensive bucket's market value remaining after preserving
       the required cash reserve.

    The approved amount is the smaller of these two limits.

    Crash deployment percentages are calculated by the crash
    deployment engine against total portfolio value. This policy
    does not impose an additional percentage-based event cap.

    This policy does not determine when a deployment should occur.
    It does not modify portfolio holdings or generate trades.
    """

    def __init__(
        self,
        required_reserve: Decimal = Decimal("0"),
    ) -> None:
        """Initialize the policy with a validated cash reserve."""

        _validate_non_negative_decimal(
            "required_reserve",
            required_reserve,
        )

        self.required_reserve: Decimal = required_reserve

        logger.debug(
            "CashDeploymentPolicy initialized: required_reserve=%s",
            self.required_reserve,
        )

    def approve(
        self,
        proposed_amount: Decimal,
        available_defensive_capital: Decimal,
    ) -> Decimal:
        """
        Determine the maximum deployment amount permitted by policy.

        Args:
            proposed_amount:
                Dollar amount recommended by the deployment engine.

            available_defensive_capital:
                Current market value of the Defensive bucket before
                subtracting the required reserve.

        Returns:
            Approved deployment amount as a Decimal.

        Raises:
            TypeError: If a monetary input is not a Decimal.
            ValueError: If a monetary input is non-finite or negative.

        Unexpected calculation errors are logged and re-raised.
        """

        logger.debug(
            "Evaluating cash deployment: proposed=%s, "
            "defensive_capital=%s, required_reserve=%s",
            proposed_amount,
            available_defensive_capital,
            self.required_reserve,
        )

        # Validate all monetary inputs before performing calculations.
        _validate_non_negative_decimal(
            "proposed_amount",
            proposed_amount,
        )
        _validate_non_negative_decimal(
            "available_defensive_capital",
            available_defensive_capital,
        )

        try:
            # Preserve the required cash reserve.
            # Only Defensive capital above the reserve is releasable.
            releasable_cash: Decimal = max(
                available_defensive_capital - self.required_reserve,
                Decimal("0"),
            )

            # The approved amount cannot exceed either the engine's
            # recommendation or the releasable Defensive capital.
            approved_amount: Decimal = min(
                proposed_amount,
                releasable_cash,
            )

            logger.info(
                "Cash deployment evaluated: proposed=%s, "
                "available=%s, reserve=%s, releasable=%s, "
                "approved=%s",
                proposed_amount,
                available_defensive_capital,
                self.required_reserve,
                releasable_cash,
                approved_amount,
            )

            return approved_amount

        except Exception:
            # Preserve the original exception and traceback.
            # Never silently convert an unexpected failure into
            # a zero-dollar approval.
            logger.exception(
                "Unexpected error while evaluating cash deployment: "
                "proposed=%s, defensive_capital=%s",
                proposed_amount,
                available_defensive_capital,
            )
            raise