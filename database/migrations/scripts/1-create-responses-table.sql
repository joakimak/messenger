-- liquibase formatted sql
-- changeset joakim.akerstrom:1

CREATE TABLE IF NOT EXISTS responses (
    idempotency_key VARCHAR(255) PRIMARY KEY,
    status TEXT NOT NULL CHECK (status IN ('processing', 'completed', 'failed')),
    content JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
