import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from engine.market_phase_detector import MarketPhaseDetector
from engine.regime.regime_engine import RegimeEngine


@patch.object(MarketPhaseDetector, "_fetch_daily_closes")
def test_regime_engine_accepts_market_phase_detector_data(mock_download):

    tickers = {
        "SPY": (249, 100, 110),
        "^VIX": (249, 18, 15),
        "QQQ": (249, 100, 110),
        "SMH": (249, 100, 110),
        "JNK": (249, 100, 105),
        "SHY": (249, 100, 100),
    }

    data = {}
    total_days = 250

    for ticker, (initial_days, price, last_price) in tickers.items():
        series = [price] * initial_days
        series += [price] * (total_days - initial_days - 1)
        series.append(last_price)
        data[ticker] = series

    mock_download.return_value = pd.DataFrame(data)

    cape_provider = MagicMock()
    cape_provider.get_latest.return_value = {
        "date": "2026.09",
        "cape": 25,
    }

    detector = MarketPhaseDetector(
        config={},
        cape_data_provider=cape_provider,
    )
    market_data = detector.get_regime_data()

    config = {
        "signals": {
            "trend": {
                "inputs": ["SPY"],
            },
            "breadth": {
                "inputs": ["SPY"],
            },
            "volatility": {
                "inputs": ["^VIX"],
            },
            "leadership": {
                "inputs": ["SMH", "QQQ"],
            },
            "credit": {
                "inputs": ["JNK", "SHY"],
            },
            "cape": {
                "inputs": ["CAPE"],
            },
        },
        "regimes": {},
        "fallback_regime": "TRANSITION",
    }

    engine = RegimeEngine(config)

    result = engine.evaluate(market_data)

    assert "signals" in result
    assert "regime" in result

    assert result["signals"]["trend"]["status"] == "bullish"
    assert result["signals"]["volatility"]["status"] == "calm"
    assert result["signals"]["breadth"]["status"] == "Strong"
    assert result["signals"]["leadership"]["above_50"] == 2
    assert result["signals"]["leadership"]["total"] == 2
    assert result["signals"]["credit"]["status"] == "Healthy"
    assert result["signals"]["cape"]["status"] == "neutral"
    assert result["signals"]["cape"]["value"] == 25
    assert result["regime"] == "TRANSITION"

