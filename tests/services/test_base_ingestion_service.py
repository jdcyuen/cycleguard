from unittest.mock import MagicMock

import pytest

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
    return IngestionServiceTest(
        account_repo=MagicMock(),
        import_history_repo=import_history_repo,
        import_audit_service=MagicMock(),
        loader=MagicMock(),
        validator=MagicMock(),
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