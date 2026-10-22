from engine.regime.signals.volatility import VolatilitySignal


def test_volatility_signal_calm():
    signal = VolatilitySignal(
        {
            "thresholds": {
                "calm": 18,
                "elevated": 25,
                "stress": 35,
            }
        }
    )

    result = signal.evaluate({"value": 15})

    assert result["status"] == "calm"
    assert result["value"] == 15


def test_volatility_signal_neutral():
    signal = VolatilitySignal(
        {
            "thresholds": {
                "calm": 18,
                "elevated": 25,
                "stress": 35,
            }
        }
    )

    result = signal.evaluate({"value": 22})

    assert result["status"] == "neutral"


def test_volatility_signal_risk_off():
    signal = VolatilitySignal(
        {
            "thresholds": {
                "calm": 18,
                "elevated": 25,
                "stress": 35,
            }
        }
    )

    result = signal.evaluate({"value": 35})

    assert result["status"] == "risk-off"

def test_volatility_signal_returns_explainable_evidence():
    signal = VolatilitySignal(
        {
            "thresholds": {
                "calm": 18,
                "elevated": 25,
                "stress": 35,
            }
        }
    )

    result = signal.evaluate({"value": 15})

    assert "evidence" in result

    evidence = result["evidence"]

    assert evidence["raw_inputs"]["value"] == 15
    assert evidence["calculated_values"]["status"] == "calm"
    assert evidence["thresholds"]["calm"] == 18
    assert evidence["thresholds"]["elevated"] == 25
    assert "rule" in evidence
    assert "why" in evidence