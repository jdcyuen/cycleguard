from pathlib import Path
from uuid import uuid4
from unittest.mock import patch
import psycopg
import pytest

from database.connection import DBConnection
from services.transactions_ingestion_service import (
    TransactionsIngestionService,
)


@pytest.mark.integration
def test_transactions_ingestion_end_to_end():
    """
    End-to-end integration test for transaction ingestion.

    Exercises:

        CSV file
            -> TransactionsCSVLoader
            -> TransactionsValidator
            -> account resolution
            -> duplicate detection
            -> import_history INSERT
            -> security resolution/upsert
            -> transaction INSERT
            -> import_history UPDATE
            -> import audit
            -> ImportResult

    The test creates its own account and removes all test data
    when finished.

    This test uses the real PostgreSQL database.
    """

    # ---------------------------------------------------------
    # Arrange
    # ---------------------------------------------------------

    account_name = f"CycleGuard Integration Test {uuid4().hex[:8]}"
    account_number = f"TEST-{uuid4().hex[:12]}"
    institution = "Fidelity"

    csv_file = Path(
        "tests",
        "data",
        "transactions",
        "transactions_integration_data.csv",
    )

    if not csv_file.exists():
        pytest.fail(
            f"Integration test CSV file not found: {csv_file}"
        )

    conn = DBConnection().connect()

    account_id = None
    import_history_id = None
    security_ids = set()

    try:
        # -----------------------------------------------------
        # Create dedicated test account
        # -----------------------------------------------------

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
                    institution,
                ),
            )

            account_id = cur.fetchone()[0]

        conn.commit()

        # -----------------------------------------------------
        # Build real ingestion service
        # -----------------------------------------------------

        service = TransactionsIngestionService.build()

        # -----------------------------------------------------
        # Act
        # -----------------------------------------------------

        result = service.ingest(
            csv_file=str(csv_file),
            name=account_name,
        )

        import_history_id = result.import_history_id

        # -----------------------------------------------------
        # Basic result assertions
        # -----------------------------------------------------

        assert result is not None

        assert result.status == "SUCCESS"

        assert result.account_id == account_id

        assert result.account_name == account_name

        assert result.institution == institution

        assert result.import_type == "transactions"

        assert result.import_history_id is not None

        assert result.rows_read > 0

        assert result.rows_imported > 0

        # -----------------------------------------------------
        # Verify import history
        # -----------------------------------------------------

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    account_id,
                    import_type,
                    filename,
                    rows_read,
                    rows_imported,
                    rows_skipped,
                    status
                FROM cycleguard.import_history
                WHERE id = %s
                """,
                (result.import_history_id,),
            )

            import_row = cur.fetchone()

        assert import_row is not None

        assert import_row[0] == result.import_history_id

        assert import_row[1] == account_id

        assert import_row[2] == "transactions"

        assert import_row[4] == result.rows_read

        assert import_row[5] == result.rows_imported

        assert import_row[6] == result.rows_skipped

        assert import_row[7] == "SUCCESS"

        # -----------------------------------------------------
        # Verify transactions were persisted
        # -----------------------------------------------------

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    security_id
                FROM cycleguard.transactions
                WHERE import_history_id = %s
                """,
                (result.import_history_id,),
            )

            transaction_rows = cur.fetchall()

        assert len(transaction_rows) == result.rows_imported

        assert len(transaction_rows) > 0

        # Capture security IDs so the test can clean up securities
        # created by security resolution.
        security_ids = {
            row[1]
            for row in transaction_rows
            if row[1] is not None
        }

        # -----------------------------------------------------
        # Verify transactions belong to test account
        # -----------------------------------------------------

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM cycleguard.transactions
                WHERE import_history_id = %s
                  AND account_id = %s
                """,
                (
                    result.import_history_id,
                    account_id,
                ),
            )

            transaction_count = cur.fetchone()[0]

        assert transaction_count == result.rows_imported

    finally:
        # ---------------------------------------------------------
        # Cleanup
        # ---------------------------------------------------------

        try:
            # -----------------------------------------------------
            # Delete transactions first because they reference
            # import_history and securities.
            # -----------------------------------------------------

            if import_history_id is not None:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        DELETE FROM cycleguard.transactions
                        WHERE import_history_id = %s
                        """,
                        (import_history_id,),
                    )

                    # -------------------------------------------------
                    # Delete import history.
                    # -------------------------------------------------

                    cur.execute(
                        """
                        DELETE FROM cycleguard.import_history
                        WHERE id = %s
                        """,
                        (import_history_id,),
                    )

            # -----------------------------------------------------
            # Delete securities created by this test.
            #
            # Only delete a security if nothing else in the database
            # references it.
            # -----------------------------------------------------

            for security_id in security_ids:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        DELETE FROM cycleguard.securities
                        WHERE id = %s
                          AND NOT EXISTS (
                              SELECT 1
                              FROM cycleguard.transactions
                              WHERE security_id = %s
                          )
                          AND NOT EXISTS (
                              SELECT 1
                              FROM cycleguard.positions
                              WHERE security_id = %s
                          )
                        """,
                        (
                            security_id,
                            security_id,
                            security_id,
                        ),
                    )

            # -----------------------------------------------------
            # Delete test account.
            # -----------------------------------------------------

            if account_id is not None:
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
            raise

        finally:
            conn.close()

@pytest.mark.integration
def test_transactions_ingestion_rolls_back_on_import_history_update_failure():
    """
    Verify that persisted transaction data is rolled back when the
    SUCCESS import-history update fails.
    """

    account_name = f"CycleGuard Rollback Test {uuid4().hex[:8]}"
    account_number = f"TEST-{uuid4().hex[:12]}"
    institution = "Fidelity"

    csv_file = Path(
        "tests",
        "data",
        "transactions",
        "transactions_integration_data.csv",
    )

    conn = DBConnection().connect()

    account_id = None

    try:
        # ---------------------------------------------------------
        # Create dedicated test account
        # ---------------------------------------------------------

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
                    institution,
                ),
            )

            account_id = cur.fetchone()[0]

        conn.commit()

        # ---------------------------------------------------------
        # Build service
        # ---------------------------------------------------------

        service = TransactionsIngestionService.build()

        # ---------------------------------------------------------
        # Force SUCCESS import-history update to fail.
        # ---------------------------------------------------------

        with patch(
            "services.base_ingestion_service.ImportHistoryRepository.update",
            side_effect=RuntimeError(
                "Import history update failed"
            ),
        ):
            with pytest.raises(
                RuntimeError,
                match="Import history update failed",
            ):
                service.ingest(
                    csv_file=str(csv_file),
                    name=account_name,
                )

        # ---------------------------------------------------------
        # Verify transaction data was rolled back.
        # ---------------------------------------------------------

        with conn.cursor() as cur:
            
            cur.execute(
                """
                SELECT COUNT(*)
                FROM cycleguard.transactions t
                JOIN cycleguard.accounts a
                    ON a.id = t.account_id
                WHERE a.id = %s
                """,
                (account_id,),
            )

            transaction_count = cur.fetchone()[0]

        assert transaction_count == 0

        # ---------------------------------------------------------
        # Verify import history was rolled back.
        # ---------------------------------------------------------

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM cycleguard.import_history
                WHERE account_id = %s
                """,
                (account_id,),
            )

            import_history_count = cur.fetchone()[0]

        assert import_history_count == 0

    finally:
        # ---------------------------------------------------------
        # Cleanup test account.
        # ---------------------------------------------------------

        try:
            if account_id is not None:
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
            raise

        finally:
            conn.close()