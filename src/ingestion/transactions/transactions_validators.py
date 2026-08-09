import pandas as pd

from config.config_manager import (
    get_config,
)

from core.logger import get_logger

logger = get_logger(__name__)


class TransactionsValidator:

    

    def __init__(self):
        pass

    def validate(
        self,
        dataframe: pd.DataFrame,
    ) -> None:

        logger.info("Validating transactions CSV")

        self._validate_not_empty(dataframe)
        self._validate_columns(dataframe)
        self._validate_required_fields(dataframe)
        self._validate_actions(dataframe)

        logger.info("Transactions validation successful")

    def _validate_not_empty(
        self,
        dataframe: pd.DataFrame,
    ) -> None:

        if dataframe.empty:

            raise ValueError(
                "Transactions CSV is empty."
            )

    def _validate_columns(
        self,
        dataframe: pd.DataFrame,
    ) -> None:

        logger.info(
            "Validating required transaction columns."
        )

        required_columns = [
            "run_date",
            "action",
            "trade_type",
            "amount",
        ]

        logger.debug(
            "Available CSV columns: %s",
            list(dataframe.columns),
        )

        logger.debug(
            "Required columns: %s",
            required_columns,
        )

        missing_columns = [
            column
            for column in required_columns
            if column not in dataframe.columns
        ]

        if missing_columns:
            logger.error(
                "Missing required column(s): %s",
                missing_columns,
            )

            logger.debug(
                "Available columns were: %s",
                list(dataframe.columns),
            )

            raise ValueError(
                f"Missing columns: "
                f"{missing_columns}"
            )

        logger.info(
            "Column validation passed. "
            "DataFrame contains %d column(s).",
            len(dataframe.columns),
        )

    def _validate_required_fields(
        self,
        dataframe: pd.DataFrame,
    ) -> None:


        logger.info(
            "Validating required transaction fields."
        )

        logger.debug(
            "Validating %d transaction row(s).",
            len(dataframe),
        )

        # --------------------------------------------------
        # Run Date
        # --------------------------------------------------

        logger.debug(
                "Checking required field: run_date"
            )

        missing_run_date = dataframe[
            dataframe["run_date"].isnull()
        ]

        parsed_dates = pd.to_datetime(
            dataframe["run_date"],
            errors="coerce",
        )

        invalid_run_date = dataframe[
            parsed_dates.isna()
        ]

        bad_run_date = dataframe.loc[
            missing_run_date.index.union(
                invalid_run_date.index
            )
        ]

        if not bad_run_date.empty:

            logger.error(
                "Found %d transaction(s) with missing or invalid run_date.",
                len(bad_run_date),
            )

            logger.error(
                "Rows with invalid run_date:\n%s",
                bad_run_date.to_string(),
            )


            raise ValueError(
                "One or more transactions are missing run_date."
            )

        logger.debug(
            "All transactions contain run_date."
        )

        # --------------------------------------------------
        # Action
        # --------------------------------------------------

        logger.debug(
            "Checking required field: action"
        )

        missing = dataframe[
            dataframe["action"].isnull()
        ]

        if not missing.empty:

            logger.error(
                "Found %d transaction(s) with missing action.",
                len(missing),
            )

            logger.debug(
                "Rows with missing action:\n%s",
                missing,
            )

            raise ValueError(
                "One or more transactions are missing action."
            )

        logger.debug(
            "All transactions contain action."
        )

        # --------------------------------------------------
        # Trade Type
        # --------------------------------------------------

        logger.debug(
            "Checking required field: trade_type"
        )

        missing = dataframe[
            dataframe["trade_type"].isnull()
        ]

        if not missing.empty:

            logger.error(
                "Found %d transaction(s) with missing trade_type.",
                len(missing),
            )

            logger.debug(
                "Rows with missing trade_type:\n%s",
                missing,
            )

            raise ValueError(
                "One or more transactions are missing trade_type."
            )

        logger.debug(
            "All transactions contain trade_type."
        )

        # --------------------------------------------------
        # Amount
        # --------------------------------------------------

        logger.debug(
            "Checking required field: amount"
        )

        missing = dataframe[
            dataframe["amount"].isnull()
        ]

        if not missing.empty:

            logger.error(
                "Found %d transaction(s) with missing amount.",
                len(missing),
            )

            logger.debug(
                "Rows with missing amount:\n%s",
                missing,
            )

            raise ValueError(
                "One or more transactions are missing amount."
            )

        logger.debug(
            "All transactions contain amount."
        )

    logger.info(
        "Required transaction field validation completed successfully."
    )

    def _validate_actions(
        self,
        dataframe: pd.DataFrame,
    ) -> None:

        logger.info("Validating transaction actions.")

        valid_actions = {
            "BUY",
            "SELL",
            "DIVIDEND",
            "REINVESTMENT",
            "CORE_PURCHASE",
            "CORE_REDEMPTION",
            "DISTRIBUTION",
        }

        logger.debug(
            "Valid actions: %s",
            sorted(valid_actions),
        )

        csv_actions = set(
            dataframe["action"]
            .dropna()
            .unique()
        )
        logger.debug(
            "Actions found in CSV: %s",
            sorted(csv_actions),
        )

        unknown_actions = (
            csv_actions
            - valid_actions
        )

        if unknown_actions:

            logger.error(
                "Unknown Fidelity actions found: %s",
                sorted(unknown_actions),
            )

            invalid_rows = dataframe[
                dataframe["action"].isin(unknown_actions)
            ]

            logger.error(
                "Rows containing unknown actions:\n%s",
                invalid_rows.to_string(),
            )
            raise ValueError(
                "Unknown Fidelity actions "
                f"found: "
                f"{sorted(unknown_actions)}"
            )

    logger.info("All transaction actions are valid.")