from models.deployment_decision import DeploymentDecision


class DeploymentDecisionService:
    """
    Creates and persists deployment decisions.
    """

    def __init__(self, repository):
        self.repository = repository

    def create(self, decision: DeploymentDecision) -> int:
        """
        Persist a deployment decision and return its ID.
        """
        return self.repository.create(decision)