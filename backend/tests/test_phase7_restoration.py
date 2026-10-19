"""Read-only reconstruction API contract, using isolated reference-only data."""

import hashlib
from datetime import UTC, datetime, timedelta

import pytest
from orbitiq.maintenance.recovery import fingerprint
from orbitiq.orbits import earth_orientation
from orbitiq.orbits.earth_orientation import TransformationError

pytest_plugins = ["test_phase5"]


def test_restoration_sequence_uses_fixed_ids_and_preserves_entire_archive(archive):
    client, path, first, second, _, record = archive
    before = fingerprint(path)
    byte_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    for sid in [first, second]:
        response = client.get("/api/snapshots", params={"snapshot_id": sid, "limit": 1})
        assert response.status_code == 200
        rows = response.json()["snapshots"]
        assert len(rows) == 1 and rows[0]["id"] == sid
        assert rows[0]["catalog_id"] == 6251
        detail = client.get(f"/api/snapshots/{sid}")
        assert detail.status_code == 200
        assert detail.json()["response_sha256"] == rows[0]["response_sha256"]
    at = (
        datetime.fromisoformat(record["EPOCH"]).replace(tzinfo=UTC) + timedelta(hours=1)
    ).isoformat()
    comparison = client.get(
        "/api/comparisons",
        params={"first_id": first, "second_id": second, "at": at, "frame": "ITRS"},
    )
    assert comparison.status_code == 200
    result = comparison.json()
    assert result["first"]["id"] == first and result["second"]["id"] == second
    assert result["state_comparison"]["status"] == "complete"
    assert result["state_comparison"]["frame"] == "ITRS"
    assert fingerprint(path) == before
    assert hashlib.sha256(path.read_bytes()).hexdigest() == byte_hash


def test_missing_shared_source_never_returns_latest_available_record(archive):
    client, path, *_ = archive
    before = fingerprint(path)
    result = client.get("/api/snapshots", params={"snapshot_id": 99999, "limit": 1})
    assert result.status_code == 200 and result.json()["snapshots"] == []
    assert client.get("/api/snapshots/99999").status_code == 404
    assert fingerprint(path) == before


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_shared_read_routes_do_not_expose_anonymous_permanent_storage(archive, method):
    client, path, first, *_ = archive
    before = fingerprint(path)
    for endpoint in ["/api/snapshots", f"/api/snapshots/{first}", "/api/comparisons"]:
        assert (
            client.request(
                method, endpoint, json={"title": "must not persist"}
            ).status_code
            == 405
        )
    assert (
        client.request(
            method, "/api/investigations", json={"title": "must not persist"}
        ).status_code
        == 404
    )
    assert fingerprint(path) == before


def test_restored_terrestrial_request_keeps_strict_resource_errors(
    archive, monkeypatch
):
    client, path, first, _, _, record = archive
    before = fingerprint(path)

    def unavailable():
        raise TransformationError(
            "eop_unavailable", "Required local resources unavailable", 503
        )

    monkeypatch.setattr(earth_orientation, "resources", unavailable)
    response = client.get(
        f"/api/snapshots/{first}/earth-fixed", params={"at": record["EPOCH"] + "Z"}
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "eop_unavailable"
    assert "position_km" not in response.json()
    assert fingerprint(path) == before
