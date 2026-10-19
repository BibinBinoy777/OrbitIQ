"""Isolated Phase 6 tests. Reference-derived payloads are NOT live evidence."""

import hashlib
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Event

import httpx
import pytest
from fastapi.testclient import TestClient
from orbitiq import database
from orbitiq.ingestion import celestrak
from orbitiq.ingestion import collection as service
from orbitiq.ingestion.celestrak import (
    DownloadedDataset,
    IngestionError,
    process_dataset,
)
from orbitiq.main import create_app
from orbitiq.services.readiness import assess
from orbitiq.storage import get_snapshot, verify_archive

NOW = datetime(2026, 10, 20, 12, tzinfo=UTC)
FIXTURE = json.loads((Path(__file__).parent / "fixtures/vallado-leo.json").read_text())[
    0
]


@pytest.fixture
def archive(tmp_path, monkeypatch):
    path = tmp_path / "phase6-reference-only.sqlite3"
    database.initialize(path)
    monkeypatch.setenv("ORBITIQ_DATABASE_PATH", str(path))
    monkeypatch.delenv("ORBITIQ_CELESTRAK_URL", raising=False)
    return path


@pytest.fixture
def dataset():
    return DownloadedDataset(
        json.dumps([FIXTURE["omm"]]).encode(),
        celestrak.BASE_URL + "?CATNR=6251&FORMAT=JSON",
        NOW,
        200,
    )


def rows(path, table="ingestion_attempts"):
    with closing(sqlite3.connect(path)) as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute(f"SELECT * FROM {table} ORDER BY id")]


def capture(monkeypatch, dataset):
    calls = []

    def fetch(catalog_id, **kwargs):
        calls.append(catalog_id)
        return dataset

    monkeypatch.setattr(celestrak, "fetch_dataset", fetch)
    return calls


def collect(path, at=NOW, **kwargs):
    return service.collect(path, 6251, now=lambda: at, jitter=lambda: 17, **kwargs)


def transport(body=b"", status=200, headers=None):
    return httpx.MockTransport(
        lambda request: httpx.Response(
            status,
            stream=httpx.ByteStream(body),
            headers=headers or {"content-type": "application/json"},
        )
    )


def test_success_atomic_linkage_and_separate_insertion_clock(
    archive, dataset, monkeypatch
):
    capture(monkeypatch, dataset)
    result = collect(archive, verify_replay=True)
    attempt = rows(archive)[0]
    snapshot = get_snapshot(archive, result["snapshot_id"])
    assert result["outcome"] == "inserted" and result["newly_inserted"]
    assert result["request_count"] == 1 and result["replay_verified"]
    assert attempt["started_at"] == NOW.isoformat()
    assert attempt["completed_at"] == attempt["validated_at"] == NOW.isoformat()
    assert attempt["acquired_at"] == dataset.retrieved_at.isoformat()
    assert attempt["inserted_at"] != attempt["acquired_at"]  # actual SQLite clock
    assert snapshot["snapshot_inserted_at"] is not None
    assert snapshot["orbital_epoch"] != snapshot["snapshot_inserted_at"]
    assert attempt["snapshot_id"] == snapshot["id"]
    assert attempt["payload_sha256"] == hashlib.sha256(dataset.raw).hexdigest()
    assert (
        attempt["validation_status"] == "passed" and attempt["parsed_record_count"] == 1
    )


def test_deduplicated_permitted_acquisition_keeps_first_source_metadata(
    archive, dataset, monkeypatch
):
    calls = capture(monkeypatch, dataset)
    first = collect(archive)
    before = get_snapshot(archive, first["snapshot_id"])
    later = NOW + timedelta(hours=2)
    monkeypatch.setattr(
        celestrak, "fetch_dataset", lambda *a, **k: replace(dataset, retrieved_at=later)
    )
    second = collect(archive, later)
    assert (
        second["snapshot_id"] == first["snapshot_id"]
        and second["outcome"] == "deduplicated"
    )
    assert get_snapshot(archive, first["snapshot_id"]) == before
    assert len(rows(archive)) == 2 and len(calls) == 1
    assert rows(archive)[1]["newly_inserted"] == 0
    assert rows(archive)[1]["acquired_at"] == later.isoformat()
    assert verify_archive(archive) == 1


def test_distinct_reference_payloads_use_existing_identity_and_actual_comparison(
    archive, dataset, monkeypatch
):
    capture(monkeypatch, dataset)
    first = collect(archive)["snapshot_id"]
    record = json.loads(dataset.raw)[0]
    record["MEAN_ANOMALY"] += 0.01
    later = NOW + timedelta(hours=2)
    capture(
        monkeypatch,
        replace(dataset, raw=json.dumps([record]).encode(), retrieved_at=later),
    )
    second = collect(archive, later)["snapshot_id"]
    assert first != second and verify_archive(archive) == 2
    with TestClient(create_app()) as client:
        history = client.get("/api/snapshots", params={"catalog_id": 6251}).json()
        assert {r["id"] for r in history["snapshots"]} == {first, second}
        for sid in [first, second]:
            detail = client.get(f"/api/snapshots/{sid}")
            assert detail.status_code == 200
            assert detail.json()["snapshot_created_at"] is not None
        at = FIXTURE["omm"]["EPOCH"] + "Z"
        result = client.get(
            "/api/comparisons",
            params={"first_id": first, "second_id": second, "at": at, "frame": "TEME"},
        )
        assert result.status_code == 200
        assert result.json()["counts"]["shared"] == 1
        again = client.get(
            "/api/comparisons",
            params={"first_id": first, "second_id": second, "at": at, "frame": "TEME"},
        ).json()
        assert again["counts"] == result.json()["counts"]
        assert again["records"] == result.json()["records"]
        assert again["element_differences"] == result.json()["element_differences"]
        assert again["state_comparison"]["status"] == "complete"
        for key in ["difference_position_km", "difference_velocity_km_s"]:
            assert (
                again["state_comparison"][key] == result.json()["state_comparison"][key]
            )


@pytest.mark.parametrize("seconds", [0, 1, 7199])
def test_cooldown_blocks_before_any_provider_request(
    archive, dataset, monkeypatch, seconds
):
    calls = capture(monkeypatch, dataset)
    collect(archive)
    with pytest.raises(IngestionError) as caught:
        collect(archive, NOW + timedelta(seconds=seconds))
    assert caught.value.category == "cooldown"
    assert calls == [6251] and len(rows(archive)) == 1


def test_alias_source_and_other_catalog_cannot_bypass_archive_gate(
    archive, dataset, monkeypatch
):
    calls = capture(monkeypatch, dataset)
    collect(archive)
    monkeypatch.setenv(
        "ORBITIQ_CELESTRAK_URL", celestrak.BASE_URL.replace("://", "://www.")
    )
    with pytest.raises(IngestionError, match="cooldown"):
        service.collect(archive, 25544, now=lambda: NOW)
    assert calls == [6251]


@pytest.mark.parametrize("status", [301, 401, 403, 404, 408, 429, 500, 502, 503])
def test_provider_errors_make_one_request_and_record_safe_failure(
    archive, status, caplog
):
    calls = []

    def failure(request):
        calls.append(request)
        return httpx.Response(
            status,
            content=b"credential=SECRET_BODY",
            headers={"Retry-After": "10000", "Set-Cookie": "SECRET_COOKIE"},
        )

    with pytest.raises(IngestionError) as caught:
        collect(archive, transport=httpx.MockTransport(failure))
    assert caught.value.status_code == status and len(calls) == 1
    attempt = rows(archive)[0]
    assert (
        attempt["outcome"] == "acquisition_failed" and attempt["http_status"] == status
    )
    assert attempt["snapshot_id"] is None and attempt["request_count"] == 1
    assert attempt["completed_at"] is not None
    gate = rows(archive, "collection_gate")[0]
    assert datetime.fromisoformat(gate["next_allowed_at"]) >= NOW + timedelta(
        seconds=10000
    )
    if status in {401, 403, 404}:
        assert datetime.fromisoformat(gate["next_allowed_at"]) >= NOW + timedelta(
            days=1
        )
    assert "SECRET" not in str(caught.value) + caplog.text + json.dumps(
        service.history(archive)
    )
    assert verify_archive(archive) == 0


@pytest.mark.parametrize(
    "kind",
    [httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError, httpx.ProxyError],
)
def test_network_failures_are_audited_without_in_process_retries(archive, kind, caplog):
    calls = []

    def failure(request):
        calls.append(request)
        raise kind("SECRET_INTERNAL")

    with pytest.raises(IngestionError):
        collect(archive, transport=httpx.MockTransport(failure))
    assert len(calls) == 1 and rows(archive)[0]["outcome"] == "acquisition_failed"
    assert "SECRET_INTERNAL" not in caplog.text


@pytest.mark.parametrize(
    "value,seconds",
    [
        ("9000", 9000),
        ("Tue, 20 Oct 2026 16:00:00 GMT", 14400),
        ("nonsense", None),
        ("-1", None),
    ],
)
def test_retry_after_delta_date_and_invalid(value, seconds):
    result = service.retry_time(value, NOW)
    assert result == (NOW + timedelta(seconds=seconds) if seconds is not None else None)


def test_retry_after_huge_delta_stops_instead_of_early_retry():
    assert service.retry_time("9" * 100, NOW) == datetime.max.replace(tzinfo=UTC)


def test_exponential_deferred_backoff_jitter_and_retry_exhaustion(archive):
    at = NOW
    for failures in range(1, 4):
        with pytest.raises(IngestionError):
            collect(
                archive,
                at,
                transport=httpx.MockTransport(
                    lambda request: (_ for _ in ()).throw(httpx.ConnectTimeout("test"))
                ),
            )
        gate = rows(archive, "collection_gate")[0]
        assert gate["consecutive_failures"] == failures
        permitted = datetime.fromisoformat(gate["next_allowed_at"])
        assert (permitted - at).total_seconds() == 7200 * 2 ** (failures - 1) + 17
        at = permitted
    with pytest.raises(IngestionError) as caught:
        collect(archive, at, transport=transport(status=200))
    assert caught.value.category == "retry_budget"
    assert len(rows(archive)) == 3


def test_operator_resume_cannot_skip_cooldown(archive, dataset, monkeypatch):
    with pytest.raises(IngestionError):
        collect(archive, transport=transport(status=403))
    calls = capture(
        monkeypatch, replace(dataset, retrieved_at=NOW + timedelta(days=1, seconds=1))
    )
    with pytest.raises(IngestionError, match="cooldown"):
        collect(archive, resume_after_review=True)
    permitted = datetime.fromisoformat(
        rows(archive, "collection_gate")[0]["next_allowed_at"]
    )
    with pytest.raises(IngestionError, match="Retry budget"):
        collect(archive, permitted)
    result = collect(archive, permitted, resume_after_review=True)
    assert result["outcome"] == "inserted" and calls == [6251]
    assert rows(archive, "collection_gate")[0]["consecutive_failures"] == 0


@pytest.mark.parametrize(
    "body,outcome,validation",
    [
        (b"", "parsing_failed", "not_run"),
        (b"[]", "parsing_failed", "not_run"),
        (b"<html>error</html>", "parsing_failed", "not_run"),
        (b"[{}]", "validation_failed", "failed"),
        (b'[{"x":1,"x":2}]', "parsing_failed", "not_run"),
        (b"[NaN]", "parsing_failed", "not_run"),
    ],
)
def test_invalid_json_or_elements_never_become_successful_snapshots(
    archive, body, outcome, validation
):
    with pytest.raises(IngestionError):
        collect(archive, transport=transport(body))
    attempt = rows(archive)[0]
    assert attempt["outcome"] == outcome and attempt["validation_status"] == validation
    assert attempt["payload_sha256"] == hashlib.sha256(body).hexdigest()
    assert attempt["acquired_at"] is not None and attempt["snapshot_id"] is None
    assert verify_archive(archive) == 0


@pytest.mark.parametrize(
    "body,headers",
    [
        (b"[]", {"content-type": "text/html"}),
        (b"x" * 65537, {"content-type": "application/json"}),
        (b"[]", {"content-type": "application/json", "content-encoding": "gzip"}),
    ],
)
def test_invalid_http_representation_records_received_status(archive, body, headers):
    with pytest.raises(IngestionError):
        collect(archive, transport=transport(body, headers=headers))
    assert rows(archive)[0]["http_status"] == 200
    assert rows(archive)[0]["outcome"] == "acquisition_failed"


def test_persistence_failure_rolls_back_snapshot_and_success_audit(
    archive, dataset, monkeypatch
):
    capture(monkeypatch, dataset)
    with closing(sqlite3.connect(archive)) as db:
        db.executescript(
            (
                "CREATE TRIGGER injected_snapshot_failure AFTER INSERT ON "
                "snapshots BEGIN SELECT RAISE(FAIL,'SECRET_STORAGE'); END;"
            )
        )
    with pytest.raises(IngestionError) as caught:
        collect(archive)
    assert caught.value.category == "storage" and "SECRET" not in str(caught.value)
    attempt = rows(archive)[0]
    assert attempt["outcome"] == "persistence_failed" and attempt["snapshot_id"] is None
    assert (
        attempt["validated_at"] is not None and attempt["validation_status"] == "passed"
    )
    assert verify_archive(archive) == 0
    with sqlite3.connect(archive) as db:
        assert db.execute("SELECT count(*) FROM snapshot_insertions").fetchone()[0] == 0


def test_success_ledger_failure_cannot_commit_a_snapshot(archive, dataset, monkeypatch):
    capture(monkeypatch, dataset)
    with sqlite3.connect(archive) as db:
        db.executescript(
            (
                "CREATE TRIGGER injected_completion_failure BEFORE UPDATE "
                "ON ingestion_attempts WHEN NEW.outcome='inserted' BEGIN "
                "SELECT RAISE(FAIL,'SECRET_LEDGER'); END;"
            )
        )
    with pytest.raises(IngestionError):
        collect(archive)
    assert verify_archive(archive) == 0
    assert rows(archive)[0]["outcome"] == "persistence_failed"


def test_unavailable_database_does_not_create_file_or_request(
    tmp_path, monkeypatch, caplog
):
    missing = tmp_path / "never-create.sqlite3"
    monkeypatch.setattr(
        celestrak, "fetch_dataset", lambda *a, **k: pytest.fail("Network not allowed")
    )
    with pytest.raises(IngestionError, match="storage unavailable"):
        collect(missing)
    assert not missing.exists() and "ledger_recorded=false" in caplog.text
    assert str(missing) not in caplog.text


def test_failure_recording_itself_fails_once_safely(
    archive, dataset, monkeypatch, caplog
):
    capture(monkeypatch, dataset)
    with sqlite3.connect(archive) as db:
        db.executescript(
            (
                "CREATE TRIGGER injected_all_completion_failure BEFORE "
                "UPDATE ON ingestion_attempts BEGIN SELECT "
                "RAISE(FAIL,'SECRET_LEDGER'); END;"
            )
        )
    with pytest.raises(IngestionError, match="could not be recorded"):
        collect(archive)
    assert rows(archive)[0]["outcome"] == "running" and verify_archive(archive) == 0
    assert "ledger_recorded=False" in caplog.text and "SECRET" not in caplog.text


def test_concurrent_collection_admission_makes_only_one_provider_call(
    archive, dataset, monkeypatch
):
    entered, release = Event(), Event()

    def fetch(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        return dataset

    monkeypatch.setattr(celestrak, "fetch_dataset", fetch)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(collect, archive)
        assert entered.wait(5)
        try:
            with pytest.raises(IngestionError) as caught:
                collect(archive)
            assert caught.value.category == "concurrent"
        finally:
            release.set()
        assert first.result()["outcome"] == "inserted"
    assert len(rows(archive)) == 1


def test_crash_lease_is_reconciled_without_resetting_cooldown(archive):
    attempt = service.reserve(archive, 6251, celestrak.BASE_URL, NOW, False)
    with pytest.raises(IngestionError, match="cooldown"):
        collect(archive, NOW + timedelta(minutes=3))
    assert rows(archive)[0]["id"] == attempt
    assert rows(archive)[0]["outcome"] == "interrupted"
    assert rows(archive, "collection_gate")[0]["active_attempt_id"] is None


def test_completed_audit_and_insertion_time_are_immutable(
    archive, dataset, monkeypatch
):
    capture(monkeypatch, dataset)
    collect(archive)
    with sqlite3.connect(archive) as db:
        for sql in [
            "DELETE FROM ingestion_attempts",
            "UPDATE ingestion_attempts SET outcome='running'",
            "UPDATE snapshot_insertions SET inserted_at='wrong'",
            "DELETE FROM snapshot_insertions",
        ]:
            with pytest.raises(sqlite3.IntegrityError, match="immutable"):
                db.execute(sql)


def test_history_is_read_only_bounded_paginated_and_redacted(archive):
    with sqlite3.connect(archive) as db:
        db.executemany(
            (
                "INSERT INTO "
                "ingestion_attempts(source,catalog_id,query_sha256,started_at,outcome)"
                " VALUES ('SECRET_SOURCE',6251,?,?, 'running')"
            ),
            [("f" * 64, NOW.isoformat()) for _ in range(105)],
        )
    before = hashlib.sha256(archive.read_bytes()).hexdigest()
    first = service.history(archive, limit=100)
    second = service.history(archive, limit=100, before_id=first["next_before_id"])
    assert len(first["attempts"]) == 100 and first["has_more"]
    assert len(second["attempts"]) == 5 and not second["has_more"]
    assert not (
        {x["id"] for x in first["attempts"]} & {x["id"] for x in second["attempts"]}
    )
    assert "SECRET_SOURCE" not in json.dumps(first)
    assert before == hashlib.sha256(archive.read_bytes()).hexdigest()
    with pytest.raises(ValueError):
        service.history(archive, limit=101)


def v2(path, dataset):
    with sqlite3.connect(path) as db:
        db.executescript(database.INITIAL_MIGRATION.read_text())
        database.apply_snapshot_migration(db)
    process_dataset(path, 6251, dataset)


def test_migration_v2_preserves_exact_rows_and_recoverable_backup(tmp_path, dataset):
    source, backup, restored = [
        tmp_path / (name + ".sqlite3") for name in ["v2", "backup", "restore"]
    ]
    v2(source, dataset)
    before = rows(source, "snapshots")
    assert database.migrate(source, backup)
    assert rows(source, "snapshots") == before
    with sqlite3.connect(source) as db:
        assert database.schema_version(db) == 3
        assert db.execute("SELECT count(*) FROM snapshot_insertions").fetchone()[0] == 0
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
    database.copy_database(backup, restored)
    assert rows(restored, "snapshots") == before
    assert verify_archive(restored) == 1
    assert not database.migrate(source, backup)
    assert get_snapshot(source, 1)["snapshot_inserted_at"] is None


def test_migration_failure_rolls_back_schema_and_rows(tmp_path, dataset, monkeypatch):
    source = tmp_path / "v2.sqlite3"
    v2(source, dataset)
    before = rows(source, "snapshots")
    broken = tmp_path / "broken.sql"
    broken.write_text("CREATE TABLE partial (id INTEGER);\nINVALID SQL;\n")
    monkeypatch.setattr(database, "INGESTION_MIGRATION", broken)
    with pytest.raises(sqlite3.Error):
        database.migrate(source, tmp_path / "backup.sqlite3")
    assert rows(source, "snapshots") == before
    with sqlite3.connect(source) as db:
        assert database.schema_version(db) == 2
        assert (
            db.execute("SELECT name FROM sqlite_master WHERE name='partial'").fetchone()
            is None
        )


def test_backup_restore_ledger_payloads_schema_and_application(
    archive, dataset, monkeypatch, tmp_path
):
    capture(monkeypatch, dataset)
    collect(archive)
    backup, restored = tmp_path / "backup.sqlite3", tmp_path / "restore.sqlite3"
    database.copy_database(archive, backup)
    database.copy_database(backup, restored)
    assert rows(restored) == rows(archive)
    assert rows(restored, "snapshots") == rows(archive, "snapshots")
    assert get_snapshot(restored, 1) == get_snapshot(archive, 1)
    assert verify_archive(restored) == 1
    monkeypatch.setenv("ORBITIQ_DATABASE_PATH", str(restored))
    with TestClient(create_app()) as client:
        assert client.get("/api/snapshots/1").status_code == 200
        assert client.get("/api/satellites/6251/snapshots").status_code == 200
        assert (
            client.get(
                "/api/comparisons", params={"first_id": 1, "second_id": 1}
            ).status_code
            == 200
        )
    before = archive.read_bytes()
    with pytest.raises(FileExistsError):
        database.copy_database(backup, archive)
    assert archive.read_bytes() == before


def test_failed_restore_and_backup_leave_source_unchanged(archive, tmp_path):
    before = archive.read_bytes()
    corrupt = tmp_path / "corrupt.sqlite3"
    corrupt.write_bytes(b"not-a-database")
    target = tmp_path / "target.sqlite3"
    with pytest.raises(sqlite3.Error):
        database.copy_database(corrupt, target)
    assert not target.exists() and archive.read_bytes() == before
    existing = tmp_path / "existing.sqlite3"
    existing.write_bytes(b"PRESERVE")
    with pytest.raises(FileExistsError):
        database.copy_database(archive, existing)
    assert existing.read_bytes() == b"PRESERVE" and archive.read_bytes() == before


def test_new_status_has_no_ingestion_history_and_no_hidden_collection(
    archive, monkeypatch
):
    monkeypatch.setattr(
        celestrak, "fetch_dataset", lambda *a, **k: pytest.fail("No collection allowed")
    )
    with TestClient(create_app()) as client:
        result = client.get("/api/readiness").json()
        assert result["components"]["ingestion"]["code"] == "no_ingestion_history"
        for route in [
            "/api/health",
            "/api/snapshots",
            "/api/discovery/satellites",
            "/api/satellites/6251/snapshots",
        ]:
            assert client.get(route).status_code == 200
    assert rows(archive) == []


def test_monitoring_dedup_does_not_refresh_orbital_epoch(archive, dataset, monkeypatch):
    capture(monkeypatch, dataset)
    collect(archive)
    later = NOW + timedelta(hours=2)
    capture(monkeypatch, replace(dataset, retrieved_at=later))
    collect(archive, later)
    result = assess(now=later)["components"]
    ingestion = result["ingestion"]
    assert ingestion["latest_payload_outcome"] == "deduplicated"
    assert ingestion["last_successful_acquisition_at"] == later.isoformat()
    assert result["orbital_data"]["latest_retrieval_at"] == NOW.isoformat()
    assert (
        ingestion["orbital_freshness_state"] == "stale"
        and ingestion["code"] == "stale_data"
    )
    assert datetime.fromisoformat(
        ingestion["last_snapshot_insertion_at"]
    ) == datetime.fromisoformat(get_snapshot(archive, 1)["snapshot_inserted_at"])


def test_monitoring_failure_preserves_older_records_and_safe_error_category(
    archive, dataset, monkeypatch
):
    capture(monkeypatch, dataset)
    collect(archive)
    monkeypatch.undo()
    monkeypatch.setenv("ORBITIQ_DATABASE_PATH", str(archive))
    with pytest.raises(IngestionError):
        collect(archive, NOW + timedelta(hours=2), transport=transport(status=503))
    status = assess(now=NOW + timedelta(hours=2, seconds=1))["components"]["ingestion"]
    assert status["code"] == "recent_failure_with_stored_data"
    assert status["latest_attempt_failed"] and status["consecutive_failures"] == 1
    assert status["last_error_category"] == "upstream_http"
    assert get_snapshot(archive, 1) is not None


@pytest.mark.parametrize("stamp", ["invalid", "", None, "2099-01-01T00:00:00Z"])
def test_monitoring_missing_or_invalid_times_never_claim_success(archive, stamp):
    with sqlite3.connect(archive) as db:
        db.execute(
            (
                "INSERT INTO "
                "ingestion_attempts(source,catalog_id,query_sha256,started_at,completed_at,outcome)"
                " VALUES ('celestrak',6251,?, ?, ?, 'acquisition_failed')"
            ),
            ("a" * 64, stamp or "", stamp),
        )
    result = assess(now=NOW)["components"]["ingestion"]
    assert result["status"] == "unknown"
    assert result["code"] == "ingestion_timestamp_unknown"


def test_monitoring_queries_are_indexed_and_bounded(archive, dataset, monkeypatch):
    capture(monkeypatch, dataset)
    collect(archive)
    statements = []
    original = sqlite3.connect

    def monitored(*args, **kwargs):
        db = original(*args, **kwargs)
        db.set_trace_callback(statements.append)
        return db

    monkeypatch.setattr(sqlite3, "connect", monitored)
    status = assess(now=NOW)["components"]["ingestion"]
    assert status["last_attempt_id"] == 1
    sql = " ".join(statements).upper()
    assert "COUNT(" not in sql and "INTEGRITY_CHECK" not in sql
    assert "ORDER BY ID DESC LIMIT 1" in sql
    with original(archive) as db:
        for condition in [
            "acquired_at IS NOT NULL",
            "validated_at IS NOT NULL",
            "outcome = 'inserted'",
        ]:
            plan = db.execute(
                "EXPLAIN QUERY PLAN SELECT id FROM ingestion_attempts WHERE "
                + condition
                + " ORDER BY id DESC LIMIT 1"
            ).fetchall()
            assert "INDEX ingestion_" in str(plan)


def test_recovery_runbook_command_verifies_real_tables_and_cleans_only_owned_target(
    archive, dataset, monkeypatch, tmp_path
):
    from orbitiq.maintenance.recovery import rehearse

    capture(monkeypatch, dataset)
    collect(archive)
    result = rehearse(archive, tmp_path / "new-recovery")
    assert result["status"] == "passed" and result["verified_snapshots"] == 1
    assert result["source_at_backup"]["tables"]["ingestion_attempts"]["rows"] == 1
    assert result["source_at_backup"] == result["restored"]
    assert (tmp_path / "new-recovery" / "backup.sqlite3").exists()
    assert not (tmp_path / "new-recovery" / "restored.sqlite3").exists()
    before = archive.read_bytes()
    with pytest.raises(FileExistsError):
        rehearse(archive, tmp_path / "new-recovery")
    assert archive.read_bytes() == before


def test_monitoring_recent_success_from_synthetic_current_epoch(
    archive, dataset, monkeypatch
):
    record = json.loads(dataset.raw)[0]
    record["OBJECT_NAME"] = "SYNTHETIC CURRENT EPOCH TEST ONLY"
    record["EPOCH"] = NOW.replace(tzinfo=None).isoformat()
    capture(monkeypatch, replace(dataset, raw=json.dumps([record]).encode()))
    collect(archive)
    status = assess(now=NOW)["components"]["ingestion"]
    assert status["status"] == "healthy" and status["code"] == "recent_success"
    assert status["latest_payload_outcome"] == "inserted"
    assert status["stored_orbital_epoch_age_seconds"] == 0


def test_provider_http_error_requires_review_even_after_cooldown(archive):
    with pytest.raises(IngestionError):
        collect(archive, transport=transport(status=503))
    permitted = datetime.fromisoformat(
        rows(archive, "collection_gate")[0]["next_allowed_at"]
    )
    with pytest.raises(IngestionError) as caught:
        collect(archive, permitted)
    assert caught.value.category == "retry_budget"
    assert len(rows(archive)) == 1


def test_legacy_schema_browsing_works_but_collection_requires_migration(
    tmp_path, dataset, monkeypatch
):
    source = tmp_path / "v2.sqlite3"
    v2(source, dataset)
    monkeypatch.setenv("ORBITIQ_DATABASE_PATH", str(source))
    assert (
        assess(now=NOW)["components"]["ingestion"]["code"]
        == "ingestion_schema_required"
    )
    with pytest.raises(IngestionError, match="schema 3"):
        collect(source, NOW + timedelta(hours=3))
    assert verify_archive(source) == 1


@pytest.mark.parametrize(
    "value",
    [
        "http://celestrak.org/NORAD/elements/gp.php",
        "https://user:SECRET@celestrak.org/NORAD/elements/gp.php",
    ],
)
def test_collection_rejects_configuration_without_request_or_secret_echo(
    archive, monkeypatch, value
):
    monkeypatch.setenv("ORBITIQ_CELESTRAK_URL", value)
    monkeypatch.setattr(
        celestrak, "fetch_dataset", lambda *a, **k: pytest.fail("Network forbidden")
    )
    with pytest.raises(IngestionError) as caught:
        collect(archive)
    assert caught.value.category == "configuration" and "SECRET" not in str(
        caught.value
    )
    assert rows(archive) == []
