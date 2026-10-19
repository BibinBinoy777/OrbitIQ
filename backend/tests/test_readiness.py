"""Readiness tests use temporary metadata-only archives, not observations."""

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from astropy.time import Time
from fastapi.testclient import TestClient
from orbitiq.database import initialize
from orbitiq.main import create_app
from orbitiq.orbits.earth_orientation import TransformationError, orientation
from orbitiq.services import readiness as service

NOW = datetime(2026, 10, 19, tzinfo=UTC)


@pytest.fixture
def archive(tmp_path, monkeypatch):
    path = tmp_path / "readiness.sqlite3"
    initialize(path)
    monkeypatch.setenv("ORBITIQ_DATABASE_PATH", str(path))
    for key in [
        "ORBITIQ_FRESH_HOURS",
        "ORBITIQ_STALE_HOURS",
        "ORBITIQ_EOP_POLICY",
        "ORBITIQ_EOP_VERIFICATION_FILE",
    ]:
        monkeypatch.delenv(key, raising=False)
    return path


def add(path, epoch=None, retrieved=None):
    with sqlite3.connect(path) as db:
        db.execute(
            """INSERT INTO snapshots (
                catalog_id, object_name, orbital_epoch, retrieved_at,
                source_url, raw_response, response_sha256, raw_record,
                normalized_record, element_units, validation_status,
                validator_version, sgp4_version
            ) VALUES (1, 'METADATA TEST ONLY', ?, ?,
                'https://celestrak.org/NORAD/elements/gp.php',
                ?, ?, '{}', '{}', '{}', 'test', 'test', 'test')""",
            (
                epoch if epoch is not None else NOW.isoformat(),
                retrieved if retrieved is not None else NOW.isoformat(),
                b"[]",
                "f" * 64,
            ),
        )


def result(at=None, now=NOW):
    return service.assess(at, now=now)


def test_empty_database_is_degraded_not_failed_liveness(archive):
    r = result("2004-04-06T07:51:28Z")
    assert r["status"] == "degraded"
    assert r["components"]["database"]["status"] == "healthy"
    assert r["components"]["orbital_data"]["code"] == "no_snapshots"
    with TestClient(create_app()) as client:
        assert client.get("/api/health").json() == {
            "status": "ok",
            "service": "OrbitIQ",
        }


@pytest.mark.parametrize(
    "hours,state,status",
    [
        (0, "fresh", "healthy"),
        (24, "fresh", "healthy"),
        (24.01, "aging", "degraded"),
        (72, "aging", "degraded"),
        (72.01, "stale", "degraded"),
    ],
)
def test_actual_epoch_freshness_boundaries(archive, hours, state, status):
    add(archive, (NOW - timedelta(hours=hours)).isoformat())
    r = result("2004-04-06T07:51:28Z")["components"]["orbital_data"]
    assert r["freshness"]["state"] == state and r["status"] == status
    assert r["freshness"]["epoch_age_seconds"] == timedelta(hours=hours).total_seconds()
    assert (
        r["latest_retrieval_at"] == NOW.isoformat() and r["accuracy_guarantee"] is False
    )


@pytest.mark.parametrize(
    "epoch,retrieved",
    [
        ("bad", None),
        (None, "bad"),
        ("", None),
        (None, ""),
        (None, "2026-10-20T00:00:00Z"),
        ("2026-10-20T00:00:00Z", None),
    ],
)
def test_unknown_or_future_metadata_is_not_fabricated(archive, epoch, retrieved):
    add(archive, epoch, retrieved)
    r = result()["components"]["orbital_data"]
    assert r["status"] == "unknown"
    assert r.get("snapshot_insertion_at") is None


def test_out_of_order_retrieval_is_not_confused_with_insertion_id(archive):
    add(archive, retrieved=NOW.isoformat())
    add(archive, retrieved=(NOW - timedelta(days=2)).isoformat())
    r = result()
    assert r["components"]["orbital_data"]["latest_retrieval_at"] == NOW.isoformat()
    assert r["components"]["database"]["latest_stored_snapshot_id"] == 2
    assert r["components"]["database"]["snapshot_insertion_at"] is None


def test_bounded_tail_does_not_claim_global_latest_in_large_history(archive):
    for _ in range(101):
        add(archive)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    r = result()["components"]["orbital_data"]
    assert r["status"] == "unknown" and r["history_complete"] is False
    assert r["inspected_count"] == 100 and r["latest_retrieval_at"] is None
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == digest


def test_sql_uses_no_full_archive_count_or_timestamp_sort(archive, monkeypatch):
    statements = []
    original = service.sqlite3.connect

    def connect(*args, **kwargs):
        db = original(*args, **kwargs)
        db.set_trace_callback(statements.append)
        return db

    monkeypatch.setattr(service.sqlite3, "connect", connect)
    result()
    sql = " ".join(statements).upper()
    assert "LIMIT 101" in sql and "ORDER BY ID DESC" in sql
    assert (
        "COUNT(" not in sql
        and "INTEGRITY_CHECK" not in sql
        and "ORDER BY RETRIEVED" not in sql
    )


@pytest.mark.parametrize(
    "mode", ["missing", "schema_missing", "schema_wrong", "columns_missing"]
)
def test_database_failure_is_safe_and_does_not_create_files(
    archive, monkeypatch, tmp_path, mode
):
    if mode == "missing":
        missing = tmp_path / "DO_NOT_CREATE.sqlite3"
        monkeypatch.setenv("ORBITIQ_DATABASE_PATH", str(missing))
    else:
        with sqlite3.connect(archive) as db:
            if mode == "schema_missing":
                db.execute("DROP TABLE schema_version")
            elif mode == "schema_wrong":
                db.execute("UPDATE schema_version SET version=999")
            else:
                db.execute("ALTER TABLE snapshots RENAME TO absent")
    r = result()
    assert r["components"]["database"]["status"] == "unavailable"
    assert str(tmp_path) not in json.dumps(r)
    if mode == "missing":
        assert not missing.exists()


def injected(monkeypatch, **changes):
    original = service.orientation

    @contextmanager
    def context():
        with original() as (data, mode):
            yield replace(data, **changes), mode

    monkeypatch.setattr(service, "orientation", context)


def test_available_eop_reports_distinct_coverage_age_and_identity(archive):
    with orientation() as (data, _):
        metadata = dict(data.metadata)
    boundary = Time(metadata["predictive_mjd"], format="mjd", scale="utc")
    now = boundary.to_datetime(timezone=UTC) + timedelta(days=17)
    r = result(now, now)["components"]["eop"]
    assert r["status"] == "degraded" and r["requested_eop_type"] == "predicted"
    assert r["covered"] and r["calculation_resources_usable"]
    assert r["dataset_release_at"] is None and r["dataset_age_seconds"] is None
    assert r["prediction_table_age_days"] == 17
    assert (
        r["first_covered_at"]
        == Time(metadata["first_mjd"], format="mjd", scale="utc")
        .to_datetime(timezone=UTC)
        .isoformat()
    )
    assert r["prediction_starts_at"] == boundary.to_datetime(timezone=UTC).isoformat()
    assert r["maintenance"]["verified_at"] is None and r["auto_download"] is False


@pytest.mark.parametrize(
    "case,usable",
    [
        ("historical", True),
        ("start_plus_second", True),
        ("start", False),
        ("before", False),
        ("after", False),
    ],
)
def test_eop_in_range_boundaries_and_outside(archive, case, usable):
    with orientation() as (data, _):
        start = Time(data.metadata["first_mjd"], format="mjd", scale="utc")
        end = Time(data.metadata["last_mjd"], format="mjd", scale="utc")
    first = start.to_datetime(timezone=UTC)
    date = {
        "historical": "2004-04-06T07:51:28Z",
        "start_plus_second": first + timedelta(seconds=1),
        "start": first,
        "before": first - timedelta(seconds=1),
        "after": end.to_datetime(timezone=UTC) + timedelta(days=1),
    }[case]
    r = result(date)["components"]["eop"]
    assert r.get("calculation_resources_usable", False) == usable
    if not usable:
        assert r["status"] == "unavailable"


@pytest.mark.parametrize(
    "seconds,expected", [(30 * 86400, "degraded"), (30 * 86400 + 1, "unavailable")]
)
def test_prediction_age_policy_exact_boundary(archive, seconds, expected):
    with orientation() as (data, _):
        boundary = Time(data.metadata["predictive_mjd"], format="mjd", scale="utc")
    start = boundary.to_datetime(timezone=UTC)
    now = start + timedelta(seconds=seconds)
    r = result(start + timedelta(days=2), now)["components"]["eop"]
    assert r["status"] == expected


def test_measured_only_policy_rejects_predictions_but_not_history(archive, monkeypatch):
    with orientation() as (data, _):
        boundary = Time(data.metadata["predictive_mjd"], format="mjd", scale="utc")
    target = boundary.to_datetime(timezone=UTC) + timedelta(days=2)
    monkeypatch.setenv("ORBITIQ_EOP_POLICY", "measured_only")
    assert (
        result(target, target)["components"]["eop"]["code"]
        == "eop_prediction_disallowed"
    )
    assert result("2004-04-06T07:51:28Z")["components"]["eop"]["status"] == "healthy"


def test_missing_eop_has_safe_partial_response(archive, monkeypatch):
    def unavailable():
        raise TransformationError(
            "eop_unavailable", "Required local resources are unavailable", 503
        )

    monkeypatch.setattr(service, "orientation", unavailable)
    r = result()
    assert r["components"]["eop"]["status"] == "unavailable"
    assert (
        r["components"]["database"]["status"] == "healthy"
        and r["components"]["leap_seconds"]["status"] == "unknown"
    )


@pytest.mark.parametrize(
    "key,value",
    [
        ("first_mjd", None),
        ("predictive_mjd", float("nan")),
        ("predictive_mjd", 1),
        ("sha256", "bad"),
    ],
)
def test_incomplete_eop_metadata_is_unknown(archive, monkeypatch, key, value):
    with orientation() as (data, _):
        metadata = {**data.metadata, key: value}
    injected(monkeypatch, metadata=metadata)
    assert result()["components"]["eop"]["code"] == "eop_metadata_unknown"


def test_leap_expiry_is_real_utc_normalized_not_invented(archive):
    with orientation() as (data, _):
        expected = data.leaps.expires.utc.to_datetime(timezone=UTC).isoformat()
        label, scale = data.leaps.expires.isot, data.leaps.expires.scale
    r = result()["components"]["leap_seconds"]
    assert r["status"] == "healthy" and r["expires_at"] == expected
    assert r["source_expiry_scale"] == scale and r["source_expiry_label"] == label


def test_unknown_leap_expiry_does_not_claim_validity(archive, monkeypatch):
    injected(monkeypatch, leaps=SimpleNamespace(expires=None))
    r = result()
    assert (
        r["components"]["leap_seconds"]["status"] == "unknown"
        and r["components"]["leap_seconds"]["expires_at"] is None
    )
    assert r["components"]["eop"]["calculation_resources_usable"] is False


def test_expired_leap_metadata_and_historical_request_are_distinct(
    archive, monkeypatch
):
    injected(
        monkeypatch, leaps=SimpleNamespace(expires=Time("2024-01-01", scale="tai"))
    )
    assert result()["components"]["leap_seconds"]["status"] == "unavailable"
    historical = result("2004-04-06T07:51:28Z")["components"]
    assert historical["leap_seconds"]["status"] == "degraded"
    assert "historical time remains covered" in historical["leap_seconds"]["message"]
    assert historical["eop"]["calculation_resources_usable"] is True


def test_safe_unexpected_service_exceptions_and_liveness(archive, monkeypatch):
    def failure(*args):
        raise RuntimeError("/secret/database/path")

    monkeypatch.setattr(service, "database_status", failure)
    monkeypatch.setattr(service, "scientific_status", failure)
    with TestClient(create_app()) as client:
        r = client.get("/api/readiness")
        assert r.status_code == 200 and "/secret" not in r.text
        assert (
            r.json()["status"] == "unavailable"
            and r.headers["cache-control"] == "no-store"
        )
        assert client.get("/api/health").status_code == 200


@pytest.mark.parametrize(
    "time", ["nope", "2026-10-19T00:00:00", "1234", "2016-12-31T23:59:60Z"]
)
def test_requested_time_validation(archive, time):
    with TestClient(create_app()) as client:
        r = client.get("/api/readiness", params={"at": time})
        assert (
            r.status_code == 422 and r.json()["error"]["code"] == "request_validation"
        )


def test_readiness_never_invokes_maintenance_or_downloads(archive, monkeypatch):
    from orbitiq.maintenance import eop

    def refuse(*args, **kwargs):
        raise AssertionError("No maintenance/download allowed")

    for name in ("prepare", "activate", "rollback"):
        monkeypatch.setattr(eop, name, refuse)
    monkeypatch.setattr("astropy.utils.iers.iers.download_file", refuse)
    r = result()
    assert r["components"]["eop"]["calculation_resources_usable"]


def test_matching_controlled_receipt_is_only_source_of_verification_time(
    archive, monkeypatch, tmp_path
):
    with orientation() as (data, _):
        meta = data.metadata
    receipt = {k: meta[k] for k in ("package_version", "sha256", "leap_seconds_sha256")}
    receipt.update(
        status="selected",
        acquired_at="2026-10-18T00:00:00Z",
        verified_at="2026-10-18T00:01:00Z",
        activated_at="2026-10-18T00:02:00Z",
    )
    file = tmp_path / "receipt.json"
    file.write_text(json.dumps(receipt))
    monkeypatch.setenv("ORBITIQ_EOP_VERIFICATION_FILE", str(file))
    assert (
        result()["components"]["eop"]["maintenance"]["record_status"]
        == "matching_operator_receipt"
    )
    receipt["sha256"] = "bad"
    file.write_text(json.dumps(receipt))
    assert result()["components"]["eop"]["maintenance"]["verified_at"] is None
