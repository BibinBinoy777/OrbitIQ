"""Bounded, redacted collection metadata for the existing readiness assessment."""

import sqlite3

from orbitiq.database import configured_path, schema_version
from orbitiq.orbits.freshness import utc
from orbitiq.storage import browsing_connection


def assess_ingestion(now, orbital):
    result = {
        "status": "unknown",
        "code": "ingestion_unknown",
        "message": (
            "Collection history cannot be assessed; stored snapshots "
            "remain independently accessible."
        ),
        "last_attempt_at": None,
        "last_attempt_completed_at": None,
        "last_successful_acquisition_at": None,
        "last_successful_validation_at": None,
        "last_snapshot_insertion_at": None,
        "next_allowed_at": None,
        "latest_attempt_failed": None,
        "consecutive_failures": None,
        "last_error_category": None,
        "latest_payload_outcome": None,
        "minimum_request_interval_seconds": 7200,
        "request_retry_mode": "deferred_operator_only",
        "orbital_freshness_basis": "orbital_epoch_not_collector_execution",
        "orbital_freshness_state": orbital.get("freshness", {}).get("state", "unknown"),
        "most_recent_stored_retrieval_age_seconds": orbital.get(
            "retrieval_age_seconds"
        ),
        "stored_orbital_epoch_age_seconds": orbital.get("freshness", {}).get(
            "epoch_age_seconds"
        ),
        "history_scope": "schema_3_attempts_only_legacy_history_not_backfilled",
        "automatic_collection": False,
    }
    try:
        with browsing_connection(configured_path()) as db:
            if schema_version(db) != 3:
                return {
                    **result,
                    "code": "ingestion_schema_required",
                    "message": (
                        "Explicit schema 3 migration is required for auditable "
                        "collection."
                    ),
                }
            latest = db.execute(
                (
                    "SELECT id,started_at,completed_at,outcome,error_category "
                    "FROM ingestion_attempts ORDER BY id DESC LIMIT 1"
                )
            ).fetchone()
            gate = db.execute(
                (
                    "SELECT "
                    "next_allowed_at,consecutive_failures,retry_blocked,active_attempt_id"
                    " FROM collection_gate WHERE id=1"
                )
            ).fetchone()
            if latest is None:
                return {
                    **result,
                    "status": "degraded",
                    "code": "no_ingestion_history",
                    "message": (
                        "No auditable collection attempts have been recorded; "
                        "legacy source retrievals are not backfilled."
                    ),
                }
            # Each lookup uses its partial ID index; no entire-ledger scan/count.
            stamps = {}
            for key, column, condition in [
                (
                    "last_successful_acquisition_at",
                    "acquired_at",
                    "acquired_at IS NOT NULL",
                ),
                (
                    "last_successful_validation_at",
                    "validated_at",
                    "validated_at IS NOT NULL",
                ),
            ]:
                row = db.execute(
                    f"SELECT {column} FROM ingestion_attempts WHERE {condition} "
                    "ORDER BY id DESC LIMIT 1"
                ).fetchone()
                stamps[key] = row[0] if row else None
            inserted = db.execute(
                "SELECT inserted_at FROM snapshot_insertions "
                "ORDER BY snapshot_id DESC LIMIT 1"
            ).fetchone()
            stamps["last_snapshot_insertion_at"] = inserted[0] if inserted else None
        times = {
            "last_attempt_at": latest["started_at"],
            "last_attempt_completed_at": latest["completed_at"],
            **stamps,
        }
        invalid = False
        for key, value in times.items():
            parsed = utc(value)
            if value is not None and (parsed is None or parsed > now):
                invalid = True
            result[key] = (
                parsed.isoformat() if parsed is not None and parsed <= now else None
            )
        error = latest["error_category"]
        safe_errors = {
            "upstream_http",
            "network",
            "proxy",
            "tls",
            "timeout",
            "validation",
            "parsing",
            "storage",
            "interrupted",
        }
        result.update(
            last_attempt_id=latest["id"],
            latest_attempt_outcome=latest["outcome"],
            latest_attempt_failed=latest["outcome"]
            not in {"running", "inserted", "deduplicated"},
            consecutive_failures=gate["consecutive_failures"],
            retry_budget_exhausted=gate["consecutive_failures"] >= 3
            or bool(gate["retry_blocked"]),
            next_allowed_at=utc(gate["next_allowed_at"]).isoformat()
            if utc(gate["next_allowed_at"])
            else None,
            last_error_category=error
            if error in safe_errors
            else "unknown"
            if error
            else None,
            latest_payload_outcome=latest["outcome"]
            if latest["outcome"] in {"inserted", "deduplicated"}
            else None,
        )
        if invalid or (
            latest["outcome"] != "running" and utc(latest["completed_at"]) is None
        ):
            return {
                **result,
                "code": "ingestion_timestamp_unknown",
                "message": (
                    "Collection timestamps are missing, invalid, or in the "
                    "future; freshness is not asserted."
                ),
            }
        if latest["outcome"] == "running":
            return {
                **result,
                "status": "degraded",
                "code": "collection_in_progress",
                "message": (
                    "A collection is in progress or needs interrupted-attempt "
                    "reconciliation; existing data remains accessible."
                ),
            }
        if result["latest_attempt_failed"]:
            return {
                **result,
                "status": "degraded",
                "code": "recent_failure_with_stored_data"
                if orbital.get("snapshots_present")
                else "upstream_unavailable",
                "message": (
                    "The last collection failed. Review the error category and "
                    "cooldown; existing validated snapshots are preserved."
                ),
            }
        freshness = result["orbital_freshness_state"]
        if freshness in {"unknown", "future_epoch"}:
            return {
                **result,
                "code": "ingestion_success_freshness_unknown",
                "message": (
                    "Collection succeeded; orbital-data freshness remains unknown."
                ),
            }
        return {
            **result,
            "status": "healthy" if freshness == "fresh" else "degraded",
            "code": "recent_success" if freshness == "fresh" else "stale_data",
            "message": (
                "Collection succeeded. Orbital freshness uses the stored "
                "element epoch; deduplicated downloads do not refresh the "
                "dataset epoch."
            ),
        }
    except (sqlite3.Error, OSError, ValueError, RuntimeError, TypeError, KeyError):
        return result
