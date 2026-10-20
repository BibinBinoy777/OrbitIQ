"""Production boundaries use isolated archives; no network or main-data writes."""

import asyncio
import hashlib
import json
import logging
from dataclasses import replace

import httpx
import pytest
from fastapi.testclient import TestClient
from orbitiq.database import initialize
from orbitiq.main import create_app
from orbitiq.runtime import Settings


@pytest.fixture
def production(tmp_path, monkeypatch):
    path = tmp_path / "private-archive.sqlite3"
    initialize(path)
    monkeypatch.setenv("ORBITIQ_DATABASE_PATH", str(path))
    monkeypatch.setenv("ORBITIQ_ENVIRONMENT", "production")
    monkeypatch.setenv("ORBITIQ_ALLOWED_HOSTS", "testserver")
    monkeypatch.setenv("ORBITIQ_EOP_POLICY", "measured_or_predicted")
    return path


@pytest.mark.parametrize(
    "name,value",
    [
        ("ORBITIQ_ENVIRONMENT", "unexpected"),
        ("ORBITIQ_ALLOWED_HOSTS", ""),
        ("ORBITIQ_ALLOWED_HOSTS", "*"),
        ("ORBITIQ_ALLOWED_HOSTS", "https://example.org"),
        ("ORBITIQ_ALLOWED_HOSTS", "bad\nheader"),
        ("ORBITIQ_DATABASE_PATH", "relative.sqlite3"),
        ("ORBITIQ_EOP_POLICY", ""),
        ("ORBITIQ_TRACK_MAX_SAMPLES", "1001"),
        ("ORBITIQ_TRACK_MAX_DURATION_SECONDS", "1"),
        ("ORBITIQ_FRESH_HOURS", "secret-invalid-value"),
    ],
)
def test_production_config_rejects_unsafe_settings(
    production, monkeypatch, name, value
):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError) as exc:
        create_app()
    assert "secret-invalid-value" not in str(exc.value)


def test_production_startup_refuses_missing_storage_without_creation(production):
    production.unlink()  # Only this newly created isolated fixture.
    with pytest.raises(RuntimeError, match="Production database validation failed"):
        with TestClient(create_app()):
            pass
    assert not production.exists()


def test_production_startup_probes_and_reads_preserve_archive(production):
    before = hashlib.sha256(production.read_bytes()).hexdigest()
    with TestClient(create_app()) as client:
        assert client.get("/api/ready").json() == {"status": "ready"}
        assert client.get("/api/health").status_code == 200
        assert client.get("/api/snapshots").status_code == 200
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404
    assert hashlib.sha256(production.read_bytes()).hexdigest() == before


def test_liveness_survives_dependency_outage_and_probe_redacts_paths(
    production, monkeypatch
):
    with TestClient(create_app()) as client:
        monkeypatch.setenv(
            "ORBITIQ_DATABASE_PATH", str(production.parent / "missing.sqlite3")
        )
        assert client.get("/api/health").status_code == 200
        response = client.get("/api/ready")
        assert response.status_code == 503
        assert response.json() == {"status": "unavailable"}
        assert str(production.parent) not in response.text


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_public_api_never_accepts_writes(production, method):
    before = production.read_bytes()
    with TestClient(create_app()) as client:
        for route in [
            "/api/snapshots",
            "/api/ingestion",
            "/api/eop",
            "/api/investigations",
        ]:
            assert (
                client.request(method, route, json={"source": "fake"}).status_code
                == 405
            )
    assert production.read_bytes() == before


def test_request_limits_hosts_headers_and_same_origin(production):
    with TestClient(create_app()) as client:
        assert (
            client.get("/api/health", headers={"Host": "evil.example"}).status_code
            == 400
        )
        assert client.get("/api/snapshots?q=" + "x" * 4096).status_code == 414
        assert (
            client.get("/api/health", headers={"x-large": "x" * 17000}).status_code
            == 431
        )
        assert client.request("GET", "/api/health", content="body").status_code == 413
        result = client.get("/api/health", headers={"Origin": "https://evil.example"})
        assert "access-control-allow-origin" not in result.headers
        assert result.headers["x-content-type-options"] == "nosniff"
        assert result.headers["x-frame-options"] == "DENY"
        assert result.headers["referrer-policy"] == "no-referrer"
        assert result.headers["cache-control"] == "no-store"


def test_request_logs_and_unexpected_errors_are_redacted(production, caplog):
    app = create_app()

    @app.get("/api/fault/{identifier}")
    def fail(identifier: str):
        raise RuntimeError("private /data/archive.sqlite3 secret-exception-value")

    with (
        caplog.at_level(logging.INFO, logger="orbitiq.requests"),
        TestClient(app) as client,
    ):
        response = client.get(
            "/api/fault/private-url-value?token=private-query-value",
            headers={
                "Authorization": "Bearer private-header-value",
                "x-request-id": "forged-id",
            },
        )
    assert response.status_code == 500
    records = [
        json.loads(r.message) for r in caplog.records if r.name == "orbitiq.requests"
    ]
    assert len(records) == 1
    assert records[0]["route"] == "/api/fault/{identifier}"
    assert records[0]["request_id"] == response.headers["x-request-id"]
    assert records[0]["request_id"] != "forged-id"
    assert records[0]["status"] == 500 and records[0]["duration_ms"] >= 0
    combined = json.dumps(records) + response.text
    assert all(
        s not in combined for s in ["private-", "secret-exception", "archive.sqlite3"]
    )


def test_calculation_admission_recovers_after_completion(production):
    async def scenario():
        app = create_app(replace(Settings.load(), max_calculations=1))
        entered, release = asyncio.Event(), asyncio.Event()

        @app.get("/api/snapshots/{sid}/position")
        async def unused(sid: int):
            pass

        # The route below has the same expensive-path shape but no scientific work.
        @app.get("/api/satellites/{sid}/ground-track/")
        async def slow(sid: int):
            entered.set()
            await release.wait()
            return {"completed": True}

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            first = asyncio.create_task(client.get("/api/satellites/5/ground-track/"))
            await asyncio.wait_for(entered.wait(), 2)
            busy = await client.get("/api/snapshots/1/position?at=2026-01-01T00:00:00Z")
            assert busy.status_code == 503 and busy.headers["retry-after"] == "1"
            assert (await client.get("/api/health")).status_code == 200
            release.set()
            assert (await first).status_code == 200
            assert (
                await client.get("/api/satellites/5/ground-track/")
            ).status_code == 200

    asyncio.run(scenario())
