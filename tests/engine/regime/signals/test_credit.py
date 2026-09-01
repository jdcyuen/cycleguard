from engine.regime.signals.credit import CreditSignal


def test_credit_signal_healthy():
    signal = CreditSignal(
        {
            "inputs": ["JNK", "SHY"],
        }
    )

    result = signal.evaluate(
        {
            "latest": {
                "JNK": 105,
                "SHY": 100,
            },
            "dma50": {
                "JNK": 100,
                "SHY": 100,
            },
        }
    )

    assert result["name"] == "credit"
    assert result["status"] == "Healthy"


def test_credit_signal_stressed():
    signal = CreditSignal(
        {
            "inputs": ["JNK", "SHY"],
        }
    )

    result = signal.evaluate(
        {
            "latest": {
                "JNK": 95,
                "SHY": 100,
            },
            "dma50": {
                "JNK": 100,
                "SHY": 100,
            },
        }
    )

    assert result["status"] == "Stressed"


def test_credit_signal_requires_two_inputs():
    signal = CreditSignal(
        {
            "inputs": ["JNK"],
        }
    )

    result = signal.evaluate(
        {
            "latest": {
                "JNK": 105,
            },
            "dma50": {
                "JNK": 100,
            },
        }
    )

    assert result["status"] == "Unknown"


def test_credit_signal_missing_input():
    signal = CreditSignal(
        {
            "inputs": ["JNK", "SHY"],
        }
    )

    result = signal.evaluate(
        {
            "latest": {
                "JNK": 105,
            },
            "dma50": {
                "JNK": 100,
            },
        }
    )

    assert result["status"] == "Unknown"