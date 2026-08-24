from unittest.mock import MagicMock, patch

import pytest
from types import SimpleNamespace

from services.base_ingestion_service import BaseIngestionService
from models.importhistory import ImportHistory


class IngestionServiceTest(BaseIngestionService):
    """
    Minimal concrete implementation of BaseIngestionService
    used only for unit testing.
    """

    @property
    def import_type(self) -> str:
        return "positions"

    def persist(
        self,
        dataframe,
        account,
        snapshot_date=None,
        import_history_id=None,
    ) -> int:
        return 0

    @classmethod
    def build(cls):
        raise NotImplementedError


@pytest.fixture
def import_history_repo():
    return MagicMock()


@pytest.fixture
def ingestion_service(import_history_repo):
    transaction_manager = MagicMock()

    transaction_context = MagicMock()
    transaction_context.__enter__.return_value = transaction_context

    transaction_manager.transaction.return_value = transaction_context

    return IngestionServiceTest(
        account_repo=MagicMock(),
        import_history_repo=import_history_repo,
        import_audit_service=MagicMock(),
        loader=MagicMock(),
        validator=MagicMock(),
        transaction_manager=transaction_manager,
    )


# ---------------------------------------------------------------------
# _record_import()
# ---------------------------------------------------------------------


def test_record_import_inserts_when_id_is_none(
    ingestion_service,
    import_history_repo,
):
    """
    A new ImportHistory with no ID should be inserted.
    """

    history = ImportHistory(
        id=None,
        account_id=1,
        import_type="positions",
        institution="Fidelity",
        filename="positions.csv",
        file_hash="abc123",
        status="RUNNING",
    )

    inserted_history = ImportHistory(
        id=123,
        account_id=1,
        import_type="positions",
        institution="Fidelity",
        filename="positions.csv",
        file_hash="abc123",
        status="RUNNING",
    )

    import_history_repo.insert.return_value = inserted_history

    result = ingestion_service._record_import(history)

    # The result should be whatever the repository returned.
    assert result is inserted_history
    assert result.id == 123

    # id=None means INSERT.
    import_history_repo.insert.assert_called_once_with(history)

    # UPDATE must not be called.
    import_history_repo.update.assert_not_called()


def test_record_import_updates_when_id_exists(
    ingestion_service,
    import_history_repo,
):
    """
    An ImportHistory with an existing ID should be updated.
    """

    history = ImportHistory(
        id=123,
        account_id=1,
        import_type="positions",
        institution="Fidelity",
        filename="positions.csv",
        file_hash="abc123",
        status="SUCCESS",
    )

    updated_history = ImportHistory(
        id=123,
        account_id=1,
        import_type="positions",
        institution="Fidelity",
        filename="positions.csv",
        file_hash="abc123",
        status="SUCCESS",
    )

    import_history_repo.update.return_value = updated_history

    result = ingestion_service._record_import(history)

    # The result should be whatever the repository returned.
    assert result is updated_history
    assert result.id == 123

    # Existing ID means UPDATE.
    import_history_repo.update.assert_called_once_with(history)

    # INSERT must not be called.
    import_history_repo.insert.assert_not_called()

@patch(
    "services.base_ingestion_service.calculate_file_hash",
    return_value="test-file-hash",
)
def test_ingest_validation_failure_does_not_persist(
    mock_calculate_file_hash,
    ingestion_service,
    import_history_repo,
):
    # Arrange
    csv_file = "test.csv"
    account_name = "Test Account"

    account = SimpleNamespace(
        id=123,
        name=account_name,
        account_number="123456",
        institution="Test Institution",
    )

    dataframe = [
        {"symbol": "AAPL", "quantity": 100},
    ]

    ingestion_service._account_repo.get_by_name.return_value = account

    import_history_repo.exists.return_value = False

    ingestion_service._loader.load.return_value = dataframe

    ingestion_service._validator.validate.side_effect = ValueError(
        "Invalid CSV data"
    )

    ingestion_service.persist = MagicMock()

    # Act / Assert
    with pytest.raises(
        ValueError,
        match="Invalid CSV data",
    ):
        ingestion_service.ingest(
            csv_file=csv_file,
            name=account_name,
        )

    # File hash was calculated.
    mock_calculate_file_hash.assert_called_once_with(csv_file)

    # Validation was reached.
    ingestion_service._validator.validate.assert_called_once_with(
        dataframe
    )

    # Persistence must NOT occur.
    ingestion_service.persist.assert_not_called()

    # Import history must NOT be created.
    import_history_repo.insert.assert_not_called()

    # Import history must NOT be updated.
    import_history_repo.update.assert_not_called()


@patch(
    "services.base_ingestion_service.calculate_file_hash",
    return_value="test-file-hash",
)
def test_ingest_persist_failure_does_not_record_import(
    mock_calculate_file_hash,
    ingestion_service,
    import_history_repo,
):
    # Arrange
    csv_file = "test.csv"
    account_name = "Test Account"

    account = SimpleNamespace(
        id=123,
        name=account_name,
        account_number="123456",
        institution="Test Institution",
    )

    dataframe = [
        {"symbol": "AAPL", "quantity": 100},
    ]

    import_history = ImportHistory(
        id=456,
        account_id=123,
        import_type="positions",
        institution="Test Institution",
        filename=csv_file,
        file_hash="test-file-hash",
        status="RUNNING",
    )

    ingestion_service._account_repo.get_by_name.return_value = account

    import_history_repo.exists.return_value = False

    ingestion_service._loader.load.return_value = dataframe

    # Validation succeeds.
    ingestion_service._validator.validate.return_value = None

    # Import history creation succeeds.
    import_history_repo.insert.return_value = import_history

    # Persistence fails.
    ingestion_service.persist = MagicMock(
        side_effect=RuntimeError("Persistence failed")
    )

    # Act / Assert
    with pytest.raises(
        RuntimeError,
        match="Persistence failed",
    ):
        ingestion_service.ingest(
            csv_file=csv_file,
            name=account_name,
        )

    # Validation completed successfully.
    ingestion_service._validator.validate.assert_called_once_with(
        dataframe
    )

    # RUNNING import history was created.
    import_history_repo.insert.assert_called_once()

    # Persistence was attempted.
    ingestion_service.persist.assert_called_once_with(
        dataframe=dataframe,
        account=account,
        snapshot_date=None,
        import_history_id=import_history.id,
    )

    # The import never reached the SUCCESS update.
    import_history_repo.update.assert_not_called()

    # Audit must never run because persistence failed.
    ingestion_service._import_audit_service.audit.assert_not_called()


@patch(
    "services.base_ingestion_service.calculate_file_hash",
    return_value="test-file-hash",
)
def test_ingest_import_history_failure_rolls_back_persisted_data(
    mock_calculate_file_hash,
    ingestion_service,
    import_history_repo,
):
    # Arrange
    csv_file = "test.csv"
    account_name = "Test Account"

    account = SimpleNamespace(
        id=123,
        name=account_name,
        account_number="123456",
        institution="Test Institution",
    )

    dataframe = [
        {"symbol": "AAPL", "quantity": 100},
    ]

    import_history = ImportHistory(
        id=456,
        account_id=123,
        import_type="positions",
        institution="Test Institution",
        filename=csv_file,
        file_hash="test-file-hash",
        status="RUNNING",
    )

    account_repo = ingestion_service._account_repo
    loader = ingestion_service._loader
    validator = ingestion_service._validator

    account_repo.get_by_name.return_value = account
    import_history_repo.exists.return_value = False
    loader.load.return_value = dataframe

    # Validation succeeds.
    validator.validate.return_value = None

    # Initial import-history INSERT succeeds.
    import_history_repo.insert.return_value = import_history

    # Persist succeeds.
    ingestion_service.persist = MagicMock(
        return_value=1
    )

    # The SUCCESS import-history UPDATE fails.
    import_history_repo.update.side_effect = RuntimeError(
        "Import history update failed"
    )

    # Configure the transaction context manager.
    transaction_manager = ingestion_service._transaction_manager

    transaction_context = MagicMock()

    transaction_manager.transaction.return_value = transaction_context
    transaction_context.__enter__.return_value = transaction_context

    # Act / Assert
    with pytest.raises(
        RuntimeError,
        match="Import history update failed",
    ):
        ingestion_service.ingest(
            csv_file=csv_file,
            name=account_name,
        )

    # Validation succeeded.
    validator.validate.assert_called_once_with(
        dataframe
    )

    import_history_repo.insert.assert_called_once()

    inserted_history = import_history_repo.insert.call_args.args[0]

    assert inserted_history.id is None
    assert inserted_history.account_id == 123
    assert inserted_history.import_type == "positions"
    assert inserted_history.institution == "Test Institution"
    assert inserted_history.filename == csv_file
    assert inserted_history.file_hash == "test-file-hash"
    assert inserted_history.status == "RUNNING"

    # Data was persisted.
    ingestion_service.persist.assert_called_once_with(
        dataframe=dataframe,
        account=account,
        snapshot_date=None,
        import_history_id=456,
    )

    # SUCCESS update was attempted.
    import_history_repo.update.assert_called_once_with(
        import_history
    )

    # Transaction must have been started.
    ingestion_service._transaction_manager.transaction.assert_called_once()

    # Transaction context must have been entered.
    transaction_context.__enter__.assert_called_once()

    # Transaction must exit with the exception.
    transaction_context.__exit__.assert_called_once()

    # Transaction must roll back.
    ingestion_service._transaction_manager.transaction.return_value.__exit__.assert_called_once()

    # The transaction must receive the RuntimeError.
    exit_args = transaction_context.__exit__.call_args.args

    assert exit_args[0] is RuntimeError
    assert isinstance(exit_args[1], RuntimeError)
    assert str(exit_args[1]) == "Import history update failed"

    # Audit must never run.
    ingestion_service._import_audit_service.audit.assert_not_called()




