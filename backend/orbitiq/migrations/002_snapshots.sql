-- Applied only by explicit migrate with a pre-upgrade backup.
CREATE TABLE snapshots (
    id INTEGER PRIMARY KEY,
    catalog_id INTEGER NOT NULL CHECK (catalog_id > 0),
    object_name TEXT NOT NULL,
    orbital_epoch TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    source_url TEXT NOT NULL,
    raw_response BLOB NOT NULL,
    response_sha256 TEXT NOT NULL,
    raw_record TEXT NOT NULL,
    normalized_record TEXT NOT NULL,
    element_units TEXT NOT NULL,
    validation_status TEXT NOT NULL,
    validator_version TEXT NOT NULL,
    sgp4_version TEXT NOT NULL
);
CREATE INDEX snapshots_catalog_id ON snapshots(catalog_id, id DESC);
CREATE TRIGGER snapshots_no_update BEFORE UPDATE ON snapshots
BEGIN SELECT RAISE(ABORT, 'snapshots are immutable'); END;
CREATE TRIGGER snapshots_no_delete BEFORE DELETE ON snapshots
BEGIN SELECT RAISE(ABORT, 'snapshots are immutable'); END;
UPDATE schema_version SET version = 2;
