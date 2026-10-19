-- Additive only: existing immutable snapshot rows are never updated/backfilled.
CREATE TABLE snapshot_insertions (
    snapshot_id INTEGER PRIMARY KEY REFERENCES snapshots(id),
    inserted_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f+00:00','now'))
);
CREATE TABLE ingestion_attempts (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,
    catalog_id INTEGER NOT NULL CHECK (catalog_id > 0),
    query_sha256 TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    inserted_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f+00:00','now')),
    outcome TEXT NOT NULL CHECK (outcome IN
      ('running','inserted','deduplicated','acquisition_failed','parsing_failed',
       'validation_failed','persistence_failed','interrupted')),
    http_status INTEGER,
    request_count INTEGER NOT NULL DEFAULT 0 CHECK (request_count BETWEEN 0 AND 1),
    acquired_at TEXT,
    validated_at TEXT,
    payload_sha256 TEXT,
    parsed_record_count INTEGER,
    validation_status TEXT NOT NULL DEFAULT 'not_run',
    snapshot_id INTEGER REFERENCES snapshots(id),
    newly_inserted INTEGER CHECK (newly_inserted IN (0,1)),
    error_category TEXT,
    CHECK ((outcome IN ('inserted','deduplicated') AND snapshot_id IS NOT NULL
        AND completed_at IS NOT NULL AND validated_at IS NOT NULL)
        OR (outcome NOT IN ('inserted','deduplicated') AND snapshot_id IS NULL))
);
CREATE INDEX ingestion_acquired ON ingestion_attempts(id DESC)
    WHERE acquired_at IS NOT NULL;
CREATE INDEX ingestion_validated ON ingestion_attempts(id DESC)
    WHERE validated_at IS NOT NULL;
CREATE INDEX ingestion_inserted ON ingestion_attempts(id DESC)
    WHERE outcome = 'inserted';
CREATE INDEX snapshots_payload_identity
    ON snapshots(catalog_id, source_url, response_sha256);
CREATE TABLE collection_gate (
    id INTEGER PRIMARY KEY CHECK (id=1),
    active_attempt_id INTEGER REFERENCES ingestion_attempts(id),
    next_allowed_at TEXT,
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    retry_blocked INTEGER NOT NULL DEFAULT 0 CHECK (retry_blocked IN (0,1))
);
INSERT INTO collection_gate(id) VALUES (1);
UPDATE schema_version SET version = 3;

CREATE TRIGGER ingestion_no_delete BEFORE DELETE ON ingestion_attempts
BEGIN SELECT RAISE(ABORT, 'ingestion audit is immutable'); END;
CREATE TRIGGER ingestion_completed_no_update BEFORE UPDATE ON ingestion_attempts
WHEN OLD.outcome != 'running'
BEGIN SELECT RAISE(ABORT, 'completed ingestion audit is immutable'); END;
CREATE TRIGGER insertions_no_update BEFORE UPDATE ON snapshot_insertions
BEGIN SELECT RAISE(ABORT, 'insertion timestamps are immutable'); END;
CREATE TRIGGER insertions_no_delete BEFORE DELETE ON snapshot_insertions
BEGIN SELECT RAISE(ABORT, 'insertion timestamps are immutable'); END;
