"""API integration using a temporary DB and offline published SGP4 fixture."""

import hashlib
from datetime import datetime, timedelta

import pytest
from orbitiq.orbits.earth_orientation import TransformationError
from orbitiq.services import ground_tracks

pytest_plugins = ["test_phase2_api"]


def query(record, sid, seconds=120):
    start = datetime.fromisoformat(record["EPOCH"] + "+00:00")
    return {
        "snapshot_id": sid,
        "start": start.isoformat(),
        "end": (start + timedelta(seconds=seconds)).isoformat(),
        "step_seconds": 60,
    }


def test_earth_fixed_preserves_original_teme_and_source(setup_api):
    client, path, sid, record = setup_api
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    params = {"at": record["EPOCH"] + "Z"}
    original = client.get(f"/api/snapshots/{sid}/position", params=params).json()
    r = client.get(f"/api/snapshots/{sid}/earth-fixed", params=params)
    assert r.status_code == 200
    result = r.json()
    teme = result["teme"]
    for k in [
        "position_km",
        "velocity_km_s",
        "response_sha256",
        "orbital_epoch",
        "retrieved_at",
        "snapshot_id",
    ]:
        assert teme[k] == original[k]
    assert result["frame"] == "ITRS" and result["input_frame"] == "TEME"
    assert result["earth_orientation"]["status"] == "measured"
    assert result["earth_orientation"]["auto_download"] is False
    assert result["geodetic"]["height_reference"] == "WGS84 ellipsoid"
    assert len(result["position_km"]) == 3 and len(result["velocity_km_s"]) == 3
    assert -90 <= result["geodetic"]["latitude_deg"] <= 90
    assert -180 <= result["geodetic"]["longitude_deg"] < 180
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_complete_ordered_deterministic_track_and_provenance(setup_api):
    client, path, sid, record = setup_api
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    q = query(record, sid, 125)
    r = client.get("/api/satellites/6251/ground-track", params=q)
    assert r.status_code == 200
    data = r.json()
    again = client.get("/api/satellites/6251/ground-track", params=q).json()
    assert (
        data["status"] == "complete"
        and data["failure_policy"] == "reject_entire_request"
    )
    assert data["sample_count"] == 3 and len(data["points"]) == 3
    times = [p["at"] for p in data["points"]]
    assert times == sorted(times)
    assert datetime.fromisoformat(data["actual_end"]) < datetime.fromisoformat(q["end"])
    for i, p in enumerate(data["points"]):
        assert p["sample_index"] == i
        assert p["teme"]["snapshot_id"] == sid and p["teme"]["catalog_id"] == 6251
        assert p["teme"]["response_sha256"] == data["response_sha256"]
        assert p["teme"]["orbital_epoch"] == data["orbital_epoch"]
        assert p["teme"]["retrieved_at"] == data["retrieved_at"]
        assert p["geodetic"] == again["points"][i]["geodetic"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


@pytest.mark.parametrize(
    "change,code",
    [
        ({"end": "2006-06-01T00:00:00Z"}, "invalid_interval"),
        ({"end": "2006-06-27T00:00:00Z"}, "sampling_limit"),
        ({"step_seconds": 0}, "request_validation"),
        ({"step_seconds": 1.2}, "request_validation"),
        ({"frame": "ECEF"}, "request_validation"),
        ({"start": "2006-06-25T00:00:00"}, "request_validation"),
        ({"start": "1483228800"}, "request_validation"),
        ({"snapshot_id": 0}, "request_validation"),
        ({"snapshot_id": 999999}, "snapshot_not_found"),
    ],
)
def test_invalid_tracks_return_safe_errors(setup_api, change, code):
    client, path, sid, record = setup_api
    q = {**query(record, sid), **change}
    r = client.get("/api/satellites/6251/ground-track", params=q)
    assert r.status_code in [404, 422] and r.json()["error"]["code"] == code
    assert "points" not in r.json() and str(path) not in r.text


def test_unknown_satellite_identity_is_explicit(setup_api):
    client, _, sid, record = setup_api
    r = client.get("/api/satellites/123/ground-track", params=query(record, sid))
    assert r.status_code == 404 and r.json()["error"]["code"] == "satellite_not_found"


def test_failure_midway_returns_no_partial_or_fabricated_points(setup_api, monkeypatch):
    client, _, sid, record = setup_api
    original = ground_tracks.earth_fixed
    calls = []

    def fail_second(state):
        calls.append(state)
        if len(calls) == 2:
            raise TransformationError(
                "eop_unavailable", "Required resource is unavailable", 503
            )
        return original(state)

    monkeypatch.setattr(ground_tracks, "earth_fixed", fail_second)
    r = client.get("/api/satellites/6251/ground-track", params=query(record, sid))
    assert r.status_code == 503 and r.json()["error"]["code"] == "eop_unavailable"
    assert len(calls) == 2 and "points" not in r.json()


def test_antimeridian_segment_breaks(setup_api, monkeypatch):
    client, _, sid, record = setup_api
    original = ground_tracks.earth_fixed
    longitudes = iter([179, -179, -178])

    def crossing(state):
        result = original(state)
        result["geodetic"]["longitude_deg"] = next(longitudes)
        return result

    monkeypatch.setattr(ground_tracks, "earth_fixed", crossing)
    r = client.get("/api/satellites/6251/ground-track", params=query(record, sid))
    assert r.status_code == 200
    assert [p["segment_id"] for p in r.json()["points"]] == [0, 1, 1]


def test_bad_configuration_and_epoch_window(setup_api, monkeypatch):
    client, _, sid, record = setup_api
    monkeypatch.setenv("ORBITIQ_TRACK_MAX_SAMPLES", "1")
    r = client.get("/api/satellites/6251/ground-track", params=query(record, sid))
    assert r.status_code == 422 and r.json()["error"]["code"] == "sampling_limit"
    monkeypatch.setenv("ORBITIQ_TRACK_MAX_SAMPLES", "invalid")
    r = client.get("/api/satellites/6251/ground-track", params=query(record, sid))
    assert (
        r.status_code == 503 and r.json()["error"]["code"] == "sampling_configuration"
    )
    r = client.get(
        f"/api/snapshots/{sid}/earth-fixed", params={"at": "2026-10-18T00:00:00Z"}
    )
    assert r.status_code == 422 and r.json()["error"]["code"] == "epoch_window_exceeded"


def test_nonfinite_generated_output_is_rejected_by_schema(setup_api, monkeypatch):
    client, path, sid, record = setup_api
    original = ground_tracks.earth_fixed

    def broken(state):
        result = original(state)
        result["geodetic"]["latitude_deg"] = float("nan")
        return result

    monkeypatch.setattr(ground_tracks, "earth_fixed", broken)
    r = client.get(
        f"/api/snapshots/{sid}/earth-fixed", params={"at": record["EPOCH"] + "Z"}
    )
    assert r.status_code == 500 and r.json()["error"]["code"] == "response_validation"
    assert str(path) not in r.text and "NaN" not in r.text


def test_offset_track_times_are_returned_in_utc(setup_api):
    client, _, sid, record = setup_api
    q = query(record, sid)
    from datetime import timezone

    for k in ["start", "end"]:
        q[k] = (
            datetime.fromisoformat(q[k])
            .astimezone(timezone(timedelta(hours=5, minutes=30)))
            .isoformat()
        )
    r = client.get("/api/satellites/6251/ground-track", params=q)
    assert r.status_code == 200
    assert r.json()["requested_start"].endswith("+00:00")
    assert r.json()["requested_start"] == r.json()["actual_start"]


def test_propagation_failure_mid_track_returns_no_coordinates(setup_api, monkeypatch):
    from orbitiq.orbits.engine import PropagationError

    client, _, sid, record = setup_api
    original = ground_tracks.analysis.propagate
    calls = []

    def fail_second(*args):
        calls.append(args)
        if len(calls) == 2:
            raise PropagationError("SGP4 failed for this sample")
        return original(*args)

    monkeypatch.setattr(ground_tracks.analysis, "propagate", fail_second)
    r = client.get("/api/satellites/6251/ground-track", params=query(record, sid))
    assert r.status_code == 422 and r.json()["error"]["code"] == "propagation_failed"
    assert len(calls) == 2 and "points" not in r.json()


def test_missing_eop_resource_is_safe_structured_503(setup_api, monkeypatch):
    from orbitiq.orbits import earth_orientation as eo

    client, path, sid, record = setup_api

    def missing():
        raise TransformationError(
            "eop_unavailable",
            "Required local Earth-orientation resources are unavailable",
            503,
        )

    monkeypatch.setattr(eo, "resources", missing)
    r = client.get(
        f"/api/snapshots/{sid}/earth-fixed", params={"at": record["EPOCH"] + "Z"}
    )
    assert r.status_code == 503 and r.json()["error"]["code"] == "eop_unavailable"
    assert "position_km" not in r.json() and str(path) not in r.text
