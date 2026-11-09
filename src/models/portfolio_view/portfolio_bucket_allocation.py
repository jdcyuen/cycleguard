"""
Module: portfolio_bucket_allocation

Purpose
-------
Define the PortfolioBucketAllocation model used to represent an
aggregate CycleGuard bucket allocation.

Architecture
------------
PortfolioBucketAllocation belongs to the Portfolio View model package.
It groups individual PortfolioHolding objects into a bucket-level
allocation for actual and target portfolio analysis.

Responsibilities
----------------
- Identify the canonical CycleGuard allocation bucket.
- Store the bucket's aggregate allocation percentage.
- Store its aggregate market value when representing actual allocation.
- Associate the actual holdings contributing to the bucket.
- Support both actual and target allocation representations.

Design Principles
-----------------
- Single Responsibility: represents one bucket-level allocation.
- Separation of Concerns: contains no database queries, calculations,
  or presentation logic.
- Reusability: can be consumed by Portfolio View, performance analysis,
  allocation monitoring, and reporting services.

Data Sources
------------
- Bucket: canonical bucket configuration in buckets.yaml.
- Percentage: calculated by the orchestration or allocation service.
- Market value: aggregated from underlying Position records.
- Holdings: PortfolioHolding model instances.

Maintenance Notes
-----------------
Percentage values use percentage points. For example, Decimal("12.5")
represents 12.5%, not 0.125.

Market value is denominated in USD.

For target allocations, market_value is None because a target percentage
does not represent an actual invested dollar amount.

An empty holdings list is valid when a configured target bucket has
no securities assigned to it.
"""

from dataclasses import dataclass, field
from decimal import Decimal

from models.portfolio_view.portfolio_holding import PortfolioHolding
from models.portfolio_view.portfolio_target_holding import (
    PortfolioTargetHolding,
)

@dataclass(slots=True)
class PortfolioBucketAllocation:
    """
    Represent the aggregate allocation of one CycleGuard bucket.

    Attributes:
        bucket:
            Canonical CycleGuard bucket identifier.

        percentage:
            Aggregate allocation percentage of the account or
            consolidated portfolio.

        market_value:
            Aggregate actual market value in USD. None for target
            allocations or when actual value is unavailable.

        holdings:
            PortfolioHolding instances contributing to this bucket.
			
		target_holdings:
            PortfolioTargetHolding instances representing configured
            security targets assigned to this bucket.
    """

    bucket: str
    """Canonical CycleGuard bucket identifier."""

    percentage: Decimal
    """Aggregate bucket allocation expressed in percentage points."""

    market_value: Decimal | None = None
    """Aggregate actual market value in USD; None when not applicable."""

    holdings: list[PortfolioHolding] = field(default_factory=list)
    """List of actual securities associated with this bucket."""
	
    target_holdings: list[PortfolioTargetHolding] = field(
        default_factory=list
    )
    """List of configured security targets associated with this bucket."""