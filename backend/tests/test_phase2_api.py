import json
import sqlite3
from contextlib import closing
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from orbitiq.database import initialize
from orbitiq.ingestion.celestrak import ingest
from orbitiq.main import create_app
from orbitiq.orbits.engine import PropagationError
from orbitiq.storage import get_snapshot


@pytest.fixture
def setup_api(tmp_path, monkeypatch):
    path = tmp_path / "science.sqlite3"
    initialize(path)
    record = json.loads(
        (Path(__file__).parent / "fixtures/vallado-leo.json").read_text()
    )[0]["omm"]
    raw = json.dumps([record]).encode()
    transport = httpx.MockTransport(
        lambda req: httpx.Response(
            200,
            stream=httpx.ByteStream(raw),
            headers={"content-type": "application/json"},
        )
    )
    sid = ingest(path, 6251, transport=transport)
    monkeypatch.setenv("ORBITIQ_DATABASE_PATH", str(path))
    monkeypatch.delenv("ORBITIQ_FRESH_HOURS", raising=False)
    monkeypatch.delenv("ORBITIQ_STALE_HOURS", raising=False)
    with TestClient(create_app()) as client:
        yield client, path, sid, record


def test_scientific_schema_and_immutable_traceability(setup_api):
    client, path, sid, record = setup_api
    original = get_snapshot(path, sid)
    response = client.get(
        f"/api/snapshots/{sid}/position",
        params={"at": record["EPOCH"] + "Z", "frame": "TEME"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["catalog_id"] == 6251 and data["snapshot_id"] == sid
    for key in ["orbital_epoch", "retrieved_at", "source_url", "response_sha256"]:
        assert data[key] == original[key]
    assert data["kind"] == "calculated" and data["frame"] == "TEME"
    assert data["units"] == {
        "position": "km",
        "velocity": "km/s",
        "epoch_offset": "days",
    }
    assert data["uncertainty"] == {
        "status": "not_quantified",
        "covariance_available": False,
        "observation_validated": False,
    }
    assert data["freshness_info"]["state"] == "stale"
    assert data["snapshot_created_at"] == original["snapshot_inserted_at"]
    assert data["snapshot_created_at"] is not None
    assert (
        data["at"] != data["calculated_at"]
        and data["calculated_at"] != data["retrieved_at"]
    )
    assert data["snapshot_validation_status"] == original["validation_status"]
    assert data["ingestion_sgp4_version"] == original["sgp4_version"]
    assert data["validator_version"] == original["validator_version"]
    assert any("freshness is stale" in w for w in data["warnings"])
    assert get_snapshot(path, sid) == original
    schema = client.get("/openapi.json").json()["components"]["schemas"][
        "ScientificPosition"
    ]
    assert schema["properties"]["position_km"]["maxItems"] == 3
    assert "kilometres" in schema["properties"]["position_km"]["description"]


@pytest.mark.parametrize(
    "at", ["bad", "2006-06-25T00:00:00", "1483228800", "2016-12-31T23:59:60Z"]
)
def test_invalid_times_have_safe_structured_errors(setup_api, at):
    client, path, sid, _ = setup_api
    r = client.get(f"/api/snapshots/{sid}/position", params={"at": at})
    assert r.status_code == 422 and r.json()["error"]["code"] == "request_validation"
    assert str(path) not in r.text and "input" not in r.json()["detail"][0]


@pytest.mark.parametrize("frame", ["ECEF", "ECI", "ITRS", "GCRS"])
def test_unsupported_frames_are_never_silently_ignored(setup_api, frame):
    client, _, sid, record = setup_api
    r = client.get(
        f"/api/snapshots/{sid}/position",
        params={"at": record["EPOCH"] + "Z", "frame": frame},
    )
    assert r.status_code == 422 and r.json()["error"]["code"] == "request_validation"


def test_missing_snapshot_and_unknown_catalog_contract(setup_api):
    client, _, _, _ = setup_api
    r = client.get("/api/snapshots/99999")
    assert r.status_code == 404 and r.json()["detail"] == "Snapshot not found"
    assert r.json()["error"]["code"] == "snapshot_not_found"
    assert client.get("/api/satellites/123/snapshots").json() == {
        "snapshots": [],
        "has_more": False,
        "next_before_id": None,
        "order": "insertion_id_desc_not_retrieval_chronology",
        "total_count": None,
        "total_count_status": "not_computed_use_global_snapshot_browser",
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("response_sha256", "bad-hash"),
        ("source_url", "https://untrusted.invalid/SECRET"),
        ("retrieved_at", "missing"),
        ("orbital_epoch", "incorrect"),
        ("validator_version", ""),
        ("raw_response", b"corrupted"),
    ],
)
def test_corrupt_or_missing_provenance_never_produces_position(setup_api, field, value):
    client, path, sid, record = setup_api
    with closing(sqlite3.connect(path)) as db:
        db.execute("DROP TRIGGER snapshots_no_update")
        db.execute(f"UPDATE snapshots SET {field}=? WHERE id=?", (value, sid))
        db.commit()
    r = client.get(
        f"/api/snapshots/{sid}/position", params={"at": record["EPOCH"] + "Z"}
    )
    assert r.status_code == 503 and r.json()["error"]["code"] == "snapshot_invalid"
    assert str(path) not in r.text and "SECRET" not in r.text


def test_unknown_freshness_is_reported_without_positive_accuracy_claim(setup_api):
    client, path, _, _ = setup_api
    with closing(sqlite3.connect(path)) as db:
        db.execute("DROP TRIGGER snapshots_no_update")
        db.execute("UPDATE snapshots SET retrieved_at='unknown'")
        db.commit()
    r = client.get("/api/satellites/6251/snapshots")
    assert r.status_code == 200
    info = r.json()["snapshots"][0]["freshness_info"]
    assert info["state"] == "unknown" and info["accuracy_guarantee"] is False


def test_bad_threshold_configuration_is_safe(setup_api, monkeypatch):
    client, path, _, _ = setup_api
    monkeypatch.setenv("ORBITIQ_FRESH_HOURS", "nan")
    r = client.get("/api/satellites/6251/snapshots")
    assert (
        r.status_code == 503 and r.json()["error"]["code"] == "freshness_configuration"
    )
    assert str(path) not in r.text


def test_propagator_error_and_out_of_window_are_structured(setup_api, monkeypatch):
    client, _, sid, record = setup_api
    r = client.get(
        f"/api/snapshots/{sid}/position", params={"at": "2026-10-18T00:00:00Z"}
    )
    assert r.status_code == 422 and r.json()["error"]["code"] == "epoch_window_exceeded"

    def reject(*args):
        raise PropagationError("SGP4 could not calculate this orbit")

    monkeypatch.setattr("orbitiq.services.analysis.propagate", reject)
    r = client.get(
        f"/api/snapshots/{sid}/position", params={"at": record["EPOCH"] + "Z"}
    )
    assert r.status_code == 422 and r.json()["error"]["code"] == "propagation_failed"


def test_invalid_scientific_response_is_a_safe_structured_failure(
    setup_api, monkeypatch
):
    client, path, sid, record = setup_api
    monkeypatch.setattr(
        "orbitiq.services.analysis.position",
        lambda *args: {"position_km": [float("nan"), 1, 2]},
    )
    r = client.get(
        f"/api/snapshots/{sid}/position", params={"at": record["EPOCH"] + "Z"}
    )
    assert r.status_code == 500 and r.json()["error"]["code"] == "response_validation"
    assert "NaN" not in r.text and str(path) not in r.text
