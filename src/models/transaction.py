from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from datetime import date


@dataclass(frozen=True)
class Transaction:
    """
    Represents a single transaction.
    """
    id: Optional[int] = None
    account_id: Optional[int] = None
    security_id: Optional[int] = None
    import_history_id: Optional[int] = None

    symbol: str = ""

    run_date: Optional[date] = None
    settlement_date: Optional[date] = None

    action: str = ""
    trade_type: str = ""

    price: Decimal = Decimal("0")
    quantity: Decimal = Decimal("0")
    commission: Decimal = Decimal("0")
    fees: Decimal = Decimal("0")
    accrued_interest: Decimal = Decimal("0")
    amount: Decimal = Decimal("0")
    cash_balance: Decimal = Decimal("0")