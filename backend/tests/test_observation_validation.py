"""Synthetic arithmetic/reference fixtures only; no measured satellite observations."""

import json
from datetime import UTC, datetime, timedelta

import pytest
from orbitiq import observation_validation as science
from orbitiq import replay
from orbitiq.maintenance.observation_validation import main
from orbitiq.maintenance.recovery import fingerprint
from orbitiq.services import analysis
from orbitiq.services import observation_validation as service

pytest_plugins = ["test_phase5"]
NOW = datetime(2026, 10, 20, tzinfo=UTC)


def observations(archive, count=2, frame="TEME"):
    client, path, sid, *_ = archive
    epoch = datetime.fromisoformat(archive[-1]["EPOCH"]).replace(tzinfo=UTC)
    result = []
    for i in range(count):
        at = epoch + timedelta(minutes=i)
        predicted = analysis.position(path, sid, at)
        if frame == "ITRS":
            from orbitiq.orbits.coordinates import earth_fixed

            predicted = earth_fixed(predicted)
        result.append(
            {
                "observation_id": f"SYNTHETIC-ONLY-{i}",
                "catalog_id": 6251,
                "source_id": "isolated-reference-fixture-not-observation-provider",
                "source_record_reference": f"synthetic-arithmetic-record-{i}",
                "observed_at": at.isoformat(),
                "time_scale": "UTC",
                "frame": frame,
                "origin": "Earth center",
                "unit": "km",
                "measurement_type": "geocentric_cartesian_position",
                "data_kind": "measurement",
                "quality": "accepted",
                "position": [
                    predicted["position_km"][0] + 3,
                    predicted["position_km"][1] - 4,
                    predicted["position_km"][2],
                ],
            }
        )
    return result


def raw(records):
    return json.dumps(
        {
            "kind": "orbitiq_observation_input",
            "schema_version": 1,
            "observations": records,
        }
    ).encode()


def capture(archive, tmp_path, records=None):
    target = tmp_path / ("a" * 32)
    report = service.create(
        (archive[1], archive[2]),
        raw(records if records is not None else observations(archive)),
        target,
        now=NOW,
    )
    return target, report


def test_cartesian_residual_literal_pythagorean_oracle():
    assert science.residual([10, 20, 30], [13, 16, 30]) == {
        "xyz_km": [3, -4, 0],
        "magnitude_km": 5,
        "sign": "observed_minus_predicted",
    }


def test_rac_right_handed_reference_and_degeneracy():
    r = science.rac([3, -4, 5], [7000, 0, 0], [0, 7, 0], "TEME")
    assert [r[k] for k in ("radial_km", "along_track_km", "cross_track_km")] == [
        3,
        -4,
        5,
    ]
    assert (
        science.rac([0, 0, 0], [1, 0, 0], [1, 0, 0], "TEME")["status"] == "unavailable"
    )
    assert (
        science.rac([0, 0, 0], [1, 0, 0], [0, 1, 0], "ITRS")["status"] == "unavailable"
    )


def test_statistics_independent_hand_calculated_oracle():
    values = [
        science.residual([0, 0, 0], [3, 4, 0]),
        science.residual([0, 0, 0], [-3, 4, 0]),
    ]
    s = science.statistics(values)
    assert s["axes"]["x"] == {
        "bias": 0,
        "mae": 3,
        "rmse": pytest.approx(3),
        "maximum_absolute": 3,
        "median_absolute": 3,
        "population_standard_deviation": pytest.approx(3),
    }
    assert (
        s["axes"]["y"]["bias"] == 4
        and s["axes"]["y"]["population_standard_deviation"] == 0
    )
    assert s["position_norm"]["rmse"] == pytest.approx(5)
    assert s["position_norm"]["median"] == 5


@pytest.mark.parametrize("values", [[], [science.residual([0, 0, 0], [1, 0, 0])]])
def test_no_zero_error_or_aggregate_from_insufficient_samples(values):
    s = science.statistics(values)
    assert s["status"] == "insufficient_samples" and s["values"] is None


@pytest.mark.parametrize(
    "bad", [[float("nan"), 0, 0], [float("inf"), 0, 0], [True, 0, 0], [1, 2]]
)
def test_invalid_numeric_vectors_rejected(bad):
    with pytest.raises(ValueError):
        science.residual([0, 0, 0], bad)


def test_operator_capture_preserves_db_and_replays_inputs(archive, tmp_path):
    before = fingerprint(archive[1]), archive[1].read_bytes()
    target, report = capture(archive, tmp_path)
    assert report["summary"]["compatible_count"] == 2
    assert report["summary"]["independently_verified_count"] == 0
    assert report["summary"]["independent_error_metrics"] is None
    assert [s["residual"]["magnitude_km"] for s in report["samples"]] == [5, 5]
    assert service.read_package(target)[0] == report
    assert main(["verify", "--directory", str(target)]) == 0
    assert (fingerprint(archive[1]), archive[1].read_bytes()) == before
    assert report["findings"] == service.findings(report["samples"], report["summary"])
    assert all(f["confidence"] is None for f in report["findings"])


@pytest.mark.parametrize(
    "key,value",
    [
        ("catalog_id", 12345),
        ("time_scale", "TAI"),
        ("frame", "GCRS"),
        ("unit", "unknown"),
        ("origin", "station"),
        ("measurement_type", "range"),
        ("measurement_type", "angular_position"),
        ("data_kind", "model_output"),
        ("quality", "rejected"),
        ("observed_at", "2100-01-01T00:00:00Z"),
    ],
)
def test_unsupported_inputs_are_excluded_with_reason_not_subtracted(
    archive, tmp_path, key, value
):
    records = observations(archive, 1)
    records[0][key] = value
    _, report = capture(archive, tmp_path, records)
    assert report["samples"][0]["status"] == "incompatible_input"
    assert report["samples"][0]["residual"] is None
    assert report["summary"]["excluded_count"] == 1
    assert (
        report["summary"]["descriptive_discrepancy_by_frame"]["TEME"]["values"] is None
    )


@pytest.mark.parametrize("method", ["id", "source", "hash"])
def test_duplicate_source_and_ids_exclude_all_copies(archive, tmp_path, method):
    records = observations(archive)
    if method == "id":
        records[1]["observation_id"] = records[0]["observation_id"]
    else:
        records[1]["source_record_reference"] = records[0]["source_record_reference"]
        if method == "hash":
            records[1]["source_id"] = "different-source-alias"
            for record in records:
                record["upstream_payload_sha256"] = "c" * 64
    _, report = capture(archive, tmp_path, records)
    assert all(s["status"] == "duplicate_observation" for s in report["samples"])
    assert report["summary"]["compatible_count"] == 0


def test_known_prediction_payload_reuse_never_independent(archive, tmp_path):
    records = observations(archive, 1)
    records[0]["upstream_payload_sha256"] = analysis.load_snapshot(
        archive[1], archive[2]
    )[0]["response_sha256"]
    _, report = capture(archive, tmp_path, records)
    assert report["samples"][0]["status"] == "reused_input"
    assert report["samples"][0]["residual"] is None


def test_temporal_candidate_is_still_unverified(archive):
    record = observations(archive, 1)[0]
    source = analysis.load_snapshot(archive[1], archive[2])[0]
    record["observed_at"] = (
        datetime.fromisoformat(source["retrieved_at"]) + timedelta(seconds=1)
    ).isoformat()
    result = science.independence(science.Observation.model_validate(record), source)
    assert (
        result["status"] == "temporal_holdout_candidate_unverified"
        and result["eligible"] is False
    )


def test_metre_normalization_and_observation_uncertainty_are_separate(
    archive, tmp_path
):
    records = observations(archive, 1)
    records[0]["position"] = [v * 1000 for v in records[0]["position"]]
    records[0]["unit"] = "m"
    records[0]["uncertainty"] = {
        "kind": "axis_standard_deviation",
        "values": [1, 2, 3],
        "unit": "m",
        "provenance": "SYNTHETIC SIGMA ONLY",
    }
    _, report = capture(archive, tmp_path, records)
    s = report["samples"][0]
    assert s["residual"]["magnitude_km"] == pytest.approx(5)
    assert s["uncertainty"]["normalized_sigma_km"] == [0.001, 0.002, 0.003]
    assert (
        s["uncertainty"]["prediction"] is None
        and s["uncertainty"]["weighted_statistics"] is False
    )


def test_itrs_uses_strict_existing_transform_and_declines_rac(archive, tmp_path):
    target, report = capture(archive, tmp_path, observations(archive, 1, "ITRS"))
    s = report["samples"][0]
    assert s["residual"]["magnitude_km"] == pytest.approx(5)
    assert s["residual"]["rac"]["status"] == "unavailable"
    assert s["prediction"]["earth_orientation"]["degraded_results_allowed"] is False
    assert main(["verify", "--directory", str(target)]) == 0


@pytest.mark.parametrize(
    "field", ["position", "observed_at", "source_record_reference"]
)
def test_invalid_records_remain_visible_and_excluded(archive, tmp_path, field):
    records = observations(archive, 1)
    del records[0][field]
    _, report = capture(archive, tmp_path, records)
    assert (
        report["samples"][0]["status"] == "invalid_input"
        and report["samples"][0]["original_record"] == records[0]
    )


@pytest.mark.parametrize(
    "bad", [b"{}", b'{"schema_version":1,"schema_version":1}', b"[[[[[[", b"0" * 65537]
)
def test_bounded_malformed_inputs_refused_before_capture(archive, tmp_path, bad):
    target = tmp_path / ("b" * 32)
    with pytest.raises((ValueError, replay.BundleError)):
        service.create((archive[1], archive[2]), bad, target)
    assert not target.exists()


def test_oversized_batch_and_no_overwrite(archive, tmp_path):
    with pytest.raises(ValueError):
        science.parse_input(raw(observations(archive, 1) * 11))
    target, report = capture(archive, tmp_path)
    original = (target / "report.json").read_bytes()
    with pytest.raises(FileExistsError):
        service.create((archive[1], archive[2]), raw(observations(archive)), target)
    assert (target / "report.json").read_bytes() == original


@pytest.mark.parametrize(
    "member", ["report.json", "observations.json", "prediction-0/manifest.json"]
)
def test_changed_package_refused(archive, tmp_path, member):
    target, _ = capture(archive, tmp_path)
    with (target / member).open("ab") as f:
        f.write(b" ")
    with pytest.raises((ValueError, replay.BundleError)):
        service.read_package(target)


def test_read_only_api_absent_empty_and_scoped_package(archive, tmp_path, monkeypatch):
    client = archive[0]
    monkeypatch.delenv("ORBITIQ_VALIDATION_ARCHIVE", raising=False)
    assert (
        client.get("/api/observation-validations").json()["status"] == "not_configured"
    )
    root = tmp_path / "validation-runs"
    root.mkdir()
    monkeypatch.setenv("ORBITIQ_VALIDATION_ARCHIVE", str(root))
    assert client.get("/api/observation-validations").json()["status"] == "empty"
    target, report = capture(archive, root)
    listing = client.get("/api/observation-validations").json()
    assert listing["runs"] == [target.name]
    assert client.get("/api/observation-validations/" + target.name).json() == report
    assert client.post("/api/observation-validations").status_code == 405
    assert client.get("/api/observation-validations/not-an-id").status_code == 422


def test_external_files_links_and_corrupt_archive_are_not_exposed(
    archive, tmp_path, monkeypatch
):
    root = tmp_path / "empty-root"
    root.mkdir()
    (root / ("a" * 32)).symlink_to(tmp_path, target_is_directory=True)
    monkeypatch.setenv("ORBITIQ_VALIDATION_ARCHIVE", str(root))
    response = archive[0].get("/api/observation-validations")
    assert response.status_code == 503 and str(root) not in response.text


def test_empty_replay_does_not_claim_calculation_success(archive, tmp_path, capsys):
    records = observations(archive, 1)
    records[0]["quality"] = "rejected"
    target, report = capture(archive, tmp_path, records)
    assert main(["verify", "--directory", str(target)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "validated_no_compatible_samples"
    assert result["predictions"] == {}


def test_outer_trusted_anchor_detects_changed_hash_list(archive, tmp_path):
    target, report = capture(archive, tmp_path)
    sha = replay.digest((target / "manifest.json").read_bytes())
    with (target / "manifest.json").open("ab") as f:
        f.write(b" ")
    with pytest.raises(ValueError, match="Trusted validation manifest"):
        service.read_package(target, sha)


def test_changed_residual_and_recomputed_wrapper_hashes_still_rejected(
    archive, tmp_path
):
    target, report = capture(archive, tmp_path)
    report["samples"][0]["prediction"]["position_km"][0] += 1
    report["samples"][0]["residual"] = science.residual(
        report["samples"][0]["prediction"]["position_km"],
        report["samples"][0]["normalized_observation_position_km"],
    )
    report["samples"][0]["residual"]["rac"] = {}
    report["summary"] = service.summarize(report["samples"])
    report["findings"] = service.findings(report["samples"], report["summary"])
    content = replay.encoded(report)
    (target / "report.json").write_bytes(content)
    m = json.loads((target / "manifest.json").read_bytes())
    m["files"]["report.json"] = {
        "sha256": replay.digest(content),
        "bytes": len(content),
    }
    (target / "manifest.json").write_bytes(replay.encoded(m))
    with pytest.raises(ValueError, match="Prediction/observation values"):
        service.read_package(target)


def test_snapshot_missing_is_safe_cli_error(tmp_path, monkeypatch, capsys):
    from orbitiq.database import initialize

    path = tmp_path / "empty.sqlite3"
    initialize(path)
    monkeypatch.setenv("ORBITIQ_DATABASE_PATH", str(path))
    obs = tmp_path / "observation-input.json"
    obs.write_bytes(raw([{}]))
    assert (
        main(
            [
                "capture",
                "--observations",
                str(obs),
                "--snapshot",
                "123",
                "--directory",
                str(tmp_path / ("b" * 32)),
            ]
        )
        == 1
    )
    assert json.loads(capsys.readouterr().out)["status"] == "blocked"


def test_unavailable_replay_is_not_success_for_a_captured_valid_sample(
    archive, tmp_path, monkeypatch, capsys
):
    target, _ = capture(archive, tmp_path)
    monkeypatch.setattr(
        replay, "verify", lambda *args, **kwargs: {"status": "unavailable"}
    )
    assert main(["verify", "--directory", str(target)]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "blocked"


def test_failed_propagation_is_preserved_as_unavailable_not_zero(
    archive, tmp_path, capsys
):
    records = observations(archive, 1)
    records[0]["observed_at"] = (
        datetime.fromisoformat(records[0]["observed_at"]) + timedelta(days=8)
    ).isoformat()
    target, report = capture(archive, tmp_path, records)
    assert report["samples"][0]["status"] == "calculation_failed"
    assert report["samples"][0]["residual"] is None
    assert service.read_package(target)[0]["summary"]["compatible_count"] == 0
    assert main(["verify", "--directory", str(target)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "validated_no_compatible_samples"
    assert all(v["status"] == "unavailable" for v in result["predictions"].values())
