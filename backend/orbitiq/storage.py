"""Append-only retrieval snapshots. No connection can implicitly create a database."""

import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import sgp4

from orbitiq.database import schema_version, validate
from orbitiq.orbits.elements import ELEMENT_UNITS, Elements
from orbitiq.orbits.freshness import utc


class StorageError(RuntimeError):
    pass


def connect(path: Path, *, write: bool = False) -> sqlite3.Connection:
    mode = "rw" if write else "ro"
    connection = sqlite3.connect(path.resolve().as_uri() + f"?mode={mode}", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        if schema_version(connection) != 2:
            raise StorageError("Explicit migration to schema version 2 is required")
        connection.execute("SELECT id FROM snapshots LIMIT 0")
        connection.execute("PRAGMA busy_timeout=5000")
    except Exception:
        connection.close()
        raise
    return connection


def save_snapshot(
    path: Path,
    raw: bytes,
    record: dict,
    elements: Elements,
    source_url: str,
    retrieved_at: datetime,
) -> int:
    response_hash = hashlib.sha256(raw).hexdigest()
    if retrieved_at.tzinfo is None or retrieved_at.utcoffset() is None:
        raise StorageError("Retrieval timestamp must include a timezone")
    with closing(connect(path, write=True)) as connection, connection:
        # Serialize lookup + insert across processes; no destructive deduplication
        # or schema rewrite is needed for existing archives.
        connection.execute("BEGIN IMMEDIATE")
        existing = connection.execute(
            """SELECT id FROM snapshots WHERE catalog_id=? AND source_url=?
            AND response_sha256=? ORDER BY id LIMIT 1""",
            (elements.catalog_id, source_url, response_hash),
        ).fetchone()
        if existing is not None:
            return existing["id"]
        cursor = connection.execute(
            """INSERT INTO snapshots
            (catalog_id, object_name, orbital_epoch, retrieved_at, source_url,
             raw_response, response_sha256, raw_record, normalized_record,
             element_units,
             validation_status,
             validator_version, sgp4_version)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                elements.catalog_id,
                elements.name,
                elements.epoch.isoformat(),
                retrieved_at.astimezone(UTC).isoformat(),
                source_url,
                raw,
                response_hash,
                json.dumps(record, allow_nan=False),
                json.dumps(elements.model_dump(mode="json", by_alias=True)),
                json.dumps(ELEMENT_UNITS),
                "structural_and_epoch_propagation_passed",
                "orbitiq-omm-v1",
                sgp4.__version__,
            ),
        )
        return cursor.lastrowid


def list_snapshots(
    path: Path,
    catalog_id: int,
    limit: int = 20,
    before_id: int | None = None,
    *,
    as_of: datetime | None = None,
) -> list[dict]:
    with closing(connect(path)) as connection:
        rows = connection.execute(
            """SELECT id, catalog_id, object_name, orbital_epoch, retrieved_at,
            source_url, response_sha256, validation_status, validator_version,
            sgp4_version, normalized_record, element_units FROM snapshots
            WHERE catalog_id = ? AND (? IS NULL OR id < ?)
            ORDER BY id DESC LIMIT ?""",
            (catalog_id, before_id, before_id, limit),
        ).fetchall()
    now = as_of or datetime.now(UTC)
    results = []
    for row in rows:
        item = dict(row)
        normalized = json.loads(item.pop("normalized_record"))
        item["frame"] = normalized["REF_FRAME"]
        item["time_system"] = normalized["TIME_SYSTEM"]
        item["mean_element_theory"] = normalized["MEAN_ELEMENT_THEORY"]
        item["element_units"] = json.loads(item["element_units"])
        try:
            epoch = datetime.fromisoformat(item["orbital_epoch"])
            if epoch.tzinfo is None:
                raise ValueError("Missing epoch timezone")
            age = (now - epoch).total_seconds() / 86400
        except (ValueError, TypeError, OverflowError):
            age = None
        item["epoch_age_days"] = age
        item["freshness"] = (
            "unknown"
            if age is None
            else "future_epoch"
            if age < 0
            else "stale"
            if age > 1
            else "recent"
        )
        item["freshness_policy"] = "recent <= 24h; not an orbit-accuracy guarantee"
        results.append(item)
    return results


def get_snapshot(path: Path, snapshot_id: int) -> dict | None:
    with closing(connect(path)) as connection:
        row = connection.execute(
            "SELECT * FROM snapshots WHERE id=?", (snapshot_id,)
        ).fetchone()
    if row is None:
        return None
    item = dict(row)
    item["raw_record"] = json.loads(item["raw_record"])
    item["normalized_record"] = json.loads(item["normalized_record"])
    item["element_units"] = json.loads(item["element_units"])
    # Original response is available internally for exact-byte backup verification.
    return item


def validate_snapshot(item: dict) -> Elements:
    """Check immutable input linkage before scientific use; no database writes."""
    raw = item["raw_response"]
    if not isinstance(raw, bytes) or len(raw) > 65536:
        raise StorageError("Invalid snapshot source bytes")
    if hashlib.sha256(raw).hexdigest() != item["response_sha256"]:
        raise StorageError("Snapshot response checksum mismatch")

    def decoded(value):
        return json.loads(value) if isinstance(value, str) else value

    record = decoded(item["raw_record"])
    if json.loads(raw) != [record]:
        raise StorageError("Snapshot raw record differs from source response")
    elements = Elements.model_validate(record)
    if (
        decoded(item["normalized_record"])
        != elements.model_dump(mode="json", by_alias=True)
        or decoded(item["element_units"]) != ELEMENT_UNITS
    ):
        raise StorageError("Snapshot normalized metadata differs from source")
    if (
        elements.catalog_id != item["catalog_id"]
        or elements.epoch.isoformat() != item["orbital_epoch"]
    ):
        raise StorageError("Snapshot catalog or epoch identity mismatch")
    if utc(item["retrieved_at"]) is None:
        raise StorageError("Snapshot retrieval timestamp is unavailable")
    source = urlsplit(item["source_url"])
    if (
        source.scheme != "https"
        or source.hostname not in {"celestrak.org", "www.celestrak.org"}
        or source.username
        or source.password
        or source.port not in (None, 443)
        or source.path != "/NORAD/elements/gp.php"
        or source.fragment
        or parse_qs(source.query)
        != {"CATNR": [str(elements.catalog_id)], "FORMAT": ["JSON"]}
    ):
        raise StorageError("Snapshot source provenance is invalid")
    if (
        item["validation_status"] != "structural_and_epoch_propagation_passed"
        or not isinstance(item["validator_version"], str)
        or not item["validator_version"]
        or not isinstance(item["sgp4_version"], str)
        or not item["sgp4_version"]
    ):
        raise StorageError("Snapshot validation provenance is unavailable")
    return elements


def verify_archive(path: Path) -> int:
    with closing(connect(path)) as connection:
        validate(connection)
        count = 0
        for row in connection.execute("SELECT * FROM snapshots"):
            validate_snapshot(dict(row))
            count += 1
    return count
