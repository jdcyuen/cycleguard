from models.deployment_decision_snapshot import (
    DeploymentDecisionSnapshot,
)
from typing import Optional

class DeploymentDecisionSnapshotRepositoryError(Exception):
    """Raised when a deployment decision snapshot repository operation fails."""


class DeploymentDecisionSnapshotRepository:
    """
    Repository for persisting DeploymentDecisionSnapshot objects.
    """

    def __init__(self, conn):
        self.conn = conn

    def create(
        self,
        snapshot: DeploymentDecisionSnapshot,
    ) -> int:
        """
        Create a deployment decision snapshot and return its database ID.
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO cycleguard.deployment_decision_snapshot (
                        deployment_decision_id,
                        snapshot_date,
                        recommended_amount,
                        actual_amount_deployed
                    )
                    VALUES (%s, %s, %s, %s)
                    RETURNING deployment_decision_snapshot_id
                    """,
                    (
                        snapshot.deployment_decision_id,
                        snapshot.snapshot_date,
                        snapshot.recommended_amount,
                        snapshot.actual_amount_deployed,
                    ),
                )

                row = cur.fetchone()

                if row is None:
                    raise DeploymentDecisionSnapshotRepositoryError(
                        "Failed to create deployment decision snapshot"
                    )

                self.conn.commit()

                return row[0]

        except DeploymentDecisionSnapshotRepositoryError:
            self.conn.rollback()
            raise

        except Exception as exc:
            self.conn.rollback()
            raise DeploymentDecisionSnapshotRepositoryError(
                "Failed to create deployment decision snapshot"
            ) from exc

    def get_by_id(
        self,
        deployment_decision_snapshot_id: int,
    ) -> Optional[DeploymentDecisionSnapshot]:
        """
        Retrieve a deployment decision snapshot by database ID.
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        deployment_decision_snapshot_id,
                        deployment_decision_id,
                        snapshot_date,
                        recommended_amount,
                        actual_amount_deployed
                    FROM cycleguard.deployment_decision_snapshot
                    WHERE deployment_decision_snapshot_id  = %s
                    """,
                    (deployment_decision_snapshot_id,),
                )

                row = cur.fetchone()

                if row is None:
                    return None

                return DeploymentDecisionSnapshot(
                    deployment_decision_snapshot_id=row[0],
                    deployment_decision_id=row[1],
                    snapshot_date=row[2],
                    recommended_amount=row[3],
                    actual_amount_deployed=row[4],
                )

        except Exception as exc:
            raise DeploymentDecisionSnapshotRepositoryError(
                f"Failed to lookup deployment decision snapshot "
                f"id={deployment_decision_snapshot_id}"
            ) from exc

















            