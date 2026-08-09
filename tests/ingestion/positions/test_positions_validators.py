import pandas as pd
import pytest

from ingestion.positions.positions_validators import (
    PositionsValidator,
)

from unittest.mock import patch

from ingestion.positions.positions_validators import (
    PositionsValidator,
    PositionsValidationError,
)

def test_validate_wraps_unexpected_error():

    validator = PositionsValidator()

    dataframe = pd.DataFrame(
        {
            "symbol": ["AAPL"],
            "quantity": [10],
            "current_value": [1000],
        }
    )

    with patch.object(
        validator,
        "_validate_columns",
        side_effect=RuntimeError(
            "boom"
        ),
    ):
        with pytest.raises(
            PositionsValidationError
        ):
            validator.validate(
                dataframe
            )


@pytest.fixture
def validator():

    return PositionsValidator()


def test_validate_success(
    validator,
):

    dataframe = pd.DataFrame(
        {
            "symbol": ["AAPL", "MSFT"],
            "quantity": [10, 5],
            "current_value": [2000.0, 1500.0],
        }
    )

    validator.validate(dataframe)


def test_validate_empty_dataframe(
    validator,
):

    dataframe = pd.DataFrame()

    with pytest.raises(
        ValueError,
        match="Positions CSV is empty",
    ):
        validator.validate(
            dataframe
        )


def test_validate_missing_symbol_column(
    validator,
):

    dataframe = pd.DataFrame(
        {
            "quantity": [10],
            "current_value": [1000],
        }
    )

    with pytest.raises(
        ValueError,
        match="Missing columns",
    ):
        validator.validate(
            dataframe
        )


def test_validate_missing_quantity_column(
    validator,
):

    dataframe = pd.DataFrame(
        {
            "symbol": ["AAPL"],
            "current_value": [1000],
        }
    )

    with pytest.raises(
        ValueError,
        match="Missing columns",
    ):
        validator.validate(
            dataframe
        )


def test_validate_missing_current_value_column(
    validator,
):

    dataframe = pd.DataFrame(
        {
            "symbol": ["AAPL"],
            "quantity": [10],
        }
    )

    with pytest.raises(
        ValueError,
        match="Missing columns",
    ):
        validator.validate(
            dataframe
        )


def test_validate_null_symbol(
    validator,
):

    dataframe = pd.DataFrame(
        {
            "symbol": [None],
            "quantity": [10],
            "current_value": [1000],
        }
    )

    with pytest.raises(
        ValueError,
        match="missing a symbol",
    ):
        validator.validate(
            dataframe
        )


def test_validate_null_quantity(
    validator,
):

    dataframe = pd.DataFrame(
        {
            "symbol": ["AAPL"],
            "quantity": [None],
            "current_value": [1000],
        }
    )

    with pytest.raises(
        ValueError,
        match="missing quantity",
    ):
        validator.validate(
            dataframe
        )


def test_validate_null_current_value(
    validator,
):

    dataframe = pd.DataFrame(
        {
            "symbol": ["AAPL"],
            "quantity": [10],
            "current_value": [None],
        }
    )

    with pytest.raises(
        ValueError,
        match="missing current value",
    ):
        validator.validate(
            dataframe
        )


def test_validate_multiple_missing_columns(
    validator,
):

    dataframe = pd.DataFrame(
        {
            "symbol": ["AAPL"],
        }
    )

    with pytest.raises(
        ValueError,
        match="Missing columns",
    ):
        validator.validate(
            dataframe
        )