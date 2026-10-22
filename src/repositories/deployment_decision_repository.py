from decimal import Decimal

from models.deployment_decision import DeploymentDecision
from typing import Optional

class DeploymentDecisionRepositoryError(Exception):
    """Raised when a deployment decision repository operation fails."""


class DeploymentDecisionRepository:
    """
    Repository for persisting DeploymentDecision objects.
    """

    def __init__(self, conn):
        self.conn = conn

    def create(self, decision: DeploymentDecision) -> int:
        """
        Insert a deployment decision and return its database ID.
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO cycleguard.deployment_decision (
                        account_id,
                        recommended_amount,
                        reason
                    )
                    SELECT
                        id,
                        %s,
                        %s
                    FROM cycleguard.accounts
                    WHERE account_number = %s
                    RETURNING id
                    """,
                    (
                        decision.recommended_amount,
                        decision.reason,
                        decision.account_number,
                    ),
                )

                row = cur.fetchone()

                if row is None:
                    raise DeploymentDecisionRepositoryError(
                        f"Account not found: {decision.account_number}"
                    )

                self.conn.commit()

                return row[0]

        except DeploymentDecisionRepositoryError:
            self.conn.rollback()
            raise

        except Exception as exc:
            self.conn.rollback()
            raise DeploymentDecisionRepositoryError(
                "Failed to insert deployment decision"
            ) from exc

    def get_by_id(
        self,
        deployment_decision_id: int,
    ) -> Optional[DeploymentDecision]:
        """
        Retrieve a deployment decision by database ID.
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        dd.id,
                        a.account_number,
                        dd.recommended_amount,
                        dd.reason
                    FROM cycleguard.deployment_decision dd
                    JOIN cycleguard.accounts a
                        ON a.id = dd.account_id
                    WHERE dd.id = %s
                    """,
                    (deployment_decision_id,),
                )

                row = cur.fetchone()

                if row is None:
                    return None

                return DeploymentDecision(
                    deployment_decision_id=row[0],
                    account_number=row[1],
                    recommended_amount=row[2],
                    reason=row[3],
                )

        except Exception as exc:
            raise DeploymentDecisionRepositoryError(
                f"Failed to lookup deployment decision "
                f"id={deployment_decision_id}"
            ) from exc