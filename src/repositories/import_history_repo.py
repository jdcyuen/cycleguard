from typing import Optional

from core.logger import get_logger


logger = get_logger(__name__)


class ImportHistoryRepositoryError(Exception):
    """Raised when import history repository operations fail."""


class ImportHistoryRepository:
    """
    Repository for cycleguard.import_history table.
    """

    def __init__(self, conn):
        self.conn = conn

    def insert(
        self,
        file_name: str,
        import_type: str,
        status: str = "STARTED",
    ) -> Optional[int]:
        """
        Creates a new import history record.

        Returns:
            import_history.id
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO import_history (
                        file_name,
                        import_type,
                        status
                    )
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (
                        file_name,
                        import_type,
                        status,
                    ),
                )

                row = cur.fetchone()

            self.conn.commit()

            return row[0] if row else None

        except Exception as exc:
            self.conn.rollback()

            logger.exception(
                "Failed inserting import history record"
            )

            raise ImportHistoryRepositoryError(
                "Unable to insert import history record"
            ) from exc


    def update_status(
        self,
        import_id: int,
        status: str,
        records_processed: Optional[int] = None,
        records_failed: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Updates import status after processing.
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE import_history
                    SET
                        status = %s,
                        records_processed = COALESCE(%s, records_processed),
                        records_failed = COALESCE(%s, records_failed),
                        error_message = COALESCE(%s, error_message),
                        completed_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (
                        status,
                        records_processed,
                        records_failed,
                        error_message,
                        import_id,
                    ),
                )

            self.conn.commit()

        except Exception as exc:
            self.conn.rollback()

            logger.exception(
                "Failed updating import history id=%s",
                import_id,
            )

            raise ImportHistoryRepositoryError(
                "Unable to update import history record"
            ) from exc


    def get_by_id(
        self,
        import_id: int,
    ) -> Optional[dict]:
        """
        Returns import history record by id.
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        id,
                        file_name,
                        import_type,
                        status,
                        records_processed,
                        records_failed,
                        error_message,
                        started_at,
                        completed_at,
                        created_at
                    FROM import_history
                    WHERE id = %s
                    """,
                    (import_id,),
                )

                row = cur.fetchone()

                if not row:
                    return None

                columns = [
                    desc[0]
                    for desc in cur.description
                ]

                return dict(zip(columns, row))

        except Exception as exc:
            logger.exception(
                "Failed retrieving import history id=%s",
                import_id,
            )

            raise ImportHistoryRepositoryError(
                "Unable to retrieve import history record"
            ) from exc


    def get_latest(
        self,
        import_type: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Returns most recent import history record.
        """

        try:
            with self.conn.cursor() as cur:

                if import_type:
                    cur.execute(
                        """
                        SELECT *
                        FROM import_history
                        WHERE import_type = %s
                        ORDER BY created_at DESC
                        LIMIT 1
                        """,
                        (import_type,),
                    )
                else:
                    cur.execute(
                        """
                        SELECT *
                        FROM import_history
                        ORDER BY created_at DESC
                        LIMIT 1
                        """
                    )

                row = cur.fetchone()

                if not row:
                    return None

                columns = [
                    desc[0]
                    for desc in cur.description
                ]

                return dict(zip(columns, row))

        except Exception as exc:
            logger.exception(
                "Failed retrieving latest import history"
            )

            raise ImportHistoryRepositoryError(
                "Unable to retrieve latest import history"
            ) from exc