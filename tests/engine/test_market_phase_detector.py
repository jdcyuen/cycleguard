import pandas as pd
import pytest
from unittest.mock import patch

from engine.market_phase_detector import MarketPhaseDetector


# ----------------------------------------------------------------------
# Helper
# ----------------------------------------------------------------------

def make_price_history(price_map):
    """
    Creates a 250-day DataFrame so both the 50DMA and 200DMA exist.

    price_map format:
        {
            "SPY": (199, 100, 101),
            "QQQ": (199, 100, 101),
            ...
        }

    tuple =
        (days_at_price1, price1, last_price)

    Example:
        (199,100,101)
        means:
            first 199 days = 100
            final day = 101

        200-day MA ≈100
        50-day MA ≈100
        current =101
    """
    data = {}

    total_days = 250

    for ticker, (initial_days, price, last_price) in price_map.items():
        series = [price] * initial_days
        series += [price] * (total_days - initial_days - 1)
        series.append(last_price)
        data[ticker] = series

    return pd.DataFrame(data)


# ----------------------------------------------------------------------
# Trend Signal
# ----------------------------------------------------------------------

def test_get_trend_signal():
    detector = MarketPhaseDetector(config={})

    assert detector.get_trend_signal(105, 100, 100) == "Bullish"
    assert detector.get_trend_signal(100, 100, 100) == "Neutral"
    assert detector.get_trend_signal(95, 100, 100) == "Bearish"


# ----------------------------------------------------------------------
# Breadth Signal
# ----------------------------------------------------------------------

def test_get_breadth_signal():
    detector = MarketPhaseDetector(config={})

    assert detector.get_breadth_signal(80) == "Strong"
    assert detector.get_breadth_signal(60) == "Improving"
    assert detector.get_breadth_signal(40) == "Weak"


# ----------------------------------------------------------------------
# VIX Signal
# ----------------------------------------------------------------------

def test_get_vix_signal():
    detector = MarketPhaseDetector(config={})

    assert detector.get_vix_signal(15) == "Calm"
    assert detector.get_vix_signal(22) == "Neutral"
    assert detector.get_vix_signal(35) == "Risk-off"


# ----------------------------------------------------------------------
# Leadership Signal
# ----------------------------------------------------------------------

def test_get_leadership_signal():
    detector = MarketPhaseDetector(config={})

    assert detector.get_leadership_signal(
        101, 100,
        102, 100,
    ) == "Strong"

    assert detector.get_leadership_signal(
        99, 100,
        98, 100,
    ) == "Weak"

    assert detector.get_leadership_signal(
        101, 100,
        99, 100,
    ) == "Mixed"


# ----------------------------------------------------------------------
# Credit Signal
# ----------------------------------------------------------------------

def test_get_credit_signal():
    detector = MarketPhaseDetector(config={})

    assert detector.get_credit_signal(
        100, 50,
        90, 50,
    ) == "Healthy"

    assert detector.get_credit_signal(
        90, 50,
        100, 50,
    ) == "Stressed"


# ----------------------------------------------------------------------
# Empty download
# ----------------------------------------------------------------------

@patch.object(MarketPhaseDetector, "_fetch_daily_closes")
def test_run_empty_download(mock_download):
    mock_download.return_value = pd.DataFrame()

    detector = MarketPhaseDetector(config={})

    results = detector.run()

    assert results["regime"] == "TRANSITION"
    assert results["score"] == 0
    assert results["trend"]["status"] == "Unknown"


# ----------------------------------------------------------------------
# Risk-On regime
# ----------------------------------------------------------------------

@patch.object(MarketPhaseDetector, "_fetch_daily_closes")
def test_run_risk_on(mock_download):

    tickers = {
        "SPY": (249, 100, 110),
        "^VIX": (249, 18, 15),
        "QQQ": (249, 100, 110),
        "SMH": (249, 100, 110),
        "JNK": (249, 100, 105),
        "SHY": (249, 100, 100),
    }

    sector_etfs = [
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

    for etf in sector_etfs:
        tickers[etf] = (249, 100, 110)

    mock_download.return_value = make_price_history(tickers)

    detector = MarketPhaseDetector(config={})

    results = detector.run()

    assert results["trend"]["status"] == "bullish"
    assert results["breadth"]["status"] == "Strong"
    assert results["volatility"]["status"] == "calm"
    assert results["leadership"]["status"] == "Strong"
    assert results["credit"]["status"] == "Healthy"

    assert results["score"] == 6
    assert results["regime"] == "TRANSITION"


# ----------------------------------------------------------------------
# Defensive regime
# ----------------------------------------------------------------------

@patch.object(MarketPhaseDetector, "_fetch_daily_closes")
def test_run_defensive(mock_download):

    tickers = {
        "SPY": (249, 100, 90),
        "^VIX": (249, 20, 35),
        "QQQ": (249, 100, 90),
        "SMH": (249, 100, 90),
        "JNK": (249, 100, 90),
        "SHY": (249, 100, 100),
    }

    sector_etfs = [
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

    for etf in sector_etfs:
        tickers[etf] = (249, 100, 90)

    mock_download.return_value = make_price_history(tickers)

    detector = MarketPhaseDetector(config={})

    results = detector.run()

    assert results["trend"]["status"] == "bearish"
    assert results["breadth"]["status"] == "Weak"
    assert results["volatility"]["status"] == "risk-off"
    assert results["leadership"]["status"] == "Weak"
    assert results["credit"]["status"] == "Stressed"

    assert results["score"] == 0
    assert results["regime"] == "DEFENSIVE"