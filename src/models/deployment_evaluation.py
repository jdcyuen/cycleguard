from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class DeploymentEvaluation:
    """Result produced by evaluating a deployment opportunity."""

    action: str
    deployment_pct: Decimal
    deployment_amount: Decimal

    # Identifies which deployment mechanism produced the decision. Source identifies the origin 
	# of a decision; it does not explain the specific reason the engine made that decision. 
	# For example, "crash" does not tell you which drawdown threshold was crossed.
	# 		"regime"	The recommendation came from normal market-regime deployment logic.
	# 		"crash"		The recommendation came from crash deployment logic.
	# 		"unknown"	No source was explicitly provided. This is the default.
    source: str = "unknown"

    # Amount originally recommended before cash-policy approval.
    proposed_amount: Decimal | None = None

    # Basis used to calculate deployment_pct.
    # "total_portfolio", "defensive_surplus", or "unknown".
    sizing_basis: str = "unknown"

    # Dollar value of the basis used to calculate deployment_pct.
    sizing_basis_amount: Decimal = Decimal("0")