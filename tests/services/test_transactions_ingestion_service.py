# tests/services/test_transactions_ingestion_service.py

from types import SimpleNamespace

import pandas as pd
import pytest

from models.security import Security
from models.transaction import Transaction
from services.transactions_ingestion_service import (
    TransactionsIngestionService,
)


@pytest.fixture
def account():
    return SimpleNamespace(id=123)


@pytest.fixture
def security_resolution_service(mocker):
    service = mocker.Mock()

    service.resolve.return_value = Security(
        id=99,
        symbol="AAPL",
        description="Apple Inc",
    )

    return service


@pytest.fixture
def transaction_repo(mocker):
    repo = mocker.Mock()
    repo.exists.return_value = False

    return repo


@pytest.fixture
def service(
    mocker,
    security_resolution_service,
    transaction_repo,
):
    return TransactionsIngestionService(
        account_repo=mocker.Mock(),
        security_repo=mocker.Mock(),
        transaction_repo=transaction_repo,
        import_history_repo=mocker.Mock(),
        security_resolution_service=security_resolution_service,
        loader=mocker.Mock(),
        validator=mocker.Mock(),
    )


def test_null_if_na_returns_none_for_nan(service):
    assert service._null_if_na(float("nan")) is None


def test_null_if_na_preserves_values(service):
    assert service._null_if_na(100) == 100
    assert service._null_if_na("BUY") == "BUY"


def test_to_transaction_creates_transaction(service):
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


def test_persist_inserts_security_transaction(
    service,
    transaction_repo,
    security_resolution_service,
    account,
):
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

    imported = service.persist(dataframe, account)

    assert imported == 1
    security_resolution_service.resolve.assert_called_once()
    transaction_repo.exists.assert_called_once()
    transaction_repo.insert.assert_called_once()


def test_persist_inserts_cash_transaction_without_security(
    service,
    transaction_repo,
    security_resolution_service,
    account,
):
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

    imported = service.persist(dataframe, account)

    assert imported == 1
    security_resolution_service.resolve.assert_not_called()

    transaction = transaction_repo.insert.call_args.args[0]

    assert transaction.security_id is None
    assert transaction.action == "DIVIDEND"


def test_persist_skips_duplicate_transaction(
    service,
    transaction_repo,
    account,
):
    transaction_repo.exists.return_value = True

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

    imported = service.persist(dataframe, account)

    assert imported == 0
    transaction_repo.insert.assert_not_called()


def test_persist_raises_when_insert_fails(
    service,
    transaction_repo,
    account,
):
    transaction_repo.insert.side_effect = RuntimeError(
        "database failure"
    )

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
        service.persist(dataframe, account)