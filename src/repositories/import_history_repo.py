from typing import Optional
import psycopg

from core.logger import get_logger
from models.importhistory import ImportHistory

logger = get_logger(__name__)


class ImportHistoryRepositoryError(Exception):
    """Raised when import history repository operations fail."""


class ImportHistoryRepository:
    """
    Repository for cycleguard.import_history table.
    """

    def __init__(self, conn):
        self.conn = conn

    def _row_to_import_history(
        self,
        row,
    ) -> ImportHistory:
        """
        Converts a database row into an
        ImportHistory entity.
        """

        return ImportHistory(
            id=row[0],
            account_id=row[1],
            import_type=row[2],
            institution=row[3],
            filename=row[4],
            file_hash=row[5],
            snapshot_date=row[6],
            import_timestamp=row[7],
            rows_read=row[8],
            rows_imported=row[9],
            rows_skipped=row[10],
            status=row[11],
            elapsed_ms=row[12],
            error_message=row[13],
        )

    def insert(self, import_history: ImportHistory) -> ImportHistory:

        """
        Creates a new import history record.

        Args:
            import_history: ImportHistory to insert.

        Returns:
            ImportHistory: The inserted record populated with database-generated
            values such as id and import_timestamp.

        Raises:
            ImportHistoryRepositoryError: If the insert fails.
        """
        sql = """
            INSERT INTO cycleguard.import_history (
                account_id,
                import_type,
                institution,
                filename,
                file_hash,
                snapshot_date,
                rows_read,
                rows_imported,
                rows_skipped,
                status,
                elapsed_ms,
                error_message
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING
                id,
                account_id,
                import_type,
                institution,
                filename,
                file_hash,
                snapshot_date,
                import_timestamp,
                rows_read,
                rows_imported,
                rows_skipped,
                status,
                elapsed_ms,
                error_message;
        """

        logger.debug(
            "Inserting import history: account_id=%s import_type=%s institution=%s filename=%s file_hash=%s rows_imported=%s",
            import_history.account_id,
            import_history.import_type,
            import_history.institution,
            import_history.filename,
            import_history.file_hash,
            import_history.rows_imported,
        )


        try:
            # Initialize default values
            status = import_history.status or "RUNNING"
            rows_read = import_history.rows_read or 0
            rows_imported = import_history.rows_imported or 0
            rows_skipped = import_history.rows_skipped or 0
            elapsed_ms = import_history.elapsed_ms or 0
            error_message = import_history.error_message

            with self.conn.cursor() as cur:

                cur.execute(
                    sql,
                    (
                        import_history.account_id,
                        import_history.import_type,
                        import_history.institution,
                        import_history.filename,
                        import_history.file_hash,
                        import_history.snapshot_date,
                        rows_read,
                        rows_imported,
                        rows_skipped,
                        status,
                        elapsed_ms,
                        error_message,
                    ),
                )

                row = cur.fetchone()

                if row is None:

                    raise ImportHistoryRepositoryError(
                        "INSERT did not return an ImportHistory row."
                    )

            result = self._row_to_import_history(row)

            logger.info(
                "Import history inserted successfully: "
                "id=%s account_id=%s rows_read=%s "
                "rows_imported=%s rows_skipped=%s",
                result.id,
                result.account_id,
                result.rows_read,
                result.rows_imported,
                result.rows_skipped,
            )

            return result

        except Exception as exc:

            logger.exception(
                "Failed creating import history "
                "account_id=%s "
                "type=%s "
                "filename=%s",
                import_history.account_id,
                import_history.import_type,
                import_history.filename,
            )
            raise ImportHistoryRepositoryError(
                "Unable to insert import history record"
            ) from exc


    def complete_import(
        self,
        import_id: int,
        *,
        rows_read: Optional[int] = None,
        rows_imported: Optional[int] = None,
        rows_skipped: Optional[int] = None,
        status: Optional[str] = None,
        elapsed_ms: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> None:

        """
        Completes an import by updating its final
        audit information.

        Any argument left as None preserves the
        existing value in the database.
        """

        sql = """
            UPDATE cycleguard.import_history
            SET
                rows_read      = COALESCE(%s, rows_read),
                rows_imported  = COALESCE(%s, rows_imported),
                rows_skipped   = COALESCE(%s, rows_skipped),
                status         = COALESCE(%s, status),
                elapsed_ms     = COALESCE(%s, elapsed_ms),
                error_message  = COALESCE(%s, error_message)
            WHERE id = %s
        """

        try:

            with self.conn.cursor() as cur:

                cur.execute(
                    sql,
                    (
                        rows_read,
                        rows_imported,
                        rows_skipped,
                        status,
                        elapsed_ms,
                        error_message,
                        import_id,
                    ),
                )

            logger.info(
                "Completed import history "
                "id=%s "
                "status=%s "
                "rows_read=%s "
                "rows_imported=%s "
                "rows_skipped=%s "
                "elapsed_ms=%s",
                import_id,
                status,
                rows_read,
                rows_imported,
                rows_skipped,
                elapsed_ms,
            )

        except Exception as exc:
            logger.exception(
                "Failed completing import history id=%s",
                import_id,
            )

            raise ImportHistoryRepositoryError(
                f"Unable to complete import history id={import_id}"
            ) from exc


    def get_by_id(
        self,
        import_id: int,
    ) -> Optional[ImportHistory]:
        """
        Returns the import history record with the
        specified ID, or None if it does not exist.
        """

        sql = """
            SELECT
                id,
                account_id,
                import_type,
                institution,
                filename,
                file_hash,
                snapshot_date,
                import_timestamp,
                rows_read,
                rows_imported,
                rows_skipped,
                status,
                elapsed_ms,
                error_message
            FROM cycleguard.import_history
            WHERE id = %s
        """

        try:

            with self.conn.cursor() as cur:

                cur.execute(sql, (import_id,))
                row = cur.fetchone()

            if row is None:
                logger.debug("Import history id=%s not found.", import_id)
                return None

            logger.debug("Retrieved import history id=%s.", import_id)
            return self._row_to_import_history(row)

        except Exception as exc:

            logger.exception("Failed retrieving import history id=%s.", import_id)

            raise ImportHistoryRepositoryError(
                f"Unable to retrieve import history id={import_id}."
            ) from exc

    def exists(
        self,
        account_id: int,
        import_type: str,
        file_hash: str,
    ) -> bool:
        """
        Returns True if the specified file has
        already been successfully imported for
        the account.

        Duplicate imports are determined by the
        combination of:

            • account_id
            • import_type
            • file_hash

        Only imports with a status of SUCCESS or
        PARTIAL are considered duplicates. FAILED
        imports may be retried.
        """

        logger.info("Checking for existing %s import.", import_type)

        logger.debug("SQL parameters: account_id=%s, import_type=%s, file_hash=%s",
                    account_id, import_type, file_hash)
        sql = """
            SELECT EXISTS (
                SELECT 1
                FROM cycleguard.import_history
                WHERE account_id = %s
                AND import_type = %s
                AND file_hash = %s
                AND status IN ('SUCCESS', 'PARTIAL')
            )
        """

        try:

            with self.conn.cursor() as cur:

                cur.execute(
                    sql,
                    (
                        account_id,
                        import_type,
                        file_hash,
                    ),
                )

                exists = cur.fetchone()[0]

            if exists:

                logger.info(
                    "Duplicate %s import found "
                    "(account_id=%s).",
                    import_type,
                    account_id,
                )

            else:

                logger.info(
                    "No prior %s import found "
                    "(account_id=%s).",
                    import_type,
                    account_id,
                )

            return exists

        except psycopg.Error as exc:

            logger.exception(
                "Failed checking import history "
                "(account_id=%s, import_type=%s).",
                account_id,
                import_type,
            )

            raise ImportHistoryRepositoryError(
                "Failed checking import history."
            ) from exc
        

    def get_latest(
        self,
        import_type: Optional[str] = None,
    ) -> Optional[ImportHistory]:

        """
        Returns the most recent import history
        record, optionally filtered by import type.
        """

        logger.info(
            "Retrieving latest import history record."
        )

        logger.debug(
            "SQL parameters: import_type=%s",
            import_type,
        )

        sql = """
            SELECT
                id,
                account_id,
                import_type,
                institution,
                filename,
                file_hash,
                snapshot_date,
                import_timestamp,
                rows_read,
                rows_imported,
                rows_skipped,
                status,
                elapsed_ms,
                error_message
            FROM cycleguard.import_history
        """

        params = ()

        if import_type:

            sql += """
                WHERE import_type = %s
            """

            params = (import_type,)

        sql += """
            ORDER BY import_timestamp DESC
            LIMIT 1
        """

        try:

            with self.conn.cursor() as cur:

                cur.execute(sql, params)

                row = cur.fetchone()

            if row is None:

                logger.info(
                    "No import history records found."
                )

                return None

            logger.debug(
                "Latest import history id=%s retrieved.",
                row[0],
            )

            return self._row_to_import_history(row)

        except psycopg.Error as exc:

            logger.exception(
                "Failed retrieving latest import history."
            )

            raise ImportHistoryRepositoryError(
                "Unable to retrieve latest import history."
            ) from exc

    def update(self, import_history: ImportHistory) -> ImportHistory:
        """
        Updates an existing import history record.

        Args:
            import_history: ImportHistory containing the updated values.

        Returns:
            ImportHistory: The updated record.

        Raises:
            ImportHistoryRepositoryError: If the update fails or no row is updated.
        """

        sql = """
            UPDATE cycleguard.import_history
            SET
                rows_read = %s,
                rows_imported = %s,
                rows_skipped = %s,
                status = %s,
                elapsed_ms = %s,
                error_message = %s
            WHERE id = %s
            RETURNING
                id,
                account_id,
                import_type,
                institution,
                filename,
                file_hash,
                snapshot_date,
                import_timestamp,
                rows_read,
                rows_imported,
                rows_skipped,
                status,
                elapsed_ms,
                error_message;
        """

        logger.debug(
            "Updating import history: "
            "id=%s status=%s rows_read=%s rows_imported=%s "
            "rows_skipped=%s elapsed_ms=%s",
            import_history.id,
            import_history.status,
            import_history.rows_read,
            import_history.rows_imported,
            import_history.rows_skipped,
            import_history.elapsed_ms,
        )

        try:
            with self.conn.cursor() as cur:

                cur.execute(
                    sql,
                    (
                        import_history.rows_read,
                        import_history.rows_imported,
                        import_history.rows_skipped,
                        import_history.status,
                        import_history.elapsed_ms,
                        import_history.error_message,
                        import_history.id,
                    ),
                )

                row = cur.fetchone()

                if row is None:
                    raise ImportHistoryRepositoryError(
                        f"No import_history record found with id={import_history.id}"
                    )

            result = self._row_to_import_history(row)

            logger.info(
                "Import history updated successfully: "
                "id=%s status=%s rows_read=%s rows_imported=%s "
                "rows_skipped=%s",
                result.id,
                result.status,
                result.rows_read,
                result.rows_imported,
                result.rows_skipped,
            )

            return result

        except Exception as exc:

            logger.exception(
                "Failed updating import history: "
                "id=%s status=%s",
                import_history.id,
                import_history.status,
            )

            raise ImportHistoryRepositoryError(
                f"Unable to update import history id={import_history.id}"
            ) from exc 

    def delete_by_import_history_id(
        self,
        import_history_id: int,
    ) -> int:

        """
        Deletes the import history record identified by import_history_id.

        ```
        Args:
            import_history_id: ID of the import history record.

        Returns:
            Number of import history records deleted.

        Raises:
            ImportHistoryRepositoryError:
                If the delete operation fails.
        """

        sql = """
            DELETE FROM cycleguard.import_history
            WHERE id = %s;
        """

        logger.info(
            "Deleting import history record: "
            "import_history_id=%s",
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
                "Deleted %s import history record(s) "
                "for import_history_id=%s",
                rows_deleted,
                import_history_id,
            )

            return rows_deleted

        except Exception as exc:

            logger.exception(
                "Failed deleting import history record "
                "import_history_id=%s",
                import_history_id,
            )

            raise ImportHistoryRepositoryError(
                "Unable to delete import history record "
                f"import_history_id={import_history_id}"
            ) from exc


    def delete(
        self,
        import_history_id: int,
    ) -> int:
    
        """
        Delete an import_history record.

        Returns:
            Number of records deleted.
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM cycleguard.import_history
                    WHERE id = %s
                    """,
                    (import_history_id,),
                )

                deleted = cur.rowcount

            return deleted

        except psycopg.Error as exc:
            logger.exception(
                "Failed deleting import history id=%s",
                import_history_id,
            )

            raise ImportHistoryRepositoryError(
                f"Unable to delete import history record "
                f"id={import_history_id}"
            ) from exc