"""Report contracts use isolated reference-derived data, never the normal archive."""

import copy
import hashlib
import json
from datetime import datetime, timedelta

import pytest
from orbitiq.maintenance.recovery import fingerprint
from orbitiq.orbits import earth_orientation
from orbitiq.orbits.earth_orientation import TransformationError
from orbitiq.services import analysis, reports

pytest_plugins = ["test_phase5"]


def definition(client, sid, mode="snapshot", other=None, frame="TEME"):
    def reference(identity):
        s = client.get(f"/api/snapshots/{identity}").json()
        return {
            "snapshot_id": s["id"],
            **{
                k: s[k]
                for k in [
                    "catalog_id",
                    "orbital_epoch",
                    "retrieved_at",
                    "response_sha256",
                ]
            },
        }

    source = reference(sid)
    value = {"schema_version": 1, "mode": mode, "source": source, "frame": frame}
    if mode != "snapshot":
        value["at"] = source["orbital_epoch"]
    if mode == "comparison":
        value.update(comparison_source=reference(other), category="all")
    if mode == "ground-track":
        value.update(
            frame="ITRS",
            track={
                "start": value["at"],
                "duration_minutes": 2,
                "step_seconds": 60,
                "selected_index": 0,
            },
        )
    return value


def export(client, value):
    return client.get(
        "/api/investigation-reports",
        params={"definition": json.dumps(value, separators=(",", ":"))},
    )


@pytest.mark.parametrize("mode", ["snapshot", "position", "ground-track", "comparison"])
def test_report_uses_exact_sources_and_keeps_archive_intact(archive, mode):
    client, path, first, second, *_ = archive
    before, byte_hash = fingerprint(path), hashlib.sha256(path.read_bytes()).hexdigest()
    value = definition(
        client, first, mode, second, "ITRS" if mode == "comparison" else "TEME"
    )
    response = export(client, value)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/json"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    r = response.json()
    assert r["schema_version"] == r["template_version"] == 1
    assert r["kind"] == "orbitiq_investigation_report" and r["status"] == "complete"
    assert r["report_id"] in response.headers["content-disposition"]
    assert r["investigation"]["id"].startswith("configuration-sha256:")
    assert r["investigation"]["created_at"] is None
    assert r["investigation"]["saved_record_id"] is None
    assert r["investigation"]["saved_metadata_status"] == "browser_only_excluded"
    assert datetime.fromisoformat(r["generated_at"]).tzinfo is not None
    assert r["validation"]["prediction_uncertainty"] == "unquantified"
    assert r["validation"]["independent_observation_validation"] == "blocked"
    assert r["validation"]["status"] == "validated_with_warnings"
    assert r["validation"]["report_generation_is_scientific_certification"] is False
    for i, source in enumerate(r["sources"]):
        expected = value["source" if i == 0 else "comparison_source"]
        assert source["reference"]["snapshot_id"] == expected["snapshot_id"]
        assert source["payload_hash"]["value"] == expected["response_sha256"]
        assert source["payload_hash"]["algorithm"] == "SHA-256"
        assert "body bytes" in source["payload_hash"]["scope"]
        assert source["source_authenticity"] == "not_independently_verified"
        assert source["publication_at"] is None and source["observation_at"] is None
        assert source["element_units"]["MEAN_MOTION"] == "rev/day"
        assert source["source_frame"] == "TEME"
    assert r["calculation"]["status"] == (
        "not_requested" if mode == "snapshot" else "complete"
    )
    if mode == "position":
        direct = client.get(
            f"/api/snapshots/{first}/position", params={"at": value["at"]}
        ).json()
        assert r["calculation"]["data"]["position_km"] == direct["position_km"]
        assert r["calculation"]["data"]["velocity_km_s"] == direct["velocity_km_s"]
        assert r["calculation"]["data"]["units"] == direct["units"]
    if mode in {"ground-track", "comparison"}:
        point = (
            r["calculation"]["data"]["points"][0]
            if mode == "ground-track"
            else r["calculation"]["data"]["state_comparison"]["first"]
        )
        assert point["frame"] == "ITRS"
        assert point["earth_orientation"]["policy"] == "measured_or_predicted"
        assert len(point["earth_orientation"]["sha256"]) == 64
        assert len(point["earth_orientation"]["leap_seconds_sha256"]) == 64
        assert point["teme"]["calculated_at"]
        assert point["units"]["position"] == "km"
    assert fingerprint(path) == before
    assert hashlib.sha256(path.read_bytes()).hexdigest() == byte_hash


def test_configuration_id_normalizes_timezones_but_export_id_is_new(archive):
    client, _, first, *_ = archive
    value = definition(client, first, "position")
    a = export(client, value).json()
    value["at"] = datetime.fromisoformat(value["at"]).isoformat().replace("+00:00", "Z")
    b = export(client, value).json()
    assert a["investigation"]["id"] == b["investigation"]["id"]
    assert a["report_id"] != b["report_id"]
    value["at"] = (
        datetime.fromisoformat(value["at"]) + timedelta(minutes=1)
    ).isoformat()
    assert (
        export(client, value).json()["investigation"]["id"] != a["investigation"]["id"]
    )


@pytest.mark.parametrize(
    "field,new",
    [
        ("catalog_id", 123),
        ("response_sha256", "0" * 64),
        ("retrieved_at", "2000-01-01T00:00:00Z"),
        ("orbital_epoch", "2000-01-01T00:00:00Z"),
    ],
)
def test_mismatched_reference_is_refused_without_replacement(archive, field, new):
    client, _, first, *_ = archive
    value = definition(client, first)
    value["source"][field] = new
    response = export(client, value)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "report_source_mismatch"
    assert "sources" not in response.json()


def test_missing_and_other_comparison_source_refused(archive):
    client, _, first, second, *_ = archive
    value = definition(client, first, "comparison", second)
    value["comparison_source"]["snapshot_id"] = 999999
    assert export(client, value).status_code == 404
    value = definition(client, first)
    value["source"]["snapshot_id"] = 999999
    assert export(client, value).status_code == 404


@pytest.mark.parametrize("mode", ["position", "ground-track", "comparison"])
def test_unavailable_calculations_are_explicit_not_zero_vectors(archive, mode):
    client, _, first, second, *_ = archive
    value = definition(client, first, mode, second)
    value["at"] = "2100-01-01T00:00:00Z"
    if mode == "ground-track":
        value["track"]["start"] = value["at"]
    response = export(client, value)
    assert response.status_code == 200
    r = response.json()
    assert r["status"] == "partial" and r["calculation"]["status"] == "unavailable"
    assert r["calculation"]["errors"]
    if mode != "comparison":
        assert r["calculation"]["data"] is None
    else:
        assert r["calculation"]["data"]["state_comparison"]["separation_km"] is None


def test_strict_eop_failure_is_a_partial_report_with_no_track(archive, monkeypatch):
    client, _, first, *_ = archive
    monkeypatch.setenv("ORBITIQ_EOP_POLICY", "measured_only")

    def missing():
        raise TransformationError(
            "eop_unavailable", "Required local resources unavailable", 503
        )

    monkeypatch.setattr(earth_orientation, "resources", missing)
    r = export(client, definition(client, first, "ground-track")).json()
    assert r["status"] == "partial" and r["calculation"]["data"] is None
    assert r["calculation"]["errors"][0]["code"] == "eop_unavailable"
    assert r["methodology"]["configured_eop_policy"] == "measured_only"
    assert "position_km" not in json.dumps(r)


def test_element_only_and_self_comparison_are_honest(archive):
    client, _, first, *_ = archive
    value = definition(client, first, "comparison", first)
    value["at"] = None
    r = export(client, value).json()
    assert r["calculation"]["status"] == "not_requested"
    assert r["calculation"]["data"]["is_self_comparison"]
    assert r["calculation"]["data"]["state_comparison"]["status"] == "not_requested"
    assert r["methodology"]["eop_applicability"] == "not_applicable"


@pytest.mark.parametrize(
    "bad", [None, {}, [], {"schema_version": 1}, {"mode": "private-investigation"}]
)
def test_empty_unsupported_or_noninvestigation_definitions_rejected(archive, bad):
    assert export(archive[0], bad).status_code == 422


@pytest.mark.parametrize(
    "key,value",
    [
        ("owner_id", "another-user"),
        ("title", "private title"),
        ("description", "secret note"),
        ("saved_record_id", "uuid"),
    ],
)
def test_no_private_server_record_or_browser_metadata_can_be_requested(
    archive, key, value
):
    client, _, first, *_ = archive
    v = definition(client, first)
    v[key] = value
    response = export(client, v)
    assert response.status_code == 422
    assert value not in response.text


@pytest.mark.parametrize(
    "field,value",
    [
        ("snapshot_id", 0),
        ("snapshot_id", True),
        ("snapshot_id", "1"),
        ("snapshot_id", 9007199254740992),
        ("response_sha256", "not-a-hash"),
        ("orbital_epoch", 123),
        ("orbital_epoch", "2020-01-01T00:00:00"),
        ("orbital_epoch", "2020-01-01T00:00:60Z"),
    ],
)
def test_malformed_identifiers_hashes_and_times_rejected(archive, field, value):
    client, _, first, *_ = archive
    v = definition(client, first)
    v["source"][field] = value
    assert export(client, v).status_code == 422


def test_duplicate_nonfinite_and_oversized_json_rejected(archive):
    client = archive[0]
    for value in [
        '{"mode":"snapshot","mode":"comparison"}',
        '{"source":NaN}',
        "[" * 1100,
        " " * 2049,
    ]:
        assert (
            client.get(
                "/api/investigation-reports", params={"definition": value}
            ).status_code
            == 422
        )


def test_track_bounds_and_selected_timestamp_rejected(archive):
    client, _, first, *_ = archive
    v = definition(client, first, "ground-track")
    for changes in [
        {"duration_minutes": 1440, "step_seconds": 10},
        {"selected_index": 9},
        {"selected_index": 1},
    ]:
        candidate = copy.deepcopy(v)
        candidate["track"].update(changes)
        assert export(client, candidate).status_code == 422


def test_changed_source_during_generation_refuses_report(archive, monkeypatch):
    client, _, first, *_ = archive
    value = definition(client, first, "position")
    original = reports.checked_source
    calls = 0

    def changed(path, reference):
        nonlocal calls
        calls += 1
        if calls > 1:
            raise analysis.AnalysisError(
                409, "report_source_mismatch", "Archive changed"
            )
        return original(path, reference)

    monkeypatch.setattr(reports, "checked_source", changed)
    assert export(client, value).status_code == 409


def test_no_write_methods_or_hidden_persistence(archive):
    client, path, first, *_ = archive
    before = fingerprint(path)
    for method in ["POST", "PUT", "PATCH", "DELETE"]:
        assert (
            client.request(
                method, "/api/investigation-reports", json=definition(client, first)
            ).status_code
            == 405
        )
    assert fingerprint(path) == before


def test_boolean_schema_is_not_a_supported_version(archive):
    client, _, first, *_ = archive
    value = definition(client, first)
    value["schema_version"] = True
    assert export(client, value).status_code == 422


def test_selected_nonzero_sample_is_captured_at_exact_time(archive):
    client, _, first, *_ = archive
    value = definition(client, first, "ground-track")
    value["track"]["selected_index"] = 1
    value["at"] = (
        datetime.fromisoformat(value["at"]) + timedelta(seconds=60)
    ).isoformat()
    report = export(client, value).json()
    assert report["status"] == "complete"
    selected = report["calculation"]["data"]["points"][1]
    assert datetime.fromisoformat(selected["at"]) == datetime.fromisoformat(value["at"])
    assert report["investigation"]["definition"]["track"]["selected_index"] == 1


def test_wrong_calculation_lineage_refuses_export(archive, monkeypatch):
    client, _, first, *_ = archive
    original = analysis.position_from_snapshot

    def wrong(*args):
        data = original(*args)
        data["response_sha256"] = "0" * 64
        return data

    monkeypatch.setattr(analysis, "position_from_snapshot", wrong)
    assert export(client, definition(client, first, "position")).status_code == 409


def test_nonfinite_output_and_export_size_limit_fail_safely(archive, monkeypatch):
    from orbitiq.api import reports as api

    client, _, first, *_ = archive
    value = definition(client, first, "position")
    original = api.build_report

    def invalid(*args):
        report = original(*args)
        report.calculation.data["position_km"][0] = float("nan")
        return report

    monkeypatch.setattr(api, "build_report", invalid)
    response = export(client, value)
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "report_invalid"
    assert "NaN" not in response.text and str(archive[1]) not in response.text
    monkeypatch.setattr(api, "build_report", original)
    monkeypatch.setattr(api, "MAX_REPORT_BYTES", 100)
    response = export(client, value)
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "report_too_large"


def test_corrupt_source_is_not_exportable_or_silently_repaired(archive):
    from test_phase5 import corrupt

    client, path, first, *_ = archive
    value = definition(client, first)
    corrupt(path, first, "response_sha256", "0" * 64)  # Isolated fixture only.
    before = path.read_bytes()
    response = export(client, value)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "snapshot_invalid"
    assert "sources" not in response.json() and str(path) not in response.text
    assert path.read_bytes() == before
