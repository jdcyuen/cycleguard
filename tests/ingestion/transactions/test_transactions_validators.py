import pandas as pd
import pytest

from ingestion.transactions.transactions_validators import (
    TransactionsValidator,
)


@pytest.fixture
def action_map():

    return {
        "BUY": "BUY",
        "SELL": "SELL",
        "DIVIDEND": "DIVIDEND",
    }


@pytest.fixture
def validator(
    action_map,
):

    return TransactionsValidator(
        action_map=action_map,
    )


def test_validate_success(
    validator,
):

    dataframe = pd.DataFrame(
        {
            "run_date": [
                pd.Timestamp(
                    "2024-01-01"
                )
            ],
            "action": [
                "BUY"
            ],
            "trade_type": [
                "Trade"
            ],
            "amount": [
                1000.00
            ],
        }
    )

    validator.validate(
        dataframe
    )


def test_validate_empty_dataframe(
    validator,
):

    dataframe = pd.DataFrame()

    with pytest.raises(
        ValueError,
        match="Transactions CSV is empty",
    ):
        validator.validate(
            dataframe
        )


def test_validate_missing_run_date_column(
    validator,
):

    dataframe = pd.DataFrame(
        {
            "action": ["BUY"],
            "trade_type": ["Trade"],
            "amount": [1000],
        }
    )

    with pytest.raises(
        ValueError,
        match="Missing columns",
    ):
        validator.validate(
            dataframe
        )


def test_validate_missing_action_column(
    validator,
):

    dataframe = pd.DataFrame(
        {
            "run_date": [
                pd.Timestamp(
                    "2024-01-01"
                )
            ],
            "trade_type": ["Trade"],
            "amount": [1000],
        }
    )

    with pytest.raises(
        ValueError,
        match="Missing columns",
    ):
        validator.validate(
            dataframe
        )


def test_validate_missing_trade_type_column(
    validator,
):

    dataframe = pd.DataFrame(
        {
            "run_date": [
                pd.Timestamp(
                    "2024-01-01"
                )
            ],
            "action": ["BUY"],
            "amount": [1000],
        }
    )

    with pytest.raises(
        ValueError,
        match="Missing columns",
    ):
        validator.validate(
            dataframe
        )


def test_validate_missing_amount_column(
    validator,
):

    dataframe = pd.DataFrame(
        {
            "run_date": [
                pd.Timestamp(
                    "2024-01-01"
                )
            ],
            "action": ["BUY"],
            "trade_type": ["Trade"],
        }
    )

    with pytest.raises(
        ValueError,
        match="Missing columns",
    ):
        validator.validate(
            dataframe
        )


def test_validate_null_run_date(
    validator,
):

    dataframe = pd.DataFrame(
        {
            "run_date": [None],
            "action": ["BUY"],
            "trade_type": ["Trade"],
            "amount": [1000],
        }
    )

    with pytest.raises(
        ValueError,
        match="missing run_date",
    ):
        validator.validate(
            dataframe
        )


def test_validate_null_action(
    validator,
):

    dataframe = pd.DataFrame(
        {
            "run_date": [
                pd.Timestamp(
                    "2024-01-01"
                )
            ],
            "action": [None],
            "trade_type": ["Trade"],
            "amount": [1000],
        }
    )

    with pytest.raises(
        ValueError,
        match="missing action",
    ):
        validator.validate(
            dataframe
        )


def test_validate_null_trade_type(
    validator,
):

    dataframe = pd.DataFrame(
        {
            "run_date": [
                pd.Timestamp(
                    "2024-01-01"
                )
            ],
            "action": ["BUY"],
            "trade_type": [None],
            "amount": [1000],
        }
    )

    with pytest.raises(
        ValueError,
        match="missing trade_type",
    ):
        validator.validate(
            dataframe
        )


def test_validate_null_amount(
    validator,
):

    dataframe = pd.DataFrame(
        {
            "run_date": [
                pd.Timestamp(
                    "2024-01-01"
                )
            ],
            "action": ["BUY"],
            "trade_type": ["Trade"],
            "amount": [None],
        }
    )

    with pytest.raises(
        ValueError,
        match="missing amount",
    ):
        validator.validate(
            dataframe
        )


def test_validate_unknown_action(
    validator,
):

    dataframe = pd.DataFrame(
        {
            "run_date": [
                pd.Timestamp(
                    "2024-01-01"
                )
            ],
            "action": [
                "UNKNOWN_ACTION"
            ],
            "trade_type": [
                "Trade"
            ],
            "amount": [
                1000
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="Unknown Fidelity actions",
    ):
        validator.validate(
            dataframe
        )


def test_validate_multiple_unknown_actions(
    validator,
):

    dataframe = pd.DataFrame(
        {
            "run_date": [
                pd.Timestamp(
                    "2024-01-01"
                ),
                pd.Timestamp(
                    "2024-01-02"
                ),
            ],
            "action": [
                "FOO",
                "BAR",
            ],
            "trade_type": [
                "Trade",
                "Trade",
            ],
            "amount": [
                100,
                200,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="Unknown Fidelity actions",
    ):
        validator.validate(
            dataframe
        )