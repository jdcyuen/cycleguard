import pandas as pd

from core.logger import get_logger


class PositionsCSVLoader:
    """
    Load and normalize portfolio CSV data.
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def load(self, file_path: str) -> list[dict]:
        """
        Load CSV file into normalized row dictionaries.
        """

        self.logger.info(f"Loading CSV file: {file_path}")

        try:
            df = pd.read_csv(file_path, index_col=False)

        except FileNotFoundError as e:
            self.logger.error(f"CSV file not found: {file_path}")
            raise e

        except Exception as e:
            self.logger.error(f"Failed to load CSV file: {file_path}")
            raise e

        if df.empty:
            self.logger.warning(f"CSV file is empty: {file_path}")
            return []

        # --------------------------------------------------
        # Normalize column names
        # --------------------------------------------------
        df.columns = [
            col.strip()
            .lower()
            .replace(" ", "_")
            .replace("/", "_")
            .replace("'", "")
            .replace("%", "percent")
            .replace("$", "dollar")
            for col in df.columns
        ]

        self.logger.info(f"Normalized columns: {list(df.columns)}")

        # --------------------------------------------------
        # Replace NaN values with None
        # --------------------------------------------------
        df = df.where(pd.notnull(df), None)

        rows = df.to_dict(orient="records")

        # --------------------------------------------------
        # Helper: Clean and convert numeric strings
        # --------------------------------------------------
        def clean_numeric(val) -> float | None:
            if val is None or pd.isna(val):
                return None
            if isinstance(val, (int, float)):
                return float(val)
            val_str = str(val).strip()
            if not val_str or val_str.lower() in ("nan", "none", "null", "n/a", "--", "cash"):
                return None
            cleaned = val_str.replace("$", "").replace("%", "").replace(",", "").replace("+", "").strip()
            try:
                return float(cleaned)
            except ValueError:
                return None

        # --------------------------------------------------
        # Filter and clean rows
        # --------------------------------------------------
        valid_rows = []
        numeric_cols = [
            "quantity",
            "average_cost_basis",
            "cost_basis_total",
            "current_value",
            "percent_of_account",
            "todays_gain_loss_dollar",
            "todays_gain_loss_percent",
            "total_gain_loss_dollar",
            "total_gain_loss_percent"
        ]

        for r in rows:
            symbol = r.get("symbol")
            account_number = r.get("account_number")
            
            # Filter out null/nan values (handling float nan)
            if symbol is None or pd.isna(symbol) or account_number is None or pd.isna(account_number):
                continue
                
            symbol_str = str(symbol).strip()
            account_str = str(account_number).strip()
            
            # Filter out disclaimers and footers (which have very long text or metadata keywords)
            if (
                not symbol_str 
                or not account_str 
                or len(account_str) > 50 
                or "downloaded" in account_str.lower()
                or "spreadsheet" in account_str.lower()
                or "brokerage" in account_str.lower()
            ):
                continue
                
            # Clean numeric values
            for col in numeric_cols:
                if col in r:
                    r[col] = clean_numeric(r[col])
                    
            valid_rows.append(r)

        self.logger.info(f"Loaded {len(valid_rows)} valid portfolio rows (filtered and cleaned from {len(rows)})")

        return valid_rows

