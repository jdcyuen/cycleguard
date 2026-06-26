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


logger = get_logger(__name__)


class TransactionsIngestionService(
    BaseIngestionService
):

    def __init__(
        self,
        account_repo,
        security_repo,
        transaction_repo,
        import_history_repo,
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

        action_map = config["system"]["action_map"]

        return cls(
            account_repo=AccountRepository(conn),
            security_repo=SecurityRepository(conn),
            transaction_repo=TransactionRepository(conn),
            import_history_repo=ImportHistoryRepository(conn),
            loader=TransactionsCSVLoader(),
            validator=TransactionsValidator(action_map=action_map),
        )

    def persist(
        self,
        dataframe,
        account,
    ) -> int:

        logger.info(
            f"Processing "
            f"{len(dataframe)} transactions "
            f"for account_id={account.id}"
        )

        rows_imported = 0

        for row in dataframe.itertuples():

            try:

                security_id = None

                if row.symbol:

                    logger.debug(
                        f"Resolving security "
                        f"{row.symbol}"
                    )

                    security = (
                        self._security_repo
                        .get_or_create(
                            symbol=row.symbol
                        )
                    )

                    security_id = security.id

                logger.debug(
                    f"Inserting transaction "
                    f"security_id={security_id}, "
                    f"action={row.action}, "
                    f"symbol={row.symbol}, "
                    f"amount={row.amount}"
                )

                self._transaction_repo.insert(
                    account_id=account.id,
                    security_id=security_id,
                    run_date=row.run_date,
                    settlement_date=row.settlement_date,
                    action=row.action,
                    trade_type=row.trade_type,
                    price=row.price,
                    quantity=row.quantity,
                    commission=row.commission,
                    fees=row.fees,
                    accrued_interest=row.accrued_interest,
                    amount=row.amount,
                    cash_balance=row.cash_balance,
                )

                rows_imported += 1

            except Exception:

                logger.exception(
                    f"Failed importing "
                    f"transaction "
                    f"action={row.action}, "
                    f"symbol={row.symbol}, "
                    f"amount={row.amount}"
                )

                raise

        logger.info(
            f"Inserted "
            f"{rows_imported} transactions"
        )

        return rows_imported