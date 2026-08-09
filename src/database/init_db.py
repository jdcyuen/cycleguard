import sys
from src.database.connection import DBConnection
from src.core.logger import get_logger

logger = get_logger(__name__)

def init_db():
    schema_sql = """
    CREATE TABLE IF NOT EXISTS snapshots (
        id SERIAL PRIMARY KEY,
        account_id INTEGER NOT NULL,
        snapshot_date DATE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        CONSTRAINT uq_snapshot_account_date
        UNIQUE (
            account_id,
            snapshot_date
        )
    );

    CREATE TABLE IF NOT EXISTS accounts (
        id SERIAL PRIMARY KEY,
        account_number VARCHAR(100) UNIQUE NOT NULL,
        name VARCHAR(255),
        provider VARCHAR(100) DEFAULT 'unknown',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS securities (
        id SERIAL PRIMARY KEY,
        symbol VARCHAR(50) UNIQUE NOT NULL,
        description VARCHAR(255),
        asset_type VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS positions (
        id SERIAL PRIMARY KEY,
        snapshot_id INTEGER NOT NULL REFERENCES snapshots(id) ON DELETE CASCADE,
        account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
        security_id INTEGER NOT NULL REFERENCES securities(id) ON DELETE CASCADE,
        quantity NUMERIC(18, 4),
        avg_cost NUMERIC(18, 4),
        cost_basis_total NUMERIC(18, 4),
        current_value NUMERIC(18, 4),
        percent_of_account NUMERIC(18, 4),
        daily_gain NUMERIC(18, 4),
        daily_gain_pct NUMERIC(18, 4),
        total_gain NUMERIC(18, 4),
        total_gain_pct NUMERIC(18, 4),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (snapshot_id, account_id, security_id)
    );
    """
    
    logger.info("Initializing database schema...")
    try:
        with DBConnection() as conn:
            with conn.cursor() as cur:
                cur.execute(schema_sql)
            conn.commit()
        logger.info("Database schema initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize database schema: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_db()
