from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

@dataclass(frozen=True)
class DeploymentDecisionSnapshot:
    """
    Represents a historical snapshot of a deployment decision
    when an actual deployment occurs.
    """

    deployment_decision_snapshot_id: Optional[int] = None
    deployment_decision_id: Optional[int] = None
    snapshot_date: Optional[date] = None
    recommended_amount: Decimal = Decimal("0")
    actual_amount_deployed: Decimal = Decimal("0")