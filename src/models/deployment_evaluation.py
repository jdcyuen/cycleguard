from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class DeploymentEvaluation:
    """Result produced by evaluating a deployment opportunity."""

    action: str
    deployment_pct: Decimal
    deployment_amount: Decimal
    source: str = "unknown"

    