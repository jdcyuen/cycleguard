import pandas as pd
import pytest

from ingestion.transactions.transactions_csv_loader import (
    TransactionsCSVLoader,
)


@pytest.fixture
def loader():

    return TransactionsCSVLoader()


def test_load_valid_csv(
    loader,
    tmp_path,
):

    csv_file = tmp_path / "transactions.csv"

    csv_file.write_text(
        """Run Date,Action,Symbol,Description,Type,Price ($),Quantity,Commission ($),Fees ($),Accrued Interest ($),Amount ($),Cash Balance ($),Settlement Date
2024-01-01,BUY,AAPL,Apple Inc,Trade,150.25,10,1.00,0.50,0.00,1502.50,10000.00,2024-01-03
"""
    )

    dataframe = loader.load(
        str(csv_file)
    )

    assert len(dataframe) == 1

    row = dataframe.iloc[0]

    assert row["action"] == "BUY"
    assert row["symbol"] == "AAPL"
    assert row["description"] == "Apple Inc"
    assert row["trade_type"] == "Trade"


def test_column_mapping(
    loader,
    tmp_path,
):

    csv_file = tmp_path / "transactions.csv"

    csv_file.write_text(
        """Run Date,Action,Symbol,Description,Type,Price ($),Quantity,Commission ($),Fees ($),Accrued Interest ($),Amount ($),Cash Balance ($),Settlement Date
2024-01-01,BUY,AAPL,Apple Inc,Trade,150.25,10,1.00,0.50,0.00,1502.50,10000.00,2024-01-03
"""
    )

    dataframe = loader.load(
        str(csv_file)
    )

    expected_columns = [
        "run_date",
        "action",
        "symbol",
        "description",
        "trade_type",
        "price",
        "quantity",
        "commission",
        "fees",
        "accrued_interest",
        "amount",
        "cash_balance",
        "settlement_date",
    ]

    for column in expected_columns:

        assert column in dataframe.columns


def test_convert_dates(
    loader,
    tmp_path,
):

    csv_file = tmp_path / "transactions.csv"

    csv_file.write_text(
        """Run Date,Action,Symbol,Description,Type,Price ($),Quantity,Commission ($),Fees ($),Accrued Interest ($),Amount ($),Cash Balance ($),Settlement Date
2024-01-01,BUY,AAPL,Apple Inc,Trade,150.25,10,1.00,0.50,0.00,1502.50,10000.00,2024-01-03
"""
    )

    dataframe = loader.load(
        str(csv_file)
    )

    assert pd.api.types.is_datetime64_any_dtype(
        dataframe["run_date"]
    )

    assert pd.api.types.is_datetime64_any_dtype(
        dataframe["settlement_date"]
    )


def test_invalid_dates_become_nat(
    loader,
    tmp_path,
):

    csv_file = tmp_path / "transactions.csv"

    csv_file.write_text(
        """Run Date,Action,Symbol,Description,Type,Price ($),Quantity,Commission ($),Fees ($),Accrued Interest ($),Amount ($),Cash Balance ($),Settlement Date
bad-date,BUY,AAPL,Apple Inc,Trade,150.25,10,1.00,0.50,0.00,1502.50,10000.00,bad-date
"""
    )

    dataframe = loader.load(
        str(csv_file)
    )

    assert pd.isna(
        dataframe.iloc[0]["run_date"]
    )

    assert pd.isna(
        dataframe.iloc[0]["settlement_date"]
    )


def test_convert_numeric_columns(
    loader,
    tmp_path,
):

    csv_file = tmp_path / "transactions.csv"

    csv_file.write_text(
        """Run Date,Action,Symbol,Description,Type,Price ($),Quantity,Commission ($),Fees ($),Accrued Interest ($),Amount ($),Cash Balance ($),Settlement Date
2024-01-01,BUY,AAPL,Apple Inc,Trade,150.25,10,1.00,0.50,0.00,1502.50,10000.00,2024-01-03
"""
    )

    dataframe = loader.load(
        str(csv_file)
    )

    row = dataframe.iloc[0]

    assert row["price"] == 150.25
    assert row["quantity"] == 10
    assert row["commission"] == 1.00
    assert row["fees"] == 0.50
    assert row["accrued_interest"] == 0.00
    assert row["amount"] == 1502.50
    assert row["cash_balance"] == 10000.00


def test_invalid_numeric_values_become_nan(
    loader,
    tmp_path,
):

    csv_file = tmp_path / "transactions.csv"

    csv_file.write_text(
        """Run Date,Action,Symbol,Description,Type,Price ($),Quantity,Commission ($),Fees ($),Accrued Interest ($),Amount ($),Cash Balance ($),Settlement Date
2024-01-01,BUY,AAPL,Apple Inc,Trade,abc,xyz,bad,bad,bad,bad,bad,2024-01-03
"""
    )

    dataframe = loader.load(
        str(csv_file)
    )

    row = dataframe.iloc[0]

    assert pd.isna(row["price"])
    assert pd.isna(row["quantity"])
    assert pd.isna(row["commission"])
    assert pd.isna(row["fees"])
    assert pd.isna(row["accrued_interest"])
    assert pd.isna(row["amount"])
    assert pd.isna(row["cash_balance"])


def test_load_file_not_found(
    loader,
):

    with pytest.raises(
        FileNotFoundError
    ):
        loader.load(
            "does_not_exist.csv"
        )