CREATE TABLE cycleguard.deployment_decision (
    id SERIAL PRIMARY KEY,

    account_id INTEGER NOT NULL,

    recommended_amount NUMERIC(20,2) NOT NULL,

    reason TEXT NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    FOREIGN KEY (account_id)
        REFERENCES cycleguard.accounts(id)
);