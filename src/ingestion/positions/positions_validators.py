import pandas as pd

from core.logger import get_logger

logger = get_logger(__name__)


class PositionsValidationError(Exception):
    """Raised when positions validation fails."""


class PositionsValidator:
    """
    Validates Fidelity positions CSV files.
    """

    REQUIRED_COLUMNS = [
        "symbol",
        "quantity",
        "market_value",
    ]

    def validate(
        self,
        dataframe: pd.DataFrame,
    ) -> None:

        logger.info(
            "Validating positions CSV"
        )

        try:

            self._validate_not_empty(
                dataframe
            )

            self._validate_columns(
                dataframe
            )

            self._validate_required_fields(
                dataframe
            )

            logger.info(
                "Positions validation successful"
            )

        except ValueError:
            raise

        except Exception as exc:

            logger.exception(
                "Unexpected error during "
                "positions validation"
            )

            raise PositionsValidationError(
                "Positions validation failed."
            ) from exc

    def _validate_not_empty(
        self,
        dataframe: pd.DataFrame,
    ) -> None:

        if dataframe.empty:

            raise ValueError(
                "Positions CSV is empty."
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

        if dataframe["symbol"].isnull().any():

            raise ValueError(
                "One or more positions "
                "are missing a symbol."
            )

        if dataframe["quantity"].isnull().any():

            raise ValueError(
                "One or more positions "
                "are missing quantity."
            )

        if dataframe["market_value"].isnull().any():

            raise ValueError(
                "One or more positions "
                "are missing market value."
            )