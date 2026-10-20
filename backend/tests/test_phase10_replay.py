"""Replay fixtures are reference-derived tests, never satellite observations."""

import copy
import json
import os
from datetime import UTC, datetime

import erfa
import numpy as np
import pytest
from orbitiq import replay
from orbitiq.maintenance.recovery import fingerprint
from orbitiq.maintenance.replay import main
from orbitiq.orbits import earth_orientation
from orbitiq.reporting import parse_definition
from orbitiq.services.replay import compare_values
from test_phase9_reports import definition

pytest_plugins = ["test_phase5"]


def bundle(archive, tmp_path, mode="position", frame="TEME", change=None):
    client, path, first, second, *_ = archive
    value = definition(client, first, mode, second, frame)
    if change:
        change(value)
    target = tmp_path / "bundle"
    captured = replay.capture(path, parse_definition(json.dumps(value)), target)
    return target, captured


def rewrite(root, filename, value):
    data = replay.encoded(value)
    (root / filename).write_bytes(data)
    manifest = json.loads((root / "manifest.json").read_bytes())
    manifest["files"][filename] = {"bytes": len(data), "sha256": replay.digest(data)}
    (root / "manifest.json").write_bytes(replay.encoded(manifest))


@pytest.mark.parametrize(
    "mode,frame",
    [
        ("snapshot", "TEME"),
        ("position", "TEME"),
        ("ground-track", "ITRS"),
        ("comparison", "TEME"),
        ("comparison", "ITRS"),
    ],
)
def test_capture_replay_all_modes_preserves_archive(archive, tmp_path, mode, frame):
    path = archive[1]
    before, sha = fingerprint(path), replay.digest(path.read_bytes())
    root, capture = bundle(archive, tmp_path, mode, frame)
    original = {p.name: p.read_bytes() for p in root.iterdir()}
    result = replay.verify(root, capture["manifest_sha256"])
    assert result["status"] == (
        "verified_source_only" if mode == "snapshot" else "matched"
    ), result
    assert (
        result["numeric_values_checked"] > 0
        if mode != "snapshot"
        else result["numeric_values_checked"] == 0
    )
    assert result["provider_authenticity"] == "not_independently_verified"
    assert result["independent_observation_validation"] == "blocked"
    assert result["current_eop_readiness_checked"] is False
    assert fingerprint(path) == before and replay.digest(path.read_bytes()) == sha
    assert original == {p.name: p.read_bytes() for p in root.iterdir()}
    assert os.stat(root).st_mode & 0o777 == 0o700
    assert all(os.stat(p).st_mode & 0o777 == 0o600 for p in root.iterdir())


def test_source_only_comparison_is_not_numerical_pass(archive, tmp_path):
    root, _ = bundle(
        archive, tmp_path, "comparison", change=lambda d: d.update(at=None)
    )
    result = replay.verify(root)
    assert result["status"] == "verified_source_only", result


def test_unavailable_original_is_not_matched(archive, tmp_path):
    root, _ = bundle(
        archive, tmp_path, change=lambda d: d.update(at="2100-01-01T00:00:00Z")
    )
    result = replay.verify(root)
    assert result["status"] == "unavailable" and result["numeric_values_checked"] == 0


@pytest.mark.parametrize(
    "name",
    [
        "report.json",
        "source-0.json",
        "source-0.response.json",
        "uv.lock",
        "iers-a.all",
        "leap-seconds.dat",
    ],
)
def test_changed_file_is_blocked(archive, tmp_path, name):
    root, _ = bundle(archive, tmp_path, "ground-track")
    with (root / name).open("ab") as stream:
        stream.write(b" ")
    assert replay.verify(root)["status"] == "blocked"


@pytest.mark.parametrize(
    "failure",
    ["missing", "extra", "symlink", "fifo", "directory", "traversal", "oversize"],
)
def test_unsafe_layout_fails_closed(archive, tmp_path, failure):
    root, _ = bundle(archive, tmp_path)
    target = root / "report.json"
    if failure == "missing":
        target.unlink()
    elif failure == "extra":
        (root / "unexpected").write_text("extra")
    elif failure in {"symlink", "fifo", "directory"}:
        target.unlink()
        if failure == "symlink":
            target.symlink_to(tmp_path / "outside")
        elif failure == "fifo":
            os.mkfifo(target)
        else:
            target.mkdir()
    elif failure == "traversal":
        manifest = json.loads((root / "manifest.json").read_bytes())
        manifest["files"]["../outside"] = manifest["files"].pop("report.json")
        (root / "manifest.json").write_bytes(replay.encoded(manifest))
    else:
        with target.open("wb") as stream:
            stream.truncate(8 * 1024 * 1024 + 1)
    assert replay.verify(root)["status"] == "blocked"


@pytest.mark.parametrize(
    "field", ["python", "packages", "backend_sha256", "uv_lock_sha256"]
)
def test_runtime_identity_mismatch_is_blocked(archive, tmp_path, field):
    root, _ = bundle(archive, tmp_path)
    manifest = json.loads((root / "manifest.json").read_bytes())
    manifest["environment"][field] = "different"
    (root / "manifest.json").write_bytes(replay.encoded(manifest))
    assert replay.verify(root)["status"] == "blocked"


def test_changed_local_runtime_is_blocked(archive, tmp_path, monkeypatch):
    root, _ = bundle(archive, tmp_path)
    value = copy.deepcopy(replay.environment())
    value["python"] = "different"
    monkeypatch.setattr(replay, "environment", lambda: value)
    assert replay.verify(root)["status"] == "blocked"


def test_manifest_anchor_detects_recomputed_checksums(archive, tmp_path):
    root, captured = bundle(archive, tmp_path)
    report = json.loads((root / "report.json").read_bytes())
    report["calculation"]["data"]["position_km"][0] += 1
    rewrite(root, "report.json", report)
    assert replay.verify(root, captured["manifest_sha256"])["status"] == "blocked"
    result = replay.verify(root)
    assert result["status"] == "mismatch" and result["mismatch_count"] == 1, result
    assert result["differences"][0]["absolute_tolerance"] == 1e-8


@pytest.mark.parametrize(
    "field",
    [
        "catalog_id",
        "response_sha256",
        "raw_record",
        "normalized_record",
        "element_units",
        "source_url",
        "validator_version",
        "id",
    ],
)
def test_source_metadata_must_validate_even_after_rehash(archive, tmp_path, field):
    root, _ = bundle(archive, tmp_path)
    source = json.loads((root / "source-0.json").read_bytes())
    source[field] = (
        {}
        if isinstance(source[field], dict)
        else 0
        if isinstance(source[field], int)
        else "invalid"
    )
    rewrite(root, "source-0.json", source)
    assert replay.verify(root)["status"] == "blocked"


@pytest.mark.parametrize(
    "raw", [b'{"kind":1,"kind":2}', b'{"x":NaN}', b'{"x":Infinity}', b"not-json"]
)
def test_malformed_json_fails_closed(archive, tmp_path, raw):
    root, _ = bundle(archive, tmp_path)
    (root / "manifest.json").write_bytes(raw)
    assert replay.verify(root)["status"] == "blocked"


def test_policy_and_tolerances_cannot_be_weakened(archive, tmp_path):
    root, _ = bundle(archive, tmp_path)
    manifest = json.loads((root / "manifest.json").read_bytes())
    manifest["tolerances"]["position_km"] = 100
    (root / "manifest.json").write_bytes(replay.encoded(manifest))
    assert replay.verify(root)["status"] == "blocked"


def test_numeric_comparator_bounds_and_tolerances():
    assert (
        compare_values({"position_km": [1.0]}, {"position_km": [1.0 + 5e-9]})[
            "mismatch_count"
        ]
        == 0
    )
    assert (
        compare_values({"velocity_km_s": [1.0]}, {"velocity_km_s": [1.0 + 5e-9]})[
            "mismatch_count"
        ]
        == 1
    )
    result = compare_values(list(range(50)), [100] * 50)
    assert result["mismatch_count"] == 50 and len(result["differences"]) == 20
    assert compare_values(True, 1)["mismatch_count"] == 1


def test_cli_no_database_and_exclusive_destinations(
    archive, tmp_path, monkeypatch, capsys
):
    root, captured = bundle(archive, tmp_path)
    monkeypatch.delenv("ORBITIQ_DATABASE_PATH", raising=False)
    out = tmp_path / "result.json"
    assert (
        main(
            [
                "verify",
                "--directory",
                str(root),
                "--expected-manifest-sha256",
                captured["manifest_sha256"],
                "--result",
                str(out),
            ]
        )
        == 0
    )
    assert json.loads(out.read_bytes())["status"] == "matched"
    saved = out.read_bytes()
    assert main(["verify", "--directory", str(root), "--result", str(out)]) == 1
    assert out.read_bytes() == saved
    assert (
        main(
            ["verify", "--directory", str(root), "--result", str(root / "output.json")]
        )
        == 1
    )
    assert main(["verify", "--directory", str(tmp_path / "missing")]) == 3
    with pytest.raises(FileExistsError):
        replay.capture(
            archive[1],
            parse_definition(
                json.dumps(
                    json.loads((root / "report.json").read_bytes())["investigation"][
                        "definition"
                    ]
                )
            ),
            root,
        )
    capsys.readouterr()


def test_historical_scope_restores_erfa_and_default_resources(archive, tmp_path):
    root, _ = bundle(archive, tmp_path, "ground-track")
    old, expires = erfa.leap_seconds.get().copy(), erfa.leap_seconds.expires
    default = earth_orientation.resources()
    assert replay.verify(root)["status"] == "matched"
    assert np.array_equal(old, erfa.leap_seconds.get())
    assert erfa.leap_seconds.expires == expires
    assert earth_orientation.resources() is default
    assert earth_orientation._REPLAY.get() is None
    with (
        pytest.raises(RuntimeError),
        earth_orientation.replay_orientation(
            default, "measured_only", datetime.now(UTC)
        ),
    ):
        raise RuntimeError("test failure")
    assert np.array_equal(old, erfa.leap_seconds.get())
    assert earth_orientation._REPLAY.get() is None


def test_offline_fresh_process_without_database(archive, tmp_path):
    import subprocess
    import sys

    root, captured = bundle(archive, tmp_path, "ground-track")
    result = subprocess.run(
        [
            sys.executable,
            str(replay.ROOT / "scripts/verify_replay_offline.py"),
            "--directory",
            str(root),
            "--expected-manifest-sha256",
            captured["manifest_sha256"],
        ],
        env={**os.environ, "PYTHONPATH": str(replay.ROOT / "backend")},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    output = json.loads(result.stdout)
    assert output["status"] == "matched"
    assert output["offline_audit"]["attempts"] == {"network": 0, "database": 0}


def test_every_track_row_is_compared(archive, tmp_path):
    root, _ = bundle(archive, tmp_path, "ground-track")
    report = json.loads((root / "report.json").read_bytes())
    report["calculation"]["data"]["points"][-1]["geodetic"]["latitude_deg"] += 0.1
    rewrite(root, "report.json", report)
    result = replay.verify(root)
    assert result["status"] == "mismatch", result
    assert result["differences"][0]["path"].endswith("points.2.geodetic.latitude_deg")


def test_maximum_track_capture_replay(archive, tmp_path):
    def expand(d):
        d["track"].update(duration_minutes=60, step_seconds=10)

    root, _ = bundle(archive, tmp_path, "ground-track", change=expand)
    report = json.loads((root / "report.json").read_bytes())
    assert len(report["calculation"]["data"]["points"]) == 361
    assert replay.verify(root)["status"] == "matched"


def test_replay_ignores_current_presentation_settings(archive, tmp_path, monkeypatch):
    root, _ = bundle(archive, tmp_path, "ground-track")
    monkeypatch.setenv("ORBITIQ_EOP_POLICY", "invalid_current_setting")
    monkeypatch.setenv("ORBITIQ_FRESH_HOURS", "invalid_current_setting")
    monkeypatch.setenv("ORBITIQ_TRACK_MAX_SAMPLES", "1")
    assert replay.verify(root)["status"] == "matched"


def test_historical_policy_clock_is_explicit(monkeypatch):
    from astropy.time import Time
    from astropy.utils import iers

    data = earth_orientation.resources()
    at = Time(data.metadata["predictive_mjd"] + 3, format="mjd")
    historical = Time(data.metadata["predictive_mjd"], format="mjd").to_datetime(UTC)
    if at >= data.leaps.expires:
        pytest.fail("Installed reference resource needs explicit update")
    with earth_orientation.replay_orientation(
        data, "measured_or_predicted", historical
    ):
        value = earth_orientation.parameters(data, at, "measured_or_predicted")
        assert value["prediction_table_age_days"] == 0
        assert value["status"] == "predicted"
    with pytest.raises(earth_orientation.TransformationError) as caught:
        earth_orientation.parameters(
            data,
            at,
            "measured_or_predicted",
            now=historical.replace(year=historical.year + 1),
        )
    assert caught.value.code == "eop_predictions_expired"
    with (
        earth_orientation.replay_orientation(data, "measured_only", historical),
        pytest.raises(earth_orientation.TransformationError) as caught,
    ):
        earth_orientation.parameters(data, at, "measured_only")
    assert caught.value.code == "eop_prediction_disallowed"
    assert iers.conf.auto_download is not None


def test_bad_resource_rehashed_still_blocked(archive, tmp_path):
    root, _ = bundle(archive, tmp_path, "ground-track")
    rewrite(root, "leap-seconds.dat", {"not": "leap second data"})
    assert replay.verify(root)["status"] == "blocked"


def test_symlink_bundle_root_refused(archive, tmp_path):
    root, _ = bundle(archive, tmp_path)
    link = tmp_path / "link"
    link.symlink_to(root, target_is_directory=True)
    assert replay.verify(link)["status"] == "blocked"


def test_invalid_capture_configuration_creates_nothing(archive, tmp_path, monkeypatch):
    target = tmp_path / "bad"
    monkeypatch.setenv("ORBITIQ_EOP_POLICY", "unknown")
    with pytest.raises(ValueError):
        replay.capture(
            archive[1],
            parse_definition(json.dumps(definition(archive[0], archive[2]))),
            target,
        )
    assert not target.exists()


@pytest.mark.parametrize("raw", ['{"x":1,"x":2}', '{"x":1e999}', "[" * 1024])
def test_cli_invalid_definition_does_not_create_files(archive, tmp_path, capsys, raw):
    source = tmp_path / "definition.json"
    source.write_text(raw)
    destination = tmp_path / "bad-capture"
    assert (
        main(["capture", "--definition", str(source), "--directory", str(destination)])
        == 1
    )
    assert not destination.exists()
    assert json.loads(capsys.readouterr().out)["status"] == "error"


@pytest.mark.parametrize("name", ["iers-a.all", "leap-seconds.dat"])
def test_missing_resource_never_substitutes_installed_file(archive, tmp_path, name):
    root, _ = bundle(archive, tmp_path, "ground-track")
    (root / name).unlink()
    assert replay.verify(root)["status"] == "blocked"
