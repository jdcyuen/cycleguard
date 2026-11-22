
from decimal import Decimal
import logging

import pytest

from engine.deployment.base_deployment_engine import BaseDeploymentEngine
from engine.deployment.crash_deployment_engine import CrashDeploymentEngine


class TestCrashDeploymentEngine:

    deployment_policy: dict[str, dict[str, float]]
    engine: CrashDeploymentEngine

    def setup_method(self) -> None:
        self.deployment_policy = {
            "levels": {
                "level_1": {
                    "drawdown": -0.10,
                    "deploy_pct": 0.03,
                },
                "level_2": {
                    "drawdown": -0.20,
                    "deploy_pct": 0.05,
                },
                "level_3": {
                    "drawdown": -0.30,
                    "deploy_pct": 0.08,
                },
                "level_4": {
                    "drawdown": -0.40,
                    "deploy_pct": 0.09,
                },
            }
        }

        self.engine = CrashDeploymentEngine(
            deployment_policy=self.deployment_policy
        )

    def test_no_deployment_below_level_1(self) -> None:
        result = self.engine.evaluate(
            drawdown=-0.05,
            total_portfolio_value=Decimal("1000000"),
        )

        assert result.action == "HOLD"
        assert result.deployment_pct == Decimal("0")
        assert result.deployment_amount == Decimal("0")
        assert result.source == "crash"

    @pytest.mark.parametrize(
        ("drawdown", "expected_pct", "expected_amount"),
        [
            (-0.15, Decimal("0.03"), Decimal("30000")),
            (-0.25, Decimal("0.05"), Decimal("50000")),
            (-0.35, Decimal("0.08"), Decimal("80000")),
            (-0.50, Decimal("0.09"), Decimal("90000")),
        ],
    )
    def test_crash_deployment_uses_total_portfolio_value(
        self,
        drawdown: float,
        expected_pct: Decimal,
        expected_amount: Decimal,
    ) -> None:
        result = self.engine.evaluate(
            drawdown=drawdown,
            total_portfolio_value=Decimal("1000000"),
        )

        assert result.action == "DEPLOY"
        assert result.deployment_pct == expected_pct
        assert result.deployment_amount == expected_amount
        assert result.source == "crash"

    def test_level_1_uses_total_portfolio_value_not_defensive_capital(
        self,
    ) -> None:
        result = self.engine.evaluate(
            drawdown=-0.15,
            total_portfolio_value=Decimal("1000000"),
        )

        # 3% of the total portfolio, not 3% of a Defensive cash balance.
        assert result.deployment_amount == Decimal("30000")

    def test_deepest_applicable_level_is_selected_without_stacking(
        self,
    ) -> None:
        result = self.engine.evaluate(
            drawdown=-0.30,
            total_portfolio_value=Decimal("1000000"),
        )

        # Level 3 applies. Earlier level percentages are not accumulated.
        assert result.deployment_pct == Decimal("0.08")
        assert result.deployment_amount == Decimal("80000")
        assert result.deployment_amount != Decimal("160000")

    def test_level_4_does_not_stack_prior_levels(self) -> None:
        result = self.engine.evaluate(
            drawdown=-0.45,
            total_portfolio_value=Decimal("1000000"),
        )

        assert result.deployment_pct == Decimal("0.09")
        assert result.deployment_amount == Decimal("90000")

    def test_exact_drawdown_threshold_triggers_level(self) -> None:
        result = self.engine.evaluate(
            drawdown=-0.20,
            total_portfolio_value=Decimal("1000000"),
        )

        assert result.action == "DEPLOY"
        assert result.deployment_pct == Decimal("0.05")
        assert result.deployment_amount == Decimal("50000")

    def test_zero_portfolio_value_produces_zero_deployment(self) -> None:
        result = self.engine.evaluate(
            drawdown=-0.30,
            total_portfolio_value=Decimal("0"),
        )

        assert result.action == "DEPLOY"
        assert result.deployment_pct == Decimal("0.08")
        assert result.deployment_amount == Decimal("0")

    @pytest.mark.parametrize(
        "portfolio_value",
        [
            Decimal("-1"),
            Decimal("NaN"),
            Decimal("Infinity"),
            Decimal("-Infinity"),
        ],
    )
    def test_invalid_portfolio_value_raises_value_error(
        self,
        portfolio_value: Decimal,
    ) -> None:
        with pytest.raises(ValueError):
            self.engine.evaluate(
                drawdown=-0.20,
                total_portfolio_value=portfolio_value,
            )

    @pytest.mark.parametrize(
        "drawdown",
        [
            -1.01,
            0.01,
            float("nan"),
            float("inf"),
            float("-inf"),
        ],
    )
    def test_invalid_drawdown_raises_value_error(
        self,
        drawdown: float,
    ) -> None:
        with pytest.raises(ValueError):
            self.engine.evaluate(
                drawdown=drawdown,
                total_portfolio_value=Decimal("1000000"),
            )

    def test_invalid_drawdown_type_raises_type_error(self) -> None:
        with pytest.raises(TypeError):
            self.engine.evaluate(
                drawdown="invalid",  # type: ignore[arg-type]
                total_portfolio_value=Decimal("1000000"),
            )

    def test_invalid_portfolio_value_type_raises_type_error(self) -> None:
        with pytest.raises(TypeError):
            self.engine.evaluate(
                drawdown=-0.20,
                total_portfolio_value=1000000,  # type: ignore[arg-type]
            )

    @pytest.mark.parametrize(
        "invalid_percentage",
        [
            -0.01,
            1.01,
            float("nan"),
            float("inf"),
            True,
        ],
    )
    def test_invalid_deployment_percentage_raises_value_error(
        self,
        invalid_percentage: float | bool,
    ) -> None:
        policy: dict[str, dict[str, float | bool]] = {
            "levels": {
                "level_1": {
                    "drawdown": -0.10,
                    "deploy_pct": invalid_percentage,
                }
            }
        }

        engine: CrashDeploymentEngine = CrashDeploymentEngine(
            deployment_policy=policy
        )

        with pytest.raises(ValueError):
            engine.evaluate(
                drawdown=-0.15,
                total_portfolio_value=Decimal("1000000"),
            )

    def test_missing_levels_configuration_raises_value_error(self) -> None:
        engine: CrashDeploymentEngine = CrashDeploymentEngine(
            deployment_policy={}
        )

        with pytest.raises(ValueError):
            engine.evaluate(
                drawdown=-0.20,
                total_portfolio_value=Decimal("1000000"),
            )

    def test_missing_deployment_percentage_raises_value_error(self) -> None:
        policy: dict[str, dict[str, float]] = {
            "levels": {
                "level_1": {
                    "drawdown": -0.10,
                }
            }
        }

        engine: CrashDeploymentEngine = CrashDeploymentEngine(
            deployment_policy=policy
        )

        with pytest.raises(ValueError):
            engine.evaluate(
                drawdown=-0.15,
                total_portfolio_value=Decimal("1000000"),
            )

    def test_evaluation_error_is_logged(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        with caplog.at_level(
            logging.ERROR,
            logger="engine.deployment.crash_deployment_engine",
        ):
            with pytest.raises(ValueError):
                self.engine.evaluate(
                    drawdown=-0.20,
                    total_portfolio_value=Decimal("-1000000"),
                )

        assert "Crash deployment evaluation rejected" in caplog.text

    def test_crash_engine_inherits_base_deployment_engine(self) -> None:
        engine: CrashDeploymentEngine = CrashDeploymentEngine()

        assert isinstance(engine, BaseDeploymentEngine)

    def test_crash_engine_does_not_require_regime_deployment_lookup(
        self,
    ) -> None:
        result = self.engine.evaluate(
            drawdown=-0.20,
            total_portfolio_value=Decimal("1000000"),
        )

        assert result.deployment_pct == Decimal("0.05")

    def test_crash_engine_has_no_regime_deployment_lookup(self) -> None:
        assert "_get_deployment_pct" not in CrashDeploymentEngine.__dict__
