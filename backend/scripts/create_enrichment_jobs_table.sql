-- Standalone DDL for enrichment_jobs table (no migration).
-- Run this once if the table does not exist; then re-run enrichment.
-- SQLite-compatible.
--
-- From repo root (Windows PowerShell):
--   sqlite3 backend/coinstack_v2.db < backend/scripts/create_enrichment_jobs_table.sql
-- Or from backend dir:
--   sqlite3 coinstack_v2.db ".read scripts/create_enrichment_jobs_table.sql"

CREATE TABLE IF NOT EXISTS enrichment_jobs (
    id VARCHAR(36) PRIMARY KEY,
    status VARCHAR(20) NOT NULL DEFAULT 'queued',
    total INTEGER NOT NULL DEFAULT 0,
    progress INTEGER NOT NULL DEFAULT 0,
    updated INTEGER NOT NULL DEFAULT 0,
    conflicts INTEGER NOT NULL DEFAULT 0,
    not_found INTEGER NOT NULL DEFAULT 0,
    errors INTEGER NOT NULL DEFAULT 0,
    result_summary TEXT,
    error_message TEXT,
    started_at DATETIME,
    completed_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS ix_enrichment_jobs_status ON enrichment_jobs(status);
