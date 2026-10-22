CREATE TABLE cycleguard.deployment_decision_snapshot (
    deployment_decision_snapshot_id SERIAL PRIMARY KEY,
    deployment_decision_id INTEGER NOT NULL,
    snapshot_date DATE NOT NULL,
    recommended_amount NUMERIC(20,2) NOT NULL,
    actual_amount_deployed NUMERIC(20,2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    FOREIGN KEY (deployment_decision_id)
        REFERENCES cycleguard.deployment_decision(id)
);