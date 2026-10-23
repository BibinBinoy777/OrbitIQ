"""Real API/shared frontend fixtures; isolated public reference-derived data only.

Regenerate deliberately: ORBITIQ_UPDATE_HISTORY_FIXTURE=1 uv run pytest
backend/tests/test_history_contract.py. Never target the application archive.
"""

import copy
import hashlib
import json
import os
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from orbitiq import database, storage
from orbitiq.api.history import router
from orbitiq.api.history_schemas import HistoricalAnalysisEnvelope
from orbitiq.main import create_app
from orbitiq.orbits.elements import Elements
from orbitiq.services import history, investigations

FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "frontend/src/test-fixtures/history-windows.json"
)
NOW = datetime(2026, 10, 20, 12, 0, 0, 123456, tzinfo=UTC)


class FixedClock(datetime):
    @classmethod
    def now(cls, tz=None):
        assert tz == UTC
        return NOW


@pytest.fixture
def window_reports(tmp_path, monkeypatch):
    path = tmp_path / "synthetic-history-windows.sqlite3"
    # Seed schema 2, then migrate and explicitly INSERT synthetic insertion clocks.
    # No immutable trigger is disabled and no existing record/timestamp is updated.
    with sqlite3.connect(path) as db:
        db.executescript(database.INITIAL_MIGRATION.read_text())
        database.apply_snapshot_migration(db)
    record = json.loads(
        (Path(__file__).parent / "fixtures/vallado-leo.json").read_text()
    )[0]["omm"]
    record["OBJECT_NAME"] = "E7 SYNTHETIC CONTRACT FIXTURE ONLY"
    for index in range(2):
        item = copy.deepcopy(record)
        item["EPOCH"] = (
            Elements.model_validate(record).epoch + timedelta(hours=6 * index)
        ).isoformat()
        item["RA_OF_ASC_NODE"] = 359.0 if index == 0 else 1.0
        storage.save_snapshot(
            path,
            json.dumps([item]).encode(),
            item,
            Elements.model_validate(item),
            "https://celestrak.org/NORAD/elements/gp.php?CATNR=6251&FORMAT=JSON",
            NOW - timedelta(days=3 - index),
        )
    with sqlite3.connect(path) as db:
        database.apply_sql(db, database.INGESTION_MIGRATION)
        db.executemany(
            "INSERT INTO snapshot_insertions(snapshot_id, inserted_at) VALUES (?,?)",
            [(sid, NOW.isoformat()) for sid in (1, 2)],
        )
        database.validate(db)
    monkeypatch.setenv("ORBITIQ_DATABASE_PATH", str(path))
    for key in ["ORBITIQ_EOP_POLICY", "ORBITIQ_FRESH_HOURS", "ORBITIQ_STALE_HOURS"]:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(history, "datetime", FixedClock)
    monkeypatch.setattr(investigations, "datetime", FixedClock)
    cases = {}
    with TestClient(create_app()) as client:

        def capture(name, **params):
            response = client.get(
                "/api/historical-analysis", params={"catalog_id": 6251, **params}
            )
            assert response.status_code == 200, response.text
            assert response.headers["cache-control"] == "no-store"
            cases[name] = response.json()

        capture("full")
        capture("first", limit=1)
        capture("older", limit=1, before_id=2, anchor_id=2)
        capture("single", anchor_id=1)
        # Deliberately lower only this isolated test's bounded-count budget.
        with monkeypatch.context() as bounded:
            bounded.setattr(storage, "COUNT_BOUND", 1)
            bounded.setattr(investigations, "COUNT_BOUND", 1)
            capture("unknown_count", limit=1)
        empty = tmp_path / "empty-history.sqlite3"
        database.initialize(empty)
        with monkeypatch.context() as no_data:
            no_data.setenv("ORBITIQ_DATABASE_PATH", str(empty))
            capture("empty")
        # Damage a separate fixture copy, never the seeded archive or real data.
        damaged = tmp_path / "damaged-history.sqlite3"
        database.copy_database(path, damaged)
        with sqlite3.connect(damaged) as db:
            db.execute("DROP TRIGGER snapshots_no_update")
            db.execute("UPDATE snapshots SET retrieved_at='invalid' WHERE id=1")
        with monkeypatch.context() as bad_data:
            bad_data.setenv("ORBITIQ_DATABASE_PATH", str(damaged))
            capture("invalid_nullable")
    return cases


def test_real_api_matches_shared_frontend_fixture(window_reports):
    if os.environ.get("ORBITIQ_UPDATE_HISTORY_FIXTURE") == "1":
        FIXTURE.write_text(json.dumps(window_reports, indent=2, allow_nan=False) + "\n")
    assert window_reports == json.loads(FIXTURE.read_text()), (
        "History contract drift: inspect changes before regenerating "
        "the synthetic fixture"
    )


@pytest.mark.parametrize(
    "case",
    ["full", "first", "older", "single", "unknown_count", "empty", "invalid_nullable"],
)
def test_documented_envelope_preserves_payload_and_hash(window_reports, case):
    report = window_reports[case]
    model = HistoricalAnalysisEnvelope.model_validate(report)
    assert model.model_dump() == report
    body = {key: value for key, value in report.items() if key != "report_id"}
    assert report["report_id"] == (
        "history-report-sha256:" + hashlib.sha256(history.encoded(body)).hexdigest()
    )
    assert report["request"]["anchor_id"] == report["pagination"]["anchor_id"]
    assert report["coverage"]["complete_anchored_history"] == (
        report["request"]["before_id"] is None and not report["pagination"]["has_more"]
    )
    if case == "older":
        assert report["coverage"]["complete_anchored_history"] is False
    if case == "invalid_nullable":
        assert report["points"][0]["usable"] is False
        assert report["points"][0]["reference"]["retrieved_at"] is None
    if case == "unknown_count":
        assert report["pagination"]["total_count"] is None
        assert (
            report["pagination"]["total_count_status"]
            == "unknown_exceeds_bounded_count"
        )


def test_openapi_documents_without_response_filtering():
    app = create_app()
    route = next(
        r for r in router.routes if getattr(r, "path", "") == "/historical-analysis"
    )
    assert route.response_model is None
    spec = app.openapi()
    response = spec["paths"]["/api/historical-analysis"]["get"]["responses"]["200"]
    assert response["content"]["application/json"]["schema"]["$ref"].endswith(
        "/HistoricalAnalysisEnvelope"
    )
    assert (
        spec["components"]["schemas"]["HistoryWindow"]["properties"]["limit"]["maximum"]
        == 20
    )
