from src.core.logger import get_logger


class IngestionService:
    def __init__(
        self, snapshot_repo, account_repo, security_repo, position_repo, loader
    ):
        self.snapshot_repo = snapshot_repo
        self.account_repo = account_repo
        self.security_repo = security_repo
        self.position_repo = position_repo
        self.loader = loader

        self.logger = get_logger(self.__class__.__name__)

    def run(self, file_path: str, snapshot_date: str, confirm: bool) -> dict:
        """
        Execute the portfolio ingestion pipeline.

        Responsibilities:
        - enforce confirmation gate
        - enforce snapshot idempotency
        - load CSV data
        - normalize accounts and securities
        - insert positions
        """

        # --------------------------------------------------
        # Confirmation gate
        # --------------------------------------------------
        if not confirm:
            raise ValueError("Ingestion not confirmed")

        self.logger.info(f"Starting ingestion for snapshot_date={snapshot_date}")

        # --------------------------------------------------
        # Idempotency check
        # --------------------------------------------------
        self.logger.info(f"Checking for existing snapshot: {snapshot_date}")

        existing_snapshot = self.snapshot_repo.get_by_date(snapshot_date)

        if existing_snapshot:
            error_msg = f"Snapshot already exists for date: {snapshot_date}"

            self.logger.error(error_msg)

            raise ValueError(error_msg)

        # --------------------------------------------------
        # Load CSV
        # --------------------------------------------------
        self.logger.info(f"Loading CSV file: {file_path}")

        rows = self.loader.load(file_path)

        if not rows:
            error_msg = "CSV file contains no rows"

            self.logger.error(error_msg)

            raise ValueError(error_msg)

        self.logger.info(f"Loaded {len(rows)} rows")

        # --------------------------------------------------
        # Create snapshot
        # --------------------------------------------------
        self.logger.info(f"Creating snapshot for date: {snapshot_date}")

        snapshot_id = self.snapshot_repo.create(snapshot_date)

        self.logger.info(f"Created snapshot_id={snapshot_id}")

        # --------------------------------------------------
        # Process rows
        # --------------------------------------------------
        self.logger.info("Processing portfolio positions")

        for row in rows:
            self.logger.info(f"Processing row: {row}")

            # ----------------------------------------------
            # Account normalization
            # ----------------------------------------------
            account_id = self.account_repo.get_or_create(
                account_number=row["account_number"],
                account_name=row.get("account_name"),
                provider=row.get("provider", "unknown"),
            )

            # ----------------------------------------------
            # Security normalization
            # ----------------------------------------------
            security_id = self.security_repo.get_or_create(
                ticker=row["symbol"],
                description=row.get("description"),
                asset_type=row.get("type"),
            )

            # ----------------------------------------------
            # Insert position
            # ----------------------------------------------
            self.position_repo.insert(
                snapshot_id=snapshot_id,
                account_id=account_id,
                security_id=security_id,
                quantity=row.get("quantity"),
                avg_cost=row.get("average_cost_basis"),
                cost_basis_total=row.get("cost_basis_total"),
                market_value=row.get("current_value"),
                percent_of_account=row.get("percent_of_account"),
                daily_gain=row.get("todays_gain_loss_dollar"),
                daily_gain_pct=row.get("todays_gain_loss_percent"),
                total_gain=row.get("total_gain_loss_dollar"),
                total_gain_pct=row.get("total_gain_loss_percent"),
            )

        # --------------------------------------------------
        # Completion
        # --------------------------------------------------
        self.logger.info(
            f"Ingestion complete. snapshot_id={snapshot_id}, rows_processed={len(rows)}"
        )

        return {
            "status": "success",
            "snapshot_id": snapshot_id,
            "snapshot_date": snapshot_date,
            "rows_processed": len(rows),
        }
