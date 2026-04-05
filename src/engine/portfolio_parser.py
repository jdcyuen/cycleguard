# portfolio_parser.py

import pandas as pd
from abc import ABC, abstractmethod
import io


# -------------------------
# INTERFACE (DIP)
# -------------------------
class IPortfolioParser(ABC):
    """Abstract interface for brokerage portfolio parsers."""
    @abstractmethod
    def parse(self, file) -> dict:
        """Parses a file-like object and returns a ticker -> value dictionary."""
        pass


# -------------------------
# IMPLEMENTATION (SRP)
# -------------------------
class FidelityParser(IPortfolioParser):
    """Responsible ONLY for parsing and cleaning Fidelity CSV exports."""
    def parse(self, file) -> dict:
        try:
            # Handle both bytes (Streamlit) and strings
            file.seek(0)
            lines = file.readlines()

            header_index = -1
            for i, line in enumerate(lines):
                decoded_line = (
                    line.decode("utf-8").lower()
                    if isinstance(line, bytes)
                    else line.lower()
                )
                if "symbol" in decoded_line and "current value" in decoded_line:
                    header_index = i
                    break

            if header_index == -1:
                return None

            # Rewind and read with header offset
            file.seek(0)
            df = pd.read_csv(
                file, 
                skiprows=header_index, 
                sep=None, 
                on_bad_lines="skip", 
                engine="python"
            )

            # Normalize column names
            df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

            if "symbol" not in df.columns or "current_value" not in df.columns:
                return None

            # Clean symbols (remove whitespace/non-ticker text)
            df["symbol"] = df["symbol"].astype(str).str.strip()

            # Clean current_value (remove $, commas, and non-numeric characters)
            if df["current_value"].dtype == "object":
                df["current_value"] = (
                    df["current_value"]
                    .astype(str)
                    .str.replace("$", "", regex=False)
                    .str.replace(",", "", regex=False)
                    .str.extract(r"(\d+\.?\d*)")
                    .astype(float)
                )

            # Filter out rows without valid symbols or values
            df = df.dropna(subset=["symbol", "current_value"])

            # Group by symbol in case of duplicate entries
            portfolio = df.groupby("symbol")["current_value"].sum().to_dict()

            return portfolio

        except Exception:
            return None
