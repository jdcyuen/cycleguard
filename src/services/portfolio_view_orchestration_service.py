
"""
CycleGuard Portfolio View Orchestration Service
================================================

MODULE
------
src/services/portfolio_view_orchestration_service.py

PURPOSE
-------
Provides a centralized application-level orchestration service for
retrieving, aggregating, analyzing, and presenting portfolio
allocation information across CycleGuard investment accounts.

The service establishes a consistent workflow for calculating actual
portfolio allocations from stored positions and comparing them with
target allocations defined in YAML account configurations.

ARCHITECTURAL POSITION
----------------------
This module belongs to the application/service orchestration layer.

Execution entry points:
    - Command-line interface (CLI)
    - Standalone Streamlit Portfolio View
    - Main CycleGuard Streamlit dashboard

                |
                v

PortfolioViewOrchestrationService
    - Reconciles YAML configurations with database accounts
    - Identifies active, configured investment accounts
    - Retrieves the latest stored portfolio snapshots
    - Coordinates actual allocation calculations
    - Coordinates target allocation calculations
    - Aggregates portfolio information across accounts
    - Validates allocation mappings and configuration consistency
    - Returns structured results to calling applications

                |
                v

Existing services, configuration, and persistence layers:
    - AccountReconciliationService
    - AccountConfigLoader
    - AccountRepository
    - SnapshotRepository
    - PositionRepository
    - Canonical bucket configuration (buckets.yaml)

RESPONSIBILITIES
---------------
1. Account Reconciliation
   Uses AccountReconciliationService to identify active accounts
   whose database records match their YAML configurations.
   Historical, pending-registration, and duplicate accounts are
   excluded from normal portfolio selection.

2. Snapshot Retrieval
   Retrieves the latest stored snapshot for each selected account
   through SnapshotRepository.

3. Actual Portfolio Allocation
   Retrieves stored positions through PositionRepository and
   coordinates their classification into configured investment
   buckets using account-specific bucket mappings.

4. Target Portfolio Allocation
   Reads bucket weights, security targets, and security-to-bucket
   mappings from the account's YAML configuration.

5. Multi-Account Aggregation
   Coordinates combined portfolio calculations using market values
   rather than averaging account-level percentages.

6. Configuration and Allocation Validation
   Identifies missing snapshots, unmapped securities, missing
   security targets, and discrepancies between configured bucket
   weights and security-level targets.

7. Structured Results
   Returns application-level result objects independent of the
   presentation framework or execution environment.

DESIGN PRINCIPLES — SOLID
---------------------------
Single Responsibility Principle:
    Coordinates the portfolio-view workflow. It does not implement
    database queries, Streamlit presentation, CLI formatting, or
    independent domain calculation rules.

Open/Closed Principle:
    Structured result objects and injected dependencies allow
    additional execution modes and presentation capabilities without
    modifying the underlying orchestration workflow.

Liskov Substitution Principle:
    Depends on the behavioral contracts of repositories, services,
    and configuration loaders rather than requiring their concrete
    implementations in orchestration logic.

Interface Segregation Principle:
    Uses existing repository and service interfaces without
    introducing unnecessary methods or expanding unrelated contracts.

Dependency Inversion Principle:
    Receives database repositories and the configuration loader
    through constructor injection. High-level orchestration depends
    on abstractions and established service contracts.

SEPARATION OF CONCERNS
-----------------------
Orchestration Service:
    Coordinates account selection, snapshot retrieval, allocation
    workflows, aggregation, validation, and result construction.

Repositories:
    Own database persistence and retrieval operations.

Account Configuration:
    Defines account-specific bucket mappings, bucket weights,
    security targets, and portfolio settings.

Domain Services:
    Own specialized business rules and calculations where applicable.

Presentation Components:
    Own Streamlit widgets, charts, tables, dialogs, and formatting.

Execution Entry Points:
    Own CLI arguments, application startup, and invocation of the
    shared orchestration service.

ERROR HANDLING AND OBSERVABILITY
------------------------------
Expected business outcomes are represented in structured results,
including accounts without stored snapshots and incomplete
allocation information.

Invalid required arguments and identifiers raise ValueError.

Unexpected configuration, repository, database, reconciliation,
or calculation failures are logged with contextual information
and traceback details, then propagated to the calling application.

Logging records workflow milestones, account counts, snapshot
selection, aggregation outcomes, and failures.

Logs must not expose full account numbers or unnecessary
position-level financial details.

DATA SAFETY
-----------
The Portfolio View workflow is read-only.

It does not:
    - Import or modify financial positions.
    - Create, update, or delete portfolio snapshots.
    - Register or delete database accounts.
    - Modify account YAML configurations.
    - Synchronize brokerage account data.
    - Generate or persist trade orders.
    - Execute trades or rebalance portfolios.

Actual allocations are calculated from existing stored snapshots.
Target allocations are read from existing YAML configuration.

Missing snapshots must never be interpreted as zero-value
accounts or silently omitted from combined portfolio calculations.

EXECUTION CONSISTENCY
--------------------
All execution modes must use the same orchestration service
rather than independently implementing account reconciliation,
snapshot selection, allocation calculations, or aggregation.

This ensures consistent portfolio information across:
    - CLI output
    - Standalone Portfolio View
    - Main CycleGuard dashboard

TESTING
-------
Unit tests should validate:
    - Dependency validation and constructor behavior.
    - Active account reconciliation.
    - Latest snapshot retrieval.
    - Actual security and bucket allocation calculations.
    - Target bucket and security allocation calculations.
    - Multi-account aggregation and market-value weighting.
    - Missing snapshot and incomplete-data handling.
    - Unmapped security and target validation.
    - Allocation discrepancies.
    - Error propagation and logging.
    - Read-only behavior.

Test module:
    tests/services/test_portfolio_view_orchestration_service.py
"""

from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

from config.account_config_loader import AccountConfigLoader
from core.logger import get_logger
from models.portfolio_view import (
    PortfolioAccountView,
    PortfolioAllocation,
    PortfolioHolding,
    PortfolioViewResult,
)
from repositories.account_repo import AccountRepository
from repositories.position_repo import PositionRepository
from repositories.snapshot_repo import SnapshotRepository
from services.account_reconciliation_service import (
    AccountReconciliationService,
)
from models.account_config import AccountConfig


logger = get_logger(__name__)


class PortfolioViewOrchestrationService:
    """Coordinate the CycleGuard Portfolio View workflow."""

    def __init__(
        self,
        db_connection: Any,
        account_repository: AccountRepository,
        snapshot_repository: SnapshotRepository,
        position_repository: PositionRepository,
        config_loader: AccountConfigLoader | None = None,
    ) -> None:
        """Initialize the service with injected dependencies."""

        if db_connection is None:
            raise ValueError("db_connection is required.")

        if account_repository is None:
            raise ValueError("account_repository is required.")

        if snapshot_repository is None:
            raise ValueError("snapshot_repository is required.")

        if position_repository is None:
            raise ValueError("position_repository is required.")

        self.db_connection = db_connection
        self.account_repository = account_repository
        self.snapshot_repository = snapshot_repository
        self.position_repository = position_repository

        self.config_loader = (
            config_loader
            if config_loader is not None
            else AccountConfigLoader()
        )

        logger.info(
            "PortfolioViewOrchestrationService initialized."
        )
		
    def list_accounts(self) -> list[PortfolioAccountView]:
        """
        Return all active, reconciled accounts available to Portfolio View.

        Returns
        -------
        list[PortfolioAccountView]
            Active accounts with their matched database records and
            YAML configurations. Accounts without snapshots remain
            eligible for selection.

        Raises
        ------
        AccountReconciliationServiceError
            If account reconciliation cannot be completed.
        Exception
            Propagates unexpected reconciliation failures.
        """

        logger.info("Loading active accounts for Portfolio View.")

        try:
            reconciliation_service = AccountReconciliationService(
                account_repo=self.account_repository,
                loader=self.config_loader,
            )

            reconciliation_result = reconciliation_service.reconcile()

            accounts = [
                PortfolioAccountView(
                    database_account=match.database_account,
                    account_config=match.account_config,
                )
                for match in reconciliation_result.active_accounts
            ]

            logger.info(
                "Portfolio View loaded %d active accounts.",
                len(accounts),
            )

            return accounts

        except Exception:
            logger.exception(
                "Failed to load active accounts for Portfolio View."
            )
            raise

    def build_account_view(
        self,
        account_id: int,
    ) -> PortfolioAccountView:
        """
        Build the initial Portfolio View result for one active account.

        Identifies the account through active account reconciliation
        and retrieves its latest stored portfolio snapshot.

        Parameters
        ----------
        account_id : int
            Database identifier of the selected account.

        Returns
        -------
        PortfolioAccountView
            Account configuration and latest snapshot. If no snapshot
            exists, the result contains an informational message.

        Raises
        ------
        ValueError
            If the account ID is invalid or the account is not active.
        Exception
            Propagates unexpected reconciliation or repository errors.
        """

        if not isinstance(account_id, int) or isinstance(account_id, bool):
            raise ValueError("account_id must be an integer.")

        if account_id <= 0:
            raise ValueError("account_id must be greater than zero.")

        logger.info(
            "Building Portfolio View for account ID %d.",
            account_id,
        )

        try:
            accounts = self.list_accounts()

            account_view = next(
                (
                    account
                    for account in accounts
                    if account.database_account.id == account_id
                ),
                None,
            )

            if account_view is None:
                raise ValueError(
                    f"Account ID {account_id} is not an active "
                    "reconciled account."
                )

            snapshot = self.snapshot_repository.get_latest_by_account(
                account_id
            )

            if snapshot is None:
                account_view.message = (
                    "No portfolio snapshot is available for this account. "
                    "Actual allocation cannot be calculated."
                )

                logger.warning(
                    "No snapshot found for active account ID %d.",
                    account_id,
                )
            else:
                account_view.snapshot = snapshot

                logger.info(
                    "Retrieved latest snapshot for account ID %d.",
                    account_id,
                )

                account_view.holdings = (
                    self._add_bucket_mappings_to_positions(
                        snapshot_id=snapshot.id,
                        account_config=account_view.account_config,
                    )
                )
				
                # Load the permitted bucket identifiers.
                bucket_names = self._load_valid_bucket_names()

                # Calculate actual allocations using snapshot positions.
                account_view.actual_allocations = (
                    self._calculate_actual_allocations(
                        holdings=account_view.holdings,
                        bucket_names=bucket_names,
                    )
                )

                # Validate the snapshot's position percentages.
                self._validate_position_percentages(
                    holdings=account_view.holdings,
                    account_view=account_view,
                )

                logger.info(
                    "Calculated actual allocations for account %s.",
                    account_view.account_config.name,
                )

            return account_view

        except ValueError:
            raise

        except Exception:
            logger.exception(
                "Failed to build Portfolio View for account ID %d.",
                account_id,
            )
            raise
			
    def _add_bucket_mappings_to_positions(
        self,
        snapshot_id: int,
        account_config: AccountConfig,
    ) -> list[PortfolioHolding]:
        """
        Retrieve snapshot positions and associate their configured buckets.

        Parameters
        ----------
        snapshot_id : int
            Database identifier of the portfolio snapshot.
        account_config : AccountConfig
            Account YAML configuration containing bucket mappings.

        Returns
        -------
        list[PortfolioHolding]
            Existing database positions enriched with bucket
            classifications. Unmapped positions are retained.

        Raises
        ------
        ValueError
            If snapshot_id is invalid.
        Exception
            Propagates unexpected repository or processing failures.
        """

        if not isinstance(snapshot_id, int) or isinstance(snapshot_id, bool):
            raise ValueError("snapshot_id must be an integer.")

        if snapshot_id <= 0:
            raise ValueError("snapshot_id must be greater than zero.")

        if account_config is None:
            raise ValueError("account_config is required.")

        logger.info(
            "Adding bucket mappings to positions for snapshot ID %d.",
            snapshot_id,
        )

        try:
            positions = (
                self.position_repository.get_by_snapshot_with_security(
                    snapshot_id
                )
            )

            holdings = []

            for position in positions:
                symbol = str(position.symbol or "").strip().upper()

                bucket = account_config.bucket_mapping.get(
                    symbol,
                    "UNMAPPED",
                )

                holdings.append(
                    PortfolioHolding(
                        position=position,
                        bucket=bucket,
                        account_name=account_config.display_name,
                    )
                )

                if bucket == "UNMAPPED":
                    logger.warning(
                        "No bucket mapping found for symbol %s "
                        "in account %s.",
                        symbol,
                        account_config.name,
                    )

            logger.info(
                "Added bucket mappings to %d positions for account %s.",
                len(holdings),
                account_config.name,
            )

            return holdings

        except Exception:
            logger.exception(
                "Failed adding bucket mappings for snapshot ID %d.",
                snapshot_id,
            )
            raise
			
    def _calculate_actual_allocations(
        self,
        holdings: list[PortfolioHolding],
        bucket_names: list[str],
    ) -> list[PortfolioAllocation]:
        """
        Calculate actual portfolio allocations by canonical bucket.

        Parameters
        ----------
        holdings : list[PortfolioHolding]
            Snapshot positions enriched with account-specific bucket
            classifications.
        bucket_names : list[str]
            Canonical bucket identifiers loaded from system
            configuration.

        Returns
        -------
        list[PortfolioAllocation]
            Actual bucket allocations, including empty buckets and
            UNMAPPED when applicable.

        Raises
        ------
        ValueError
            If bucket_names is invalid.
        Exception
            Propagates unexpected calculation failures.
        """

        if not isinstance(bucket_names, list) or not bucket_names:
            raise ValueError("bucket_names must be a non-empty list.")

        logger.info(
            "Calculating actual allocations for %d holdings.",
            len(holdings),
        )

        try:
            allocations = []

            for bucket in bucket_names:
                bucket_holdings = [
                    holding
                    for holding in holdings
                    if holding.bucket == bucket
                ]

                market_value = sum(
                    (
                        holding.position.current_value
                        for holding in bucket_holdings
                    ),
                    Decimal("0"),
                )

                percentage = sum(
                    (
                        holding.position.percent_of_account
                        for holding in bucket_holdings
                        if holding.position.percent_of_account is not None
                    ),
                    Decimal("0"),
                )

                allocations.append(
                    PortfolioAllocation(
                        bucket=bucket,
                        percentage=percentage,
                        market_value=market_value,
                        holdings=bucket_holdings,
                    )
                )

            unmapped_holdings = [
                holding
                for holding in holdings
                if holding.bucket == "UNMAPPED"
            ]

            if unmapped_holdings:
                allocations.append(
                    PortfolioAllocation(
                        bucket="UNMAPPED",
                        percentage=sum(
                            (
                                holding.position.percent_of_account
                                for holding in unmapped_holdings
                                if holding.position.percent_of_account is not None
                            ),
                            Decimal("0"),
                        ),
                        market_value=sum(
                            (
                                holding.position.current_value
                                for holding in unmapped_holdings
                            ),
                            Decimal("0"),
                        ),
                        holdings=unmapped_holdings,
                    )
                )

            logger.info(
                "Calculated %d actual bucket allocations.",
                len(allocations),
            )

            return allocations

        except Exception:
            logger.exception(
                "Failed calculating actual portfolio allocations."
            )
            raise
			
    def _validate_position_percentages(
        self,
        holdings: list[PortfolioHolding],
        account_view: PortfolioAccountView,
    ) -> None:
        """
        Validate that snapshot position percentages reconcile to 100%.

        Missing percentages are reported separately from numerical
        discrepancies. The stored position percentages remain unchanged.

        Parameters
        ----------
        holdings : list[PortfolioHolding]
            Positions belonging to the account snapshot.
        account_view : PortfolioAccountView
            Account view receiving any data-quality warnings.

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If holdings or account_view is invalid.
        Exception
            Propagates unexpected validation failures.
        """

        if not isinstance(holdings, list):
            raise ValueError("holdings must be a list.")

        if account_view is None:
            raise ValueError("account_view is required.")

        reconciliation_tolerance = Decimal("0.05")
        expected_total = Decimal("100")

        logger.info(
            "Validating position percentages for account %s.",
            account_view.account_config.name,
        )
		
        if not holdings:
            warning = (
                "Position percentage reconciliation is incomplete. "
                "No positions are available to reconcile."
            )

            account_view.validation_warnings.append(warning)

            logger.warning(
                "%s Account: %s.",
                warning,
                account_view.account_config.name,
            )

            return

        try:
            missing_symbols = [
                holding.position.symbol
                for holding in holdings
                if holding.position.percent_of_account is None
            ]

            if missing_symbols:
                warning = (
                    "Position percentage reconciliation is incomplete. "
                    "Missing percentages for: "
                    + ", ".join(sorted(missing_symbols))
                    + "."
                )
                account_view.validation_warnings.append(warning)

                logger.warning(
                    "%s Account: %s.",
                    warning,
                    account_view.account_config.name,
                )

            available_percentages = [
                holding.position.percent_of_account
                for holding in holdings
                if holding.position.percent_of_account is not None
            ]

            actual_total = sum(
                available_percentages,
                Decimal("0"),
            )

            if missing_symbols:
                return

            difference = actual_total - expected_total

            if abs(difference) > reconciliation_tolerance:
                warning = (
                    "Position percentages do not reconcile to 100%. "
                    f"Recorded total: {actual_total:.4f}%; "
                    f"difference: {difference:+.4f} percentage points."
                )

                account_view.validation_warnings.append(warning)

                logger.warning(
                    "%s Account: %s.",
                    warning,
                    account_view.account_config.name,
                )

            else:
                logger.info(
                    "Position percentages reconcile successfully. "
                    "Account: %s; total: %.4f%%.",
                    account_view.account_config.name,
                    actual_total,
                )

        except Exception:
            logger.exception(
                "Failed validating position percentages for account %s.",
                account_view.account_config.name,
            )
            raise
			
    def _load_valid_bucket_names(self) -> list[str]:
        """
        Load valid bucket identifiers from system configuration.

        Returns:
            list[str]: The permitted CycleGuard bucket names.

        Raises:
            FileNotFoundError: If buckets.yaml does not exist.
            ValueError: If the YAML structure or bucket list is invalid.
            Exception: Propagates unexpected loading failures.
        """

        config_path = (
            Path(__file__).resolve().parent.parent
            / "config"
            / "system"
            / "buckets.yaml"
        )

        logger.info(
            "Loading valid bucket names from '%s'.",
            config_path,
        )

        try:
            if not config_path.is_file():
                raise FileNotFoundError(
                    f"Bucket configuration not found: {config_path}"
                )

            with config_path.open("r", encoding="utf-8") as stream:
                config = yaml.safe_load(stream) or {}

            if not isinstance(config, dict):
                raise ValueError(
                    "Bucket configuration must be a YAML mapping."
                )

            bucket_names = config.get("buckets")

            if not isinstance(bucket_names, list) or not bucket_names:
                raise ValueError(
                    "Bucket configuration must contain a non-empty "
                    "'buckets' list."
                )

            if any(
                not isinstance(bucket, str) or not bucket.strip()
                for bucket in bucket_names
            ):
                raise ValueError(
                    "Every bucket name must be a non-empty string."
                )

            bucket_names = [
                bucket.strip()
                for bucket in bucket_names
            ]

            if len(bucket_names) != len(set(bucket_names)):
                raise ValueError(
                    "Bucket configuration contains duplicate names."
                )

            logger.info(
                "Loaded %d valid bucket names.",
                len(bucket_names),
            )

            return bucket_names

        except Exception:
            logger.exception(
                "Failed to load valid bucket names."
            )
            raise