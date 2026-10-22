"""Offline provider failure/restart probes; synthetic reference payloads only."""

import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from orbitiq.database import initialize, validate
from orbitiq.ingestion import celestrak, collection
from orbitiq.main import create_app
from orbitiq.services.readiness import assess
from orbitiq.storage import get_snapshot, verify_archive

RECORD = json.loads((Path(__file__).parent / "fixtures/vallado-leo.json").read_text())[
    0
]["omm"]
NOW = datetime(2030, 1, 1, tzinfo=UTC)


@pytest.fixture
def archive(tmp_path, monkeypatch):
    path = tmp_path / "synthetic-only.sqlite3"
    initialize(path)
    monkeypatch.setenv("ORBITIQ_DATABASE_PATH", str(path))
    monkeypatch.delenv("ORBITIQ_CELESTRAK_URL", raising=False)
    return path


def collect(path, raw, at=NOW):
    return collection.collect(
        path,
        6251,
        now=lambda: at,
        jitter=lambda: 0,
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                stream=httpx.ByteStream(raw),
                headers={"content-type": "application/json"},
            )
        ),
    )


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"[]",
        b"[{",
        json.dumps(
            [RECORD, {**RECORD, "EPOCH": "2006-06-24T19:46:43.980096"}]
        ).encode(),
        json.dumps([RECORD, {"NORAD_CAT_ID": 6251}]).encode(),
        json.dumps([{**RECORD, "MEAN_MOTION": -1}]).encode(),
    ],
    ids=[
        "empty-body",
        "empty-list",
        "malformed",
        "known-and-new",
        "partial",
        "invalid",
    ],
)
def test_whole_response_rejection_preserves_previous_snapshot_and_history(archive, raw):
    good = collect(archive, json.dumps([RECORD]).encode())
    original = get_snapshot(archive, good["snapshot_id"])
    with pytest.raises(celestrak.IngestionError):
        collect(archive, raw, NOW + timedelta(hours=2))
    assert get_snapshot(archive, good["snapshot_id"]) == original
    history = collection.history(archive)["attempts"]
    assert history[0]["outcome"] in {"parsing_failed", "validation_failed"}
    assert history[0]["snapshot_id"] is None and history[0]["request_count"] == 1
    assert history[1]["outcome"] == "inserted"
    assert verify_archive(archive) == 1


def test_older_epoch_appends_history_without_rewriting_newer_payload(archive):
    original = collect(archive, json.dumps([RECORD]).encode())
    preserved = get_snapshot(archive, original["snapshot_id"])
    # Altered metadata is a TEST ONLY input; no fabricated observation is published.
    older = {**RECORD, "EPOCH": "2006-06-24T19:46:43.980096"}
    result = collect(archive, json.dumps([older]).encode(), NOW + timedelta(hours=2))
    assert result["newly_inserted"] and result["snapshot_id"] != original["snapshot_id"]
    assert get_snapshot(archive, original["snapshot_id"]) == preserved
    assert (
        get_snapshot(archive, result["snapshot_id"])["orbital_epoch"]
        < preserved["orbital_epoch"]
    )
    readiness = assess(now=NOW + timedelta(hours=3))
    assert readiness["components"]["orbital_data"]["freshness"]["state"] == "stale"
    assert verify_archive(archive) == 2


def test_interrupted_stream_restart_and_exact_retry_preserve_audit(archive):
    raw = json.dumps([RECORD]).encode()
    first = collect(archive, raw)
    preserved = get_snapshot(archive, first["snapshot_id"])
    calls = []

    class Interrupted(httpx.SyncByteStream):
        def __iter__(self):
            yield raw[:30]
            raise httpx.ReadError("private response fragment must not escape")

    def interrupted(request):
        calls.append(request.url)
        return httpx.Response(
            200, stream=Interrupted(), headers={"content-type": "application/json"}
        )

    failed_at = NOW + timedelta(hours=2)
    with pytest.raises(celestrak.IngestionError) as error:
        collection.collect(
            archive,
            6251,
            now=lambda: failed_at,
            jitter=lambda: 0,
            transport=httpx.MockTransport(interrupted),
        )
    assert error.value.category == "network" and "private" not in str(error.value)
    assert len(calls) == 1
    assert get_snapshot(archive, first["snapshot_id"]) == preserved
    assert collection.history(archive)["attempts"][0]["outcome"] == "acquisition_failed"
    # A genuinely new ASGI app and reopened connections retain archive and cooldown.
    with TestClient(create_app()) as client:
        assert client.get("/api/health").status_code == 200
        assert client.get("/api/ready").status_code == 200
        assert len(client.get("/api/snapshots").json()["snapshots"]) == 1
    with pytest.raises(celestrak.IngestionError, match="permitted"):
        collect(archive, raw, failed_at + timedelta(minutes=1))
    recovered = collect(archive, raw, failed_at + timedelta(hours=2))
    assert recovered["outcome"] == "deduplicated"
    assert recovered["snapshot_id"] == first["snapshot_id"]
    assert [a["outcome"] for a in collection.history(archive)["attempts"]] == [
        "deduplicated",
        "acquisition_failed",
        "inserted",
    ]
    assert get_snapshot(archive, first["snapshot_id"]) == preserved
    with closing(sqlite3.connect(archive)) as db:
        validate(db)
    assert verify_archive(archive) == 1


def test_interrupt_after_snapshot_insert_rolls_back_and_reconciles(
    archive, monkeypatch
):
    raw = json.dumps([RECORD]).encode()
    original = celestrak.process_dataset
    interrupted = False

    def stop_before_commit(*args, **kwargs):
        nonlocal interrupted
        result = original(*args, **kwargs)
        interrupted = True
        raise KeyboardInterrupt(result)

    with monkeypatch.context() as patch:
        patch.setattr(celestrak, "process_dataset", stop_before_commit)
        with pytest.raises(KeyboardInterrupt):
            collect(archive, raw)
    assert interrupted and verify_archive(archive) == 0
    assert collection.history(archive)["attempts"][0]["outcome"] == "running"
    with pytest.raises(celestrak.IngestionError) as error:
        collect(archive, raw, NOW + timedelta(minutes=1))
    assert error.value.category == "concurrent"
    with pytest.raises(celestrak.IngestionError) as error:
        collect(archive, raw, NOW + timedelta(minutes=3))
    assert error.value.category == "cooldown"
    assert collection.history(archive)["attempts"][0]["outcome"] == "interrupted"
    recovered = collect(archive, raw, NOW + timedelta(hours=2))
    assert recovered["outcome"] == "inserted" and verify_archive(archive) == 1
    assert [a["outcome"] for a in collection.history(archive)["attempts"]] == [
        "inserted",
        "interrupted",
    ]


def test_missing_gate_refuses_collection_with_safe_error_and_no_request(archive):
    with closing(sqlite3.connect(archive)) as db, db:
        db.execute("DELETE FROM collection_gate")
    before = archive.read_bytes()
    calls = []

    def forbidden(request):
        calls.append(request)
        raise AssertionError("Invalid storage must never contact the provider")

    with pytest.raises(celestrak.IngestionError) as error:
        collection.collect(
            archive, 6251, transport=httpx.MockTransport(forbidden), now=lambda: NOW
        )
    assert error.value.category == "storage"
    assert "gate" in str(error.value).lower()
    assert calls == [] and collection.history(archive)["attempts"] == []
    assert archive.read_bytes() == before
