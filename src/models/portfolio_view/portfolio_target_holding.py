"""
Module: portfolio_target_holding

Purpose
-------
Define the PortfolioTargetHolding model used to represent a
security-level allocation target configured for an account.

Architecture
------------
PortfolioTargetHolding belongs to the Portfolio View model package.
It represents a configured target independently of actual database
positions, allowing target securities to appear even when the account
does not currently hold them.

Responsibilities
----------------
- Identify the target security by ticker symbol.
- Associate the security with its canonical allocation bucket.
- Store its configured account-level target percentage.
- Optionally identify the account associated with the target.

Design Principles
-----------------
- Single Responsibility: represents one security-level allocation target.
- Separation of Concerns: contains no database queries, calculations,
  or presentation logic.
- Independence: does not require an actual Position record.

Data Sources
------------
- Symbol: account security_targets configuration.
- Bucket: account bucket_mapping configuration.
- Target percentage: account security_targets configuration.

Maintenance Notes
-----------------
Target percentages use percentage points. For example, Decimal("12.5")
represents 12.5%, not 0.125.
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(slots=True)
class PortfolioTargetHolding:
    """
    Represent one security-level allocation target.

    Attributes:
        symbol:
            Security ticker symbol.

        bucket:
            Canonical CycleGuard allocation bucket assigned to
            the security.

        target_percentage:
            Configured target percentage of the total account,
            expressed in percentage points.

        account_name:
            Optional account name identifying the source of the
            target configuration.
    """

    symbol: str
    """Security ticker symbol."""

    bucket: str
    """Canonical CycleGuard allocation bucket."""

    target_percentage: Decimal
    """Configured account-level target in percentage points."""

    account_name: str | None = None
    """Optional name of the account associated with this target."""