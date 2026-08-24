from uuid import uuid4

import pytest

from database.connection import DBConnection
from services.import_rollback_service import ImportRollbackService


@pytest.mark.integration
def test_import_rollback_can_delete_import_history():
    """
    Verify rollback deletes all import data, including the
    import_history record when delete_import_history=True.
    """

    conn = DBConnection().connect()

    account_id = None
    import_history_id = None

    try:
        # -----------------------------------------------------
        # Arrange: create dedicated test account
        # -----------------------------------------------------

        account_name = (
            f"Rollback Integration Test {uuid4().hex[:8]}"
        )
        account_number = (
            f"ROLLBACK-{uuid4().hex[:12]}"
        )

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO cycleguard.accounts (
                    account_number,
                    name,
                    institution
                )
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (
                    account_number,
                    account_name,
                    "Fidelity",
                ),
            )

            account_id = cur.fetchone()[0]

            # Create import_history record
            cur.execute(
                """
                INSERT INTO cycleguard.import_history (
                    account_id,
                    import_type,
                    institution,
                    filename,
                    file_hash,
                    snapshot_date,
                    status
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                RETURNING id
                """,
                (
                    account_id,
                    "transactions",
                    "Fidelity",
                    "rollback_test.csv",
                    uuid4().hex,
                    "2026-08-23",
                    "SUCCESS",
                ),
            )

            import_history_id = cur.fetchone()[0]

        conn.commit()

        # -----------------------------------------------------
        # Build real repositories/service
        # -----------------------------------------------------

        from repositories.import_history_repo import (
            ImportHistoryRepository,
        )
        from repositories.position_repo import PositionRepository
        from repositories.snapshot_repo import SnapshotRepository
        from repositories.transaction_repo import TransactionRepository
        from database.transaction_manager import TransactionManager

        import_history_repo = ImportHistoryRepository(conn)
        position_repo = PositionRepository(conn)
        snapshot_repo = SnapshotRepository(conn)
        transaction_repo = TransactionRepository(conn)
        transaction_manager = TransactionManager(conn)

        service = ImportRollbackService(
            transaction_manager=transaction_manager,
            import_history_repo=import_history_repo,
            position_repo=position_repo,
            snapshot_repo=snapshot_repo,
            transaction_repo=transaction_repo,
        )

        # -----------------------------------------------------
        # Act
        # -----------------------------------------------------

        result = service.rollback(
            import_history_id=import_history_id,
            delete_import_history=True,
        )

        # -----------------------------------------------------
        # Assert
        # -----------------------------------------------------

        assert result["import_history_id"] == import_history_id
        assert result["import_history_deleted"] == 1

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM cycleguard.import_history
                WHERE id = %s
                """,
                (import_history_id,),
            )

            assert cur.fetchone()[0] == 0

    finally:
        # -----------------------------------------------------
        # Cleanup
        # -----------------------------------------------------

        if account_id is not None:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        DELETE FROM cycleguard.accounts
                        WHERE id = %s
                        """,
                        (account_id,),
                    )

                conn.commit()

            except Exception:
                conn.rollback()

        conn.close()

@pytest.mark.integration
def test_import_rollback_keeps_import_history_by_default():
    """
    Verify rollback deletes imported data but keeps the
    import_history record when delete_import_history is omitted.
    """

    conn = DBConnection().connect()

    account_id = None
    import_history_id = None

    try:
        # -----------------------------------------------------
        # Arrange: create dedicated test account
        # -----------------------------------------------------

        account_name = (
            f"Rollback Keep History Test {uuid4().hex[:8]}"
        )
        account_number = (
            f"ROLLBACK-KEEP-{uuid4().hex[:12]}"
        )

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO cycleguard.accounts (
                    account_number,
                    name,
                    institution
                )
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (
                    account_number,
                    account_name,
                    "Fidelity",
                ),
            )

            account_id = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO cycleguard.import_history (
                    account_id,
                    import_type,
                    institution,
                    filename,
                    file_hash,
                    snapshot_date,
                    status
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                RETURNING id
                """,
                (
                    account_id,
                    "transactions",
                    "Fidelity",
                    "rollback_keep_history_test.csv",
                    uuid4().hex,
                    "2026-08-23",
                    "SUCCESS",
                ),
            )

            import_history_id = cur.fetchone()[0]

        conn.commit()

        # -----------------------------------------------------
        # Build real repositories/service
        # -----------------------------------------------------

        from database.transaction_manager import TransactionManager
        from repositories.import_history_repo import (
            ImportHistoryRepository,
        )
        from repositories.position_repo import PositionRepository
        from repositories.snapshot_repo import SnapshotRepository
        from repositories.transaction_repo import TransactionRepository

        service = ImportRollbackService(
            transaction_manager=TransactionManager(conn),
            import_history_repo=ImportHistoryRepository(conn),
            position_repo=PositionRepository(conn),
            snapshot_repo=SnapshotRepository(conn),
            transaction_repo=TransactionRepository(conn),
        )

        # -----------------------------------------------------
        # Act
        # -----------------------------------------------------

        result = service.rollback(
            import_history_id=import_history_id,
        )

        # -----------------------------------------------------
        # Assert
        # -----------------------------------------------------

        assert result["import_history_id"] == import_history_id
        assert result["import_history_deleted"] == 0

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM cycleguard.import_history
                WHERE id = %s
                """,
                (import_history_id,),
            )

            assert cur.fetchone()[0] == 1

    finally:
        # -----------------------------------------------------
        # Cleanup
        # -----------------------------------------------------

        if account_id is not None:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        DELETE FROM cycleguard.accounts
                        WHERE id = %s
                        """,
                        (account_id,),
                    )

                conn.commit()

            except Exception:
                conn.rollback()

        conn.close()