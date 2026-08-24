from core.logger import get_logger

from repositories.import_history_repo import (
    ImportHistoryRepository,
)

from repositories.position_repo import (
    PositionRepository,
)

from repositories.snapshot_repo import (
    SnapshotRepository,
)

from repositories.transaction_repo import (
    TransactionRepository,
)

from database.transaction_manager import TransactionManager

logger = get_logger(__name__)




class ImportRollbackService:

    """
    Rolls back data created by a specific import.

    ```
    The import_history record is the root of the rollback.
    """

    def __init__(
        self,
        transaction_manager: TransactionManager,
        import_history_repo: ImportHistoryRepository,
        position_repo: PositionRepository,
        snapshot_repo: SnapshotRepository,
        transaction_repo: TransactionRepository,
    ):
        self._transaction_manager = transaction_manager
        self._import_history_repo = import_history_repo
        self._position_repo = position_repo
        self._snapshot_repo = snapshot_repo
        self._transaction_repo = transaction_repo

    def rollback(
        self,
        import_history_id: int,
        delete_import_history: bool = False,
    ) -> dict:

        """
        Roll back all data created by an import.

        Returns:
            Summary of deleted records.
        """

        logger.info(
            "Starting import rollback: import_history_id=%s",
            import_history_id,
        )

        transactions_deleted = 0
        positions_deleted = 0
        snapshots_deleted = 0
        import_history_deleted = 0

        try:

            with self._transaction_manager.transaction():
                transactions_deleted = (
                    self._transaction_repo.delete_by_import_history_id(import_history_id)
                )

                positions_deleted = (
                    self._position_repo.delete_by_import_history_id(import_history_id)
                )

                snapshots_deleted = (
                    self._snapshot_repo.delete_by_import_history_id(import_history_id)
                )

                if delete_import_history:
                    import_history_deleted = (
                        self._import_history_repo.delete(import_history_id)
                    ) 

            
        except Exception:
            logger.exception(
                "Import rollback failed; transaction was rolled back",
                extra={"import_history_id": import_history_id},
            )
            raise

        logger.info(
            "Import rollback completed",
            extra={
                "import_history_id": import_history_id,
                "transactions_deleted": transactions_deleted,
                "positions_deleted": positions_deleted,
                "snapshots_deleted": snapshots_deleted,
                "import_history_deleted": import_history_deleted,
            },
        )

        logger.info(
            "Import rollback completed successfully: "
            "import_history_id=%s",
            import_history_id,
        )

        return {
            "import_history_id": import_history_id,
            "transactions_deleted": transactions_deleted,
            "positions_deleted": positions_deleted,
            "snapshots_deleted": snapshots_deleted,
            "import_history_deleted": import_history_deleted,
        }

