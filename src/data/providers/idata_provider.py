from abc import ABC, abstractmethod
import pandas as pd
from data.providers.data_provider_error import DataProviderError


class IDataProvider(ABC):
    """Abstract interface for CycleGuard data sources."""

    @abstractmethod
    def fetch_data(self, ticker: str, start_date: str) -> pd.DataFrame:
        pass

    @abstractmethod
    def fetch_multiple_tickers(
        self,
        tickers: list[str],
        period: str = "1y",
    ) -> pd.DataFrame:
        pass