from unittest.mock import Mock

import pytest

from database.transaction_manager import TransactionManager


def test_transaction_commits_when_block_succeeds():
    connection = Mock()
    transaction_manager = TransactionManager(connection)

    with transaction_manager.transaction():
        pass

    connection.commit.assert_called_once_with()
    connection.rollback.assert_not_called()


def test_transaction_rolls_back_when_block_fails():
    connection = Mock()
    transaction_manager = TransactionManager(connection)

    with pytest.raises(RuntimeError, match="database failure"):
        with transaction_manager.transaction():
            raise RuntimeError("database failure")

    connection.rollback.assert_called_once_with()
    connection.commit.assert_not_called()


def test_transaction_reraises_original_exception():
    connection = Mock()
    transaction_manager = TransactionManager(connection)

    error = RuntimeError("database failure")

    with pytest.raises(RuntimeError) as exc_info:
        with transaction_manager.transaction():
            raise error

    assert exc_info.value is error
    connection.rollback.assert_called_once_with()
    connection.commit.assert_not_called()