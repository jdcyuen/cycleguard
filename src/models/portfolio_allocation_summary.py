"""
Module: portfolio_allocation_summary

Purpose
-------
Define the PortfolioAllocationSummary model representing an
aggregated portfolio-level allocation.
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PortfolioAllocationSummary:
    """
    Represent the aggregated allocation summary of a portfolio.

    Attributes:
        portfolio_value:
            Total portfolio market value in USD.

        buckets:
            Mapping of bucket names to their aggregated allocation
            data.
    """

    portfolio_value: Decimal
    """Total portfolio market value in USD."""

    buckets: dict[str, object]
    """Aggregated allocation data keyed by bucket name."""