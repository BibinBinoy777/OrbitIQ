"""Explicit collection with durable admission, audit, and deferred retry policy.

One HTTP request per invocation, globally gated per archive for at least two hours.
Retries are operator invocations after next_allowed_at, never a sleeping loop.
"""

import argparse
import hashlib
import json
import logging
import random
import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime

from orbitiq.database import configured_path, schema_version
from orbitiq.ingestion import celestrak
from orbitiq.ingestion.celestrak import IngestionError
from orbitiq.orbits.freshness import utc
from orbitiq.storage import browsing_connection, connect

INTERVAL_SECONDS = 7200
MAX_FAILURES = 3
LEASE_SECONDS = 120
LOG = logging.getLogger(__name__)


def clock():
    return datetime.now(UTC)


def retry_time(value, now):
    """Return a future HTTP Retry-After (delta seconds or HTTP date), if valid."""
    if not isinstance(value, str) or len(value) > 128:
        return None
    try:
        if value.strip().isdigit():
            return now + timedelta(seconds=int(value.strip()))
        result = utc(parsedate_to_datetime(value))
        return result if result and result >= now else None
    except (ValueError, TypeError, OverflowError):
        # An unrepresentably large numeric delay must not cause early retries.
        return datetime.max.replace(tzinfo=UTC) if value.strip().isdigit() else None


def collection_gate(db):
    row = db.execute("SELECT * FROM collection_gate WHERE id=1").fetchone()
    if row is None:
        raise IngestionError(
            "Collection gate is missing; inspect configured storage", category="storage"
        )
    return dict(row)


def reserve(path, catalog_id, source, now, resume):
    """Short transaction before network I/O; no writer lock during acquisition."""
    with closing(connect(path, write=True)) as db, db:
        if schema_version(db) != 3:
            raise IngestionError(
                "Explicit migration to schema 3 is required", category="storage"
            )
        db.execute("BEGIN IMMEDIATE")
        gate = collection_gate(db)
        active = gate["active_attempt_id"]
        if active is not None:
            row = db.execute(
                "SELECT started_at FROM ingestion_attempts WHERE id=?", (active,)
            ).fetchone()
            started = utc(row[0]) if row else None
            if started is None or (now - started).total_seconds() < LEASE_SECONDS:
                raise IngestionError(
                    "Another collection is active; no provider request made",
                    category="concurrent",
                )
            db.execute(
                (
                    "UPDATE ingestion_attempts SET outcome='interrupted', "
                    "completed_at=?, error_category='interrupted' WHERE id=? "
                    "AND outcome='running'"
                ),
                (now.isoformat(), active),
            )
            db.execute(
                (
                    "UPDATE collection_gate SET active_attempt_id=NULL, "
                    "consecutive_failures=consecutive_failures+1 WHERE id=1"
                )
            )
            gate["consecutive_failures"] += 1
        permitted = utc(gate["next_allowed_at"])
        # Preserve the first pre-ledger real retrieval's provider interval.
        latest = db.execute(
            "SELECT retrieved_at FROM snapshots ORDER BY id DESC LIMIT 1"
        ).fetchone()
        previous = utc(latest[0]) if latest else None
        if previous:
            permitted = max(
                permitted or previous, previous + timedelta(seconds=INTERVAL_SECONDS)
            )
        blocked = None
        if permitted is not None and now < permitted:
            blocked = IngestionError(
                f"Provider cooldown; next permitted collection {permitted.isoformat()}",
                category="cooldown",
            )
        elif (
            gate["consecutive_failures"] >= MAX_FAILURES or gate["retry_blocked"]
        ) and not resume:
            blocked = IngestionError(
                (
                    "Retry budget exhausted; inspect the source and explicitly "
                    "use --resume-after-review after cooldown"
                ),
                category="retry_budget",
            )
        if blocked:
            # Persist reconciliation even when no new collection can start.
            db.commit()
            raise blocked
        query = f"CATNR={catalog_id}&FORMAT=JSON"
        attempt = db.execute(
            (
                "INSERT INTO "
                "ingestion_attempts(source,catalog_id,query_sha256,started_at,outcome)"
                " VALUES (?,?,?,?,'running')"
            ),
            (
                source,
                catalog_id,
                hashlib.sha256(query.encode()).hexdigest(),
                now.isoformat(),
            ),
        ).lastrowid
        permitted = now + timedelta(seconds=INTERVAL_SECONDS)
        db.execute(
            (
                "UPDATE collection_gate SET active_attempt_id=?, "
                "next_allowed_at=?, consecutive_failures=?, retry_blocked=0 WHERE id=1"
            ),
            (
                attempt,
                permitted.isoformat(),
                gate["consecutive_failures"],
            ),
        )
        return attempt


def finish_failure(path, attempt, error, facts, now, jitter):
    """One best-effort failure write; no recursive logging/persistence retries."""
    with closing(connect(path, write=True)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        gate = collection_gate(db)
        if gate["active_attempt_id"] != attempt:
            raise IngestionError("Collection ownership changed", category="storage")
        failures = gate["consecutive_failures"] + 1
        # HTTP errors require human review. Network/timeouts alone may use the
        # remaining deferred budget; 401/403/404 and other permanent errors stop it.
        permanent = error.category in {"validation", "parsing", "tls", "storage"} or (
            error.status_code is not None and error.status_code != 200
        )
        seconds = INTERVAL_SECONDS * (2 ** min(failures - 1, 2)) + max(
            0, min(float(jitter()), 300)
        )
        if error.status_code in {401, 403, 404}:
            seconds = max(seconds, 86400)
        next_at = max(
            now + timedelta(seconds=seconds),
            retry_time(error.retry_after, now) or now,
            utc(gate["next_allowed_at"]) or now,
        )
        stage = (
            "persistence_failed"
            if error.category == "storage"
            else "parsing_failed"
            if error.category == "parsing"
            else "validation_failed"
            if facts.get("acquired_at")
            else "acquisition_failed"
        )
        fields = {
            **facts,
            "outcome": stage,
            "completed_at": now.isoformat(),
            "error_category": error.category,
            "http_status": error.status_code or facts.get("http_status"),
            "parsed_record_count": error.parsed_count
            if error.parsed_count is not None
            else facts.get("parsed_record_count"),
        }
        assignments = ",".join(f"{key}=?" for key in fields)
        db.execute(
            f"UPDATE ingestion_attempts SET {assignments} "
            "WHERE id=? AND outcome='running'",
            (*fields.values(), attempt),
        )
        db.execute(
            (
                "UPDATE collection_gate SET active_attempt_id=NULL, "
                "next_allowed_at=?, consecutive_failures=?, retry_blocked=? WHERE id=1"
            ),
            (
                next_at.isoformat(),
                failures,
                int(permanent),
            ),
        )
        return next_at.isoformat()


def collect(
    path,
    catalog_id,
    *,
    transport=None,
    now=clock,
    jitter=lambda: random.SystemRandom().uniform(0, 300),
    resume_after_review=False,
    verify_replay=False,
):
    """Use the existing fetch/parser/persistence pipeline; never initialize storage."""
    celestrak.validate_catalog_id(catalog_id)
    source = celestrak.configured_source()
    started = utc(now())
    if started is None:
        raise IngestionError(
            "Collection clock must be timezone aware", category="configuration"
        )
    try:
        attempt = reserve(path, catalog_id, source, started, resume_after_review)
    except (sqlite3.Error, OSError, RuntimeError) as error:
        LOG.error(
            "collection_failed category=storage stage=admission ledger_recorded=false"
        )
        raise IngestionError(
            "Collection storage unavailable; no request made", category="storage"
        ) from error
    facts = {"request_count": 1, "validation_status": "not_run"}
    try:
        dataset = celestrak.fetch_dataset(catalog_id, transport=transport)
        facts.update(
            http_status=dataset.http_status,
            acquired_at=dataset.retrieved_at.isoformat(),
            payload_sha256=hashlib.sha256(dataset.raw).hexdigest(),
        )
        celestrak.parse_response(dataset.raw, catalog_id)
        facts.update(
            parsed_record_count=1,
            validated_at=now().isoformat(),
            validation_status="passed",
        )
        with closing(connect(path, write=True)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            gate = db.execute(
                "SELECT active_attempt_id FROM collection_gate WHERE id=1"
            ).fetchone()
            if gate is None or gate[0] != attempt:
                raise IngestionError("Collection ownership changed", category="storage")
            changes = db.total_changes
            snapshot = celestrak.process_dataset(
                path, catalog_id, dataset, connection=db
            )
            inserted = db.total_changes > changes
            if (
                verify_replay
                and celestrak.process_dataset(path, catalog_id, dataset, connection=db)
                != snapshot
            ):
                raise IngestionError(
                    "Exact-byte replay changed snapshot identity", category="storage"
                )
            fields = {
                **facts,
                "outcome": "inserted" if inserted else "deduplicated",
                "snapshot_id": snapshot,
                "newly_inserted": int(inserted),
                "completed_at": now().isoformat(),
            }
            assignments = ",".join(f"{key}=?" for key in fields)
            db.execute(
                f"UPDATE ingestion_attempts SET {assignments} "
                "WHERE id=? AND outcome='running'",
                (*fields.values(), attempt),
            )
            next_at = max(
                utc(
                    db.execute(
                        "SELECT next_allowed_at FROM collection_gate WHERE id=1"
                    ).fetchone()[0]
                ),
                utc(dataset.retrieved_at) + timedelta(seconds=INTERVAL_SECONDS),
            )
            db.execute(
                (
                    "UPDATE collection_gate SET active_attempt_id=NULL, "
                    "consecutive_failures=0, next_allowed_at=? WHERE id=1"
                ),
                (next_at.isoformat(),),
            )
        result = {
            "status": "success",
            "attempt_id": attempt,
            "snapshot_id": snapshot,
            "outcome": fields["outcome"],
            "provider_response_received": True,
            "parsed": True,
            "validated": True,
            "persisted": True,
            "newly_inserted": inserted,
            "deduplicated": not inserted,
            "payload_sha256": facts["payload_sha256"],
            "retrieved_at": facts["acquired_at"],
            "completed_at": fields["completed_at"],
            "next_allowed_at": next_at.isoformat(),
            "request_count": 1,
            "replay_verified": verify_replay,
        }
        LOG.info(
            "collection_completed attempt_id=%s outcome=%s", attempt, fields["outcome"]
        )
        return result
    except (IngestionError, sqlite3.Error, OSError, RuntimeError) as cause:
        error = (
            cause
            if isinstance(cause, IngestionError)
            else IngestionError(
                "Snapshot transaction failed; no success recorded", category="storage"
            )
        )
        if error.category in {"parsing", "validation"} and facts.get("acquired_at"):
            facts["validation_status"] = (
                "failed" if error.category == "validation" else "not_run"
            )
        try:
            next_at = finish_failure(path, attempt, error, facts, utc(now()), jitter)
            suffix = f"; next permitted collection {next_at}"
            recorded = True
        except (sqlite3.Error, OSError, RuntimeError, ValueError):
            suffix = (
                "; completion could not be recorded; operator reconciliation required"
            )
            recorded = False
        LOG.error(
            "collection_failed attempt_id=%s category=%s ledger_recorded=%s",
            attempt,
            error.category,
            recorded,
        )
        raise IngestionError(
            str(error) + suffix, category=error.category, status_code=error.status_code
        ) from None


# Raw bytes, URLs, paths and internal errors are deliberately absent from history.
HISTORY_COLUMNS = (
    "id,catalog_id,query_sha256,started_at,completed_at,inserted_at,outcome,"
    "http_status,request_count,acquired_at,validated_at,payload_sha256,"
    "parsed_record_count,validation_status,snapshot_id,newly_inserted,error_category"
)


def history(path, *, limit=20, before_id=None):
    if (
        type(limit) is not int
        or not 1 <= limit <= 100
        or (
            before_id is not None
            and (
                type(before_id) is not int or not 1 <= before_id <= 9223372036854775807
            )
        )
    ):
        raise ValueError("Invalid ingestion history bounds")
    with browsing_connection(path) as db:
        where = "WHERE id < ?" if before_id else ""
        args = (before_id, limit + 1) if before_id else (limit + 1,)
        rows = [
            dict(row)
            for row in db.execute(
                f"SELECT {HISTORY_COLUMNS} FROM ingestion_attempts {where} "
                "ORDER BY id DESC LIMIT ?",
                args,
            )
        ]
    return {
        "attempts": rows[:limit],
        "has_more": len(rows) > limit,
        "next_before_id": rows[limit - 1]["id"] if len(rows) > limit else None,
        "order": "attempt_id_desc",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    command = sub.add_parser("collect")
    command.add_argument("catalog_id", type=int)
    command.add_argument(
        "--resume-after-review",
        action="store_true",
        help="Explicit operator retry-budget reset; cannot bypass cooldown",
    )
    command.add_argument("--verify-replay", action="store_true")
    command = sub.add_parser("history")
    command.add_argument("--limit", type=int, default=20)
    command.add_argument("--before-id", type=int)
    args = parser.parse_args()
    try:
        path = configured_path()
        result = (
            collect(
                path,
                args.catalog_id,
                resume_after_review=args.resume_after_review,
                verify_replay=args.verify_replay,
            )
            if args.command == "collect"
            else history(path, limit=args.limit, before_id=args.before_id)
        )
    except (ValueError, OSError, RuntimeError, sqlite3.Error) as error:
        category = error.category if isinstance(error, IngestionError) else "storage"
        message = (
            str(error)
            if isinstance(error, IngestionError)
            else "Operation unavailable; inspect configured storage and bounds"
        )
        parser.exit(
            1,
            json.dumps({"status": "failed", "category": category, "message": message})
            + "\n",
        )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
