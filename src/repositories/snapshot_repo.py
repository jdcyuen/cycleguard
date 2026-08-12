from models.snapshot import Snapshot
from typing import Optional


from datetime import date
import psycopg
from core.logger import get_logger

logger = get_logger(__name__)

class SnapshotRepositoryError(Exception):
    """Raised when snapshot repository operations fail."""


class SnapshotRepository:
    def __init__(
        self,
        conn,
    ):
        self.conn = conn

    def get_by_date(
        self,
        snapshot_date,
    ) -> Optional[Snapshot]:

        """
        Returns snapshot_id if exists, else None
        """
        logger.info(f"Retrieving snapshot with date={snapshot_date}")
        logger.debug("SQL parameters: snapshot_date=%s", snapshot_date)

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        id,
                        snapshot_date
                    FROM cycleguard.snapshots
                    WHERE snapshot_date = %s
                    """,
                    (snapshot_date,),
                )

                row = cur.fetchone()

                if row is None:
                    return None

                logger.info(f"Retrieved snapshot with date={snapshot_date}")

                return Snapshot(
                    id=row[0],
                    snapshot_date=row[1],
                )


        except psycopg.Error as exc:
            logger.exception(f"Failed to lookup snapshot for date={snapshot_date}")
            raise SnapshotRepositoryError(
                f"Failed to lookup snapshot "
                f"for date={snapshot_date}"
            ) from exc

    def create(
        self,
        snapshot: Snapshot,
    ) -> Snapshot:

        """
        Creates snapshot and returns snapshot_id
        """
        logger.info(
            f"Creating snapshot with date={snapshot.snapshot_date}"
        )
        logger.debug(
            "SQL parameters: snapshot_date=%s",
            snapshot.snapshot_date,
        )   
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO cycleguard.snapshots(snapshot_date)
                    VALUES (%s)
                    RETURNING id, snapshot_date
                    """,
                    (snapshot.snapshot_date,),
                )

                row = cur.fetchone()
                logger.info(
                    f"Snapshot created successfully with date={snapshot.snapshot_date}"
                )
            self.conn.commit()
            logger.info(
                f"Snapshot committed successfully with date={snapshot.snapshot_date}"
            )

            return Snapshot(
                id=row[0],
                snapshot_date=row[1],
            )

        except psycopg.IntegrityError as exc:
            self.conn.rollback()
            logger.exception(
                f"Failed to create snapshot for date={snapshot.snapshot_date}"   
            )
            raise SnapshotRepositoryError(
                f"Snapshot already exists "
                f"for date={snapshot.snapshot_date}"
            ) from exc

        except psycopg.Error as exc:
            self.conn.rollback()
            logger.exception(
                f"Failed to create snapshot for date={snapshot.snapshot_date}"
            )
            raise SnapshotRepositoryError(
                f"Failed to create snapshot "
                f"for date={snapshot.snapshot_date}"
            ) from exc

    def ensure_not_exists(
        self,
        snapshot_date,
    ) -> None:
    
        """
        Hard guard against duplicates.
        """
        logger.info(
            f"Checking if snapshot exists for date={snapshot_date}"
        )

        existing = self.get_by_date(snapshot_date)

        if existing is not None:

            logger.warning(
                "Snapshot already exists "
                "(id=%s, snapshot_date=%s).",
                existing.id,
                existing.snapshot_date,
            )

            logger.error(
                "Duplicate snapshot detected. "
                "Import cannot continue."
            )

            raise ValueError(
                f"Snapshot already exists "
                f"for {snapshot_date}"
            )
        logger.info(
            "No existing snapshot found for "
            "snapshot_date=%s.",
            snapshot_date,
        )
    def get_by_account_and_date(
        self,
        account_id: int,
        snapshot_date: date,
    ) -> Optional[Snapshot]:
        """
        Returns the snapshot for an account on a specific date,
        or None if no snapshot exists.
        """

        sql = """
            SELECT
                id,
                snapshot_date
            FROM cycleguard.snapshots
            WHERE account_id = %s
            AND snapshot_date = %s
        """

        try:
            with self.conn.cursor() as cur:

                cur.execute(
                    sql,
                    (
                        account_id,
                        snapshot_date,
                    ),
                )

                row = cur.fetchone()

            if row is None:

                logger.debug(
                    "No snapshot found for account_id=%s on %s",
                    account_id,
                    snapshot_date,
                )

                return None

            logger.debug(
                "Found snapshot id=%s for account_id=%s on %s",
                row[0],
                account_id,
                snapshot_date,
            )

            return Snapshot(
                id=row[0],
                snapshot_date=row[1],
            )

        except Exception as exc:

            logger.exception(
                "Failed retrieving snapshot for account_id=%s on %s",
                account_id,
                snapshot_date,
            )

            raise SnapshotRepositoryError(
                f"Unable to retrieve snapshot for "
                f"account_id={account_id} "
                f"on {snapshot_date}"
            ) from exc
    
    def delete_by_import_history_id(
        self,
        import_history_id: int,
    ) -> int:

        """
        Deletes all snapshots created by the specified import.

        ```
        Args:
            import_history_id: ID of the import history record.

        Returns:
            Number of snapshots deleted.

        Raises:
            SnapshotRepositoryError:
                If the delete operation fails.
        """

        sql = """
            DELETE FROM cycleguard.snapshots
            WHERE import_history_id = %s;
        """

        logger.info(
            "Deleting snapshots for import_history_id=%s",
            import_history_id,
        )

        try:
            with self.conn.cursor() as cur:

                cur.execute(
                    sql,
                    (import_history_id,),
                )

                rows_deleted = cur.rowcount

            logger.info(
                "Deleted %s snapshot(s) "
                "for import_history_id=%s",
                rows_deleted,
                import_history_id,
            )

            return rows_deleted

        except Exception as exc:

            logger.exception(
                "Failed deleting snapshots "
                "for import_history_id=%s",
                import_history_id,
            )

            raise SnapshotRepositoryError(
                "Unable to delete snapshots "
                f"for import_history_id={import_history_id}"
            ) from exc
