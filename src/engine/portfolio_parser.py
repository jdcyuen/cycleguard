# portfolio_parser.py

from abc import ABC, abstractmethod
import io
import csv


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
            file.seek(0)
            
            # Handle both bytes (Streamlit) and strings robustly
            if isinstance(file.read(0), bytes):
                wrapper = io.TextIOWrapper(file, encoding='utf-8', errors='replace')
            else:
                wrapper = file
                
            wrapper.seek(0)
            reader = csv.reader(wrapper)
            
            # Based on user confirmation:
            # Column C (index 2) = Symbol
            # Column H (index 7) = Current Value
            symbol_idx = 2
            val_idx = 7
            
            portfolio = {}
            
            # Extract data
            for row in reader:
                if len(row) <= max(symbol_idx, val_idx):
                    continue
                    
                sym = row[symbol_idx].strip()
                val_str = row[val_idx].strip()
                
                # Skip meaningless or empty symbols, or the header row itself
                if not sym or "pending" in sym.lower() or "core" in sym.lower() or "symbol" in sym.lower():
                    continue
                    
                # Clean current value
                val_str = val_str.replace('$', '').replace(',', '')
                try:
                    val = float(val_str)
                    
                    # Strip asterisks (e.g. FDRXX**)
                    clean_sym = sym.replace("*", "")
                    
                    portfolio[clean_sym] = portfolio.get(clean_sym, 0.0) + val
                except ValueError:
                    continue
                    
            return portfolio
            
        except Exception:
            return None
