from pathlib import Path
from uuid import uuid4

from datetime import date
import pytest

from database.connection import DBConnection

from services.positions_ingestion_service import (
PositionsIngestionService,
)

@pytest.mark.integration
def test_positions_ingestion_end_to_end():

    """
    End-to-end integration test for positions ingestion.

    ```
    Exercises:

        CSV file
            -> PositionsCSVLoader
            -> PositionsValidator
            -> account resolution
            -> import_history INSERT
            -> snapshot INSERT
            -> security resolution
            -> position INSERT
            -> import_history UPDATE
            -> import audit
            -> ImportResult

    The test creates its own account and removes all
    test data when finished.

    This test uses the real PostgreSQL database.
    """

    # ---------------------------------------------------------
    # Arrange
    # ---------------------------------------------------------

    account_name = (
        f"Positions Integration Test {uuid4().hex[:8]}"
    )
    account_number = (
        f"POSITION-{uuid4().hex[:12]}"
    )
    institution = "Fidelity"

    csv_file = Path(
        "tests",
        "data",
        "positions",
        "positions_integration_data_Jul-31-2026.csv",
    )

    if not csv_file.exists():
        pytest.fail(
            f"Integration test CSV file not found: {csv_file}"
        )

    conn = DBConnection().connect()

    account_id = None
    import_history_id = None
    snapshot_id = None

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

        service = PositionsIngestionService.build()

        # -----------------------------------------------------
        # Act
        # -----------------------------------------------------

        result = service.ingest(
            csv_file=str(csv_file),
            name=account_name,
            snapshot_date="2026-07-31",
        )

        import_history_id = result.import_history_id
        snapshot_id = result.snapshot_id

        # -----------------------------------------------------
        # Basic result assertions
        # -----------------------------------------------------

        assert result is not None

        assert result.status == "SUCCESS"

        assert result.account_id == account_id

        assert result.account_name == account_name

        assert result.institution == institution

        assert result.import_type == "positions"

        assert result.import_history_id is not None

        assert result.snapshot_id is not None

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
                    institution,
                    status,
                    rows_read,
                    rows_imported
                FROM cycleguard.import_history
                WHERE id = %s
                """,
                (import_history_id,),
            )

            history = cur.fetchone()

        assert history is not None
        assert history[0] == import_history_id
        assert history[1] == account_id
        assert history[2] == "positions"
        assert history[3] == institution
        assert history[4] == "SUCCESS"
        assert history[5] == result.rows_read
        assert history[6] == result.rows_imported

        # -----------------------------------------------------
        # Verify snapshot
        # -----------------------------------------------------

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    snapshot_date,
                    import_history_id
                FROM cycleguard.snapshots
                WHERE id = %s
                """,
                (snapshot_id,),
            )

            snapshot = cur.fetchone()

        assert snapshot is not None
        assert snapshot[0] == snapshot_id
        assert snapshot[1] == date(2026, 7, 31)
        assert snapshot[2] == import_history_id

        # -----------------------------------------------------
        # Verify positions
        # -----------------------------------------------------

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM cycleguard.positions
                WHERE import_history_id = %s
                """,
                (import_history_id,),
            )

            position_count = cur.fetchone()[0]

        assert position_count == result.rows_imported
        assert position_count > 0

    finally:
        # -----------------------------------------------------
        # Cleanup
        # -----------------------------------------------------

        if conn is not None:
            try:
                with conn.cursor() as cur:

                    if import_history_id is not None:
                        cur.execute(
                            """
                            DELETE FROM cycleguard.positions
                            WHERE import_history_id = %s
                            """,
                            (import_history_id,),
                        )

                        cur.execute(
                            """
                            DELETE FROM cycleguard.snapshots
                            WHERE import_history_id = %s
                            """,
                            (import_history_id,),
                        )

                        cur.execute(
                            """
                            DELETE FROM cycleguard.import_history
                            WHERE id = %s
                            """,
                            (import_history_id,),
                        )

                    if account_id is not None:
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
