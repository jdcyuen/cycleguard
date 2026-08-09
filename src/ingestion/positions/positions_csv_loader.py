import pandas as pd
from ingestion.common.base_csv_loader import BaseCsvLoader
#from models.position import Position
from core.logger import get_logger
from decimal import Decimal, InvalidOperation


class PositionsCSVLoader(BaseCsvLoader[pd.DataFrame]):
    """
    Load and normalize portfolio CSV data.
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

       
    # --------------------------------------------------
    # Helper: Clean and convert numeric strings
    # --------------------------------------------------
    @staticmethod
    def clean_numeric(val) -> Decimal | None:
            
        if val is None or pd.isna(val):
            return None

        cleaned = (
                str(val)
                .replace("$", "")
                .replace("%", "")
                .replace(",", "")
                .replace("+", "")
                .strip()
            )

        if cleaned.lower() in ("", "nan", "none", "null", "n/a", "--", "cash"):
            return None

        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None

    def load(self, file_path: str) ->  pd.DataFrame:
        """
        Load CSV file into normalized row dictionaries.
        """

        self.logger.info(
            "Loading CSV file: %s",
            file_path,
        )

        try:
            df = pd.read_csv(file_path, index_col=False)

        except FileNotFoundError:
            self.logger.exception(
                "CSV file not found: %s",
                file_path,
            )
            raise

        except Exception:
            self.logger.exception(
                "Failed loading CSV file: %s",
                file_path,
            )
            raise

        if df.empty:
            self.logger.warning(
                "CSV file is empty: %s",
                file_path,
            )
            return pd.DataFrame()

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

            # Normalize symbol
            if symbol is not None:
                symbol = str(symbol).replace("*", "").strip()
                r["symbol"] = symbol
            
            # Filter out missing/null symbol or account values
            if (
                symbol is None
                or str(symbol).strip().lower() in ("", "nan", "none")
                or account_number is None
                or str(account_number).strip().lower() in ("", "nan", "none")
            ):
                continue
                
            symbol_str = str(symbol).strip()
            account_num_str = str(account_number).strip()
            
            # Filter out disclaimers and footers (which have very long text or metadata keywords)
            if (
                not symbol_str 
                or not account_num_str 
                or len(account_num_str) > 50 
                or "downloaded" in account_num_str.lower()
                or "spreadsheet" in account_num_str.lower()
                or "brokerage" in account_num_str.lower()
                or symbol_str.__eq__("Pending activity")
                
            ):
                continue
                
            # Clean numeric values
            for col in numeric_cols:
                if col in r:
                    r[col] = self.clean_numeric(r[col])
                    
            valid_rows.append(r)

        self.logger.info(f"Loaded {len(valid_rows)} valid portfolio rows (filtered and cleaned from {len(rows)})")

        positions_dataframe = pd.DataFrame(valid_rows)
        return positions_dataframe