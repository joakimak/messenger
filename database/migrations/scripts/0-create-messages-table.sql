-- liquibase formatted sql
-- changeset joakim.akerstrom:0

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    username VARCHAR(32) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_messages_username ON messages (username);
CREATE INDEX idx_messages_created_at ON messages (created_at);
