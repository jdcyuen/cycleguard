CREATE TABLE cycleguard.transactions (
    id SERIAL PRIMARY KEY,

    account_id INTEGER NOT NULL,
    security_id INTEGER,

    run_date DATE NOT NULL,
    settlement_date DATE,

    action VARCHAR(100) NOT NULL,
    transaction_type VARCHAR(100),

    description VARCHAR(255),

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