from abc import ABC, abstractmethod
from decimal import Decimal

from models.deployment import DeploymentDecision


class BaseDeploymentEngine(ABC):
    """
    Base interface for CycleGuard deployment engines.
    """
    """
    def __init__(self, deployment_policy: dict | None = None):
        self.deployment_policy = deployment_policy or {}

        for regime, deployment_pct in self.deployment_policy.items():
            if deployment_pct < Decimal("0"):
                raise ValueError(
                    "Deployment percentage cannot be negative"
                )

            if deployment_pct > Decimal("1.0"):
                raise ValueError(
                    "Deployment percentage cannot exceed 100%"
                )
    """               

    def __init__(self, deployment_policy: dict | None = None):
        self.deployment_policy = deployment_policy or {}

    @abstractmethod
    def _get_deployment_pct(self, regime: str) -> Decimal:
        """
        Return the deployment percentage for the supplied context.
        """
        raise NotImplementedError

    @abstractmethod
    def evaluate(
        self,
        regime_result: dict,
        available_capital: Decimal,
    ) -> DeploymentDecision:
        """
        Evaluate a deployment decision.
        """
        raise NotImplementedError