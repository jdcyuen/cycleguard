from abc import ABC, abstractmethod
from decimal import Decimal


class DeploymentSizingStrategy(ABC):
    """
    Determines deployment size from regime results and available capital.
    """

    @abstractmethod
    def calculate(
        self,
        regime_result: dict,
        available_capital: Decimal,
    ) -> Decimal:
        """
        Return the deployment percentage to apply.
        """
        raise NotImplementedError