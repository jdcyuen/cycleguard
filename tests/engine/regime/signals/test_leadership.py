from engine.regime.signals.leadership import LeadershipSignal


def test_leadership_signal_strong():
    signal = LeadershipSignal(
        {
            "inputs": ["QQQ", "SMH"],
        }
    )

    result = signal.evaluate(
        {
            "latest": {
                "QQQ": 110,
                "SMH": 120,
            },
            "dma50": {
                "QQQ": 100,
                "SMH": 100,
            },
        }
    )

    assert result["name"] == "leadership"
    assert result["status"] == "Strong"
    assert result["above_50"] == 2
    assert result["total"] == 2


def test_leadership_signal_weak():
    signal = LeadershipSignal(
        {
            "inputs": ["QQQ", "SMH"],
        }
    )

    result = signal.evaluate(
        {
            "latest": {
                "QQQ": 90,
                "SMH": 95,
            },
            "dma50": {
                "QQQ": 100,
                "SMH": 100,
            },
        }
    )

    assert result["status"] == "Weak"
    assert result["above_50"] == 0
    assert result["total"] == 2


def test_leadership_signal_mixed():
    signal = LeadershipSignal(
        {
            "inputs": ["QQQ", "SMH"],
        }
    )

    result = signal.evaluate(
        {
            "latest": {
                "QQQ": 110,
                "SMH": 95,
            },
            "dma50": {
                "QQQ": 100,
                "SMH": 100,
            },
        }
    )

    assert result["status"] == "Mixed"
    assert result["above_50"] == 1
    assert result["total"] == 2


def test_leadership_signal_supports_multiple_inputs():
    signal = LeadershipSignal(
        {
            "inputs": ["QQQ", "SMH", "IWM", "XLF"],
        }
    )

    result = signal.evaluate(
        {
            "latest": {
                "QQQ": 110,
                "SMH": 120,
                "IWM": 105,
                "XLF": 90,
            },
            "dma50": {
                "QQQ": 100,
                "SMH": 100,
                "IWM": 100,
                "XLF": 100,
            },
        }
    )

    assert result["status"] == "Mixed"
    assert result["above_50"] == 3
    assert result["total"] == 4


def test_leadership_signal_unknown_when_no_inputs():
    signal = LeadershipSignal(
        {
            "inputs": [],
        }
    )

    result = signal.evaluate(
        {
            "latest": {},
            "dma50": {},
        }
    )

    assert result["status"] == "Unknown"


def test_leadership_signal_ignores_missing_inputs():
    signal = LeadershipSignal(
        {
            "inputs": ["QQQ", "SMH", "IWM"],
        }
    )

    result = signal.evaluate(
        {
            "latest": {
                "QQQ": 110,
                "SMH": 90,
            },
            "dma50": {
                "QQQ": 100,
                "SMH": 100,
            },
        }
    )

    assert result["status"] == "Mixed"
    assert result["above_50"] == 1
    assert result["total"] == 2