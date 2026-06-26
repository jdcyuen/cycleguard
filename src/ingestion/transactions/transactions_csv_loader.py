import pandas as pd

from core.logger import get_logger

logger = get_logger(__name__)


class TransactionsCSVLoader:
    """
    Loads Fidelity transactions CSV files.
    """

    COLUMN_MAPPING = {
        "Run Date": "run_date",
        "Action": "action",
        "Symbol": "symbol",
        "Description": "description",
        "Type": "trade_type",
        "Price ($)": "price",
        "Quantity": "quantity",
        "Commission ($)": "commission",
        "Fees ($)": "fees",
        "Accrued Interest ($)": "accrued_interest",
        "Amount ($)": "amount",
        "Cash Balance ($)": "cash_balance",
        "Settlement Date": "settlement_date",
    }

    def load(self, csv_file: str) -> pd.DataFrame:
        """
        Load Fidelity transactions CSV.

        Parameters
        ----------
        csv_file : str
            Path to CSV file.

        Returns
        -------
        pd.DataFrame
        """

        logger.info(
            f"Loading transactions CSV: "
            f"{csv_file}"
        )

        dataframe = pd.read_csv(csv_file)

        logger.debug(
            f"CSV contains "
            f"{len(dataframe)} rows"
        )

        dataframe.rename(
            columns=self.COLUMN_MAPPING,
            inplace=True,
        )

        self._convert_dates(dataframe)

        self._convert_numeric_columns( dataframe)

        logger.info(
            f"Loaded "
            f"{len(dataframe)} transaction rows"
        )

        return dataframe

    def _convert_dates(
        self,
        dataframe: pd.DataFrame,
    ) -> None:

        for column in [
            "run_date",
            "settlement_date",
        ]:

            dataframe[column] = pd.to_datetime(
                dataframe[column],
                errors="coerce",
            )

    def _convert_numeric_columns(
        self,
        dataframe: pd.DataFrame,
    ) -> None:

        numeric_columns = [
            "price",
            "quantity",
            "commission",
            "fees",
            "accrued_interest",
            "amount",
            "cash_balance",
        ]

        for column in numeric_columns:

            dataframe[column] = pd.to_numeric(
                dataframe[column],
                errors="coerce",
            )