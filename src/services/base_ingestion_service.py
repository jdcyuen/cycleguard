from models import importhistory
from abc import ABC, abstractmethod

from core.logger import get_logger

from ingestion.common.file_hash import (
    calculate_file_hash,
)

from models.import_result import (
    ImportResult,
)

from repositories.import_history_repo import (
    ImportHistoryRepository,
)

from models.importhistory import (
    ImportHistory,
)

from models.import_audit import ImportAuditStatus

import yfinance as yf

logger = get_logger(__name__)


class BaseIngestionService(ABC):
    """
    Base class for all ingestion services.

    Implements the common ingestion workflow:

        1. Resolve account
        2. Calculate file hash
        3. Check duplicate import
        4. Load CSV
        5. Validate CSV
        6. Persist data
        7. Record import history
        8. Return ImportResult
    """

    def __init__(
        self,
        account_repo,
        import_history_repo,
        loader,
        validator,
        import_audit_service,
    ):

        self._account_repo = account_repo
        self._import_history_repo = (import_history_repo)
        self._loader = loader
        self._validator = validator
        self._import_audit_service = import_audit_service

    def ingest(
        self,
        csv_file: str,
        name: str,
        snapshot_date=None,
        dry_run: bool = False,
    ) -> ImportResult:

        print("Reached BaseIngestionService")
        logger.info(f"Starting {self.import_type} import for account '{name}'")
        logger.info(f"Calculating file hash: {csv_file}")

        file_hash = calculate_file_hash(csv_file)

        logger.debug(f"File hash: {file_hash}")

        account = self._get_account(name)

        logger.info(
            f"Resolved account "
            f"'{name}' "
            f"(id={account.id})"
        )

        logger.info("Checking import history")

        self._check_duplicate_import(
            account_id=account.id,
            file_hash=file_hash,
        )

        logger.info(f"Loading CSV: {csv_file}")

        dataframe = self._loader.load(csv_file)
        logger.info("Loader returned object of type: %s", type(dataframe).__name__)
        logger.debug("Loader class: %s",type(dataframe))
        logger.info("Loader returned type: %s",type(dataframe).__name__)

        if isinstance(dataframe, list):
            logger.info(
                "List contains %d objects.",
                len(dataframe),
            )

            if dataframe:
                logger.info(
                    "First object type: %s",
                    type(dataframe[0]).__name__,
                )
        logger.info(f"Loaded {len(dataframe)} rows")

        logger.info("Validating CSV contents")
        self._validator.validate(dataframe)
        logger.info("Validation successful")

        if dry_run:
            logger.info("Dry run requested.")

            return ImportResult(
                account_id=account.id,
                account_name=name,
                institution=account.institution,
                import_type=self.import_type,
                filename=csv_file,
                snapshot_date=snapshot_date,
                rows_read=len(dataframe),
                rows_imported=0,
                rows_skipped=0,
                import_history_id=None,
                snapshot_id=None,
                elapsed_ms=0,
                status="SUCCESS",
                warnings=[],
            )

        history = ImportHistory(
            account_id=account.id,
            import_type=self.import_type,
            institution=account.institution,
            filename=csv_file,
            file_hash=file_hash,
            snapshot_date=snapshot_date,
            status="RUNNING",
        )

        import_history = self._record_import(
            history,
        )   

        logger.info(f"Persisting {len(dataframe)} rows")
        num_rows_imported = self.persist(
            dataframe=dataframe,
            account=account,
            snapshot_date=snapshot_date,
            import_history_id=import_history.id,
        )
        logger.info(f"Persisted {num_rows_imported} rows")

        logger.info("Recording import history")

        
        import_history.rows_read = len(dataframe)
        import_history.rows_imported = num_rows_imported
        import_history.rows_skipped = len(dataframe) - num_rows_imported
        import_history.status = "SUCCESS"
        updated_import_history = self._record_import(
            import_history,
        )
        logger.info(
            f"{self.import_type} import "
            f"completed successfully"
        )

        # ---------------------------------------------------------
        # Audit the completed import
        # ---------------------------------------------------------

        logger.info(
            "Starting import audit "
            "for import_id=%s",
            updated_import_history.id,
        )

        audit_result = self._import_audit_service.audit(
            updated_import_history.id,
        )

        if audit_result.status != ImportAuditStatus.PASS:
            logger.error(
                "Import audit FAILED "
                "for import_id=%s: %s",
                updated_import_history.id,
                audit_result.message,
            )

            raise ValueError(
                f"Import audit failed: "
                f"{audit_result.message}"
            )
        #An import isn't considered successfully completed unless the persisted data passes the audit.
        logger.info(
            "Import audit completed "
            "for import_id=%s: status=%s, message=%s",
            updated_import_history.id,
            audit_result.status,
            audit_result.message,
        )

        logger.info(
            f"{self.import_type} import "
            f"completed successfully"
        )


        return ImportResult(
            account_id=account.id,
            account_name=name,
            institution=account.institution,
            import_type=self.import_type,
            filename=csv_file,
            snapshot_date=snapshot_date,
            rows_read=len(dataframe),
            rows_imported=num_rows_imported,
            rows_skipped=len(dataframe) - num_rows_imported,
            import_history_id=updated_import_history.id,
            snapshot_id=None,
            elapsed_ms=0,
            status="SUCCESS",
            warnings=[],
        )

    def _get_account(
        self,
        account_name: str,
    ):

        account = (
            self._account_repo
            .get_by_name(account_name)
        )

        if account is None:

            logger.error(
                f"Account not found: "
                f"{account_name}"
            )

            raise ValueError(
                f"Unknown account: "
                f"{account_name}"
            )

        logger.info(
            f"Resolved account:"
            f" id={account.id},"
            f" name={account.name},"
            f" number={account.account_number}"
        )

        return account

    def _check_duplicate_import(
        self,
        account_id: int,
        file_hash: str,
    ) -> None:

        logger.info(
            f"Checking if import already exists for account_id={account_id}, import_type={self.import_type}, file_hash={file_hash}"
        )
        logger.info(type(self._import_history_repo))
        logger.info(dir(self._import_history_repo))

        exists = (
            self._import_history_repo
            .exists(
                account_id=account_id,
                import_type=self.import_type,
                file_hash=file_hash,
            )
        )

        if exists:

            logger.warning(
                f"Duplicate import detected "
                f"for import_type="
                f"{self.import_type}"
            )

            raise ValueError(
                "File has already "
                "been imported."
            )

    def _record_import(
        self, 
        history: ImportHistory
    ) -> ImportHistory:

        if history.id is None:
            new_import_history = self._import_history_repo.insert(history)

            logger.info(
                "Import history created for %s: id=%s",
                self.import_type,
                new_import_history.id,
            )

            return new_import_history

        updated_import_history = self._import_history_repo.update(
            history
        )

        logger.info(
            "Import history updated for %s: id=%s",
            self.import_type,
            updated_import_history.id,
        )

        return updated_import_history

    @property
    def account_repo(self):
        """
        Read-only access to the account repository.

        Used by CLI helpers for account validation
        and account selection.
        """
        return self._account_repo    

    @property
    @abstractmethod
    def import_type(self) -> str:
        """
        Returns:
            positions
            transactions
        """
        pass

    @abstractmethod
    def persist(
        self,
        dataframe,
        account,
        snapshot_date=None,
        import_history_id=None,
    ) -> int:
        """
        Persist imported data.

        Returns:
            Number of rows imported.
        """
        pass

    @classmethod
    @abstractmethod
    def build(cls):
        """
        Construct and return a fully configured ingestion service.
        """
        raise NotImplementedError