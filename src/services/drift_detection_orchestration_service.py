
"""
CycleGuard Drift Detection Orchestration Service
================================================

PURPOSE
-------
Coordinates the drift detection workflow for a configured investment
account. It matches database accounts to YAML account configurations,
selects the latest stored portfolio snapshot, and delegates drift
calculations to the existing DriftDetectionService.

WHY THIS MODULE EXISTS
----------------------
CycleGuard supports multiple execution modes: the main dashboard, a
standalone Drift Detection dashboard, and a command-line interface.
Without a shared orchestration layer, each entry point would need to
implement its own account matching, snapshot selection, and evaluation
workflow. That duplication creates inconsistent behavior and increases
maintenance and testing costs.

This module centralizes the workflow so all execution modes use the
same application-level behavior and drift calculation engine.

ARCHITECTURAL POSITION
----------------------
This module belongs to the application/service orchestration layer.

Execution entry points:
    - Command-line interface
    - Standalone Streamlit application
    - Main CycleGuard dashboard

                |
                v

DriftDetectionOrchestrationService
    - Matches database accounts to YAML configurations
    - Retrieves the latest stored snapshot
    - Coordinates the evaluation workflow
    - Returns a structured result or propagates failures

                |
                v

Existing service and persistence layers:
    - DriftDetectionService
    - PortfolioAggregationService
    - AccountConfigLoader
    - AccountRepository
    - SnapshotRepository
    - PositionRepository

RESPONSIBILITIES AND DESIGN PRINCIPLES
--------------------------------------
1. Single Responsibility:
   Coordinates the drift detection workflow. It does not implement
   drift formulas, database queries, or presentation logic.

2. Dependency Inversion:
   Receives repositories and the configuration loader through
   constructor injection, allowing isolated unit tests.

3. Separation of Concerns:
   DriftDetectionService owns drift calculations; repositories own
   persistence; entry points own user interaction and output formatting.

4. Consistent Behavior:
   Account matching uses the existing dashboard normalization rule.
   Evaluation uses the latest stored snapshot and the configured
   account targets and bucket mappings.

ERROR HANDLING AND OBSERVABILITY
--------------------------------
A missing snapshot is a normal business outcome represented in the
returned result. Invalid account or snapshot identifiers raise
ValueError. Unexpected configuration, repository, database, or
calculation failures are logged with traceback information and
re-raised so callers can handle the failure appropriately.

Logs record workflow milestones and failures without deliberately
logging full account numbers or position-level financial details.

DATA SAFETY
-----------
The orchestration workflow evaluates an existing stored snapshot. It
does not import positions, create snapshots, synchronize Fidelity data,
persist trade proposals, or execute trades. Read-only behavior depends
on the underlying services and repositories performing read operations.

EXTENSION GUIDANCE
------------------
New execution modes should call this service rather than reimplement
account matching or drift evaluation. New calculation rules belong in
DriftDetectionService or the appropriate domain service. UI formatting
belongs in the relevant presentation layer.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from config.account_config_loader import AccountConfigLoader
from core.logger import get_logger
from repositories.account_repo import AccountRepository
from repositories.position_repo import PositionRepository
from repositories.snapshot_repo import SnapshotRepository
from services.drift_detection_service import DriftDetectionService
from services.portfolio_aggregation_service import (
    PortfolioAggregationService,
)

logger = get_logger(__name__)


def normalize_account_number(value: Any) -> str:
    """Normalize account numbers using the existing dashboard rule."""
    if value is None:
        return ""
    return "".join(str(value).split()).strip()


def get_snapshot_date(snapshot: Any) -> date | None:
    """Return a snapshot date, accepting date or datetime values."""
    if snapshot is None:
        return None

    value = getattr(snapshot, "snapshot_date", None)
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return None


@dataclass(slots=True)
class DriftDetectionResult:
    """Structured outcome for one account's latest stored snapshot."""

    database_account: Any
    account_config: Any
    snapshot: Any = None
    rows: list[dict[str, Any]] = field(default_factory=list)
    message: str | None = None

    @property
    def snapshot_date(self) -> date | None:
        """Return the selected snapshot's date, when available."""
        return get_snapshot_date(self.snapshot)


class DriftDetectionOrchestrationService:
    """Coordinate account matching and drift evaluation."""

    def __init__(
        self,
        db_connection: Any,
        account_repository: AccountRepository,
        snapshot_repository: SnapshotRepository,
        config_loader: AccountConfigLoader | None = None,
    ) -> None:
        if db_connection is None:
            raise ValueError("db_connection is required.")
        if account_repository is None:
            raise ValueError("account_repository is required.")
        if snapshot_repository is None:
            raise ValueError("snapshot_repository is required.")

        self.db_connection = db_connection
        self.account_repository = account_repository
        self.snapshot_repository = snapshot_repository
        self.config_loader = (
            config_loader if config_loader is not None else AccountConfigLoader()
        )

    def list_configured_accounts(self) -> list[tuple[Any, Any]]:
        """Match database accounts to YAML configurations by account number."""
        try:
            configurations = self.config_loader.load()
            database_accounts = self.account_repository.list_accounts()
        except Exception:
            logger.exception(
                "Failed to load account configurations or database accounts."
            )
            raise

        configs_by_number = {}
        for config in configurations:
            account_number = normalize_account_number(
                getattr(config, "account_number", None)
            )
            if account_number:
                configs_by_number[account_number] = config

        matched = []
        unmatched_count = 0

        for account in database_accounts:
            account_number = normalize_account_number(
                getattr(account, "account_number", None)
            )
            config = configs_by_number.get(account_number)

            if config is None:
                unmatched_count += 1
                logger.warning(
                    "No YAML configuration matched database account %s.",
                    getattr(account, "name", "<unnamed>"),
                )
                continue

            matched.append((account, config))

        logger.info(
            "Drift account matching completed: %d matched, %d unmatched.",
            len(matched),
            unmatched_count,
        )
        return matched

    def evaluate_account(
        self,
        database_account: Any,
        account_config: Any,
    ) -> DriftDetectionResult:
        """Evaluate drift using an account's latest stored snapshot."""
        if database_account is None:
            raise ValueError("database_account is required.")
        if account_config is None:
            raise ValueError("account_config is required.")

        account_id = getattr(database_account, "id", None)
        if not isinstance(account_id, int) or isinstance(account_id, bool):
            raise ValueError(
                "Database account must have a valid integer ID."
            )

        account_label = getattr(database_account, "name", "<unnamed>")

        try:
            snapshot = self.snapshot_repository.get_latest_by_account(
                account_id
            )
        except Exception:
            logger.exception(
                "Failed to retrieve the latest snapshot for account %s.",
                account_label,
            )
            raise

        if snapshot is None:
            logger.warning(
                "No stored snapshot exists for account %s.",
                account_label,
            )
            return DriftDetectionResult(
                database_account=database_account,
                account_config=account_config,
                message="No stored snapshot exists for this account.",
            )

        snapshot_id = getattr(snapshot, "id", None)
        if not isinstance(snapshot_id, int) or isinstance(snapshot_id, bool):
            raise ValueError(
                "Latest snapshot must have a valid integer ID."
            )

        try:
            position_repository = PositionRepository(self.db_connection)
            portfolio_service = PortfolioAggregationService(
                position_repository,
                account_config,
            )
            drift_service = DriftDetectionService(
                portfolio_service,
                account_config,
            )
            rows = drift_service.evaluate(snapshot_id)
        except Exception:
            logger.exception(
                "Drift evaluation failed for account %s, snapshot ID %s.",
                account_label,
                snapshot_id,
            )
            raise

        logger.info(
            "Drift evaluation completed for account %s, snapshot ID %s: "
            "%d result rows.",
            account_label,
            snapshot_id,
            len(rows),
        )

        return DriftDetectionResult(
            database_account=database_account,
            account_config=account_config,
            snapshot=snapshot,
            rows=rows,
        )
