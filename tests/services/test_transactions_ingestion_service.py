# tests/services/test_transactions_ingestion_service.py

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from models.security import Security
from models.transaction import Transaction

from services.transactions_ingestion_service import (
    TransactionsIngestionService,
)



@pytest.fixture
def service():
    return TransactionsIngestionService(
        account_repo=MagicMock(),
        security_repo=MagicMock(),
        transaction_repo=MagicMock(),
        import_history_repo=MagicMock(),
        import_audit_service=MagicMock(),
        security_resolution_service=MagicMock(),
        loader=MagicMock(),
        validator=MagicMock(),
    )

@patch(
    "services.transactions_ingestion_service.DBConnection"
)
@patch(
    "services.transactions_ingestion_service.AccountRepository"
)
@patch(
    "services.transactions_ingestion_service.SecurityRepository"
)
@patch(
    "services.transactions_ingestion_service.TransactionRepository"
)
@patch(
    "services.transactions_ingestion_service.ImportHistoryRepository"
)
@patch(
    "services.transactions_ingestion_service.ImportAuditService"
)
@patch(
    "services.transactions_ingestion_service.SecurityResolutionService"
)
@patch(
    "services.transactions_ingestion_service.TransactionsCSVLoader"
)
@patch(
    "services.transactions_ingestion_service.TransactionsValidator"
)

def test_build(
    mock_validator,
    mock_loader,
    mock_security_resolution_service,
    mock_import_audit_service,
    mock_import_history_repo,
    mock_transaction_repo,
    mock_security_repo,
    mock_account_repo,
    mock_db_connection,
):
    conn = MagicMock()

    mock_db_connection.return_value.connect.return_value = conn

    service = TransactionsIngestionService.build()

    assert isinstance(
        service,
        TransactionsIngestionService,
    )

    mock_db_connection.return_value.connect.assert_called_once()

    mock_account_repo.assert_called_once_with(conn)
    mock_security_repo.assert_called_once_with(conn)
    mock_transaction_repo.assert_called_once_with(conn)
    mock_import_history_repo.assert_called_once_with(conn)

    mock_import_audit_service.assert_called_once()

    mock_security_resolution_service.assert_called_once_with(
        security_repo=mock_security_repo.return_value,
    )

    mock_loader.assert_called_once()
    mock_validator.assert_called_once()

def test_persist_success():

    transaction_repo = MagicMock()
    transaction_repo.exists.return_value = False

    security_resolution_service = MagicMock()

    security_resolution_service.resolve.return_value = Security(
        id=99,
        symbol="AAPL",
        description="Apple Inc",
    )

    service = TransactionsIngestionService(
        account_repo=MagicMock(),
        security_repo=MagicMock(),
        transaction_repo=transaction_repo,
        import_history_repo=MagicMock(),
        import_audit_service=MagicMock(),
        security_resolution_service=security_resolution_service,
        loader=MagicMock(),
        validator=MagicMock(),
    )

    account = SimpleNamespace(id=123)

    dataframe = pd.DataFrame(
        [
            {
                "symbol": "AAPL",
                "description": "Apple Inc",
                "run_date": "2026-01-01",
                "settlement_date": "2026-01-02",
                "action": "BUY",
                "trade_type": "TRADE",
                "price": 100,
                "quantity": 10,
                "commission": 0,
                "fees": 0,
                "accrued_interest": None,
                "amount": 1000,
                "cash_balance": 9000,
            }
        ]
    )

    result = service.persist(
        dataframe=dataframe,
        account=account,
        import_history_id=123,
    )

    assert result == 1

    security_resolution_service.resolve.assert_called_once()

    transaction_repo.exists.assert_called_once()

    transaction_repo.insert.assert_called_once()

    transaction = transaction_repo.insert.call_args.args[0]

    assert isinstance(transaction, Transaction)
    assert transaction.account_id == 123
    assert transaction.security_id == 99
    assert transaction.import_history_id == 123
    assert transaction.action == "BUY"
    assert transaction.amount == 1000


def test_import_type():
    service = TransactionsIngestionService(
        account_repo=MagicMock(),
        security_repo=MagicMock(),
        transaction_repo=MagicMock(),
        import_history_repo=MagicMock(),
        import_audit_service=MagicMock(),
        security_resolution_service=MagicMock(),
        loader=MagicMock(),
        validator=MagicMock(),
    )

    assert service.import_type == "transactions"


def test_null_if_na_returns_none_for_nan():
    service = TransactionsIngestionService(
        account_repo=MagicMock(),
        security_repo=MagicMock(),
        transaction_repo=MagicMock(),
        import_history_repo=MagicMock(),
        import_audit_service=MagicMock(),
        security_resolution_service=MagicMock(),
        loader=MagicMock(),
        validator=MagicMock(),
    )

    assert service._null_if_na(float("nan")) is None


def test_null_if_na_preserves_values():
    service = TransactionsIngestionService(
        account_repo=MagicMock(),
        security_repo=MagicMock(),
        transaction_repo=MagicMock(),
        import_history_repo=MagicMock(),
        import_audit_service=MagicMock(),
        security_resolution_service=MagicMock(),
        loader=MagicMock(),
        validator=MagicMock(),
    )

    assert service._null_if_na(100) == 100
    assert service._null_if_na("BUY") == "BUY"


def test_to_transaction_creates_transaction():

    service = TransactionsIngestionService(
        account_repo=MagicMock(),
        security_repo=MagicMock(),
        transaction_repo=MagicMock(),
        import_history_repo=MagicMock(),
        import_audit_service=MagicMock(),
        security_resolution_service=MagicMock(),
        loader=MagicMock(),
        validator=MagicMock(),
    )

    row = SimpleNamespace(
        run_date="2026-01-01",
        settlement_date="2026-01-02",
        action="BUY",
        trade_type="TRADE",
        price=100,
        quantity=5,
        commission=0,
        fees=0,
        accrued_interest=None,
        amount=500,
        cash_balance=10000,
    )

    transaction = service._to_transaction(
        row=row,
        account_id=1,
        security_id=99,
    )

    assert isinstance(transaction, Transaction)
    assert transaction.account_id == 1
    assert transaction.security_id == 99
    assert transaction.action == "BUY"
    assert transaction.quantity == 5
    assert transaction.amount == 500


def test_persist_inserts_security_transaction():

    transaction_repo = MagicMock()
    transaction_repo.exists.return_value = False

    security_resolution_service = MagicMock()

    security_resolution_service.resolve.return_value = Security(
        id=99,
        symbol="AAPL",
        description="Apple Inc",
    )

    service = TransactionsIngestionService(
        account_repo=MagicMock(),
        security_repo=MagicMock(),
        transaction_repo=transaction_repo,
        import_history_repo=MagicMock(),
        import_audit_service=MagicMock(),
        security_resolution_service=security_resolution_service,
        loader=MagicMock(),
        validator=MagicMock(),
    )

    account = SimpleNamespace(id=123)

    dataframe = pd.DataFrame(
        [
            {
                "symbol": "AAPL",
                "description": "Apple Inc",
                "run_date": "2026-01-01",
                "settlement_date": "2026-01-02",
                "action": "BUY",
                "trade_type": "TRADE",
                "price": 100,
                "quantity": 10,
                "commission": 0,
                "fees": 0,
                "accrued_interest": None,
                "amount": 1000,
                "cash_balance": 9000,
            }
        ]
    )

    imported = service.persist(
        dataframe,
        account,
        import_history_id=123,
    )

    assert imported == 1

    security_resolution_service.resolve.assert_called_once()
    transaction_repo.exists.assert_called_once()
    transaction_repo.insert.assert_called_once()

    transaction = transaction_repo.insert.call_args.args[0]

    assert transaction.security_id == 99
    assert transaction.import_history_id == 123


def test_persist_inserts_cash_transaction_without_security():

    transaction_repo = MagicMock()
    transaction_repo.exists.return_value = False

    security_resolution_service = MagicMock()

    service = TransactionsIngestionService(
        account_repo=MagicMock(),
        security_repo=MagicMock(),
        transaction_repo=transaction_repo,
        import_history_repo=MagicMock(),
        import_audit_service=MagicMock(),
        security_resolution_service=security_resolution_service,
        loader=MagicMock(),
        validator=MagicMock(),
    )

    account = SimpleNamespace(id=123)

    dataframe = pd.DataFrame(
        [
            {
                "symbol": None,
                "description": None,
                "run_date": "2026-01-01",
                "settlement_date": "2026-01-01",
                "action": "DIVIDEND",
                "trade_type": "CASH",
                "price": None,
                "quantity": None,
                "commission": None,
                "fees": None,
                "accrued_interest": None,
                "amount": 50,
                "cash_balance": 10050,
            }
        ]
    )

    imported = service.persist(
        dataframe,
        account,
        import_history_id=123,
    )

    assert imported == 1

    security_resolution_service.resolve.assert_not_called()

    transaction = transaction_repo.insert.call_args.args[0]

    assert transaction.security_id is None
    assert transaction.action == "DIVIDEND"
    assert transaction.import_history_id == 123


def test_persist_skips_duplicate_transaction():

    transaction_repo = MagicMock()
    transaction_repo.exists.return_value = True

    service = TransactionsIngestionService(
        account_repo=MagicMock(),
        security_repo=MagicMock(),
        transaction_repo=transaction_repo,
        import_history_repo=MagicMock(),
        import_audit_service=MagicMock(),
        security_resolution_service=MagicMock(),
        loader=MagicMock(),
        validator=MagicMock(),
    )

    account = SimpleNamespace(id=123)

    dataframe = pd.DataFrame(
        [
            {
                "symbol": "AAPL",
                "description": "Apple Inc",
                "run_date": "2026-01-01",
                "settlement_date": "2026-01-02",
                "action": "BUY",
                "trade_type": "TRADE",
                "price": 100,
                "quantity": 10,
                "commission": 0,
                "fees": 0,
                "accrued_interest": None,
                "amount": 1000,
                "cash_balance": 9000,
            }
        ]
    )

    imported = service.persist(
        dataframe,
        account,
        import_history_id=123,
    )

    assert imported == 0
    transaction_repo.insert.assert_not_called()


def test_persist_raises_when_insert_fails():

    transaction_repo = MagicMock()
    transaction_repo.exists.return_value = False
    transaction_repo.insert.side_effect = RuntimeError(
        "database failure"
    )

    service = TransactionsIngestionService(
        account_repo=MagicMock(),
        security_repo=MagicMock(),
        transaction_repo=transaction_repo,
        import_history_repo=MagicMock(),
        import_audit_service=MagicMock(),
        security_resolution_service=MagicMock(),
        loader=MagicMock(),
        validator=MagicMock(),
    )

    account = SimpleNamespace(id=123)

    dataframe = pd.DataFrame(
        [
            {
                "symbol": "AAPL",
                "description": "Apple Inc",
                "run_date": "2026-01-01",
                "settlement_date": "2026-01-02",
                "action": "BUY",
                "trade_type": "TRADE",
                "price": 100,
                "quantity": 10,
                "commission": 0,
                "fees": 0,
                "accrued_interest": None,
                "amount": 1000,
                "cash_balance": 9000,
            }
        ]
    )

    with pytest.raises(RuntimeError):
        service.persist(
            dataframe,
            account,
            import_history_id=123,
        )

    transaction_repo.exists.assert_called_once()
    transaction_repo.insert.assert_called_once()

@patch(
    "services.base_ingestion_service.calculate_file_hash",
    return_value="test-file-hash",
)
def test_transactions_dry_run_does_not_persist(
    mock_file_hash,
    service,
):
    account = SimpleNamespace(
        id=123,
        name="Joint WROS TOD",
        institution="Fidelity",
        account_number="123456",
    )

    service._account_repo.get_by_name.return_value = account

    service._import_history_repo.exists.return_value = False

    service._loader.load.return_value = pd.DataFrame(
        [
            {
                "symbol": "AAPL",
                "description": "Apple Inc",
                "run_date": "2026-01-01",
                "settlement_date": "2026-01-02",
                "action": "BUY",
                "trade_type": "TRADE",
                "price": 100,
                "quantity": 10,
                "commission": 0,
                "fees": 0,
                "accrued_interest": None,
                "amount": 1000,
                "cash_balance": 9000,
            }
        ]
    )

    service.persist = MagicMock()

    result = service.ingest(
        csv_file="transactions.csv",
        name="Joint WROS TOD",
        snapshot_date="2026-01-01",
        dry_run=True,
    )

    assert result.account_id == 123
    assert result.account_name == "Joint WROS TOD"
    assert result.institution == "Fidelity"
    assert result.import_type == "transactions"
    assert result.filename == "transactions.csv"
    assert result.snapshot_date == "2026-01-01"

    assert result.rows_read == 1
    assert result.rows_imported == 0
    assert result.rows_skipped == 0

    assert result.import_history_id is None
    assert result.snapshot_id is None
    assert result.status == "SUCCESS"
    assert result.warnings == []

    service.persist.assert_not_called()
    service._import_history_repo.insert.assert_not_called()