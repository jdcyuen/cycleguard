from contextlib import contextmanager
from unittest.mock import Mock

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