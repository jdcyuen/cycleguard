from engine.regime.signals.cape import CapeSignal


def test_cape_signal_expensive():
    signal = CapeSignal(
        {
            "inputs": ["CAPE"],
            "thresholds": {
                "expensive": 30,
                "neutral": 25,
                "cheap": 20,
            },
        }
    )

    result = signal.evaluate(
        {
            "latest": {
                "CAPE": 35,
            }
        }
    )

    assert result["name"] == "cape"
    assert result["status"] == "expensive"
    assert result["value"] == 35


def test_cape_signal_neutral():
    signal = CapeSignal(
        {
            "inputs": ["CAPE"],
            "thresholds": {
                "expensive": 30,
                "neutral": 25,
                "cheap": 20,
            },
        }
    )

    result = signal.evaluate(
        {
            "latest": {
                "CAPE": 27,
            }
        }
    )

    assert result["status"] == "neutral"


def test_cape_signal_attractive():
    signal = CapeSignal(
        {
            "inputs": ["CAPE"],
            "thresholds": {
                "expensive": 30,
                "neutral": 25,
                "cheap": 20,
            },
        }
    )

    result = signal.evaluate(
        {
            "latest": {
                "CAPE": 22,
            }
        }
    )

    assert result["status"] == "attractive"


def test_cape_signal_cheap():
    signal = CapeSignal(
        {
            "inputs": ["CAPE"],
            "thresholds": {
                "expensive": 30,
                "neutral": 25,
                "cheap": 20,
            },
        }
    )

    result = signal.evaluate(
        {
            "latest": {
                "CAPE": 18,
            }
        }
    )

    assert result["status"] == "cheap"


def test_cape_signal_unknown_without_input():
    signal = CapeSignal(
        {
            "inputs": [],
        }
    )

    result = signal.evaluate(
        {
            "latest": {
                "CAPE": 25,
            }
        }
    )

    assert result["status"] == "unknown"


def test_cape_signal_unknown_when_data_missing():
    signal = CapeSignal(
        {
            "inputs": ["CAPE"],
        }
    )

    result = signal.evaluate(
        {
            "latest": {}
        }
    )

    assert result["status"] == "unknown"