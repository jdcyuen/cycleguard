import pandas as pd
import pytest

from data.providers.data_provider_error import DataProviderError
from data.providers.yfinance_data_provider import YFinanceDataProvider


def test_fetch_data_raises_data_provider_error_on_yfinance_failure(monkeypatch):
    def mock_download(*args, **kwargs):
        raise RuntimeError("Yahoo Finance unavailable")

    monkeypatch.setattr(
        "data.providers.yfinance_data_provider.yf.download",
        mock_download,
    )

    provider = YFinanceDataProvider()

    with pytest.raises(DataProviderError):
        provider.fetch_data("SPY", "2025-01-01")

def test_fetch_multiple_tickers_raises_data_provider_error_on_yfinance_failure(
    monkeypatch,
):
    def mock_download(*args, **kwargs):
        raise RuntimeError("Yahoo Finance unavailable")

    monkeypatch.setattr(
        "data.providers.yfinance_data_provider.yf.download",
        mock_download,
    )

    provider = YFinanceDataProvider()

    with pytest.raises(DataProviderError):
        provider.fetch_multiple_tickers(["SPY", "QQQ"])