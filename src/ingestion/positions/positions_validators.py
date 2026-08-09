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
        "current_value",
    ]

    def validate(
        self,
        dataframe: pd.DataFrame,
    ) -> None:

        logger.info("Validating positions CSV")

        try:

            self._validate_not_empty(dataframe)
            self._validate_columns(dataframe)
            self._validate_required_fields(dataframe)
            logger.info("Positions validation successful")

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

        logger.info("Validating DataFrame is not empty.")
        logger.debug("DataFrame contains %d row(s).", len(dataframe),)
        if dataframe.empty:
            logger.error("Validation failed: DataFrame is empty.")
            raise ValueError("Positions CSV is empty.")
        logger.info("DataFrame contains %d row(s). Validation passed.", len(dataframe),)

    
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

        logger.info(
            "Validating required position fields."
        )

        # --------------------------------------------------
        # Symbol
        # --------------------------------------------------

        logger.debug("Checking required field: symbol")

        if dataframe["symbol"].isnull().any():

            missing = dataframe[dataframe["symbol"].isnull()]

            logger.error("Found %d position(s) with missing symbol.", len(missing),)
            logger.debug("Rows with missing symbol:\n%s", missing )

            raise ValueError(
                "One or more positions "
                "are missing a symbol."
            )

        logger.debug("All positions contain a symbol.")

        # --------------------------------------------------
        # Quantity
        # --------------------------------------------------

        logger.debug("Checking required field: quantity")

        missing_quantity = dataframe[
            dataframe["quantity"].isna()
            & (dataframe["symbol"] != "FDRXX")
        ]

        if not missing_quantity.empty:
            logger.error(
                "Found %d position(s) with missing quantity.",
                len(missing_quantity),
            )

            logger.debug(
                "Symbols missing quantity: %s",
                missing_quantity["symbol"].tolist(),
            )
            raise ValueError(
                "One or more positions are missing quantity."
            )

        logger.debug("All positions contain a quantity.")

        # --------------------------------------------------
        # Current Value
        # --------------------------------------------------

        logger.debug("Checking required field: current_value")
        
        if dataframe["current_value"].isnull().any():
            missing = dataframe[
                dataframe["current_value"].isnull()
            ]

            logger.error(
                "Found %d position(s) with missing current value.",
                len(missing),
            )

            logger.debug(
                "Rows with missing current value:\n%s",
                missing,
            )
            raise ValueError(
                "One or more positions "
                "are missing current value."
            )

        logger.info(
            "Required field validation completed successfully."
        )    