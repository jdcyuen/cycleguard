import pandas as pd

from src.core.logger import get_logger


class CSVLoader:
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
            df = pd.read_csv(file_path)

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

        self.logger.info(f"Loaded {len(rows)} portfolio rows")

        return rows
