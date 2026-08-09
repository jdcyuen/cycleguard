import pandas as pd
from ingestion.common.base_csv_loader import BaseCsvLoader
from models.transaction import Transaction
from core.logger import get_logger

logger = get_logger(__name__)


class TransactionsCSVLoader( BaseCsvLoader[Transaction]):

    def __init__(
        self,
        action_map: list[dict],
    ):
        self.action_map = action_map

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

    def normalize_action(
        self,
        action: str | None,
    ) -> str | None:

        if action is None or pd.isna(action):
            return None

        if not isinstance(action, str):
            action = str(action)

        action = action.strip().upper()

        for rule in self.action_map:

            if rule["match"] in action:

                logger.debug(
                    "Normalized action '%s' -> '%s'",
                    action,
                    rule["normalized"],
                )

                return rule["normalized"]

        logger.warning(
            "Unable to normalize action: %s",
            action,
        )

        return action

    def load(self, csv_file: str) -> list[Transaction]:
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

        logger.debug(
            "Original columns: %s",
            list(dataframe.columns),
        )

        dataframe.rename(
            columns=self.COLUMN_MAPPING,
            inplace=True,
        )

        logger.debug(
            "Normalizing transaction actions."
        )

        missing_actions = dataframe[
            dataframe["action"].isna()
        ]

        if not missing_actions.empty:

            logger.warning(
                "Found %d rows with missing action.",
                len(missing_actions),
            )

            logger.debug(
                "Rows with missing action:\n%s",
                missing_actions.to_string(),
            )

        dataframe["action"] = dataframe["action"].apply(
            self.normalize_action
        )

        logger.debug(
            "Normalized columns: %s",
            list(dataframe.columns),
        )

        # --------------------------------------------------
        # Debug rows before removing empty rows
        # --------------------------------------------------

        missing_action_symbol = dataframe[
            dataframe["action"].isna()
            & dataframe["symbol"].isna()
        ]

        if not missing_action_symbol.empty:

            logger.warning(
                "Found %d rows with missing action AND symbol before cleanup.",
                len(missing_action_symbol),
            )

            logger.debug(
                "Rows removed by empty row cleanup:\n%s",
                missing_action_symbol.to_string(),
            )

        # --------------------------------------------------
        # Remove rows without transaction data
        # --------------------------------------------------

        before_count = len(dataframe)

        dataframe = dataframe.dropna(
            subset=[
                "action",
                "symbol",
            ],
            how="all",
        )

        after_count = len(dataframe)

        logger.info(
            "Removed %d empty transaction rows.",
            before_count - after_count,
        )

        # --------------------------------------------------
        # Debug remaining blank actions
        # --------------------------------------------------

        remaining_blank_actions = dataframe[
            dataframe["action"].isna()
        ]

        if not remaining_blank_actions.empty:

            logger.warning(
                "Found %d remaining rows with missing action after cleanup.",
                len(remaining_blank_actions),
            )

            logger.debug(
                "Remaining rows with missing action:\n%s",
                remaining_blank_actions.to_string(),
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