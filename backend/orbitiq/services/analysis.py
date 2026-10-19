"""Read-only scientific orchestration with validated immutable input lineage."""

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from orbitiq.orbits.engine import PropagationError, propagate
from orbitiq.orbits.freshness import FreshnessPolicy, classify, utc
from orbitiq.storage import (
    StorageError,
    get_snapshot,
    list_snapshots,
    validate_snapshot,
)


class AnalysisError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def policy() -> FreshnessPolicy:
    try:
        return FreshnessPolicy.configured()
    except ValueError:
        raise AnalysisError(
            503, "freshness_configuration", "Freshness policy is unavailable"
        ) from None


def storage_read(function, *args, **kwargs):
    try:
        return function(*args, **kwargs)
    except (sqlite3.Error, StorageError, OSError, ValueError, KeyError, TypeError):
        raise AnalysisError(
            503,
            "storage_unavailable",
            "Orbital storage is unavailable or needs migration",
        ) from None


def load_snapshot(path: Path, snapshot_id: int):
    item = storage_read(get_snapshot, path, snapshot_id)
    if item is None:
        raise AnalysisError(404, "snapshot_not_found", "Snapshot not found")
    try:
        elements = validate_snapshot(item)
    except (
        ValueError,
        ValidationError,
        StorageError,
        KeyError,
        TypeError,
        OverflowError,
    ):
        raise AnalysisError(
            503,
            "snapshot_invalid",
            "Stored snapshot failed scientific provenance validation",
        ) from None
    return item, elements


def snapshot_history(path: Path, catalog_id: int, limit: int, before_id: int | None):
    now = datetime.now(UTC)
    thresholds = policy()
    items = storage_read(
        list_snapshots, path, catalog_id, limit + 1, before_id, as_of=now
    )
    has_more = len(items) > limit
    items = items[:limit]
    for item in items:
        item["freshness_info"] = classify(
            item.get("orbital_epoch"),
            item.get("retrieved_at"),
            as_of=now,
            policy=thresholds,
        )
        item["snapshot_created_at"] = item.get("snapshot_inserted_at")
    return {
        "snapshots": items,
        "has_more": has_more,
        "next_before_id": items[-1]["id"] if has_more else None,
        "order": "insertion_id_desc_not_retrieval_chronology",
        "total_count": None,
        "total_count_status": "not_computed_use_global_snapshot_browser",
    }


def snapshot_detail(path: Path, snapshot_id: int):
    item, _ = load_snapshot(path, snapshot_id)
    item.pop("raw_response")
    item["freshness_info"] = classify(
        item["orbital_epoch"],
        item["retrieved_at"],
        as_of=datetime.now(UTC),
        policy=policy(),
    )
    item["snapshot_created_at"] = item.get("snapshot_inserted_at")
    item["snapshot_creation_time_status"] = (
        "recorded" if item["snapshot_created_at"] else "not_recorded_legacy"
    )
    return item


def position(path: Path, snapshot_id: int, at: datetime):
    item, elements = load_snapshot(path, snapshot_id)
    return position_from_snapshot(item, elements, at)


def position_from_snapshot(item, elements, at: datetime):
    """Reuse validated, fixed source within one bounded multi-sample request."""
    try:
        result = propagate(elements, at)
    except PropagationError as error:
        raise AnalysisError(422, error.code, str(error)) from None
    freshness = classify(
        item["orbital_epoch"],
        item["retrieved_at"],
        as_of=utc(result["calculated_at"]),
        policy=policy(),
    )
    if freshness["state"] != "fresh":
        result["warnings"].append(
            f"Source element freshness is {freshness['state']}; "
            "recent retrieval does not guarantee an accurate orbit."
        )
    return {
        **result,
        "snapshot_id": item["id"],
        "catalog_id": item["catalog_id"],
        "retrieved_at": item["retrieved_at"],
        "source_url": item["source_url"],
        "response_sha256": item["response_sha256"],
        "freshness_info": freshness,
        "snapshot_created_at": item.get("snapshot_inserted_at"),
        "snapshot_validation_status": item["validation_status"],
        "validator_version": item["validator_version"],
        "ingestion_sgp4_version": item["sgp4_version"],
    }
