from models.deployment_evaluation import DeploymentEvaluation
from abc import ABC, abstractmethod
from decimal import Decimal



class BaseDeploymentEngine(ABC):
    """
    Base interface for CycleGuard deployment engines.
    """            

    def __init__(self, deployment_policy: dict | None = None):
        self.deployment_policy = deployment_policy or {}

    

    @abstractmethod
    def evaluate(
        self,
        context: object,
        available_capital: Decimal,
    ) -> DeploymentEvaluation:
        """
        Evaluate a deployment decision.
        """
        raise NotImplementedError