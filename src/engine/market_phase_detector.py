# src/engine/market_phase_detector.p


import pandas as pd
import logging

from config.config_manager import get_config
from engine.regime.signals.breadth import BreadthSignal

from data.providers.idata_provider import IDataProvider
from data.providers.yfinance_data_provider import YFinanceDataProvider
from data.providers.cape_data_provider import CapeDataProvider

logger = logging.getLogger(__name__)

class MarketPhaseDetector:
    """
    Fetches and prepares market data for the RegimeEngine.
    """

    def __init__(
        self,
        config=None,
        data_provider: IDataProvider = None,
        cape_data_provider: CapeDataProvider = None,
    ):
        self.config = config if config else get_config()
        self.regime_config = self.config.get("regime", {}).get("regime_system", {})
        self.signals = self.regime_config.get("signals", {})
        self.data_provider = data_provider if data_provider else YFinanceDataProvider()
        self.cape_data_provider = (
            cape_data_provider if cape_data_provider else CapeDataProvider()
        )
        logger.debug(
            "MarketPhaseDetector initialized with data_provider=%s, "
            "cape_data_provider=%s",
            type(self.data_provider).__name__,
            type(self.cape_data_provider).__name__,
        )

    def _fetch_daily_closes(self, tickers: list, period="1y") -> pd.DataFrame:
        """Fetch daily closing prices through the configured data provider."""
        if not tickers:
            return pd.DataFrame()

        return self.data_provider.fetch_multiple_tickers(
            tickers,
            period=period,
        )

    def get_regime_data(self) -> dict:
        """
        Fetch and prepare market data for the new RegimeEngine.

        Returns the normalized data structure expected by regime signals.
        """
        trend_inputs = self.signals.get("trend", {}).get("inputs", ["SPY"])
        trend_proxy = trend_inputs[0]

        volatility_inputs = self.signals.get(
            "volatility", {}
        ).get("inputs", ["^VIX"])
        vix = volatility_inputs[0]

        leadership_inputs = self.signals.get(
            "leadership", {}
        ).get("inputs", ["SMH", "QQQ"])

        credit_inputs = self.signals.get(
            "credit", {}
        ).get("inputs", ["JNK", "SHY"])

        breadth_inputs = self.signals.get(
            "breadth", {}
        ).get("inputs", [])

        all_tickers = list(
            set(
                [trend_proxy, vix]
                + leadership_inputs
                + credit_inputs
                + breadth_inputs
            )
        )

        logger.debug(
            "Fetching regime market data for %d tickers: %s",
            len(all_tickers),
            sorted(all_tickers),
        )

        closes = self._fetch_daily_closes(all_tickers, period="1y")
        logger.debug(
            "Fetched regime market data: rows=%d, columns=%d",
            len(closes),
            len(closes.columns) if not closes.empty else 0,
        )

        if closes.empty:
            logger.warning("No market data returned for regime evaluation.")

            return {
                "latest": {},
                "dma50": {},
                "dma200": {},
            }

        latest = closes.ffill().iloc[-1]
        dma50 = closes.apply(lambda series: series.dropna().rolling(window=50).mean().iloc[-1])
        dma200 = closes.apply(lambda series: series.dropna().rolling(window=200).mean().iloc[-1])
        cape = self.cape_data_provider.get_latest()

        logger.debug(
            "Retrieved latest CAPE observation: date=%s, value=%.4f",
            cape["date"],
            cape["cape"],
        )

        return {
            "latest": {
                **latest.to_dict(),
                "CAPE": cape["cape"],
            },
            "dma50": dma50.to_dict(),
            "dma200": dma200.to_dict(),
        }

    