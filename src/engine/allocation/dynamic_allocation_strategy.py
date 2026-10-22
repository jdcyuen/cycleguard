from abc import ABC, abstractmethod
from decimal import Decimal


class DynamicAllocationStrategy(ABC):
    """Strategy for distributing remaining allocation among dynamic securities."""

    @abstractmethod
    def allocate(
        self,
        available_target: Decimal,
        securities: dict[str, Decimal],
    ) -> dict[str, Decimal]:
        """Return desired portfolio-level targets for dynamic securities."""
        raise NotImplementedError