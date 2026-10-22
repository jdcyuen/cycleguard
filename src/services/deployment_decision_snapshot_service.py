from models.deployment_decision_snapshot import (
    DeploymentDecisionSnapshot,
)


class DeploymentDecisionSnapshotService:
    """
    Creates and persists deployment decision snapshots.
    """

    def __init__(self, repository):
        self.repository = repository

    def create(
        self,
        snapshot: DeploymentDecisionSnapshot,
    ) -> int:
        """
        Persist a deployment decision snapshot and return its ID.
        """
        return self.repository.create(snapshot)