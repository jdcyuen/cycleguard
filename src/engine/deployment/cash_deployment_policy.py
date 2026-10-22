
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


class CashDeploymentPolicy:
    """
    Cash Deployment Policy

    Determines how much of the available defensive capital may be
    released for a proposed deployment. Applies the required cash
    reserve and maximum per-event deployment limit to ensure that
    the approved amount does not exceed the proposed deployment,
    releasable defensive capital, or event cap.

    This policy is separate from deployment trigger detection and
    sizing. It does not modify portfolio holdings or generate trades;
    it returns the approved deployment amount for downstream
    allocation and trade planning.
    """

    def __init__(
        self,
        required_reserve: Decimal = Decimal("0"),
        max_deployment_per_event: Decimal = Decimal("0.15"),
    ):
        for name, value in (
            ("required_reserve", required_reserve),
            ("max_deployment_per_event", max_deployment_per_event),
        ):
            if not isinstance(value, Decimal) or not value.is_finite():
                raise ValueError(f"{name} must be a finite Decimal")
            if value < Decimal("0"):
                raise ValueError(f"{name} cannot be negative")

        if max_deployment_per_event > Decimal("1"):
            raise ValueError(
                "max_deployment_per_event cannot exceed 100%"
            )

        self.required_reserve = required_reserve
        self.max_deployment_per_event = max_deployment_per_event

    
    def approve(
        self,
        proposed_amount: Decimal,
        available_defensive_capital: Decimal,
        portfolio_value: Decimal,
    ) -> Decimal:
        """
        Determine the maximum deployment amount permitted by the
        Cash Deployment Policy.
        """

        # Validate that all monetary inputs are finite, non-negative
        # Decimal values before performing financial calculations.
        for name, value in (
            ("proposed_amount", proposed_amount),
            ("available_defensive_capital", available_defensive_capital),
            ("portfolio_value", portfolio_value),
        ):
            if not isinstance(value, Decimal) or not value.is_finite():
                raise ValueError(f"{name} must be a finite Decimal")

            if value < Decimal("0"):
                raise ValueError(f"{name} cannot be negative")

        # A zero-value portfolio cannot support a percentage-based
        # deployment limit, so no capital may be approved.
        if portfolio_value == Decimal("0"):
            return Decimal("0")

        # Preserve the required defensive cash reserve.
        # Only the amount remaining above the reserve is releasable.
        releasable_cash = max(
            available_defensive_capital - self.required_reserve,
            Decimal("0"),
        )

        # Calculate the maximum amount permitted for this event
        # using the configured percentage of total portfolio value.
        event_cap = (
            portfolio_value * self.max_deployment_per_event
        )

        # Approve the smallest of the proposed amount, releasable
        # defensive cash, and the maximum per-event deployment.
        # This ensures the policy cannot approve more than any
        # individual constraint permits.
        approved_amount = min(
            proposed_amount,
            releasable_cash,
            event_cap,
        )

        # Record the inputs and result for audit and troubleshooting.
        logger.info(
            "Cash deployment evaluated: proposed=%s, available=%s, "
            "reserve=%s, event_cap=%s, approved=%s",
            proposed_amount,
            available_defensive_capital,
            self.required_reserve,
            event_cap,
            approved_amount,
        )

        # Return the approved amount without modifying the portfolio
        # or creating trades. Allocation and trade planning follow later.
        return approved_amount

