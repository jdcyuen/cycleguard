from abc import ABC, abstractmethod

from core.logger import get_logger

from ingestion.common.file_hash import (
    calculate_file_hash,
)

from ingestion.common.import_result import (
    ImportResult,
)

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
    ):

        self._account_repo = account_repo
        self._import_history_repo = (
            import_history_repo
        )
        self._loader = loader
        self._validator = validator

    def ingest(
        self,
        csv_file: str,
        account_name: str,
    ) -> ImportResult:

        logger.info(
            f"Starting {self.import_type} import "
            f"for account '{account_name}'"
        )

        logger.info(
            f"Calculating file hash: {csv_file}"
        )

        file_hash = calculate_file_hash(
            csv_file
        )

        logger.debug(
            f"File hash: {file_hash}"
        )

        account = self._get_account(
            account_name
        )

        logger.info(
            f"Resolved account "
            f"'{account_name}' "
            f"(id={account.id})"
        )

        logger.info(
            "Checking import history"
        )

        self._check_duplicate_import(
            account_id=account.id,
            file_hash=file_hash,
        )

        logger.info(
            f"Loading CSV: {csv_file}"
        )

        dataframe = self._loader.load(
            csv_file
        )

        logger.info(
            f"Loaded "
            f"{len(dataframe)} rows"
        )

        logger.info(
            "Validating CSV contents"
        )

        self._validator.validate(
            dataframe
        )

        logger.info(
            "Validation successful"
        )

        logger.info(
            f"Persisting "
            f"{len(dataframe)} rows"
        )

        rows_imported = self.persist(
            dataframe=dataframe,
            account=account,
        )

        logger.info(
            f"Persisted "
            f"{rows_imported} rows"
        )

        logger.info(
            "Recording import history"
        )

        self._record_import(
            account_id=account.id,
            file_name=csv_file,
            file_hash=file_hash,
            row_count=rows_imported,
        )

        logger.info(
            f"{self.import_type} import "
            f"completed successfully"
        )

        return ImportResult(
            account_name=account_name,
            import_type=self.import_type,
            rows_imported=rows_imported,
            file_name=csv_file,
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

        return account

    def _check_duplicate_import(
        self,
        account_id: int,
        file_hash: str,
    ) -> None:

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
        account_id: int,
        file_name: str,
        file_hash: str,
        row_count: int,
    ) -> None:

        self._import_history_repo.insert(
            account_id=account_id,
            import_type=self.import_type,
            file_name=file_name,
            file_hash=file_hash,
            row_count=row_count,
        )

        logger.info(
            f"Import history recorded "
            f"for {self.import_type}"
        )

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
    ) -> int:
        """
        Persist imported data.

        Returns:
            Number of rows imported.
        """
        pass