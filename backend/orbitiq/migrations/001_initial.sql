-- Explicit initial migration, applied only to a newly reserved database file.
-- Future migrations must be additive, versioned, and separately tested.
BEGIN;
CREATE TABLE schema_version (version INTEGER NOT NULL);
INSERT INTO schema_version VALUES (1);
COMMIT;
