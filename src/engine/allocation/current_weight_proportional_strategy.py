
"""
CurrentWeightProportionalStrategy 

Distributes the remaining portfolio allocation among dynamic securities 
in proportion to their current dollar values. 

Example: 
    Bucket target = 10% 
    Explicit security target (FTEC) = 7% 
    Remaining dynamic allocation = 3% 

    Current dynamic holdings: 
        AAPL = $6,000 
        SPMO = $4,000 
        Total = $10,000 

    Current proportions: 
        AAPL = 60% 
        SPMO = 40% 

    Dynamic allocation: 
        AAPL = 60% × 3% = 1.8% 
        SPMO = 40% × 3% = 1.2% 

    Final bucket allocation: 
        FTEC = 7.0% 
        AAPL = 1.8% 
        SPMO = 1.2% 
        Total = 10.0% 

The strategy determines only how the remaining allocation is distributed. 
It does not decide whether a security should be bought, sold, or held. 
Those decisions are handled by the Allocation Engine. 

Using current weights provides a relatively stable, low-turnover 
allocation approach while preserving the existing relationship between 
dynamic securities. 

This strategy is intentionally separate from the Allocation Engine so 
that alternative strategies, such as equal-weight or performance-based 
allocation, can be introduced later without changing the engine itself. 

"""

from decimal import Decimal

from engine.allocation.dynamic_allocation_strategy import DynamicAllocationStrategy


class CurrentWeightProportionalStrategy(DynamicAllocationStrategy):
    """Allocates the remaining target proportionally to current security values."""

    def allocate(
        self,
        available_target: Decimal,
        securities: dict[str, Decimal],
    ) -> dict[str, Decimal]:
        if available_target < Decimal("0"):
            raise ValueError("Available target cannot be negative")

        if not securities:
            return {}

        total_value = sum(securities.values())

        if total_value <= Decimal("0"):
            return {symbol: Decimal("0") for symbol in securities}

        return {
            symbol: available_target * (value / total_value)
            for symbol, value in securities.items()
        }