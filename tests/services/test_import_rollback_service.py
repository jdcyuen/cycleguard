from contextlib import contextmanager
from unittest.mock import Mock, MagicMock
from services.import_rollback_service import ImportRollbackService

import pytest

from services.import_rollback_service import ImportRollbackService


@pytest.fixture
def transaction_manager():
    manager = Mock()

    @contextmanager
    def transaction():
        yield

    manager.transaction.side_effect = transaction

    return manager


@pytest.fixture
def transactions_repository():
    return Mock()


@pytest.fixture
def positions_repository():
    return Mock()


@pytest.fixture
def snapshots_repository():
    return Mock()


@pytest.fixture
def import_history_repository():
    return Mock()


@pytest.fixture
def service(
    transaction_manager,
    transactions_repository,
    positions_repository,
    snapshots_repository,
    import_history_repository,
):
    return ImportRollbackService(
        transaction_manager=transaction_manager,
        import_history_repo=import_history_repository,
        position_repo=positions_repository,
        snapshot_repo=snapshots_repository,
        transaction_repo=transactions_repository,
    )

def test_rollback_success():
    # Arrange
    import_history_id = 123

    transaction_manager = MagicMock()
    import_history_repo = MagicMock()
    position_repo = MagicMock()
    snapshot_repo = MagicMock()
    transaction_repo = MagicMock()

    transaction_repo.delete_by_import_history_id.return_value = 10
    position_repo.delete_by_import_history_id.return_value = 5
    snapshot_repo.delete_by_import_history_id.return_value = 1
    import_history_repo.delete.return_value = 1

    service = ImportRollbackService(
        transaction_manager=transaction_manager,
        import_history_repo=import_history_repo,
        position_repo=position_repo,
        snapshot_repo=snapshot_repo,
        transaction_repo=transaction_repo,
    )

    # Act
    result = service.rollback(import_history_id)

    # Assert
    assert result == {
        "import_history_id": 123,
        "transactions_deleted": 10,
        "positions_deleted": 5,
        "snapshots_deleted": 1,
        "import_history_deleted": 1,
    }

    transaction_manager.transaction.assert_called_once_with()

    transaction_repo.delete_by_import_history_id.assert_called_once_with(
        import_history_id
    )

    position_repo.delete_by_import_history_id.assert_called_once_with(
        import_history_id
    )

    snapshot_repo.delete_by_import_history_id.assert_called_once_with(
        import_history_id
    )

    import_history_repo.delete.assert_called_once_with(
        import_history_id
    )

    transaction_manager.transaction.return_value.__enter__.assert_called_once_with()

    transaction_manager.transaction.return_value.__exit__.assert_called_once_with(
        None,
        None,
        None,
    )

def test_rollback_deletes_all_import_data(
    service,
    transaction_manager,
    transactions_repository,
    positions_repository,
    snapshots_repository,
    import_history_repository,
):
    import_history_id = 123

    transactions_repository.delete_by_import_history_id.return_value = 10
    positions_repository.delete_by_import_history_id.return_value = 5
    snapshots_repository.delete_by_import_history_id.return_value = 1
    import_history_repository.delete.return_value = 1

    result = service.rollback(import_history_id)

    transaction_manager.transaction.assert_called_once_with()

    transactions_repository.delete_by_import_history_id.assert_called_once_with(
        import_history_id
    )
    positions_repository.delete_by_import_history_id.assert_called_once_with(
        import_history_id
    )
    snapshots_repository.delete_by_import_history_id.assert_called_once_with(
        import_history_id
    )
    import_history_repository.delete.assert_called_once_with(
        import_history_id
    )

    assert result == {
        "import_history_id": import_history_id,
        "transactions_deleted": 10,
        "positions_deleted": 5,
        "snapshots_deleted": 1,
        "import_history_deleted": 1,
    }


def test_rollback_stops_when_repository_fails(
    service,
    positions_repository,
    snapshots_repository,
    import_history_repository,
):
    import_history_id = 123

    positions_repository.delete_by_import_history_id.side_effect = (
        RuntimeError("position delete failed")
    )

    with pytest.raises(
        RuntimeError,
        match="position delete failed",
    ):
        service.rollback(import_history_id)

    snapshots_repository.delete_by_import_history_id.assert_not_called()
    import_history_repository.delete.assert_not_called()


def test_rollback_propagates_repository_error(
    service,
    positions_repository,
):
    import_history_id = 123

    error = RuntimeError("position delete failed")

    positions_repository.delete_by_import_history_id.side_effect = error

    with pytest.raises(RuntimeError) as exc_info:
        service.rollback(import_history_id)

    assert exc_info.value is error

@pytest.mark.parametrize(
    "failing_repo",
    [
        "transaction",
        "position",
        "snapshot",
        "import_history",
    ],
)
def test_rollback_repository_failure_rolls_back_transaction(
    failing_repo,
):
    # Arrange
    import_history_id = 123

    transaction_manager = MagicMock()
    import_history_repo = MagicMock()
    position_repo = MagicMock()
    snapshot_repo = MagicMock()
    transaction_repo = MagicMock()

    transaction_error = RuntimeError(
        f"{failing_repo} repository failure"
    )

    # Configure repository failure and successful operations
    # before the failure point.
    if failing_repo == "transaction":
        transaction_repo.delete_by_import_history_id.side_effect = (
            transaction_error
        )

    elif failing_repo == "position":
        transaction_repo.delete_by_import_history_id.return_value = 10

        position_repo.delete_by_import_history_id.side_effect = (
            transaction_error
        )

    elif failing_repo == "snapshot":
        transaction_repo.delete_by_import_history_id.return_value = 10
        position_repo.delete_by_import_history_id.return_value = 5

        snapshot_repo.delete_by_import_history_id.side_effect = (
            transaction_error
        )

    elif failing_repo == "import_history":
        transaction_repo.delete_by_import_history_id.return_value = 10
        position_repo.delete_by_import_history_id.return_value = 5
        snapshot_repo.delete_by_import_history_id.return_value = 1

        import_history_repo.delete.side_effect = transaction_error

    service = ImportRollbackService(
        transaction_manager=transaction_manager,
        import_history_repo=import_history_repo,
        position_repo=position_repo,
        snapshot_repo=snapshot_repo,
        transaction_repo=transaction_repo,
    )

    # Act
    with pytest.raises(
        RuntimeError,
        match=f"{failing_repo} repository failure",
    ):
        service.rollback(import_history_id)

    # Assert: transaction was started.
    transaction_manager.transaction.assert_called_once_with()

    transaction_manager.transaction.return_value.__enter__.assert_called_once_with()

    # Assert: transaction context manager received the exception.
    exit_call = (
        transaction_manager
        .transaction
        .return_value
        .__exit__
    )

    assert exit_call.call_count == 1

    exc_type, exc_value, exc_traceback = exit_call.call_args.args

    assert exc_type is RuntimeError
    assert exc_value is transaction_error
    assert exc_traceback is not None

    # Assert: operations before the failure were executed.
    if failing_repo in ("position", "snapshot", "import_history"):
        transaction_repo.delete_by_import_history_id.assert_called_once_with(
            import_history_id
        )

    if failing_repo in ("snapshot", "import_history"):
        position_repo.delete_by_import_history_id.assert_called_once_with(
            import_history_id
        )

    if failing_repo == "import_history":
        snapshot_repo.delete_by_import_history_id.assert_called_once_with(
            import_history_id
        )

    # Assert: the failing operation was called.
    if failing_repo == "transaction":
        transaction_repo.delete_by_import_history_id.assert_called_once_with(
            import_history_id
        )

    elif failing_repo == "position":
        position_repo.delete_by_import_history_id.assert_called_once_with(
            import_history_id
        )

    elif failing_repo == "snapshot":
        snapshot_repo.delete_by_import_history_id.assert_called_once_with(
            import_history_id
        )

    elif failing_repo == "import_history":
        import_history_repo.delete.assert_called_once_with(
            import_history_id
        )

    # Assert: operations AFTER the failure were NOT executed.
    if failing_repo in ("transaction", "position", "snapshot"):
        import_history_repo.delete.assert_not_called()

    if failing_repo in ("transaction", "position"):
        snapshot_repo.delete_by_import_history_id.assert_not_called()

    if failing_repo == "transaction":
        position_repo.delete_by_import_history_id.assert_not_called()

def test_rollback_commits_on_success():
    # Arrange
    import_history_id = 123

    transaction_manager = MagicMock()
    import_history_repo = MagicMock()
    position_repo = MagicMock()
    snapshot_repo = MagicMock()
    transaction_repo = MagicMock()

    transaction_repo.delete_by_import_history_id.return_value = 10
    position_repo.delete_by_import_history_id.return_value = 5
    snapshot_repo.delete_by_import_history_id.return_value = 1
    import_history_repo.delete.return_value = 1

    service = ImportRollbackService(
        transaction_manager=transaction_manager,
        import_history_repo=import_history_repo,
        position_repo=position_repo,
        snapshot_repo=snapshot_repo,
        transaction_repo=transaction_repo,
    )

    # Act
    result = service.rollback(import_history_id)

    # Assert
    assert result == {
        "import_history_id": import_history_id,
        "transactions_deleted": 10,
        "positions_deleted": 5,
        "snapshots_deleted": 1,
        "import_history_deleted": 1,
    }

    # Transaction was started.
    transaction_manager.transaction.assert_called_once_with()

    transaction_manager.transaction.return_value.__enter__.assert_called_once_with()

    # No exception means the transaction context exited normally.
    transaction_manager.transaction.return_value.__exit__.assert_called_once_with(
        None,
        None,
        None,
    )