from decimal import Decimal

import pytest

from engine.deployment.crash_deployment_engine import CrashDeploymentEngine


class TestCrashDeploymentEngine:

    def setup_method(self):
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

    def test_no_deployment_below_level_1(self):
        result = self.engine.evaluate(
            drawdown=-0.05,
            available_capital=Decimal("100000"),
        )

        assert result.action == "HOLD"
        assert result.deployment_pct == Decimal("0")
        assert result.deployment_amount == Decimal("0")

    def test_level_1_deployment(self):
        result = self.engine.evaluate(
            drawdown=-0.15,
            available_capital=Decimal("100000"),
        )

        assert result.action == "DEPLOY"
        assert result.deployment_pct == Decimal("0.03")
        assert result.deployment_amount == Decimal("3000")

    def test_level_2_deployment(self):
        result = self.engine.evaluate(
            drawdown=-0.25,
            available_capital=Decimal("100000"),
        )

        assert result.action == "DEPLOY"
        assert result.deployment_pct == Decimal("0.05")
        assert result.deployment_amount == Decimal("5000")

    def test_level_3_deployment(self):
        result = self.engine.evaluate(
            drawdown=-0.35,
            available_capital=Decimal("100000"),
        )

        assert result.action == "DEPLOY"
        assert result.deployment_pct == Decimal("0.08")
        assert result.deployment_amount == Decimal("8000")

    def test_level_4_deployment(self):
        result = self.engine.evaluate(
            drawdown=-0.50,
            available_capital=Decimal("100000"),
        )

        assert result.action == "DEPLOY"
        assert result.deployment_pct == Decimal("0.09")
        assert result.deployment_amount == Decimal("9000")

    def test_crash_deployment_engine_uses_base_evaluate_signature(self):
        from engine.deployment.base_deployment_engine import BaseDeploymentEngine

        engine = CrashDeploymentEngine()

        assert isinstance(engine, BaseDeploymentEngine)

    def test_crash_deployment_engine_does_not_require_regime_deployment_lookup(self):
        engine = self.engine

        result = engine.evaluate(
            drawdown=-0.20,
            available_capital=Decimal("100000"),
        )

        assert result.deployment_pct == Decimal("0.05")

    def test_crash_deployment_engine_does_not_require_regime_deployment_lookup(self):
        result = self.engine.evaluate(
            drawdown=-0.20,
            available_capital=Decimal("100000"),
        )

        assert result.deployment_pct == Decimal("0.05")

    def test_crash_deployment_engine_has_no_regime_deployment_lookup(self):
        assert "_get_deployment_pct" not in CrashDeploymentEngine.__dict__
