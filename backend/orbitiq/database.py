"""Explicit, no-overwrite SQLite maintenance commands."""

import argparse
import os
import sqlite3
from contextlib import closing
from pathlib import Path

INITIAL_MIGRATION = Path(__file__).parent / "migrations" / "001_initial.sql"
SNAPSHOT_MIGRATION = INITIAL_MIGRATION.with_name("002_snapshots.sql")
INGESTION_MIGRATION = INITIAL_MIGRATION.with_name("003_ingestion.sql")
LATEST_SCHEMA = 3


def schema_version(connection: sqlite3.Connection) -> int:
    rows = connection.execute("SELECT version FROM schema_version").fetchall()
    if len(rows) != 1 or rows[0][0] not in (1, 2, 3):
        raise ValueError("Unsupported OrbitIQ database schema")
    return rows[0][0]


def apply_sql(connection: sqlite3.Connection, path: Path) -> None:
    statement = ""
    for line in path.read_text().splitlines(keepends=True):
        statement += line
        if sqlite3.complete_statement(statement):
            connection.execute(statement)
            statement = ""
    if statement.strip():
        raise ValueError("Incomplete migration SQL")


def apply_snapshot_migration(connection: sqlite3.Connection) -> None:
    apply_sql(connection, SNAPSHOT_MIGRATION)


def configured_path() -> Path:
    value = os.environ.get("ORBITIQ_DATABASE_PATH", "")
    path = Path(value)
    if not value or not path.is_absolute():
        raise ValueError("ORBITIQ_DATABASE_PATH must be an absolute file path")
    return path


def connect_existing(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)


def validate(connection: sqlite3.Connection) -> None:
    if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise ValueError("SQLite integrity check failed")
    version = schema_version(connection)
    if version >= 2:
        connection.execute("SELECT id, raw_response FROM snapshots LIMIT 0")
    if version >= 3:
        connection.execute("SELECT id, outcome FROM ingestion_attempts LIMIT 0")
        connection.execute("SELECT snapshot_id FROM snapshot_insertions LIMIT 0")
        connection.execute("SELECT next_allowed_at FROM collection_gate LIMIT 0")
        if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise ValueError("SQLite foreign key check failed")


def reserve(path: Path) -> None:
    # Exclusive creation prevents an existing file from being replaced.
    with path.open("xb"):
        pass


def initialize(path: Path) -> None:
    reserve(path)
    try:
        with closing(sqlite3.connect(path)) as connection, connection:
            connection.executescript(INITIAL_MIGRATION.read_text())
            apply_snapshot_migration(connection)
            apply_sql(connection, INGESTION_MIGRATION)
            validate(connection)
    except Exception:
        path.unlink()
        raise


def copy_database(source: Path, destination: Path) -> None:
    if source.resolve() == destination.resolve():
        raise ValueError("Source and destination must differ")
    with closing(connect_existing(source)) as original:
        validate(original)
        reserve(destination)
        try:
            with closing(sqlite3.connect(destination)) as copied, copied:
                original.backup(copied)
                validate(copied)
        except Exception:
            destination.unlink()
            raise


def migrate(path: Path, backup: Path) -> bool:
    """Lock writers, back up the old schema, then atomically apply forward SQL."""
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=rw", uri=True)) as db:
        try:
            db.execute("BEGIN IMMEDIATE")
            validate(db)
            if schema_version(db) == LATEST_SCHEMA:
                db.rollback()
                return False
            copy_database(path, backup)
            if schema_version(db) == 1:
                apply_snapshot_migration(db)
            apply_sql(db, INGESTION_MIGRATION)
            validate(db)
            db.commit()
        except Exception:
            db.rollback()
            raise
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    sub.add_parser("check")
    sub.add_parser("verify-archive")
    sub.add_parser("migrate").add_argument("--backup", type=Path, required=True)
    sub.add_parser("backup").add_argument("destination", type=Path)
    sub.add_parser("restore").add_argument("source", type=Path)
    args = parser.parse_args()
    try:
        path = configured_path()
        if args.command == "init":
            initialize(path)
        elif args.command == "check":
            with closing(connect_existing(path)) as connection:
                validate(connection)
        elif args.command == "verify-archive":
            from orbitiq.storage import verify_archive

            print(f"Verified {verify_archive(path)} archived snapshots")
        elif args.command == "migrate":
            changed = migrate(path, args.backup)
            if not changed:
                print(f"Already at schema version {LATEST_SCHEMA}; no changes made")
                return
        elif args.command == "backup":
            copy_database(path, args.destination)
        else:
            copy_database(args.source, path)
    except (OSError, ValueError, RuntimeError, sqlite3.Error) as error:
        parser.exit(1, f"Database operation refused: {error}\n")
    print(f"{args.command}: successful")


if __name__ == "__main__":
    main()
