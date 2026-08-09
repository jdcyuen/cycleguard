
from models.snapshot import Snapshot
from models.security import Security
from models.position import Position
from core.logger import get_logger

from database.connection import DBConnection

from services.base_ingestion_service import (BaseIngestionService,)

from ingestion.positions.positions_csv_loader import (PositionsCSVLoader,)

from ingestion.positions.positions_validators import (PositionsValidator,)

from repositories.account_repo import (AccountRepository,)

from repositories.security_repo import (SecurityRepository,)

from repositories.snapshot_repo import (SnapshotRepository,)

from repositories.position_repo import (PositionRepository,)

from repositories.import_history_repo import (ImportHistoryRepository,)

from services.security_resolution_service import (SecurityResolutionService,)

logger = get_logger(__name__)


class PositionsIngestionServiceError(Exception):
    """Raised when positions ingestion fails."""

class SnapshotAlreadyExistsError(PositionsIngestionServiceError):
    """
    Raised when attempting to import a snapshot that
    already exists for an account and snapshot date.
    """

class PositionsIngestionService(BaseIngestionService):

    def __init__(
        self,
        account_repo,
        security_repo,
        snapshot_repo,
        position_repo,
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
        self._snapshot_repo = snapshot_repo
        self._position_repo = position_repo
        self._security_resolution_service = security_resolution_service

    @property
    def import_type(self) -> str:

        return "positions"

    @classmethod
    def build(cls):

        logger.info("Building PositionsIngestionService" )

        try:

            conn = DBConnection().connect()

            security_resolution_service = SecurityResolutionService(
                security_repo=SecurityRepository(conn),
            )

            return cls(
                account_repo=AccountRepository(conn),
                security_repo=SecurityRepository(conn),
                snapshot_repo=SnapshotRepository(conn),
                position_repo=PositionRepository(conn),
                import_history_repo=ImportHistoryRepository(conn),
                loader=PositionsCSVLoader(),
                validator=PositionsValidator(),
                security_resolution_service=security_resolution_service,
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


    def _to_position(
        self,
        row,
        account_id: int,
        snapshot_id: int,
        security_id: int,
            import_history_id: int,
    ) -> Position:
        return Position(
            account_id=account_id,
            security_id=security_id,
            snapshot_id=snapshot_id,
            import_history_id=import_history_id,

            quantity=row.quantity,
            ave_cost=row.average_cost_basis,
            cost_basis_total=row.cost_basis_total,
            current_value=row.current_value,
            percent_of_account=row.percent_of_account,
            daily_gain=row.todays_gain_loss_dollar,
            daily_gain_pct=row.todays_gain_loss_percent,
            total_gain=row.total_gain_loss_dollar,
            total_gain_pct=row.total_gain_loss_percent,
        )

    def persist(
        self,
        dataframe,
        account,
        snapshot_date,
        import_history_id
    ) -> int:

        logger.info(
            "Beginning positions persistence "
            "for account='%s' (id=%s)",
            account.name,
            account.id,
        )
        try:

            existing = self._snapshot_repo.get_by_account_and_date(
                account.id,
                snapshot_date,
            )

            if existing:
                logger.warning(
                    "Snapshot already exists. "
                    "account='%s', snapshot_date=%s, snapshot_id=%s",
                    account.name,
                    snapshot_date,
                    existing.id,
                )

                raise SnapshotAlreadyExistsError(
                    f"Snapshot already exists for account "
                    f"'{account.name}' on {snapshot_date}."
                )

            logger.info(f"Creating snapshot for account_id={account.id}")

            snapshot = self._snapshot_repo.create(
                Snapshot(
                    account_id=account.id,
                    snapshot_date=snapshot_date,
                    import_history_id=import_history_id,
                )
            )

            logger.info(f"Created snapshot id={snapshot.id}")

        except SnapshotAlreadyExistsError:
            raise

        except Exception as exc:

            logger.exception(f"Failed creating snapshot for account_id={account.id}")

            raise PositionsIngestionServiceError(
                f"Unable to create snapshot "
                f"for account_id={account.id}"
            ) from exc

        rows_imported = 0

        for row in dataframe.itertuples():

            try:
                if row.symbol:
                    logger.debug(f"Resolving security {row.symbol}")
                    security = self._security_resolution_service.resolve(
                        Security(
                            symbol=row.symbol,
                            description=row.description,
                    )
                )
                logger.info(f"Security resolved: {security}")

                logger.debug(
                    f"Inserting position "
                    f"symbol={row.symbol}, "
                    f"description={row.description}, "
                )

                position = self._to_position(
                    row=row,
                    account_id=account.id,
                    snapshot_id=snapshot.id,
                    security_id=security.id,
                    import_history_id=import_history_id,
                )

                logger.debug(
                    "Created Position model "
                    "symbol=%s quantity=%s current_value=%s",
                    security.symbol,
                    position.quantity,
                    position.current_value,
                )

                logger.debug(
                    "Persisting position "
                    "for security_id=%s",
                    security.id,
                )
                
                self._position_repo.insert(position)

                rows_imported += 1

                logger.info(
                    "Imported position %d: %s",
                    rows_imported,
                    security.symbol,
                )

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
            f"{snapshot.id}"
        )

        return rows_imported