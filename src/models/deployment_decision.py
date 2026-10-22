from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class DeploymentDecision:
    """
    Represents a deployment opportunity identified by CycleGuard.
    """

    deployment_decision_id: Optional[int] = None
    account_number: str = ""
    recommended_amount: Decimal = Decimal("0")
    reason: str = ""