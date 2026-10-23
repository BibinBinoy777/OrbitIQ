"""Cross-workflow acceptance using disposable public-reference-derived fixtures.

The altered epoch/name below are synthetic test inputs, not provider retrievals
or independent observations. No ordinary/private application archive is opened.
"""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from orbitiq.database import copy_database, initialize
from orbitiq.ingestion.celestrak import DownloadedDataset, process_dataset
from orbitiq.main import create_app
from orbitiq.maintenance.recovery import fingerprint
from orbitiq.storage import get_snapshot, verify_archive


@pytest.mark.parametrize("mode", ["position", "ground-track", "comparison"])
def test_exact_investigation_survives_new_input_restart_and_separate_restore(
    tmp_path, monkeypatch, mode
):
    path = tmp_path / "E5-SYNTHETIC-ONLY.sqlite3"
    monkeypatch.setenv("ORBITIQ_DATABASE_PATH", str(path))
    monkeypatch.setenv("ORBITIQ_ENVIRONMENT", "test")
    monkeypatch.delenv("ORBITIQ_EOP_POLICY", raising=False)
    monkeypatch.delenv("ORBITIQ_FRESH_HOURS", raising=False)
    monkeypatch.delenv("ORBITIQ_STALE_HOURS", raising=False)
    # Development startup and health never silently create the missing database.
    with TestClient(create_app()) as client:
        assert client.get("/api/health").status_code == 200
        assert client.get("/api/ready").status_code == 503
        assert not path.exists()
    initialize(path)
    record = json.loads(
        (Path(__file__).parent / "fixtures/vallado-leo.json").read_text()
    )[0]["omm"]
    catalog = record["NORAD_CAT_ID"]
    epoch = datetime.fromisoformat(record["EPOCH"]).replace(tzinfo=UTC)

    def append(hours):
        raw = json.dumps(
            [
                {
                    **record,
                    "OBJECT_NAME": "E5 SYNTHETIC ONLY",
                    "EPOCH": (epoch + timedelta(hours=hours)).isoformat(),
                }
            ]
        ).encode()
        return process_dataset(
            path,
            catalog,
            DownloadedDataset(
                raw,
                f"https://celestrak.org/NORAD/elements/gp.php?CATNR={catalog}&FORMAT=JSON",
                datetime(2030, 1, 1, tzinfo=UTC) + timedelta(hours=hours),
                200,
            ),
        )

    first, second = append(0), append(2)
    original = get_snapshot(path, first)

    def ref(client, sid):
        source = client.get(f"/api/snapshots/{sid}")
        assert source.status_code == 200
        item = source.json()
        return {
            "snapshot_id": sid,
            **{
                k: item[k]
                for k in (
                    "catalog_id",
                    "orbital_epoch",
                    "retrieved_at",
                    "response_sha256",
                )
            },
        }

    with TestClient(create_app()) as client:
        assert client.get("/api/ready").json() == {"status": "ready"}
        value = {
            "schema_version": 1,
            "mode": mode,
            "source": ref(client, first),
            "frame": "TEME",
            "at": epoch.isoformat(),
        }
        if mode == "ground-track":
            value.update(
                frame="ITRS",
                track={
                    "start": epoch.isoformat(),
                    "duration_minutes": 2,
                    "step_seconds": 60,
                    "selected_index": 0,
                },
            )
        if mode == "comparison":
            value.update(comparison_source=ref(client, second), category="all")
        response = client.get(
            "/api/investigation-reports", params={"definition": json.dumps(value)}
        )
        assert response.status_code == 200
        captured = response.json()
        assert captured["status"] == "complete"

    # A later synthetic input appears in discovery but cannot retarget the save.
    latest = append(4)
    assert latest not in (first, second)
    assert get_snapshot(path, first) == original
    before = fingerprint(path)
    for destination in (path, tmp_path / "separately-restored.sqlite3"):
        if destination != path:
            copy_database(path, destination)
            assert fingerprint(destination) == before
        monkeypatch.setenv("ORBITIQ_DATABASE_PATH", str(destination))
        with TestClient(create_app()) as client:
            assert client.get("/api/ready").status_code == 200
            listing = client.get(
                "/api/discovery/satellites", params={"catalog_id": catalog}
            ).json()
            assert [s["id"] for s in listing["snapshots"]] == [latest, second, first]
            response = client.get(
                "/api/investigation-reports", params={"definition": json.dumps(value)}
            )
            assert response.status_code == 200
            restored = response.json()
            assert restored["status"] == "complete"
            assert restored["investigation"] == captured["investigation"]
            assert restored["report_id"] != captured["report_id"]
            assert [s["reference"] for s in restored["sources"]] == [
                s["reference"] for s in captured["sources"]
            ]
            assert (
                restored["validation"]["independent_observation_validation"]
                == "blocked"
            )
            assert restored["validation"]["prediction_uncertainty"] == "unquantified"

            def states(report):
                data = report["calculation"]["data"]
                return (
                    data["points"]
                    if mode == "ground-track"
                    else [
                        data["state_comparison"][side] for side in ("first", "second")
                    ]
                    if mode == "comparison"
                    else [data]
                )

            for previous, current in zip(
                states(captured), states(restored), strict=True
            ):
                for key in ("position_km", "velocity_km_s", "at", "frame", "units"):
                    assert current[key] == previous[key]
                if mode == "ground-track":
                    # Table age is evaluated at execution, not at the saved
                    # sample instant; resources and numerical EOP stay fixed.
                    old_eop, new_eop = (
                        dict(state["earth_orientation"])
                        for state in (previous, current)
                    )
                    assert new_eop.pop("prediction_table_age_days") >= old_eop.pop(
                        "prediction_table_age_days"
                    )
                    assert new_eop == old_eop
            assert verify_archive(destination) == 3
            assert fingerprint(destination) == before
    assert fingerprint(path) == before
    with pytest.raises(FileExistsError):
        copy_database(path, tmp_path / "separately-restored.sqlite3")
    assert fingerprint(path) == before
