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

    