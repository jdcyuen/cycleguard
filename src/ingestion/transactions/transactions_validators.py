import pandas as pd

from config.config_manager import (
    get_config,
)

from core.logger import get_logger

logger = get_logger(__name__)


class TransactionsValidator:

    REQUIRED_COLUMNS = [
        "run_date",
        "action",
        "trade_type",
        "amount",
    ]

    def __init__(
        self,
        action_map: dict,
    ):
        self._action_map = action_map

    def validate(
        self,
        dataframe: pd.DataFrame,
    ) -> None:

        logger.info(
            "Validating transactions CSV"
        )

        self._validate_not_empty(
            dataframe
        )

        self._validate_columns(
            dataframe
        )

        self._validate_required_fields(
            dataframe
        )

        self._validate_actions(
            dataframe
        )

        logger.info(
            "Transactions validation successful"
        )

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

        missing_columns = [
            column
            for column in self.REQUIRED_COLUMNS
            if column not in dataframe.columns
        ]

        if missing_columns:

            raise ValueError(
                f"Missing columns: "
                f"{missing_columns}"
            )

    def _validate_required_fields(
        self,
        dataframe: pd.DataFrame,
    ) -> None:

        if dataframe["run_date"].isnull().any():

            raise ValueError(
                "One or more transactions "
                "are missing run_date."
            )

        if dataframe["action"].isnull().any():

            raise ValueError(
                "One or more transactions "
                "are missing action."
            )

        if dataframe["trade_type"].isnull().any():

            raise ValueError(
                "One or more transactions "
                "are missing trade_type."
            )

        if dataframe["amount"].isnull().any():

            raise ValueError(
                "One or more transactions "
                "are missing amount."
            )

    def _validate_actions(
        self,
        dataframe: pd.DataFrame,
    ) -> None:

        config = get_config()

        action_map = (
            config
            .get("system", {})
            .get("actions", {})
        )

        valid_actions = set(
            self._action_map.keys()
        )

        csv_actions = set(
            dataframe["action"]
            .dropna()
            .unique()
        )

        unknown_actions = (
            csv_actions
            - valid_actions
        )

        if unknown_actions:

            raise ValueError(
                "Unknown Fidelity actions "
                f"found: "
                f"{sorted(unknown_actions)}"
            )