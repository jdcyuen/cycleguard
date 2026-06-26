from core.logger import get_logger

from database.connection import DBConnection

from services.base_ingestion_service import (
    BaseIngestionService,
)

from ingestion.positions.positions_csv_loader import (
    PositionsCSVLoader,
)

from ingestion.positions.positions_validators import (
    PositionsValidator,
)

from repositories.account_repo import (
    AccountRepository,
)

from repositories.security_repo import (
    SecurityRepository,
)

from repositories.snapshot_repo import (
    SnapshotRepository,
)

from repositories.position_repo import (
    PositionRepository,
)

from repositories.import_history_repo import (
    ImportHistoryRepository,
)

logger = get_logger(__name__)


class PositionsIngestionServiceError(Exception):
    """Raised when positions ingestion fails."""


class PositionsIngestionService(
    BaseIngestionService
):

    def __init__(
        self,
        account_repo,
        security_repo,
        snapshot_repo,
        position_repo,
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
        self._snapshot_repo = snapshot_repo
        self._position_repo = position_repo

    @property
    def import_type(self) -> str:

        return "positions"

    @classmethod
    def build(cls):

        logger.info(
            "Building PositionsIngestionService"
        )

        try:

            conn = DBConnection().connect()

            return cls(
                account_repo=AccountRepository(conn),
                security_repo=SecurityRepository(conn),
                snapshot_repo=SnapshotRepository(conn),
                position_repo=PositionRepository(conn),
                import_history_repo=ImportHistoryRepository(conn),
                loader=PositionsCSVLoader(),
                validator=PositionsValidator(),
            )

        except Exception as exc:

            logger.exception(
                "Failed building "
                "PositionsIngestionService"
            )

            raise PositionsIngestionServiceError(
                "Unable to initialize "
                "positions ingestion service."
            ) from exc

    def persist(
        self,
        dataframe,
        account,
    ) -> int:

        try:

            logger.info(
                f"Creating snapshot for "
                f"account_id={account.id}"
            )

            snapshot_id = (
                self._snapshot_repo
                .create_snapshot(
                    account_id=account.id
                )
            )

            logger.info(
                f"Created snapshot "
                f"id={snapshot_id}"
            )

        except Exception as exc:

            logger.exception(
                f"Failed creating snapshot "
                f"for account_id={account.id}"
            )

            raise PositionsIngestionServiceError(
                f"Unable to create snapshot "
                f"for account_id={account.id}"
            ) from exc

        rows_imported = 0

        for row in dataframe.itertuples():

            try:

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

                logger.debug(
                    f"Inserting position "
                    f"symbol={row.symbol}, "
                    f"quantity={row.quantity}"
                )

                self._position_repo.insert(
                    snapshot_id=snapshot_id,
                    security_id=security.id,
                    quantity=row.quantity,
                    market_value=row.market_value,
                    cost_basis=row.cost_basis,
                )

                rows_imported += 1

            except Exception as exc:

                logger.exception(
                    f"Failed importing "
                    f"position "
                    f"symbol={row.symbol}"
                )

                raise PositionsIngestionServiceError(
                    f"Unable to import position "
                    f"for symbol "
                    f"'{row.symbol}'"
                ) from exc

        logger.info(
            f"Inserted "
            f"{rows_imported} positions "
            f"for snapshot "
            f"{snapshot_id}"
        )

        return rows_imported