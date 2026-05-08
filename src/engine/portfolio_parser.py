# src/data/portfolio_parser.py

from abc import ABC, abstractmethod
import io
import csv
from typing import Dict, Optional


# -------------------------
# INTERFACE (DIP)
# -------------------------
class IPortfolioParser(ABC):
    """Abstract interface for brokerage portfolio parsers."""

    @abstractmethod
    def parse(self, file) -> Dict[str, float]:
        pass


# -------------------------
# IMPLEMENTATION (SRP)
# -------------------------
class FidelityParser(IPortfolioParser):
    """Parses Fidelity CSV exports into a clean portfolio dictionary."""

    def parse(self, file) -> Optional[Dict[str, float]]:
        try:
            file.seek(0)

            # Handle both file types safely
            if isinstance(file.read(0), bytes):
                wrapper = io.TextIOWrapper(file, encoding="utf-8", errors="replace")
            else:
                wrapper = file

            wrapper.seek(0)
            reader = csv.reader(wrapper)

            symbol_idx = None
            value_idx = None
            portfolio: Dict[str, float] = {}

            for row in reader:
                if not row:
                    continue

                # Normalize row for header detection
                lower = [col.strip().lower() for col in row]

                # Detect header row dynamically
                if "symbol" in lower and "current value" in lower:
                    symbol_idx = lower.index("symbol")
                    value_idx = lower.index("current value")
                    continue

                # Skip until headers are found
                if symbol_idx is None or value_idx is None:
                    continue

                # Guard against malformed rows
                if len(row) <= max(symbol_idx, value_idx):
                    continue

                sym = row[symbol_idx].strip()
                val_str = row[value_idx].strip()

                # Skip invalid rows / headers repeated in data
                if not sym or sym.lower() == "symbol":
                    continue

                # Clean currency formatting
                val_str = val_str.replace("$", "").replace(",", "").strip()

                try:
                    value = float(val_str)
                    clean_sym = sym.replace("*", "")
                    portfolio[clean_sym] = portfolio.get(clean_sym, 0.0) + value
                except ValueError:
                    continue

            # If no valid headers were found, treat as invalid file
            if symbol_idx is None or value_idx is None:
                return None

            return portfolio

        except Exception:
            # In production you may want logging here instead of silent fail
            return None
