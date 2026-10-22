import pandas as pd
import pytest
from unittest.mock import patch

from engine.market_phase_detector import MarketPhaseDetector
from data.providers.idata_provider import IDataProvider


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


@patch.object(MarketPhaseDetector, "_fetch_daily_closes")
def test_get_regime_data(mock_download):

    tickers = {
        "SPY": (249, 100, 110),
        "^VIX": (249, 18, 15),
        "QQQ": (249, 100, 110),
        "SMH": (249, 100, 110),
        "JNK": (249, 100, 105),
        "SHY": (249, 100, 100),
    }

    mock_download.return_value = make_price_history(tickers)

    detector = MarketPhaseDetector(config={})

    data = detector.get_regime_data()

    assert "latest" in data
    assert "dma50" in data
    assert "dma200" in data

    assert data["latest"]["SPY"] == 110
    assert data["dma50"]["SPY"] == pytest.approx(100.2)
    assert data["dma200"]["SPY"] == pytest.approx(100.05)  
    assert data["latest"]["CAPE"] == pytest.approx(40.575838) 

def test_get_regime_data_handles_misaligned_ticker_dates():
    dates = pd.date_range("2025-01-01", periods=252, freq="B")

    spy = pd.Series(range(252), index=dates, dtype=float)
    spy.iloc[-1] = 300

    vix_dates = pd.date_range("2024-12-31", periods=253, freq="B")
    vix = pd.Series(range(253), index=vix_dates, dtype=float)

    closes = pd.DataFrame({"SPY": spy, "^VIX": vix})

    with patch.object(
        MarketPhaseDetector,
        "_fetch_daily_closes",
        return_value=closes,
    ):
        detector = MarketPhaseDetector(config={})
        data = detector.get_regime_data()

    assert pd.notna(data["dma50"]["SPY"])
    assert pd.notna(data["dma200"]["SPY"])

def test_market_phase_detector_uses_injected_data_provider():
    class MockDataProvider(IDataProvider):
        def fetch_data(self, ticker: str, start_date: str) -> pd.DataFrame:
            return pd.DataFrame()

        def fetch_multiple_tickers(
            self,
            tickers: list[str],
            period: str = "1y",
        ) -> pd.DataFrame:
            return make_price_history(
                {ticker: (249, 100, 101) for ticker in tickers}
            )

    provider = MockDataProvider()
    detector = MarketPhaseDetector(config={}, data_provider=provider)

    result = detector._fetch_daily_closes(["SPY", "QQQ"])

    assert list(result.columns) == ["SPY", "QQQ"]
    assert len(result) == 250