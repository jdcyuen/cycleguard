
"""
Module: portfolio_holding

Purpose
-------
Defines the PortfolioHolding model, which enriches an existing CycleGuard
Position with portfolio-specific allocation information.

Architecture
------------
Position is the authoritative model for the actual investment record.
PortfolioHolding references Position and adds contextual information
needed by Portfolio View and future portfolio analysis services.

Responsibilities
----------------
- Reference an existing Position model.
- Associate the position with a canonical CycleGuard bucket.
- Store the configured security target percentage.
- Preserve the human-readable account identity.

Design Principles
-----------------
- Single Responsibility: adds portfolio context without duplicating
  position financial data.
- Dependency Inversion: depends on the Position model abstraction
  rather than database access.
- Separation of Concerns: contains no database queries, calculations,
  or Streamlit presentation logic.
- Reusability: can be consumed by allocation, performance, comparison,
  and technical analysis services.

Data Sources
------------
- Position: existing CycleGuard Position model.
- Bucket: account YAML bucket_mapping.
- Target percentage: account YAML security_targets.
- Account name: reconciled account configuration.

Maintenance Notes
-----------------
The Position reference is an in-memory object relationship, not a
database foreign key.

PortfolioHolding does not own, modify, or duplicate the Position's
financial fields.

Target percentages are percentage points of the entire account.
For example, Decimal("5.0") represents 5%, not 0.05.

A None target percentage means no configured target is available.
"""

from dataclasses import dataclass
from decimal import Decimal

from models.position import Position


@dataclass(slots=True)
class PortfolioHolding:
    """
    Enrich an existing Position with portfolio allocation context.

    Attributes:
        position:
            The authoritative Position model containing the actual
            security and financial information.

        bucket:
            The canonical CycleGuard bucket assigned to the position.
            UNMAPPED identifies a position without a valid bucket mapping.

        target_percentage:
            Configured security target as a percentage of the entire
            account. None means no target is configured.

        account_name:
            Human-readable account display name. Used to identify the
            source account when multiple accounts are combined.
    """

    position: Position
    """Underlying investment position; source of actual financial data."""

    bucket: str
    """Canonical allocation bucket assigned to the position."""

    target_percentage: Decimal | None = None
    """Configured target percentage of the entire account."""

    account_name: str | None = None
    """Display name of the account containing this position."""
