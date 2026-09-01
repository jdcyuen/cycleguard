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