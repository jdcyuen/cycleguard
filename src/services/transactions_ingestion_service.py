from ingestion.positions import positions_validators
from models.security import Security                                                                                    
import pandas as pd


from core.logger import get_logger

from config.config_manager import (
    get_config,
)

from database.connection import DBConnection

from services.base_ingestion_service import (
    BaseIngestionService,
)

from ingestion.transactions.transactions_csv_loader import (
    TransactionsCSVLoader,
)

from ingestion.transactions.transactions_validators import (
    TransactionsValidator,
)

from repositories.account_repo import (
    AccountRepository,
)

from repositories.security_repo import (
    SecurityRepository,
)

from repositories.transaction_repo import (
    TransactionRepository,
)

from repositories.import_history_repo import (
    ImportHistoryRepository,
)

from models.transaction import Transaction
from services.security_resolution_service import (
    SecurityResolutionService,
)


logger = get_logger(__name__)


class TransactionsIngestionService(BaseIngestionService):

    def __init__(
        self,
        account_repo,
        security_repo,
        transaction_repo,
        import_history_repo,
        security_resolution_service,
        loader,
        validator,
    ):

        super().__init__(
            account_repo=account_repo,
            import_history_repo=import_history_repo,
            loader=loader,
            validator=validator,
        )

        self._security_repo = security_repo
        self._transaction_repo = (
            transaction_repo
        )
        self._security_resolution_service = security_resolution_service

    @property
    def import_type(self) -> str:

        return "transactions"

    @classmethod
    def build(cls):

        logger.info(
            "Building TransactionsIngestionService"
        )

        conn = DBConnection().connect()

        config = get_config()

        action_map = config["system"]["action_map"]["actions"]

        logger.debug(
            "Loaded %d action mapping rules.",
            len(action_map),
        )

        logger.debug(
            "First rule: %s",
            action_map[0] if action_map else None,
        )

        security_resolution_service = SecurityResolutionService(
            security_repo=SecurityRepository(conn),
        )

        return cls(
            account_repo=AccountRepository(conn),
            security_repo=SecurityRepository(conn),
            transaction_repo=TransactionRepository(conn),
            import_history_repo=ImportHistoryRepository(conn),
            loader=TransactionsCSVLoader(action_map=action_map),
            validator=TransactionsValidator(),
            security_resolution_service=security_resolution_service,
        )

    

    @staticmethod
    def _null_if_na(value):
        logger.debug(
            "_null_if_na(): value=%r (%s)",
            value,
            type(value).__name__,
        )

        if pd.isna(value):
            logger.debug(
                "_null_if_na(): converting %r to None",
                value,
            )
            return None

        logger.debug(
            "_null_if_na(): leaving value unchanged: %r",
            value,
        )

        return value

    def _to_transaction(
        self,
        row,
        account_id: int,
        security_id: int | None,
        import_history_id: int | None = None,
    ) -> Transaction:
        """
        Convert a cleaned DataFrame row into a Transaction object.
        """

        transaction = Transaction(
            account_id=account_id,
            security_id=security_id,
            run_date=self._null_if_na(row.run_date),
            settlement_date=self._null_if_na(row.settlement_date),
            action=self._null_if_na(row.action),
            trade_type=self._null_if_na(row.trade_type),
            price=self._null_if_na(row.price),
            quantity=self._null_if_na(row.quantity),
            commission=self._null_if_na(row.commission),
            fees=self._null_if_na(row.fees),
            accrued_interest=self._null_if_na(row.accrued_interest),
            amount=self._null_if_na(row.amount),
            cash_balance=self._null_if_na(row.cash_balance),
            import_history_id=import_history_id,
        )

        logger.debug(
            "Created Transaction:\n%s",
            transaction,
        )

        return transaction

    def persist(
        self,
        dataframe,
        account,
        snapshot_date=None,
        import_history_id=None,
    ) -> int:

        logger.info(
            "Processing %d transactions for account_id=%d",
            len(dataframe),
            account.id,
        )

        logger.debug(
    "Transaction DataFrame columns:\n%s",
    "\n".join(dataframe.columns),
)

        rows_imported = 0

        for row in dataframe.itertuples():

            try:
                security_id = None
                if row.symbol:

                    logger.debug(f"Resolving security {row.symbol}")
                    security = self._security_resolution_service.resolve(
                        Security(
                            symbol=row.symbol,
                            description=row.description
                        )
                    )
                    security_id = security.id
                    logger.info(f"Security resolved: {security}")


                transaction = self._to_transaction(
                    row=row,
                    account_id=account.id,
                    security_id=security_id,
                    import_history_id=import_history_id,
                )

                logger.debug(
                    "Persisting transaction: %s",
                    transaction,
                )

                if self._transaction_repo.exists(transaction):
                    logger.debug(
                        "Transaction already exists "
                        "action=%s, symbol=%s, amount=%s",
                        row.action,
                        row.symbol,
                        row.amount,
                    )
                    continue
                else:
                    self._transaction_repo.insert(
                        transaction
                    )
                    rows_imported += 1

            except Exception:

                logger.exception(
                    "Failed importing transaction "
                    "action=%s, symbol=%s, amount=%s",
                    row.action,
                    row.symbol,
                    row.amount,
                )
                raise

        logger.info(
            "Inserted %d transactions",
            rows_imported,
        )

        return rows_imported
