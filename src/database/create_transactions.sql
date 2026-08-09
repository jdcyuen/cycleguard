CREATE TABLE cycleguard.transactions (
    id SERIAL PRIMARY KEY,

    account_id INTEGER NOT NULL,
    security_id INTEGER,

    run_date DATE NOT NULL,
    settlement_date DATE,

    action VARCHAR(100) NOT NULL,
    trade_type VARCHAR(100),

    price NUMERIC(20,6),
    quantity NUMERIC(20,6),

    commission NUMERIC(20,2),
    fees NUMERIC(20,2),
    accrued_interest NUMERIC(20,2),

    amount NUMERIC(20,2) NOT NULL,
    cash_balance NUMERIC(20,2),

    created_at TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (account_id)
        REFERENCES cycleguard.accounts(id),

    FOREIGN KEY (security_id)
        REFERENCES cycleguard.securities(id)
);

CREATE TABLE cycleguard.import_history (
    id SERIAL PRIMARY KEY,

    account_id INTEGER NOT NULL,

    import_type VARCHAR(50) NOT NULL,
    institution VARCHAR(100) NOT NULL,

    filename VARCHAR(255) NOT NULL,
    file_hash VARCHAR(64) NOT NULL,

    snapshot_date DATE,
    import_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),

    rows_read INTEGER NOT NULL DEFAULT 0,
    rows_imported INTEGER NOT NULL DEFAULT 0,
    rows_skipped INTEGER NOT NULL DEFAULT 0,

    status VARCHAR(20) NOT NULL DEFAULT 'STARTED',
    elapsed_ms INTEGER NOT NULL DEFAULT 0,

    error_message TEXT,

    FOREIGN KEY (account_id)
        REFERENCES cycleguard.accounts(id),

    CONSTRAINT uq_import_history
        UNIQUE (
            account_id,
            import_type,
            file_hash
        )
);


ALTER TABLE cycleguard.transactions
ADD CONSTRAINT uq_transaction
UNIQUE
(
    account_id,
    run_date,
    security_id,
    amount,
    action,
    trade_type
);

-- Since import_type and status only allow a small set of values, add CHECK constraints to enforce them
-- This prevents invalid values (for example, "Position" or "Complete") from ever being written to the database 
-- and helps keep your audit trail consistent.

ALTER TABLE cycleguard.import_history
ADD CONSTRAINT chk_import_type
CHECK (
    import_type IN (
        'POSITIONS',
        'TRANSACTIONS'
    )
);

ALTER TABLE cycleguard.import_history
ADD CONSTRAINT chk_import_status
CHECK (
    status IN (
        'STARTED',
        'SUCCESS',
        'PARTIAL',
        'FAILED'
    )
);