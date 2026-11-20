from uuid import uuid4

import pytest
from psycopg2.errors import UniqueViolation

from database.connection import DBConnection


@pytest.mark.integration
def test_account_number_unique_index_ignores_case_and_whitespace():
    """
    Verify PostgreSQL rejects account numbers that differ only
    by letter case or whitespace.
    """

    conn = DBConnection().connect()
    account_ids = []

    suffix = uuid4().hex[:12]
    account_number = f"CG Norm {suffix}"
    duplicate_account_number = f"cg\tnorm\n{suffix}"

    try:
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
                    f"Normalization Integration Test {suffix}",
                    "Fidelity",
                ),
            )

            account_ids.append(cur.fetchone()[0])

        conn.commit()

        with pytest.raises(UniqueViolation):
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
                        duplicate_account_number,
                        f"Duplicate Normalization Test {suffix}",
                        "Fidelity",
                    ),
                )

                account_ids.append(cur.fetchone()[0])

        conn.rollback()

    finally:
        try:
            conn.rollback()

            if account_ids:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        DELETE FROM cycleguard.accounts
                        WHERE id = ANY(%s)
                        """,
                        (account_ids,),
                    )

                conn.commit()

        except Exception:
            conn.rollback()
            raise

        finally:
            conn.close()
