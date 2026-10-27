import logging
from decimal import Decimal
from models.deployment_evaluation import DeploymentEvaluation

from engine.deployment.crash_deployment_engine import CrashDeploymentEngine
from engine.regime.regime_engine import RegimeEngine
from services.portfolio_aggregation_service import (
    PortfolioAggregationService,
)
from engine.allocation.allocation_engine import AllocationEngine
from repositories.snapshot_repo import SnapshotRepository
from repositories.account_repo import AccountRepository
from engine.deployment.cash_deployment_policy import CashDeploymentPolicy

from datetime import date

logger = logging.getLogger(__name__)

class DeploymentOrchestrationService:
    """
    Coordinates portfolio aggregation, regime evaluation,
    and deployment decision-making.
    """

    def __init__(
        self,
        portfolio_service: PortfolioAggregationService,
        regime_engine: RegimeEngine,
        crash_manager,
        regime_deployment_engine,
        crash_deployment_engine,
        account,
        allocation_engine: AllocationEngine,
        account_repository: AccountRepository | None = None,
        snapshot_repository: SnapshotRepository | None = None,
        cash_deployment_policy: CashDeploymentPolicy | None = None,
    ):
        self.portfolio_service = portfolio_service
        self.regime_engine = regime_engine
        self.crash_manager = crash_manager
        self.regime_deployment_engine = regime_deployment_engine
        self.crash_deployment_engine = crash_deployment_engine
        self.account = account
        self.allocation_engine = allocation_engine
        self.account_repository = account_repository
        self.snapshot_repository = snapshot_repository
        self.cash_deployment_policy = (
            cash_deployment_policy
            if cash_deployment_policy is not None
            else CashDeploymentPolicy()
        )


    # DeploymentOrchestrationService.evaluate() gathers available capital, obtains 
    # both the normal regime-based and crash-based deployment decisions, then applies 
    # the business rule that a crash deployment overrides the normal regime decision; 
    # if there is no crash deployment, the regime decision wins.
    def evaluate(
        self,
        snapshot_id: int | None,
        market_data: dict,
    ) -> DeploymentEvaluation:
        
        """
        Coordinates the deployment evaluation lifecycle.

        Steps:
        1. Validate inputs and verify that the account's latest portfolio
        snapshot is dated today.
        2. Determine available deployment capital from positive defensive-bucket
        drift.
        3. Evaluate the regime-based deployment recommendation.
        4. Evaluate the crash-based deployment recommendation.
        5. Give crash deployment priority when its action is DEPLOY.
        6. Otherwise, return the regime-based recommendation if dynamic
        deployment is enabled; return HOLD if it is disabled.

        Args:
            snapshot_id: Optional snapshot ID. If None, the service resolves
                the account's latest snapshot. Any supplied ID is replaced
                by the verified latest snapshot ID. The latest snapshot must
                be dated today.
            market_data: Dictionary of market data used for regime evaluation.

        Returns:
            The final DeploymentEvaluation. A crash deployment takes priority
            over the regime-based recommendation.

        Raises:
            ValueError: If the inputs are invalid, required repositories or
                account data are missing, or today's snapshot cannot be verified.
        """


        # 1. Validate inputs
        if snapshot_id is not None and (
            not isinstance(snapshot_id, int)
            or isinstance(snapshot_id, bool)
            or snapshot_id <= 0
        ):
            raise ValueError(
                "Snapshot ID must be a positive integer or None"
            )

        if not isinstance(market_data, dict):
            raise ValueError(
                "Market data must be a dictionary"
            )


        try:
            if self.account_repository is None or self.snapshot_repository is None:
                logger.error(
                    "Deployment repositories are not configured for account '%s'",
                    self.account.name,
                )
                raise ValueError(
                    "Deployment repositories are not configured."
                )

            account_record = self.account_repository.get_by_name(
                self.account.name
            )

            if account_record is None or account_record.id is None:
                logger.error(
                    "No database account found for account '%s'",
                    self.account.name,
                )
                raise ValueError(
                    "No database account found. "
                    "Please download and import the latest portfolio CSV."
                )

            latest_snapshot = self.snapshot_repository.get_latest_by_account(
                account_record.id
            )

            if latest_snapshot is None:
                logger.warning(
                    "No portfolio snapshot found for account '%s' (account_id=%s)",
                    self.account.name,
                    account_record.id,
                )
                raise ValueError(
                    "No portfolio snapshot found. "
                    "Please download and import the latest portfolio CSV."
                )

            if latest_snapshot.snapshot_date != date.today():
                logger.warning(
                    "Stale portfolio snapshot for account '%s': "
                    "snapshot_date=%s, today=%s",
                    self.account.name,
                    latest_snapshot.snapshot_date,
                    date.today(),
                )
                raise ValueError(
                    "The latest portfolio snapshot is not from today. "
                    "Please download and import the latest portfolio CSV."
                )

            snapshot_id = latest_snapshot.id

            logger.info(
                "Using latest portfolio snapshot for account '%s': "
                "snapshot_id=%s, snapshot_date=%s",
                self.account.name,
                snapshot_id,
                latest_snapshot.snapshot_date,
            )

        except ValueError:
            raise

        except Exception:
            logger.exception(
                "Failed to validate portfolio snapshot freshness "
                "for account '%s'",
                self.account.name,
            )
            raise ValueError(
                "Unable to verify the latest portfolio snapshot. "
                "Please try again or download and import the latest portfolio CSV."
            )

        

        # 2. Get deployable capital from defensive bucket surplus
        bucket_allocations = self.portfolio_service.get_bucket_allocation(snapshot_id)    
        defensive_allocation = bucket_allocations.get("defensive")

        available_capital = (
            max(
                defensive_allocation.drift_value,
                Decimal("0"),
            )
            if defensive_allocation
            else Decimal("0")
        )

        # 3. Determine the current market regime
        regime_result = self.regime_engine.evaluate(
            market_data
        )

        # 4. Determine regime-based deployment
        regime_decision = (
            self.regime_deployment_engine.evaluate(
                regime_result,
                available_capital,
            )
        )
        # 5. Determine whether a crash is occurring
        crash_result = self.crash_manager.run()

        # 6. Determine crash-based deployment
        crash_decision = (
            self.crash_deployment_engine.evaluate(
                crash_result["drawdown"],
                available_capital,
            )
        )
        
                # 7. Select the winning deployment decision.
        # Crash deployment always has priority.
        if crash_decision.action == "DEPLOY":
            selected_decision = crash_decision

        # 8. Suppress normal regime deployment when disabled.
        elif not self.account.settings.enable_dynamic_deployment:
            return DeploymentEvaluation(
                action="HOLD",
                deployment_pct=Decimal("0"),
                deployment_amount=Decimal("0"),
                source="regime",
            )

        else:
            selected_decision = regime_decision

        # 9. Apply the cash deployment policy to proposed deployments.
        if selected_decision.action != "DEPLOY":
            return selected_decision

        portfolio_value = self.portfolio_service.get_portfolio_value(
            snapshot_id
        )

        approved_amount = self.cash_deployment_policy.approve(
            proposed_amount=selected_decision.deployment_amount,
            available_defensive_capital=available_capital,
            portfolio_value=portfolio_value,
        )

        # Preserve the original decision when the policy does not
        # change the proposed amount.
        if approved_amount == selected_decision.deployment_amount:
            return selected_decision

        # Do not return a DEPLOY decision if no capital is approved.
        if approved_amount <= Decimal("0"):
            return DeploymentEvaluation(
                action="HOLD",
                deployment_pct=Decimal("0"),
                deployment_amount=Decimal("0"),
                source=selected_decision.source,
            )

        # The percentage is relative to the available defensive surplus,
        # consistent with the deployment engines.
        approved_pct = (
            approved_amount / available_capital
            if available_capital > Decimal("0")
            else Decimal("0")
        )

        return DeploymentEvaluation(
            action="DEPLOY",
            deployment_pct=approved_pct,
            deployment_amount=approved_amount,
            source=selected_decision.source,
        )

    def allocate_deployment(
        self,
        snapshot_id: int,
        deployment_amount: Decimal,
    ) -> dict[str, Decimal]:
        """
        Allocate an approved deployment amount across eligible securities.
        """

        try:
            if not isinstance(snapshot_id, int) or snapshot_id <= 0:
                raise ValueError(
                    "Snapshot ID must be a positive integer"
                )

            if not isinstance(deployment_amount, Decimal):
                raise TypeError(
                    "Deployment amount must be a Decimal"
                )

            if not deployment_amount.is_finite():
                raise ValueError(
                    "Deployment amount must be finite"
                )

            if deployment_amount < Decimal("0"):
                raise ValueError(
                    "Deployment amount cannot be negative"
                )

            if deployment_amount == Decimal("0"):
                return {}

            actual_targets = (
                self.portfolio_service
                .calculate_position_portfolio_weights(
                    snapshot_id
                )
            )

            portfolio_value = (
                self.portfolio_service.get_portfolio_value(
                    snapshot_id
                )
            )

            desired_targets = {
                symbol: Decimal(str(target))
                for symbol, target
                in self.account.security_targets.items()
            }

            eligible_securities = [
                symbol
                for symbol in desired_targets
                if self.account.bucket_mapping.get(symbol)
                != "defensive"
            ]

            logger.info(
                "Allocating approved deployment: "
                "snapshot_id=%s, deployment_amount=%s, "
                "eligible_security_count=%s",
                snapshot_id,
                deployment_amount,
                len(eligible_securities),
            )

            # Pass the account's configured position limits to the engine.
            # Symbol-specific overrides take precedence over the account
            # default and constrain how much new capital each position can
            # receive.
            position_limits = self.account.position_limits

            logger.info(
                "Applying account position limits to deployment: "
                "account=%s, default_max_position_pct=%s, "
                "override_count=%s",
                self.account.name,
                position_limits.max_position_pct,
                len(position_limits.overrides),
            )

            allocations = self.allocation_engine.allocate_deployment(
                deployment_amount=deployment_amount,
                actual_targets=actual_targets,
                desired_targets=desired_targets,
                portfolio_value=portfolio_value,
                eligible_securities=eligible_securities,
                position_limits=position_limits,
            )

            logger.info(
                "Approved deployment allocated: "
                "snapshot_id=%s, approved_amount=%s, "
                "actual_allocated_amount=%s",
                snapshot_id,
                deployment_amount,
                sum(allocations.values(), Decimal("0")),
            )

            return allocations

        except Exception:
            logger.exception(
                "Failed to allocate approved deployment: "
                "snapshot_id=%s, deployment_amount=%s",
                snapshot_id,
                deployment_amount,
            )
            raise