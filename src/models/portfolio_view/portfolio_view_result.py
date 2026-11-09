
"""
Module: portfolio_view_result

Purpose
-------
Defines the PortfolioViewResult model returned by the
PortfolioViewOrchestrationService.

Architecture
------------
This is the top-level result model for CycleGuard's Portfolio View.
It provides a consistent response structure to dashboard components,
standalone Streamlit applications, and CLI consumers.

Responsibilities
----------------
- Identify the selected account or consolidated portfolio view.
- Provide the available active account views.
- Provide the holdings and allocations for presentation.
- Identify accounts with missing snapshots.
- Report validation warnings.
- Indicate whether actual and target allocation data is complete.

Design Principles
-----------------
- Single Responsibility: represents the complete result of a Portfolio
  View orchestration request.
- Separation of Concerns: contains no database queries, calculations,
  or presentation logic.
- Reusability: can be consumed by the main dashboard, standalone
  application, CLI, and future portfolio analysis services.

Data Sources
------------
- Account views: PortfolioAccountView models.
- Holdings: PortfolioHolding models.
- Allocations: PortfolioBucketAllocation models.
- Completeness indicators: determined by the orchestration service.

Maintenance Notes
-----------------
selected_account_id is None when the user selects All Accounts.

missing_snapshot_accounts identifies accounts that do not have an
available snapshot. Missing snapshots must never be treated as zero
portfolio value.

actual_allocation_complete indicates whether actual allocation data
includes all selected active accounts.

target_allocation_complete indicates whether target allocation data
includes all selected active accounts.

Completeness indicators describe data availability, not investment
performance or portfolio quality.
"""

from dataclasses import dataclass, field

from models.portfolio_view.portfolio_account_view import PortfolioAccountView
from models.portfolio_view.portfolio_holding import PortfolioHolding
from models.portfolio_view.portfolio_bucket_allocation import (
    PortfolioBucketAllocation,
)


@dataclass(slots=True)
class PortfolioViewResult:
    """
    Represent the complete result of a Portfolio View request.

    Attributes:
        selected_account_id:
            Database ID of the selected account. None represents
            All Accounts.

        accounts:
            List of active reconciled account views.

        holdings:
            Holdings included in the selected account or consolidated view.

        actual_allocations:
            Actual bucket allocations for the selected account or
            consolidated portfolio.

        target_allocations:
            Configured bucket allocations for the selected account or
            consolidated portfolio.

        missing_snapshot_accounts:
            Display names of accounts without an available snapshot.

        validation_warnings:
            Configuration and data-quality warnings.

        actual_allocation_complete:
            Indicates whether actual allocation data is complete.

        target_allocation_complete:
            Indicates whether target allocation data is complete.

        message:
            Optional informational message about the result.
    """

    selected_account_id: int | None = None
    """Selected database account ID; None represents All Accounts."""

    accounts: list[PortfolioAccountView] = field(default_factory=list)
    """List of active reconciled account views."""

    holdings: list[PortfolioHolding] = field(default_factory=list)
    """List of securities included in the selected portfolio view."""

    actual_allocations: list[PortfolioBucketAllocation] = field(default_factory=list)
    """List of actual bucket allocations."""

    target_allocations: list[PortfolioBucketAllocation] = field(default_factory=list)
    """List of configured target bucket allocations."""

    missing_snapshot_accounts: list[str] = field(default_factory=list)
    """Display names of accounts without an available snapshot."""

    validation_warnings: list[str] = field(default_factory=list)
    """List of configuration and data-quality warnings."""

    actual_allocation_complete: bool = True
    """Indicates whether actual allocation data includes all selected accounts."""

    target_allocation_complete: bool = True
    """Indicates whether target allocation data includes all selected accounts."""

    message: str | None = None
    """Optional informational message about the Portfolio View result."""
