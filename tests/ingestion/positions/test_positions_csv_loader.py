import pytest
from decimal import Decimal

from ingestion.positions.positions_csv_loader import (
    PositionsCSVLoader,
)

def _load_to_records(loader, file_path):
    res = loader.load(file_path)
    if hasattr(res, "to_dict"):
        return res.to_dict(orient="records")
    return res


@pytest.fixture
def loader():

    return PositionsCSVLoader()


def test_load_valid_csv(
    loader,
    tmp_path,
):

    csv_file = tmp_path / "positions.csv"

    csv_file.write_text(
        """Symbol,Account Number,Quantity,Current Value
AAPL,12345,10,"$2,500.00"
MSFT,12345,5,"$1,500.00"
"""
    )

    rows = _load_to_records(loader, str(csv_file))

    assert len(rows) == 2

    assert rows[0]["symbol"] == "AAPL"
    assert rows[0]["quantity"] == 10.0
    assert rows[0]["current_value"] == 2500.0

    assert rows[1]["symbol"] == "MSFT"
    assert rows[1]["quantity"] == 5.0
    assert rows[1]["current_value"] == 1500.0


def test_load_csv_with_headers_only(
    loader,
    tmp_path,
):

    csv_file = tmp_path / "empty.csv"

    csv_file.write_text(
        "Symbol,Account Number,Quantity\n"
    )

    rows = _load_to_records(loader, str(csv_file))

    assert rows == []


def test_load_file_not_found(
    loader,
):

    with pytest.raises(
        FileNotFoundError
    ):

        loader.load(
            "missing_file.csv"
        )


def test_column_normalization(
    loader,
    tmp_path,
):

    csv_file = tmp_path / "positions.csv"

    csv_file.write_text(
        """Symbol,Account Number,Current Value,Total Gain/Loss %
AAPL,12345,1000,+15%
"""
    )

    rows = _load_to_records(loader, str(csv_file))

    row = rows[0]

    assert "account_number" in row
    assert "current_value" in row
    assert "total_gain_loss_percent" in row


def test_filters_disclaimer_rows(
    loader,
    tmp_path,
):

    csv_file = tmp_path / "positions.csv"

    csv_file.write_text(
        """Symbol,Account Number,Quantity
AAPL,12345,10
FOOTER,"Downloaded from Fidelity Brokerage Services",0
"""
    )

    rows = _load_to_records(loader, str(csv_file))

    assert len(rows) == 1

    assert rows[0]["symbol"] == "AAPL"


def test_filters_missing_symbol(
    loader,
    tmp_path,
):

    csv_file = tmp_path / "positions.csv"

    csv_file.write_text(
        """Symbol,Account Number,Quantity
,12345,10
AAPL,12345,5
"""
    )

    rows = _load_to_records(loader, str(csv_file))

    assert len(rows) == 1

    assert rows[0]["symbol"] == "AAPL"


def test_numeric_cleanup(
    loader,
    tmp_path,
):

    csv_file = tmp_path / "positions.csv"

    csv_file.write_text(
        """Symbol,Account Number,Quantity,Current Value,Total Gain Loss Percent
AAPL,12345,"1,000","$12,345.67","+15.25%"
"""
    )

    rows = _load_to_records(loader, str(csv_file))

    row = rows[0]

    assert row["quantity"] == Decimal("1000")
    assert row["current_value"] == Decimal("12345.67")
    assert row["total_gain_loss_percent"] == Decimal("15.25")


def test_numeric_cleanup_special_values(
    loader,
    tmp_path,
):

    csv_file = tmp_path / "positions.csv"

    csv_file.write_text(
        """Symbol,Account Number,Quantity,Current Value
AAPL,12345,Cash,N/A
"""
    )

    rows = _load_to_records(loader, str(csv_file))

    row = rows[0]

    assert row["quantity"] is None
    assert row["current_value"] is None