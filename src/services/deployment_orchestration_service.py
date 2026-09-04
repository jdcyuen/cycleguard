from models.deployment import DeploymentDecision

from engine.deployment.crash_deployment_engine import CrashDeploymentEngine
from engine.regime.regime_engine import RegimeEngine
from services.portfolio_aggregation_service import (
    PortfolioAggregationService,
)


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
    ):
        self.portfolio_service = portfolio_service
        self.regime_engine = regime_engine
        self.crash_manager = crash_manager
        self.regime_deployment_engine = regime_deployment_engine
        self.crash_deployment_engine = crash_deployment_engine

    # DeploymentOrchestrationService.evaluate() gathers available capital, obtains 
    # both the normal regime-based and crash-based deployment decisions, then applies 
    # the business rule that a crash deployment overrides the normal regime decision; 
    # if there is no crash deployment, the regime decision wins.
    def evaluate(
        self,
        snapshot_id: int,
        market_data: dict,
    ) -> DeploymentDecision:

         # 1. Validate inputs
        if not isinstance(snapshot_id, int) or snapshot_id <= 0:
            raise ValueError(
                "Snapshot ID must be a positive integer"
            )

        if not isinstance(market_data, dict):
            raise ValueError(
                "Market data must be a dictionary"
            )

        # 2. Get available capital
        available_capital = (
            self.portfolio_service.get_available_capital(
                snapshot_id
            )
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
        
        # 7. Crash deployment has priority over regime deployment
        if crash_decision.action == "DEPLOY":
            return crash_decision

        # 8. Otherwise use the regime decision
        return regime_decision
        # TODO: This logic will need to be updated when the crash deployment engine is implemented