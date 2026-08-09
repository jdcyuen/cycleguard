from typing import Optional

import psycopg
from core.logger import get_logger
# pyrefly: ignore [missing-import]
from models.security import Security

logger = get_logger(__name__)

class SecurityRepositoryError(Exception):
    """Raised when security repository operations fail."""


class SecurityRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_by_symbol(
        self,
        symbol: str,
    ) -> Optional[Security]:

        logger.info(f"Retrieving security with symbol={symbol}")
        logger.debug("SQL parameters: symbol=%s", symbol)

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, symbol, description
                    FROM cycleguard.securities
                    WHERE symbol = %s
                    """,
                    (symbol,),
                )

                row = cur.fetchone()

                logger.info(f"Retrieved security with symbol={symbol}")
                if row is None:
                    return None

                return Security(
                    id=row[0],
                    symbol=row[1],
                    description=row[2],
                )

        except psycopg.Error as exc:
            logger.exception(
                f"Failed to lookup security '{symbol}'"
            )
            raise SecurityRepositoryError(
                f"Failed to lookup security '{symbol}'"
            ) from exc
            
    def get_by_id(
        self,
        security_id: int,
    ) -> Optional[Security]:


        """
        Returns a Security by id.
        """

        logger.info(
            "Looking up security id=%s",
            security_id,
        )

        try:

            with self.conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT
                        id,
                        symbol,
                        description
                    FROM cycleguard.securities
                    WHERE id = %s
                    """,
                    (security_id,),
                )

                row = cur.fetchone()

                if row is None:
                    return None

                return Security(
                    id=row[0],
                    symbol=row[1],
                    description=row[2],
                )

        except psycopg.Error as exc:

            logger.exception(
                "Security lookup failed."
            )

            raise SecurityRepositoryError(
                "Unable to lookup security."
            ) from exc


    def upsert(self, security: Security) -> Security:

        logger.info("Creating or updating security '%s'", security.symbol)
        logger.debug("Security model: %s",security)

        sql = """
            INSERT INTO cycleguard.securities (
                symbol,
                description,
                asset_type
            )
            VALUES (
                %s,
                %s,
                %s
            )
            ON CONFLICT (symbol)
            DO UPDATE SET
                description = COALESCE(NULLIF(securities.description, ''), EXCLUDED.description),
                asset_type = COALESCE(NULLIF(securities.asset_type, ''), EXCLUDED.asset_type)
            RETURNING
                id,
                symbol,
                description,
                asset_type;

        """
        logger.debug("Executing SQL:\n%s", sql)

        logger.debug(
            "SQL parameters: "
            "symbol=%s, "
            "description=%s, "
            "asset_type=%s",
            security.symbol,
            security.description,
            security.asset_type,
        )

        try:
            with self.conn.cursor() as cur:

                logger.debug(
                    "Executing INSERT ... ON CONFLICT for '%s'",
                    security.symbol,
                )

                cur.execute(
                    sql,
                    (
                        security.symbol,
                        security.description,
                        security.asset_type,
                    )
                )

                row = cur.fetchone()
                logger.debug("Database returned row: %s", row)

            self.conn.commit()

            logger.info("Committed security '%s'", security.symbol )

            return Security(
                id=row[0],
                symbol=row[1],
                description=row[2],
                asset_type=row[3],
            )

        except Exception as exc:
            self.conn.rollback()

            logger.exception(
                "Failed to create or update security '%s'",
                security.symbol,
            )

            raise SecurityRepositoryError(
                f"Unable to create or update security '{security.symbol}'"
            ) from exc

    def list_securities(
        self,
    ) -> list[Security]:
        """
        Returns all securities.
        """

        try:

            with self.conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT
                        id,
                        symbol,
                        description
                    FROM cycleguard.securities
                    ORDER BY symbol
                    """
                )

                rows = cur.fetchall()

                return [
                    Security(
                        id=row[0],
                        symbol=row[1],
                        description=row[2],
                    )
                    for row in rows
                ]

        except psycopg.Error as exc:

            raise SecurityRepositoryError(
                "Unable to retrieve securities."
            ) from exc

    def update_if_missing(
        self,
        security: Security,
    ) -> Security:

        """
        Updates only fields that are currently NULL in the database.

        Existing non-NULL values are preserved.
        """

        logger.info(
            "Updating missing fields for security '%s'",
            security.symbol,
        )

        logger.debug(
            "SQL parameters: id=%s, symbol=%s, description=%s, asset_type=%s",
            security.id,
            security.symbol,
            security.description,
            security.asset_type,
        )

        try:
            with self.conn.cursor() as cur:

                cur.execute(
                    """
                    UPDATE cycleguard.securities
                    SET
                        description = COALESCE(description, %s),
                        asset_type  = COALESCE(asset_type, %s)
                    WHERE id = %s
                    RETURNING
                        id,
                        symbol,
                        description,
                        asset_type
                    """,
                    (
                        security.description,
                        security.asset_type,
                        security.id,
                    ),
                )

                row = cur.fetchone()

                if row is None:
                    self.conn.rollback()
                    raise SecurityRepositoryError(
                        f"Security id={security.id} not found."
                    )

                self.conn.commit()

                logger.info(
                    "Security updated successfully for security_id=%s",
                    security.id,
                )

                updated = Security(
                    id=row[0],
                    symbol=row[1],
                    description=row[2],
                    asset_type=row[3],
                )

            logger.info(
                "Updated missing fields for security '%s'",
                updated.symbol,
            )

            return updated

        except psycopg.Error as exc:

            self.conn.rollback()

            logger.exception(
                "Failed updating security '%s'",
                security.symbol,
            )

            raise SecurityRepositoryError(
                f"Unable to update security '{security.symbol}'"
            ) from exc