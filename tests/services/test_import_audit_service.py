from unittest.mock import MagicMock

import pytest

from services.import_audit_service import ImportAuditService
from models.import_audit import (
    ImportAuditStatus,
    ImportAuditResult,
)


@pytest.fixture
def import_history_repository():
    return MagicMock()


@pytest.fixture
def position_repository():
    return MagicMock()


@pytest.fixture
def transaction_repository():
    return MagicMock()


@pytest.fixture
def snapshot_repository():
    return MagicMock()


@pytest.fixture
def service(
    import_history_repository,
    position_repository,
    transaction_repository,
    snapshot_repository,
):
    return ImportAuditService(
        import_history_repository=import_history_repository,
        position_repository=position_repository,
        transaction_repository=transaction_repository,
        snapshot_repository=snapshot_repository,
    )


# ---------------------------------------------------------------------
# Import history
# ---------------------------------------------------------------------


def test_audit_fails_when_import_history_not_found(
    service,
    import_history_repository,
):
    import_history_repository.get_by_id.return_value = None

    result = service.audit(123)

    assert isinstance(result, ImportAuditResult)
    assert result.import_id == 123
    assert result.status == ImportAuditStatus.FAIL
    assert "Import history not found" in result.message

    import_history_repository.get_by_id.assert_called_once_with(123)


# ---------------------------------------------------------------------
# Positions
# ---------------------------------------------------------------------


def test_audit_positions_passes_when_count_matches(
    service,
    import_history_repository,
    position_repository,
    snapshot_repository,
):
    import_history = MagicMock()
    import_history.import_type = "positions"
    import_history.rows_imported = 5
    import_history.snapshot_date = "2026-08-14"

    import_history_repository.get_by_id.return_value = import_history

    position_repository.count_by_import_history_id.return_value = 5

    snapshot_repository.get_by_date.return_value = MagicMock(
        id=456,
        snapshot_date="2026-08-14",
    )

    result = service.audit(123)

    assert result.import_id == 123
    assert result.status == ImportAuditStatus.PASS
    assert "5 positions verified" in result.message

    import_history_repository.get_by_id.assert_called_once_with(123)

    position_repository.count_by_import_history_id.assert_called_once_with(
        123
    )

    snapshot_repository.get_by_date.assert_called_once_with(
        "2026-08-14"
    )


def test_audit_positions_fails_when_count_does_not_match(
    service,
    import_history_repository,
    position_repository,
    snapshot_repository,
):
    import_history = MagicMock()
    import_history.import_type = "positions"
    import_history.rows_imported = 5
    import_history.snapshot_date = "2026-08-14"

    import_history_repository.get_by_id.return_value = import_history

    position_repository.count_by_import_history_id.return_value = 4

    result = service.audit(123)

    assert result.import_id == 123
    assert result.status == ImportAuditStatus.FAIL

    assert (
        "Position count mismatch"
        in result.message
    )

    assert (
        "expected 5"
        in result.message
    )

    assert (
        "found 4"
        in result.message
    )

    position_repository.count_by_import_history_id.assert_called_once_with(
        123
    )

    snapshot_repository.get_by_date.assert_not_called()


def test_audit_positions_fails_when_snapshot_not_found(
    service,
    import_history_repository,
    position_repository,
    snapshot_repository,
):
    import_history = MagicMock()
    import_history.import_type = "positions"
    import_history.rows_imported = 5
    import_history.snapshot_date = "2026-08-14"

    import_history_repository.get_by_id.return_value = import_history

    position_repository.count_by_import_history_id.return_value = 5

    snapshot_repository.get_by_date.return_value = None

    result = service.audit(123)

    assert result.import_id == 123
    assert result.status == ImportAuditStatus.FAIL

    assert "Snapshot not found" in result.message
    assert "2026-08-14" in result.message

    snapshot_repository.get_by_date.assert_called_once_with(
        "2026-08-14"
    )


def test_audit_positions_does_not_check_snapshot_when_count_fails(
    service,
    import_history_repository,
    position_repository,
    snapshot_repository,
):
    import_history = MagicMock()
    import_history.import_type = "positions"
    import_history.rows_imported = 10
    import_history.snapshot_date = "2026-08-14"

    import_history_repository.get_by_id.return_value = import_history

    position_repository.count_by_import_history_id.return_value = 8

    result = service.audit(123)

    assert result.status == ImportAuditStatus.FAIL

    snapshot_repository.get_by_date.assert_not_called()


# ---------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------


def test_audit_transactions_passes_when_count_matches(
    service,
    import_history_repository,
    transaction_repository,
):
    import_history = MagicMock()
    import_history.import_type = "transactions"
    import_history.rows_imported = 25
    import_history.snapshot_date = None

    import_history_repository.get_by_id.return_value = import_history

    transaction_repository.count_by_import_history_id.return_value = 25

    result = service.audit(123)

    assert result.import_id == 123
    assert result.status == ImportAuditStatus.PASS
    assert "25 transactions verified" in result.message

    import_history_repository.get_by_id.assert_called_once_with(123)

    transaction_repository.count_by_import_history_id.assert_called_once_with(
        123
    )


def test_audit_transactions_fails_when_count_does_not_match(
    service,
    import_history_repository,
    transaction_repository,
):
    import_history = MagicMock()
    import_history.import_type = "transactions"
    import_history.rows_imported = 25
    import_history.snapshot_date = None

    import_history_repository.get_by_id.return_value = import_history

    transaction_repository.count_by_import_history_id.return_value = 23

    result = service.audit(123)

    assert result.import_id == 123
    assert result.status == ImportAuditStatus.FAIL

    assert "Transaction count mismatch" in result.message
    assert "expected 25" in result.message
    assert "found 23" in result.message

    transaction_repository.count_by_import_history_id.assert_called_once_with(
        123
    )


# ---------------------------------------------------------------------
# Unsupported import type
# ---------------------------------------------------------------------


def test_audit_fails_for_unsupported_import_type(
    service,
    import_history_repository,
):
    import_history = MagicMock()
    import_history.import_type = "unknown"
    import_history.rows_imported = 10

    import_history_repository.get_by_id.return_value = import_history

    result = service.audit(123)

    assert result.import_id == 123
    assert result.status == ImportAuditStatus.FAIL
    assert "Unsupported import type" in result.message

    import_history_repository.get_by_id.assert_called_once_with(123)