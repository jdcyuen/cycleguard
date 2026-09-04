from dataclasses import dataclass
from decimal import Decimal

from models.trade import Trade


@dataclass(frozen=True)
class TradePlan:
    """A proposed set of trades generated from a deployment decision."""

    deployment_amount: Decimal
    sells: tuple[Trade, ...]
    buys: tuple[Trade, ...]
    reason: str