"""Append-only retrieval snapshots. No connection can implicitly create a database."""

import hashlib
import json
import sqlite3
import time
from contextlib import closing, contextmanager
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
        if schema_version(connection) not in (2, 3):
            raise StorageError("Explicit migration to schema version 2 is required")
        connection.execute("SELECT id FROM snapshots LIMIT 0")
        connection.execute("PRAGMA busy_timeout=5000")
        connection.execute("PRAGMA foreign_keys=ON")
    except Exception:
        connection.close()
        raise
    return connection


def insertion_column(connection):
    if schema_version(connection) >= 3:
        return (
            "(SELECT inserted_at FROM snapshot_insertions "
            "WHERE snapshot_id=snapshots.id) AS snapshot_inserted_at"
        )
    return "NULL AS snapshot_inserted_at"


def save_snapshot(
    path: Path,
    raw: bytes,
    record: dict,
    elements: Elements,
    source_url: str,
    retrieved_at: datetime,
    *,
    connection=None,
) -> int:
    if retrieved_at.tzinfo is None or retrieved_at.utcoffset() is None:
        raise StorageError("Retrieval timestamp must include a timezone")
    if connection is not None:
        return insert_snapshot(
            connection, raw, record, elements, source_url, retrieved_at
        )
    with closing(connect(path, write=True)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        return insert_snapshot(db, raw, record, elements, source_url, retrieved_at)


def insert_snapshot(connection, raw, record, elements, source_url, retrieved_at):
    response_hash = hashlib.sha256(raw).hexdigest()
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
    if schema_version(connection) >= 3:
        connection.execute(
            "INSERT INTO snapshot_insertions(snapshot_id) VALUES (?)",
            (cursor.lastrowid,),
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
    conditions, values = ["catalog_id = ?"], [catalog_id]
    if before_id is not None:
        conditions.append("id < ?")
        values.append(before_id)
    with browsing_connection(path) as connection:
        rows = connection.execute(
            "SELECT " + insertion_column(connection) + ", "
            """id, catalog_id, object_name, orbital_epoch, retrieved_at,
            source_url, response_sha256, validation_status, validator_version,
            sgp4_version, normalized_record, element_units FROM snapshots
            WHERE """ + " AND ".join(conditions) + " ORDER BY id DESC LIMIT ?",
            (*values, limit),
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
            "SELECT *, " + insertion_column(connection) + " FROM snapshots WHERE id=?",
            (snapshot_id,),
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


@contextmanager
def browsing_connection(path: Path):
    """A bounded read transaction; never creates, migrates or writes storage."""
    with closing(connect(path)) as connection:
        connection.execute("PRAGMA query_only=ON")
        connection.execute("PRAGMA busy_timeout=250")
        deadline = time.monotonic() + 0.25
        steps = 0

        def budget():
            nonlocal steps
            steps += 100
            return int(steps > 50000 or time.monotonic() > deadline)

        connection.set_progress_handler(budget, 100)
        connection.execute("BEGIN")
        yield connection


# Only bounded public metadata is read in listings; source bodies remain private
# to explicit detail/provenance validation. No SQL wildcard/timestamp sort scan.
BROWSE_COLUMNS = """id, catalog_id, substr(object_name,1,128) AS object_name,
    substr(orbital_epoch,1,80) AS orbital_epoch,
    substr(retrieved_at,1,80) AS retrieved_at,
    substr(source_url,1,1024) AS source_url,
    substr(response_sha256,1,65) AS response_sha256,
    substr(validation_status,1,128) AS validation_status,
    substr(validator_version,1,128) AS validator_version,
    substr(sgp4_version,1,32) AS sgp4_version,
    substr(normalized_record,1,8193) AS normalized_record"""
BROWSE_SCAN = 250
COUNT_BOUND = 1000


def browse_snapshots(
    path,
    *,
    limit=20,
    before_id=None,
    anchor_id=None,
    catalog_id=None,
    snapshot_id=None,
    query="",
    match="partial",
    context_snapshot_id=None,
    selected_only=False,
):
    """Seek pages through all stored history, with bounded search scan windows."""
    with browsing_connection(path) as connection:
        columns = BROWSE_COLUMNS + ", " + insertion_column(connection)
        maximum = connection.execute(
            "SELECT id FROM snapshots ORDER BY id DESC LIMIT 1"
        ).fetchone()
        anchor = anchor_id if anchor_id is not None else maximum[0] if maximum else None
        context = None
        if context_snapshot_id is not None:
            context = connection.execute(
                f"SELECT {columns} FROM snapshots WHERE id=?",
                (context_snapshot_id,),
            ).fetchone()
            if context is None:
                return {"context_missing": True}
        conditions, values = ["id <= ?"], [anchor or 0]
        if catalog_id is not None:
            conditions.append("catalog_id = ?")
            values.append(catalog_id)
        if snapshot_id is not None or selected_only:
            conditions.append("id = ?")
            values.append(
                snapshot_id if snapshot_id is not None else context_snapshot_id
            )
        where = " AND ".join(conditions)
        # COUNT itself would scan an unbounded index. Read at most 1001 IDs.
        count_rows = connection.execute(
            f"SELECT id FROM snapshots WHERE {where} ORDER BY id DESC LIMIT ?",
            (*values, COUNT_BOUND + 1),
        ).fetchall()
        count = len(count_rows) if len(count_rows) <= COUNT_BOUND else None
        if before_id is not None:
            conditions.append("id < ?")
            values.append(before_id)
        rows = connection.execute(
            f"SELECT {columns} FROM snapshots WHERE "
            + " AND ".join(conditions)
            + " ORDER BY id DESC LIMIT ?",
            (*values, (BROWSE_SCAN if query else limit) + 1),
        ).fetchall()
    return {
        "rows": [dict(row) for row in rows],
        "anchor_id": anchor,
        "context": dict(context) if context is not None else None,
        "candidate_count": count,
        "query": query,
        "match": match,
        "limit": limit,
    }
