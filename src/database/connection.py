import os
import logging
from typing import Optional

import psycopg2
from psycopg2.extensions import connection

from src.config.config_manager import get_config
from src.core.logger import get_logger

logger = get_logger(__name__)


class DBConnection:

    """
    Handles PostgreSQL database connections.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:

        # Load the configuration (this automatically resolves dev/test/prod based on the environment)
        config = get_config()
        db_config = config.get("system", {}).get("database", {})
        
        # Use explicitly passed arguments, environment variables, fallback to YAML config, and finally fallback to sensible defaults
        self._host = host or os.getenv("DB_HOST") or db_config.get("host", "localhost")
        
        env_port = os.getenv("DB_PORT")
        self._port = port or (int(env_port) if env_port else None) or db_config.get("port", 5433)
        
        self._database = database or os.getenv("DB_NAME") or os.getenv("DB_DATABASE") or db_config.get("dbname", "cycleguard")

        # Passwords and users should come from OS environment variables!
        self._user = user or os.getenv("DB_USER", "postgres")
        self._password = password or os.getenv("DB_PASSWORD")
        if not self._password:
            logger.warning(
                "No DB_PASSWORD environment variable found. Connection may fail if a password is required."
            )
        self._connection: Optional[connection] = None

    def connect(self) -> connection:
        """
        Create and return a PostgreSQL connection.
        """
        if self._connection is None or self._connection.closed:
            logger.info("Opening PostgreSQL connection")

            self._connection = psycopg2.connect(
                host=self._host,
                port=self._port,
                database=self._database,
                user=self._user,
                password=self._password,
            )

        return self._connection

    def close(self) -> None:
        """
        Close the PostgreSQL connection.
        """
        if self._connection and not self._connection.closed:
            logger.info("Closing PostgreSQL connection")
            self._connection.close()

    def __enter__(self) -> connection:
        """
        Support context manager usage.
        """
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Automatically close connection on exit.
        """
        self.close()
