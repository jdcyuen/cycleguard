from typing import Optional

import psycopg

from models.account import Account
from core.logger import get_logger

logger = get_logger(__name__)

class AccountRepositoryError(Exception):
    """Raised when account repository operations fail."""


class AccountRepository:

    def __init__(self, conn):
        self.conn = conn

    def get_by_id(
        self,
        account_id: int,
    ) -> Optional[Account]:

        logger.info(f"Looking up account by id = '{account_id}'.")

        try:

            with self.conn.cursor() as cur:

                logger.debug(
                    f"SQL parameter: id={account_id}"
                )
                cur.execute(
                    """
                    SELECT id, account_number, name, institution
                    FROM cycleguard.accounts
                    WHERE id = %s
                    """,
                    (account_id,),
                )

                row = cur.fetchone()

                if row is None:
                    logger.info(f"Account '{account_id}'  not found.")
                    return None
                else:
                    logger.info(
                        f"Found account "
                        f"'{account_id}' "
                        f"(id={row[0]})."
                    )

                return Account(
                    id=row[0],
                    account_number=row[1],
                    name=row[2],
                    institution=row[3],
                )

        except psycopg.Error as exc:
            logger.exception(f"Failed to lookup account id={account_id}.")
            raise AccountRepositoryError(
                f"Failed to lookup account id={account_id}"
            ) from exc

    def get_by_name(
        self,
        name: str,
    ) -> Optional[Account]:

        logger.info(f"Looking up account '{name}'.")

        try:
            with self.conn.cursor() as cur:

                logger.debug("Executing account lookup query.")
                logger.debug(f"SQL parameter: name={name}")

                cur.execute(
                    """
                    SELECT id, account_number, name, institution
                    FROM cycleguard.accounts
                    WHERE name = %s
                    """,
                    (name,),
                )
                logger.debug("Retrieved account row.")

                row = cur.fetchone()

                if row is None:
                    logger.info(f"Account '{name}' not found.")
                    return None
                else:
                    
                    
                    logger.info(f"Found account '{name}' (id={row[0]}).")
                    logger.debug("Account row: %s", row)

                return Account(
                    id=row[0],
                    account_number=row[1],
                    name=row[2],
                    institution=row[3],
                )

        except psycopg.Error as exc:
            logger.exception(f"Failed to lookup account '{name}'.")

            raise AccountRepositoryError(
                f"Failed to lookup account '{name}'"
            ) from exc

    def list_accounts(
        self,
    ) -> list[Account]:

        logger.info("Retrieving account list.")

        try:
            with self.conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT id, account_number, name, institution
                    FROM cycleguard.accounts
                    ORDER BY name
                    """
                )

                accounts = cur.fetchall()
                logger.info(f"Retrieved {len(accounts)} accounts.")
                logger.debug(
                    "Accounts: %s",
                    [row[2] for row in accounts],
                )
                return [
                    Account(
                        id=row[0],
                        account_number=row[1],
                        name=row[2],
                        institution=row[3],
                    )
                    for row in accounts
                ]

        except psycopg.Error as exc:
            logger.exception(f"Failed to list accounts.")
            raise AccountRepositoryError(
                "Failed to list accounts"
            ) from exc

    def create(
        self,
        account: Account
    ) -> Account:

        logger.info(f"Creating new account {account.name}")

        try:
            with self.conn.cursor() as cur:

                logger.info(f"Creating account '{account.name}'.")
                logger.debug(
                    "Insert parameters: "
                    "account_number=%s, "
                    "name=%s, "
                    "institution=%s",
                    account.account_number,
                    account.name,
                    account.institution,
                )
                cur.execute(
                    """
                    INSERT INTO cycleguard.accounts(account_number, name, institution)
                    VALUES (%s, %s, %s)
                    RETURNING id, account_number, name, institution
                    """,
                    (account.account_number, account.name, account.institution)
                )

                row = cur.fetchone()

                self.conn.commit()

                logger.debug("Account insert committed.")
                logger.info(f"Created account '{account.name}' (id={row[0]})." )

                return Account(
                    id=row[0],
                    account_number=row[1],
                    name=row[2],
                    institution=row[3],
                )

        except psycopg.IntegrityError as exc:

            self.conn.rollback()
            logger.exception(f"Account '{account.name}' already exists.")

            raise AccountRepositoryError(
                f"Account '{account.name}' already exists."
            ) from exc

        except psycopg.Error as exc:

            self.conn.rollback()
            logger.exception(f"Failed to create account '{ account.name}'.")

            raise AccountRepositoryError(
                f"Failed to create account '{account.name}'"
            ) from exc

    
    