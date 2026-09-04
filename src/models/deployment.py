from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class DeploymentDecision:
    """Result produced by the CycleGuard Deployment Engine."""

    action: str
    deployment_pct: Decimal
    deployment_amount: Decimal