

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

def test_trend_signal_neutral_between_moving_averages():
    signal = TrendSignal()

    result = signal.evaluate(
        {
            "current": 105,
            "dma50": 110,
            "dma200": 100,
        }
    )

    assert result["status"] == "neutral"   

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

def test_trend_signal_returns_explainable_evidence():
    signal = TrendSignal()

    result = signal.evaluate(
        {
            "current": 105,
            "dma50": 100,
            "dma200": 100,
        }
    )

    assert "evidence" in result
    assert result["evidence"]["raw_inputs"]["current"] == 105
    assert result["evidence"]["calculated_values"]["dma50"] == 100
    assert result["evidence"]["calculated_values"]["dma200"] == 100
    assert "rule" in result["evidence"]
    assert "why" in result["evidence"]

def test_trend_signal_evidence_shows_comparison_result():
    signal = TrendSignal(
        {
            "inputs": ["SPY"],
        }
    )

    result = signal.evaluate(
        {
            "current": 105,
            "dma50": 100,
            "dma200": 102,
        }
    )

    evidence = result["evidence"]

    assert evidence["comparison"]["proxy"] == "SPY"
    assert evidence["comparison"]["current"] == 105
    assert evidence["comparison"]["sma50"] == 100
    assert evidence["comparison"]["sma200"] == 102
    assert evidence["comparison"]["status"] == "BULLISH"

def test_trend_signal_why_explains_status():
    signal = TrendSignal()

    result = signal.evaluate(
        {
            "current": 105,
            "dma50": 100,
            "dma200": 102,
        }
    )

    why = result["evidence"]["why"]

    assert "SPY current price is 105" in why
    assert "50-day SMA is 100" in why
    assert "200-day SMA is 102" in why
    assert "price is bullish" in why