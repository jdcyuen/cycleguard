from engine.regime.regime_engine import RegimeEngine
from pathlib import Path
import yaml

class DummySignal:
    def __init__(self, name, status):
        self._name = name
        self.status = status

    @property
    def name(self):
        return self._name

    def evaluate(self, data):
        return {
            "name": self.name,
            "status": self.status,
        }


def test_regime_engine_builds_signals_from_config():
    config = {
        "signals": {
            "trend": {},
        },
        "regimes": {},
        "fallback_regime": "TRANSITION",
    }

    engine = RegimeEngine(config)

    assert len(engine.aggregator.signals) == 1
    assert engine.aggregator.signals[0].name == "trend"


def test_regime_engine_evaluates_signals_and_classifies():
    config = {
        "signals": {
            "trend": {},
        },
        "regimes": {
            "RISK_ON": {
                "conditions": {
                    "trend": "bullish",
                },
            },
        },
        "fallback_regime": "TRANSITION",
    }

    engine = RegimeEngine(config)

    result = engine.evaluate(
        {
            "current": 105,
            "dma50": 100,
            "dma200": 100,
        }
    )

    assert result["signals"]["trend"]["status"] == "bullish"
    assert result["regime"] == "RISK_ON"

def test_regime_engine_works_with_regime_yaml():
    project_root = Path(__file__).resolve().parents[3]
    regime_path = project_root / "src" / "config" / "system" / "regime.yaml"

    with open(regime_path, "r") as f:
        config = yaml.safe_load(f)

    regime_config = config["regime_system"]

    engine = RegimeEngine(regime_config)

    assert len(engine.aggregator.signals) == 6
    assert engine.classifier.fallback_regime == "TRANSITION"

def test_regime_engine_evaluates_all_configured_signals():
    project_root = Path(__file__).resolve().parents[3]
    regime_path = project_root / "src" / "config" / "system" / "regime.yaml"

    with open(regime_path, "r") as f:
        config = yaml.safe_load(f)

    regime_config = config["regime_system"]
    engine = RegimeEngine(regime_config)

    result = engine.evaluate(
        {
            "current": 105,
            "dma50": {
                "SPY": 100,
                "QQQ": 100,
                "SMH": 100,
                "JNK": 100,
                "SHY": 100,
            },
            "dma200": {
                "SPY": 100,
            },
            "value": 15,
            "latest": {
                "CAPE": 25,
                "SPY": 105,
                "^VIX": 15,
                "QQQ": 105,
                "SMH": 105,
                "JNK": 105,
                "SHY": 100,
            },
        }
    )

    assert len(result["signals"]) == 6
    assert "trend" in result["signals"]
    assert "breadth" in result["signals"]
    assert "volatility" in result["signals"]
    assert "leadership" in result["signals"]
    assert "credit" in result["signals"]
    assert "cape" in result["signals"]
    assert "regime" in result