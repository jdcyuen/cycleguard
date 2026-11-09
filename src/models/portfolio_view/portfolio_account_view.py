
"""
Module: portfolio_account_view

Purpose
-------
Defines the PortfolioAccountView model representing the assembled
portfolio information for one CycleGuard account.

Architecture
------------
This model belongs to the Portfolio View model package. It brings
together account identity, configuration, snapshot information,
individual holdings, actual allocations, and target allocations.

The PortfolioViewOrchestrationService creates and populates this model.
Dashboard components consume it for presentation.

Responsibilities
----------------
- Identify the database account and its YAML configuration.
- Reference the latest available account snapshot.
- Store the account's enriched holdings.
- Store actual and configured target bucket allocations.
- Report validation warnings and account-specific status information.

Design Principles
-----------------
- Single Responsibility: represents the assembled view of one account.
- Separation of Concerns: contains no repository access, database queries,
  calculations, or Streamlit presentation logic.
- Reusability: provides a consistent account-level model for portfolio
  overview, performance, comparison, and analysis features.

Data Sources
------------
- Database account: Account model.
- Account configuration: AccountConfig model.
- Snapshot: Snapshot model.
- Holdings: PortfolioHolding models.
- Allocations: PortfolioBucketAllocation models.

Maintenance Notes
-----------------
A missing snapshot is represented by None and must not be interpreted
as an account with zero holdings or zero value.

Actual allocations represent observed portfolio data.
Target allocations represent configured YAML objectives.

Validation warnings describe configuration or data-quality issues.
They do not automatically modify account configuration.
"""

from dataclasses import dataclass, field

from models.account import Account
from models.account_config import AccountConfig
from models.snapshot import Snapshot
from models.portfolio_view.portfolio_holding import PortfolioHolding
from models.portfolio_view.portfolio_bucket_allocation import (
    PortfolioBucketAllocation,
)


@dataclass(slots=True)
class PortfolioAccountView:
    """
    Represent the assembled Portfolio View for one account.

    Attributes:
        database_account:
            Database account record identifying the account.

        account_config:
            YAML configuration associated with the account.

        snapshot:
            Latest available database snapshot for the account.

        holdings:
            List of securities associated with the account.

        actual_allocations:
            Actual bucket allocations calculated from account holdings.

        target_allocations:
            Configured bucket allocations derived from YAML targets.

        validation_warnings:
            Account-specific configuration or data-quality warnings.

        message:
            Optional informational message about the account view.
    """

    database_account: Account
    """Database account record."""

    account_config: AccountConfig
    """YAML configuration associated with the account."""

    snapshot: Snapshot | None = None
    """Latest available account snapshot; None when no snapshot exists."""

    holdings: list[PortfolioHolding] = field(default_factory=list)
    """List of securities associated with the account."""

    actual_allocations: list[PortfolioBucketAllocation] = field(default_factory=list)
    """List of actual bucket allocations for the account."""

    target_allocations: list[PortfolioBucketAllocation] = field(default_factory=list)
    """List of configured target bucket allocations for the account."""

    validation_warnings: list[str] = field(default_factory=list)
    """List of configuration or data-quality warnings for the account. This is intended to identify problems with the account's data or configuration that could make the Portfolio View misleading or incomplete"""

    message: str | None = None
    """Optional informational message about the account view."""
