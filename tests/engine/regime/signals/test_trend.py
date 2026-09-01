

from engine.regime.signals.trend import TrendSignal


def test_trend_signal_bullish():
    signal = TrendSignal()

    result = signal.evaluate(
        {
            "current": 105,
            "dma50": 100,
            "dma200": 100,
        }
    )

    assert result["status"] == "bullish"


def test_trend_signal_neutral():
    signal = TrendSignal()

    result = signal.evaluate(
        {
            "current": 100,
            "dma50": 100,
            "dma200": 100,
        }
    )

    assert result["status"] == "neutral"


def test_trend_signal_bearish():
    signal = TrendSignal()

    result = signal.evaluate(
        {
            "current": 95,
            "dma50": 100,
            "dma200": 100,
        }
    )

    assert result["status"] == "bearish"

def test_trend_signal_uses_configured_proxy():
    signal = TrendSignal(
        {
            "inputs": ["VTI"],
        }
    )

    assert signal.name == "trend"

    result = signal.evaluate(
        {
            "current": 105,
            "dma50": 100,
            "dma200": 100,
        }
    )

    assert result["proxy"] == "VTI"
    assert result["status"] == "bullish"