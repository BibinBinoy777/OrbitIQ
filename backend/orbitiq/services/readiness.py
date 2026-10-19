"""Read-only, bounded scientific readiness; not liveness or orbit accuracy."""

import json
import math
import os
import re
import sqlite3
import time
import warnings
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

import erfa
from astropy.time import Time
from astropy.utils.exceptions import AstropyWarning

from orbitiq.database import configured_path
from orbitiq.orbits.earth_orientation import (
    TransformationError,
    orientation,
    parameters,
)
from orbitiq.orbits.freshness import FreshnessPolicy, classify, utc

STATUSES = {"healthy", "degraded", "unavailable", "unknown"}
LIMIT = 100


def section(status, code, message, **facts):
    return {"status": status, "code": code, "message": message, **facts}


def database_status(now):
    database = section(
        "unavailable",
        "database_unavailable",
        "Configure a reachable existing orbital database.",
        reachable=False,
        schema_available=False,
        reads_available=False,
    )
    orbital = section(
        "unknown",
        "orbital_unavailable",
        "Orbital metadata cannot be assessed until database reads succeed.",
    )
    try:
        path = configured_path()
        with closing(
            sqlite3.connect(
                path.resolve().as_uri() + "?mode=ro", uri=True, timeout=0.25
            )
        ) as db:
            database["reachable"] = True
            deadline = time.monotonic() + 0.1
            steps = 0

            def budget():
                nonlocal steps
                steps += 100
                return int(steps > 5000 or time.monotonic() > deadline)

            db.set_progress_handler(budget, 100)
            db.execute("PRAGMA query_only=ON")
            versions = db.execute(
                "SELECT version FROM schema_version LIMIT 2"
            ).fetchall()
            if versions != [(2,)]:
                return section(
                    "unavailable",
                    "schema_unavailable",
                    (
                        "Required orbital schema 2 is unavailable; "
                        "operator review is needed."
                    ),
                    reachable=True,
                    schema_available=False,
                    reads_available=False,
                ), orbital
            db.execute(
                (
                    "SELECT id, catalog_id, orbital_epoch, "
                    "retrieved_at FROM snapshots LIMIT 0"
                )
            )
            database.update(schema_available=True)
            rows = db.execute(
                (
                    "SELECT id, catalog_id, "
                    "substr(orbital_epoch,1,80), "
                    "substr(retrieved_at,1,80) FROM snapshots ORDER "
                    "BY id DESC LIMIT 101"
                )
            ).fetchall()
        database = section(
            "healthy",
            "database_readable",
            "Database schema and bounded metadata reads are available.",
            reachable=True,
            schema_available=True,
            reads_available=True,
            schema_version=2,
            integrity_scope="metadata_read_not_full_integrity_scan",
        )
        if not rows:
            return database, section(
                "degraded",
                "no_snapshots",
                (
                    "No satellite snapshot is stored yet; use "
                    "explicit ingestion before exploration."
                ),
                snapshots_present=False,
                inspected_count=0,
                history_complete=True,
                latest_retrieval_at=None,
            )
        complete = len(rows) <= LIMIT
        rows = rows[:LIMIT]
        latest_stored = rows[0]
        database.update(
            latest_stored_snapshot_id=latest_stored[0],
            latest_stored_retrieved_at=utc(latest_stored[3]).isoformat()
            if utc(latest_stored[3])
            else None,
            snapshot_insertion_at=None,
            insertion_time_status="not_recorded",
        )
        valid = [(r, utc(r[3])) for r in rows]
        all_valid = all(t is not None for _, t in valid)
        latest = max(
            ((r, t) for r, t in valid if t is not None),
            key=lambda v: v[1],
            default=None,
        )
        global_known = complete and all_valid
        facts = {
            "snapshots_present": True,
            "inspected_count": len(rows),
            "inspection_limit": LIMIT,
            "history_complete": complete,
            "global_latest_known": global_known,
            "latest_retrieval_at": latest[1].isoformat()
            if latest and global_known
            else None,
            "ingestion_error_status": "not_recorded",
            "last_ingestion_error": None,
        }
        if not global_known or latest is None:
            return database, section(
                "unknown",
                "history_partial" if not complete else "timestamp_unknown",
                (
                    "Global latest retrieval is unknown: inspect "
                    "archive metadata; this check reads only the "
                    "latest 100 insertions."
                ),
                **facts,
            )
        row, retrieved = latest
        policy = FreshnessPolicy.configured()
        freshness = classify(row[2], row[3], as_of=now, policy=policy)
        state = freshness["state"]
        status = (
            "healthy"
            if state == "fresh"
            else "unknown"
            if state in {"unknown", "future_epoch"}
            else "degraded"
        )
        return database, section(
            status,
            "orbital_" + state,
            (
                "Freshness uses orbital epoch, not recent "
                "retrieval; historical calculations may remain "
                "available. Review ageing or unknown source data "
                "before current-time use."
            ),
            **facts,
            snapshot_id=row[0],
            catalog_id=row[1],
            orbital_epoch=utc(row[2]).isoformat() if utc(row[2]) else None,
            retrieval_age_seconds=(now - retrieved).total_seconds(),
            freshness=freshness,
            policy_basis="orbital_epoch",
            accuracy_guarantee=False,
        )
    except ValueError:
        if database.get("schema_available"):
            return database, section(
                "unknown",
                "freshness_configuration",
                "Orbital freshness policy is invalid; operator review is needed.",
            )
    except (sqlite3.Error, OSError, TypeError, OverflowError):
        pass
    return database, orbital


def iso_epoch(value):
    if (
        not isinstance(value, Time)
        or not value.isscalar
        or not math.isfinite(float(value.mjd))
    ):
        raise ValueError("Unknown time metadata")
    return value.utc.to_datetime(timezone=UTC).isoformat()


def maintenance_record(metadata):
    filename = os.environ.get("ORBITIQ_EOP_VERIFICATION_FILE")
    unknown = {
        "record_status": "not_recorded",
        "acquired_at": None,
        "verified_at": None,
        "activated_at": None,
    }
    if not filename:
        return unknown
    try:
        path = Path(filename)
        if not path.is_absolute() or path.stat().st_size > 65536:
            raise ValueError
        receipt = json.loads(path.read_text())
        if receipt.get("status") != "selected" or any(
            receipt.get(k) != metadata.get(k)
            for k in ("package_version", "sha256", "leap_seconds_sha256")
        ):
            raise ValueError
        times = {
            k: utc(receipt.get(k))
            for k in ("acquired_at", "verified_at", "activated_at")
        }
        if any(t is None for t in times.values()):
            raise ValueError
        return {
            "record_status": "matching_operator_receipt",
            **{k: t.isoformat() for k, t in times.items()},
        }
    except (OSError, ValueError, TypeError, AttributeError):
        return {**unknown, "record_status": "unknown_or_mismatched"}


def scientific_status(at, now):
    eop = section(
        "unavailable",
        "eop_unavailable",
        (
            "Required local EOP resources are unavailable; "
            "use controlled operator maintenance."
        ),
    )
    leap = section(
        "unknown",
        "leap_unknown",
        (
            "Leap-second validity could not be determined; "
            "operator verification is needed."
        ),
        expires_at=None,
        expiry_known=False,
    )
    try:
        with orientation() as (data, mode), warnings.catch_warnings():
            warnings.simplefilter("error", AstropyWarning)
            warnings.simplefilter("error", erfa.ErfaWarning)
            meta = data.metadata
            try:
                expires = iso_epoch(data.leaps.expires)
                expiry = utc(expires)
                target_expired = (at - expiry).total_seconds() >= -0.5
                current_expired = now >= expiry
                expired = target_expired
                leap = section(
                    "unavailable"
                    if expired
                    else "degraded"
                    if current_expired
                    else "healthy",
                    "leap_expired" if expired or current_expired else "leap_valid",
                    (
                        "Local leap-second validity is exhausted; perform"
                        " controlled maintenance."
                    )
                    if expired
                    else (
                        "Current-time validity is exhausted; the requested"
                        " historical time remains covered. Perform controlled"
                        " maintenance before current-time calculations."
                    )
                    if current_expired
                    else (
                        "Requested time and current assessment are before"
                        " the recorded leap-file expiry."
                    ),
                    source="astropy-iers-data bundled Leap_Second.dat",
                    package_version=meta.get("package_version"),
                    sha256=meta.get("leap_seconds_sha256"),
                    expires_at=expires,
                    expiry_known=True,
                    source_expiry_label=data.leaps.expires.isot,
                    source_expiry_scale=data.leaps.expires.scale,
                    requested_time_covered=not target_expired,
                    current_time_expired=current_expired,
                    expires_in_days=(expiry - now).total_seconds() / 86400,
                )
            except (ValueError, TypeError, AttributeError, OverflowError):
                pass
            required = ("first_mjd", "last_mjd", "predictive_mjd")
            if (
                any(
                    not isinstance(meta.get(k), (int, float))
                    or not math.isfinite(meta[k])
                    for k in required
                )
                or not meta["first_mjd"] < meta["predictive_mjd"] <= meta["last_mjd"]
                or not all(
                    isinstance(meta.get(k), str) and meta[k]
                    for k in ("package_version", "source")
                )
                or not all(
                    re.fullmatch(r"[a-f0-9]{64}", str(meta.get(k, "")))
                    for k in ("sha256", "leap_seconds_sha256")
                )
            ):
                return section(
                    "unknown",
                    "eop_metadata_unknown",
                    (
                        "EOP coverage or identity metadata are "
                        "incomplete; operator verification is needed."
                    ),
                ), leap
            target = Time(at, scale="utc")
            age = float(Time(now, scale="utc").mjd - meta["predictive_mjd"])
            facts = {
                "source": meta["source"],
                "package_version": meta["package_version"],
                "sha256": meta["sha256"],
                "first_covered_at": iso_epoch(
                    Time(meta["first_mjd"], format="mjd", scale="utc")
                ),
                "last_covered_at": iso_epoch(
                    Time(meta["last_mjd"], format="mjd", scale="utc")
                ),
                "prediction_starts_at": iso_epoch(
                    Time(meta["predictive_mjd"], format="mjd", scale="utc")
                ),
                "dataset_release_at": None,
                "dataset_age_seconds": None,
                "release_time_status": "not_recorded",
                "prediction_table_age_days": age,
                "max_prediction_table_age_days": 30,
                "prediction_age_state": "within_policy" if age <= 30 else "expired",
                "policy": mode,
                "auto_download": False,
                "covered": False,
                "calculation_resources_usable": False,
                "maintenance": maintenance_record(meta),
            }
            facts["covered"] = bool(meta["first_mjd"] <= target.mjd <= meta["last_mjd"])
            if not facts["covered"]:
                return section(
                    "unavailable",
                    "eop_out_of_range",
                    "Requested epoch is outside local EOP coverage.",
                    **facts,
                ), leap
            if leap["status"] == "unknown":
                return section(
                    "unknown",
                    "leap_validity_unknown",
                    (
                        "Requested calculation readiness is unknown "
                        "because leap validity is unknown."
                    ),
                    **facts,
                ), leap
            try:
                values = parameters(data, target, mode, now=now)
                predicted = values["status"] == "predicted"
                facts.update(
                    covered=True,
                    calculation_resources_usable=leap.get("requested_time_covered")
                    is True,
                    requested_eop_type=values["status"],
                    ut1_source=values["ut1_source"],
                    polar_motion_source=values["polar_motion_source"],
                )
                eop = section(
                    "degraded" if predicted or age > 30 else "healthy",
                    "eop_predicted" if predicted else "eop_measured",
                    (
                        "Requested epoch uses labelled IERS predictions; "
                        "monitor prediction age and schedule controlled "
                        "maintenance."
                    )
                    if predicted
                    else (
                        "Requested epoch uses measured/final EOP; "
                        "prediction-region age is reported separately."
                    ),
                    **facts,
                )
            except TransformationError as error:
                eop = section("unavailable", error.code, str(error), **facts)
            if leap["status"] == "unknown":
                eop.update(
                    status="unknown",
                    code="leap_validity_unknown",
                    calculation_resources_usable=False,
                    message=(
                        "Requested calculation readiness is unknown "
                        "because leap validity is unknown."
                    ),
                )
    except TransformationError as error:
        eop = section("unavailable", error.code, str(error))
    except (
        ValueError,
        TypeError,
        AttributeError,
        KeyError,
        IndexError,
        OSError,
        ArithmeticError,
        AstropyWarning,
        erfa.ErfaWarning,
    ):
        eop = section(
            "unknown",
            "resource_assessment_unknown",
            (
                "Scientific resource assessment failed safely; "
                "operator verification is needed."
            ),
        )
    return eop, leap


def assess(at=None, *, now=None):
    now = utc(now or datetime.now(UTC))
    at = utc(at or now)
    if now is None or at is None:
        raise ValueError("Readiness times must be timezone-aware")
    try:
        database, orbital = database_status(now)
    except Exception:
        database = section(
            "unavailable",
            "database_assessment_failed",
            "Database assessment failed safely; operator review is needed.",
        )
        orbital = section(
            "unknown",
            "orbital_unavailable",
            "Orbital readiness could not be determined.",
        )
    try:
        eop, leap = scientific_status(at, now)
    except Exception:
        eop = section(
            "unknown",
            "resource_assessment_unknown",
            "Scientific resource assessment failed safely; operator review is needed.",
        )
        leap = section(
            "unknown",
            "leap_unknown",
            "Leap validity could not be determined.",
            expires_at=None,
            expiry_known=False,
        )
    components = {
        "database": database,
        "orbital_data": orbital,
        "eop": eop,
        "leap_seconds": leap,
    }
    status = next(
        (
            s
            for s in ("unavailable", "unknown", "degraded", "healthy")
            if any(c["status"] == s for c in components.values())
        ),
        "unknown",
    )
    return {
        "status": status,
        "kind": "calculated_readiness_assessment",
        "evaluated_at": now.isoformat(),
        "requested_at": at.isoformat(),
        "time_system": "UTC",
        "components": components,
        "scope": (
            "Resource and metadata readiness, not orbit "
            "accuracy, observations, full archive integrity "
            "or readiness for every date."
        ),
        "automatic_updates": False,
    }
