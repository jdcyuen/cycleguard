import pytest
from engine.regime.signals.breadth import BreadthSignal


def test_breadth_signal_strong():
    signal = BreadthSignal(
        {
            "inputs": ["A", "B", "C", "D"],
            "thresholds": {
                "strong": 65,
                "neutral": 50,
                "weak": 35,
            },
        }
    )

    result = signal.evaluate(
        {
            "latest": {
                "A": 110,
                "B": 110,
                "C": 110,
                "D": 90,
            },
            "dma50": {
                "A": 100,
                "B": 100,
                "C": 100,
                "D": 100,
            },
        }
    )

    assert result["status"] == "Strong"
    assert result["value"] == 75
    assert result["valid_total"] == 4
    assert result["passing"] == ["A", "B", "C"]
    assert result["failing"] == ["D"]


def test_breadth_signal_improving():
    signal = BreadthSignal(
        {
            "inputs": ["A", "B", "C", "D"],
        }
    )

    result = signal.evaluate(
        {
            "latest": {
                "A": 110,
                "B": 110,
                "C": 90,
                "D": 90,
            },
            "dma50": {
                "A": 100,
                "B": 100,
                "C": 100,
                "D": 100,
            },
        }
    )

    assert result["status"] == "Improving"
    assert result["value"] == 50


def test_breadth_signal_weak():
    signal = BreadthSignal(
        {
            "inputs": ["A", "B", "C", "D"],
        }
    )

    result = signal.evaluate(
        {
            "latest": {
                "A": 110,
                "B": 90,
                "C": 90,
                "D": 90,
            },
            "dma50": {
                "A": 100,
                "B": 100,
                "C": 100,
                "D": 100,
            },
        }
    )

    assert result["status"] == "Weak"
    assert result["value"] == 25

def test_breadth_signal_returns_explainable_evidence():
    signal = BreadthSignal(
        {
            "inputs": ["XLC", "XLY", "XLP"],
        }
    )

    result = signal.evaluate(
        {
            "latest": {
                "XLC": 105,
                "XLY": 110,
                "XLP": 95,
            },
            "dma50": {
                "XLC": 102,
                "XLY": 105,
                "XLP": 98,
            },
            "dma200": {
                "XLC": 100,
                "XLY": 100,
                "XLP": 100,
            },
        }
    )

    assert "evidence" in result

    evidence = result["evidence"]

    # Evidence structure
    assert "raw_inputs" in evidence
    assert "calculated_values" in evidence
    assert "etfs" in evidence
    assert "thresholds" in evidence
    assert "rule" in evidence
    assert "why" in evidence

    # Aggregate breadth calculation
    assert evidence["calculated_values"]["pct_above_50"] == pytest.approx(66.6666667)
    assert evidence["calculated_values"]["passing_count"] == 2
    assert evidence["calculated_values"]["failing_count"] == 1
    assert evidence["calculated_values"]["valid_total"] == 3

    # XLC passed
    assert evidence["etfs"]["XLC"]["current"] == 105
    assert evidence["etfs"]["XLC"]["sma50"] == 102
    assert evidence["etfs"]["XLC"]["status"] == "PASS"

    # XLY passed
    assert evidence["etfs"]["XLY"]["current"] == 110
    assert evidence["etfs"]["XLY"]["sma50"] == 105
    assert evidence["etfs"]["XLY"]["status"] == "PASS"

    # XLP failed
    assert evidence["etfs"]["XLP"]["current"] == 95
    assert evidence["etfs"]["XLP"]["sma50"] == 98
    assert evidence["etfs"]["XLP"]["status"] == "FAIL"


def test_breadth_signal_uses_configured_proxies():
    signal = BreadthSignal(
        {
            "inputs": ["XLC", "XLY", "XLP"],
        }
    )

    assert signal.proxies == ["XLC", "XLY", "XLP"]

def test_breadth_signal_loads_proxies_from_regime_config():
    from config.config_manager import get_config

    config = get_config("dev")

    breadth_config = config["regime"]["regime_system"]["signals"]["breadth"]

    assert breadth_config["inputs"] == [
        "XLC",
        "XLY",
        "XLP",
        "XLE",
        "XLF",
        "XLV",
        "XLI",
        "XLB",
        "XLRE",
        "XLK",
        "XLU",
    ]