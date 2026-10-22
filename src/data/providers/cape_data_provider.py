from datetime import date
from pathlib import Path

import pandas as pd

from data.providers.data_provider_error import DataProviderError


class CapeDataProvider:
    """Provides Shiller CAPE observations from the Shiller data file."""

    def __init__(self, data_file: str | None = None):
        if data_file:
            self.data_file = Path(data_file)
        else:
            self.data_file = (
                Path(__file__).resolve().parents[1] / "cape" / "ie_data.xls"
            )

    def _load_data(self) -> pd.DataFrame:
        try:
            df = pd.read_excel(
                self.data_file,
                sheet_name="Data",
                header=7,
            )
        except Exception as exc:
            raise DataProviderError(
                f"Failed to load CAPE data from: {self.data_file}"
            ) from exc

        df = df[["Date", "CAPE"]].dropna(subset=["Date", "CAPE"]).copy()

        return df

    def get_latest(self) -> dict:
        df = self._load_data()

        if df.empty:
            raise DataProviderError("No CAPE observations available.")

        row = df.iloc[-1]

        return {
            "date": str(row["Date"]),
            "cape": float(row["CAPE"]),
        }

    def get_for_date(self, as_of_date: date) -> dict:
        df = self._load_data()

        if df.empty:
            raise DataProviderError("No CAPE observations available.")

        dates = pd.to_datetime(
            df["Date"].astype(str),
            format="%Y.%m",
            errors="coerce",
        )

        target = pd.Timestamp(as_of_date)

        valid = df.loc[dates <= target]

        if valid.empty:
            raise DataProviderError(
                f"No CAPE observation available on or before {as_of_date}."
            )

        row = valid.iloc[-1]

        return {
            "date": str(row["Date"]),
            "cape": float(row["CAPE"]),
        }