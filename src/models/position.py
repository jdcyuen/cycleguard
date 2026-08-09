from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class Position:
    """
    Represents a single portfolio position.
    """

    id: Optional[int] = None

    account_id: Optional[int] = None
    security_id: Optional[int] = None
    snapshot_id: Optional[int] = None
    import_history_id: Optional[int] = None

    symbol: str = ""
    quantity: Decimal = Decimal("0")
    ave_cost: Decimal = Decimal("0")
    cost_basis_total: Optional[Decimal] = None

    current_value: Decimal = Decimal("0")
    percent_of_account: Decimal = Decimal("0")

    daily_gain: Optional[Decimal] = None
    daily_gain_pct: Optional[Decimal] = None

    total_gain: Optional[Decimal] = None
    total_gain_pct: Optional[Decimal] = None