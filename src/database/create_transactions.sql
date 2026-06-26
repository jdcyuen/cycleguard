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

    file_name VARCHAR(255) NOT NULL,
    file_hash VARCHAR(64) NOT NULL,

    row_count INTEGER,

    status VARCHAR(20) NOT NULL DEFAULT 'SUCCESS',

    imported_at TIMESTAMP NOT NULL DEFAULT NOW(),

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