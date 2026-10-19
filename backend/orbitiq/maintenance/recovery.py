"""Explicit consistent backup and isolated restore verification; no source writes."""

import argparse
import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from orbitiq.api.orbits import database_path
from orbitiq.database import (
    configured_path,
    connect_existing,
    copy_database,
    schema_version,
    validate,
)
from orbitiq.main import create_app
from orbitiq.storage import verify_archive


def fingerprint(path):
    """Offline full verification; never called by a dashboard or health request."""
    with closing(connect_existing(path)) as db:
        db.execute("PRAGMA query_only=ON")
        db.execute("BEGIN")
        validate(db)
        schema = db.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
        ).fetchall()
        tables = {}
        for kind, name, _, _ in schema:
            if kind != "table":
                continue
            quoted = '"' + name.replace('"', '""') + '"'
            columns = db.execute(f"PRAGMA table_info({quoted})").fetchall()
            keys = sorted([r for r in columns if r[5]], key=lambda r: r[5])
            order = (
                ",".join('"' + r[1].replace('"', '""') + '"' for r in keys) or "rowid"
            )
            digest = hashlib.sha256()
            count = 0
            for row in db.execute(f"SELECT * FROM {quoted} ORDER BY {order}"):
                encoded = json.dumps(
                    [{"blob_hex": v.hex()} if isinstance(v, bytes) else v for v in row],
                    ensure_ascii=True,
                    separators=(",", ":"),
                ).encode()
                digest.update(len(encoded).to_bytes(8, "big"))
                digest.update(encoded)
                count += 1
            tables[name] = {"rows": count, "sha256": digest.hexdigest()}
        return {
            "schema_version": schema_version(db),
            "schema_sha256": hashlib.sha256(
                json.dumps(schema, sort_keys=True).encode()
            ).hexdigest(),
            "schema_objects": [{"type": r[0], "name": r[1]} for r in schema],
            "tables": tables,
            "integrity": "ok",
            "foreign_keys": "ok"
            if not db.execute("PRAGMA foreign_key_check").fetchall()
            else "failed",
        }


def rehearse(source, directory, *, keep_restored=False):
    directory.mkdir(parents=False, exist_ok=False)
    backup, restored = directory / "backup.sqlite3", directory / "restored.sqlite3"
    before = fingerprint(source)
    created_at = datetime.now(UTC).isoformat()
    copy_database(source, backup)
    point = fingerprint(backup)
    copy_database(backup, restored)
    recovered = fingerprint(restored)
    if recovered != point:
        raise ValueError("Restored database differs from backup point")
    verified = verify_archive(restored)
    with closing(connect_existing(restored)) as db:
        ids = [r[0] for r in db.execute("SELECT id FROM snapshots ORDER BY id LIMIT 2")]
    app = create_app()
    app.dependency_overrides[database_path] = lambda: restored
    checks = []
    with TestClient(app) as client:
        response = client.get("/api/snapshots", params={"limit": 2})
        checks.append({"route": "/api/snapshots", "http_status": response.status_code})
        for sid in ids:
            response = client.get(f"/api/snapshots/{sid}")
            checks.append(
                {"route": f"/api/snapshots/{sid}", "http_status": response.status_code}
            )
        if ids:
            response = client.get(
                "/api/comparisons", params={"first_id": ids[0], "second_id": ids[-1]}
            )
            checks.append(
                {
                    "route": "/api/comparisons",
                    "http_status": response.status_code,
                    "counts": response.json().get("counts"),
                    "self_comparison": len(ids) == 1,
                }
            )
    if any(c["http_status"] != 200 for c in checks):
        raise ValueError("Restored application check failed")
    after = fingerprint(source)
    if before != point or after != point:
        raise ValueError(
            "Source changed during recovery rehearsal; "
            "repeat while collection is quiescent"
        )
    result = {
        "status": "passed",
        "created_at": created_at,
        "completed_at": datetime.now(UTC).isoformat(),
        "method": "SQLite Connection.backup; exclusive new files; no source writes",
        "backup_name": backup.name,
        "backup_bytes": backup.stat().st_size,
        "backup_sha256": hashlib.sha256(backup.read_bytes()).hexdigest(),
        "source_at_backup": point,
        "restored": recovered,
        "source_unchanged_during_rehearsal": True,
        "verified_snapshots": verified,
        "api_checks": checks,
        "restored_target_separate": restored.resolve() != source.resolve(),
        "restored_retained": keep_restored,
    }
    with (directory / "verification.json").open("x") as file:
        json.dump(result, file, indent=2)
        file.write("\n")
    if not keep_restored:
        restored.unlink()  # Only the target created above; backup retained.
    return result


def main():
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--directory",
        type=Path,
        required=True,
        help="A new directory; existing paths are refused",
    )
    parser.add_argument("--keep-restored", action="store_true")
    args = parser.parse_args()
    try:
        result = rehearse(
            configured_path(), args.directory, keep_restored=args.keep_restored
        )
    except (OSError, ValueError, RuntimeError, sqlite3.Error):
        parser.exit(
            1,
            "Recovery verification failed; source was not a restore target. "
            "Inspect the isolated artifacts.\n",
        )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
