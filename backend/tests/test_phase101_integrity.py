"""Hardening tests: untrusted data, numerical semantics, isolated reference inputs."""

import json
import math
import os
import socket
import sqlite3
import subprocess
from concurrent.futures import ThreadPoolExecutor

import pytest
from orbitiq import replay
from orbitiq.maintenance.recovery import fingerprint
from orbitiq.maintenance.replay import main
from orbitiq.replay_isolation import ReplayIsolationError, offline_replay
from orbitiq.services.replay import compare_values
from test_phase10_replay import bundle, rewrite

pytest_plugins = ["test_phase5"]


@pytest.mark.parametrize(
    "raw",
    [
        b'{"x":1,"x":2}',
        b'{"x":1e999}',
        b'{"x":NaN}',
        b"[" * 33 + b"0" + b"]" * 33,
    ],
)
def test_json_rejects_ambiguous_nonfinite_and_deep_input(raw):
    with pytest.raises(replay.BundleError):
        replay.decoded(raw)


def test_json_budgets_and_quoted_brackets():
    assert replay.decoded(b'{"value":"[[[\\"{{{"}') == {"value": '[[["{{{'}
    for value in ([0] * 4097, "x" * 16385, [[0] * 4096] * 50):
        with pytest.raises(replay.BundleError) as caught:
            replay.decoded(json.dumps(value).encode())
        assert caught.value.code == "json_limit"
    with pytest.raises(replay.BundleError):
        replay.decoded(
            json.dumps({str(i): 0 for i in range(2100)}).encode(), manifest=True
        )


def test_encoding_and_hash_rules_are_stable():
    a = {"z": "é", "a": [1, 2.0, -0.0]}
    b = {"a": [1, 2.0, -0.0], "z": "é"}
    assert replay.encoded(a) == replay.encoded(b)
    assert (
        replay.encoded(a)
        == b'{\n  "a": [\n    1,\n    2.0,\n    -0.0\n  ],\n  "z": "\\u00e9"\n}\n'
    )
    assert replay.digest(replay.encoded(a)) == replay.digest(replay.encoded(b))
    assert replay.digest(b'{"a":1}') != replay.digest(b'{ "a": 1 }')


@pytest.mark.parametrize(
    "change",
    [
        lambda m: m.pop("schema_version"),
        lambda m: m.pop("kind"),
        lambda m: m.update(schema_version=2),
        lambda m: m.update(schema_version=True),
        lambda m: m.update(kind="zip_archive"),
        lambda m: m["settings"].update(eop_policy="automatic_download"),
        lambda m: m.update(captured_at="2026-10-20T00:00:00"),
    ],
)
def test_required_version_and_policy_contract(archive, tmp_path, change):
    root, _ = bundle(archive, tmp_path)
    manifest = json.loads((root / "manifest.json").read_bytes())
    change(manifest)
    (root / "manifest.json").write_bytes(replay.encoded(manifest))
    result = replay.verify(root)
    assert result["status"] == "blocked"
    assert result["replay_started_at"] is None
    assert result["validation"]["status"] == "failed"


@pytest.mark.parametrize(
    "member",
    ["source-0.json", "source-0.response.json", "iers-a.all", "leap-seconds.dat"],
)
def test_missing_inputs_name_affected_calculation(archive, tmp_path, member):
    root, _ = bundle(archive, tmp_path, "ground-track")
    (root / member).unlink()
    result = replay.verify(root)
    assert result["status"] == "blocked" and result["code"] == "missing_input"
    assert result["required_member"] == member
    assert result["affected_calculation"] == (
        "terrestrial_transform"
        if member in {"iers-a.all", "leap-seconds.dat"}
        else "source_based_calculation"
    )
    assert result["replay_started_at"] is None
    assert str(tmp_path) not in json.dumps(result)


def test_validate_has_no_orbital_replay(archive, tmp_path, monkeypatch, capsys):
    root, _ = bundle(archive, tmp_path, "ground-track")

    def forbidden(*_):
        pytest.fail("Recalculation ran during input validation")

    monkeypatch.setattr(replay, "recalculate", forbidden)
    assert main(["validate", "--directory", str(root)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "validated"
    assert result["validation"]["status"] == "passed"
    assert result["replay_started_at"] is None
    assert result["numeric_values_checked"] == 0


@pytest.mark.parametrize(
    "field,value",
    [
        ("frame", "GCRS"),
        ("units", {"position": "m", "velocity": "m/s"}),
        ("at", "2006-06-25T19:47:43.980096Z"),
        ("snapshot_id", 9999),
        ("calculated_at", "2026-10-20T00:00:00"),
        ("position_km", [1, 2]),
        ("velocity_km_s", [True, 2, 3]),
        ("gravity_model", "WGS84"),
    ],
)
def test_contradictory_state_blocked_before_recalculation(
    archive, tmp_path, monkeypatch, field, value
):
    root, _ = bundle(archive, tmp_path)
    report = json.loads((root / "report.json").read_bytes())
    report["calculation"]["data"][field] = value
    rewrite(root, "report.json", report)

    def forbidden(*_):
        pytest.fail("Invalid scientific metadata reached orbital replay")

    monkeypatch.setattr(replay, "recalculate", forbidden)
    result = replay.verify(root)
    assert result["status"] == "blocked", result
    assert result["replay_started_at"] is None
    assert result["validation"]["stage"] == "scientific_preflight"


@pytest.mark.parametrize(
    "field",
    ["sha256", "leap_seconds_sha256", "package_version", "polar_motion_x_arcsec"],
)
def test_resource_metadata_is_validated_before_replay(
    archive, tmp_path, monkeypatch, field
):
    root, _ = bundle(archive, tmp_path, "ground-track")
    report = json.loads((root / "report.json").read_bytes())
    report["calculation"]["data"]["points"][0]["earth_orientation"].pop(field)
    rewrite(root, "report.json", report)
    monkeypatch.setattr(
        replay,
        "recalculate",
        lambda *_: pytest.fail("Missing EOP metadata reached replay"),
    )
    result = replay.verify(root)
    assert result["code"] == "resource_identity_mismatch", result
    assert result["replay_started_at"] is None


@pytest.mark.parametrize(
    "operation,category",
    [
        (lambda path: socket.create_connection(("127.0.0.1", 9)), "network"),
        (lambda path: sqlite3.connect(path), "database"),
        (
            lambda path: subprocess.run(
                ["python", "-c", "raise SystemExit(9)"], check=True
            ),
            "process",
        ),
        (lambda path: os.system("exit 9"), "process"),
    ],
)
def test_core_replay_policy_prohibits_side_effects(
    archive, tmp_path, monkeypatch, operation, category
):
    root, _ = bundle(archive, tmp_path)
    output = tmp_path / "unexpected.sqlite3"

    def injected(*_):
        operation(output)
        pytest.fail("Forbidden operation returned")

    monkeypatch.setattr(replay, "recalculate", injected)
    result = replay.verify(root)
    assert (
        result["status"] == "blocked"
        and result["code"] == "offline_operation_forbidden"
    ), result
    assert result["offline_policy"]["attempts"][category] == 1
    assert not output.exists()


def test_policy_cannot_be_swallowed_into_success(archive, tmp_path, monkeypatch):
    root, _ = bundle(archive, tmp_path)
    original = replay.recalculate

    def injected(*args):
        try:
            socket.getaddrinfo("localhost", 9)
        except ReplayIsolationError:
            pass
        return original(*args)

    monkeypatch.setattr(replay, "recalculate", injected)
    result = replay.verify(root)
    assert (
        result["status"] == "blocked"
        and result["offline_policy"]["attempts"]["network"] == 1
    )


def test_scoped_policy_does_not_change_other_threads_or_normal_sqlite():
    with offline_replay(), ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(lambda: sqlite3.connect(":memory:").close())
        assert future.result(timeout=5) is None
        with pytest.raises(ReplayIsolationError):
            sqlite3.connect(":memory:")
    with sqlite3.connect(":memory:") as connection:
        assert connection.execute("SELECT 1").fetchone() == (1,)


def test_three_replays_repeat_without_archive_or_bundle_mutation(archive, tmp_path):
    root, captured = bundle(archive, tmp_path, "ground-track")
    before = {p.name: replay.digest(p.read_bytes()) for p in root.iterdir()}
    db_before, db_sha = fingerprint(archive[1]), replay.digest(archive[1].read_bytes())
    results = [replay.verify(root, captured["manifest_sha256"]) for _ in range(3)]
    assert all(
        r["status"] == "matched"
        and r["numerical_outcome"] == "exact_output_reproduction"
        for r in results
    ), results
    assert len({r["actual_projection_sha256"] for r in results}) == 1
    assert all(
        r["expected_projection_sha256"] == r["actual_projection_sha256"]
        for r in results
    )
    assert before == {p.name: replay.digest(p.read_bytes()) for p in root.iterdir()}
    assert (
        fingerprint(archive[1]) == db_before
        and replay.digest(archive[1].read_bytes()) == db_sha
    )
    p = results[0]["provenance"]
    assert p["original_calculation_times"]
    assert p["source_references"][0]["retrieved_at"] != p["package_created_at"]
    assert (
        p["requested_calculation"]["track"]["start"] == p["requested_calculation"]["at"]
    )
    assert p["original_report_generated_at"] != results[0]["replay_started_at"]


def test_full_replay_distinguishes_tolerance_from_exact_and_mismatch(archive, tmp_path):
    root, _ = bundle(archive, tmp_path)
    report = json.loads((root / "report.json").read_bytes())
    report["calculation"]["data"]["position_km"][0] += 5e-9
    rewrite(root, "report.json", report)
    result = replay.verify(root)
    assert (
        result["status"] == "matched"
        and result["numerical_outcome"] == "tolerance_agreement"
    ), result
    detail = result["agreements_within_tolerance"][0]
    assert 0 < detail["absolute_difference"] < detail["absolute_tolerance"] == 1e-8
    assert detail["unit"] == "km" and detail["passed"] is True
    assert detail["relative_difference"] > 0
    report["calculation"]["data"]["position_km"][0] += 1e-4
    rewrite(root, "report.json", report)
    result = replay.verify(root)
    assert result["status"] == "mismatch" and result["numerical_outcome"] == "mismatch"
    assert result["differences"][0]["passed"] is False


def test_zero_signed_zero_angles_and_residual_diagnostics():
    detail = compare_values({"position_km": [0.0]}, {"position_km": [1e-9]})[
        "agreements_within_tolerance"
    ][0]
    assert (
        detail["relative_difference"] is None and detail["absolute_difference"] == 1e-9
    )
    assert compare_values([0.0], [-0.0])["outcome"] == "tolerance_agreement"
    result = compare_values(
        {"longitude_deg": 179.9999999999}, {"longitude_deg": -179.9999999999}
    )
    assert result["outcome"] == "tolerance_agreement"
    assert result["agreements_within_tolerance"][0]["relative_difference"] is None
    assert (
        result["agreements_within_tolerance"][0]["difference_method"]
        == "wrapped_remainder_360"
    )
    tiny = compare_values({"longitude_deg": 0.0}, {"longitude_deg": 1e-14})[
        "agreements_within_tolerance"
    ][0]
    assert tiny["absolute_difference"] == 1e-14
    for v in [math.inf, math.nan]:
        result = compare_values({"position_km": [1.0]}, {"position_km": [v]})
        assert result["outcome"] == "mismatch"
        json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("extra", ["evil.py", "manifest.json.exe", "/absolute/path"])
def test_unsupported_members_are_not_opened_or_executed(
    archive, tmp_path, monkeypatch, extra
):
    root, _ = bundle(archive, tmp_path)
    marker = tmp_path / "executed"
    if extra.startswith("/"):
        m = json.loads((root / "manifest.json").read_bytes())
        m["files"][extra] = m["files"].pop("report.json")
        (root / "manifest.json").write_bytes(replay.encoded(m))
    else:
        (root / extra).write_text("raise RuntimeError('must not execute')")
    monkeypatch.setattr(
        replay, "recalculate", lambda *_: marker.write_text("unexpected")
    )
    result = replay.verify(root)
    assert result["status"] == "blocked" and result["replay_started_at"] is None
    assert not marker.exists()


def test_excessive_files_stop_scanning_at_first_unknown_member(
    archive, tmp_path, monkeypatch
):
    root, _ = bundle(archive, tmp_path)
    count = []

    class Entries:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def __iter__(self):
            for i in range(100000):
                count.append(i)
                yield type("Entry", (), {"name": f"unknown-{i}"})()

    monkeypatch.setattr(os, "scandir", lambda _: Entries())
    assert replay.verify(root)["code"] == "unexpected_member"
    assert len(count) == 1


def test_unsupported_archive_format_never_extracts(archive, tmp_path):
    import zipfile

    malicious = tmp_path / "evil.zip"
    with zipfile.ZipFile(malicious, "w") as z:
        z.writestr("../escaped.py", "raise SystemExit(1)")
    before = set(tmp_path.iterdir())
    assert replay.verify(malicious)["status"] == "blocked"
    assert set(tmp_path.iterdir()) == before


def test_published_golden_evidence_lifecycle(tmp_path):
    from importlib.util import module_from_spec, spec_from_file_location

    path = replay.ROOT / "scripts/verify_phase101_golden.py"
    spec = spec_from_file_location("phase101_golden", path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.run(tmp_path / "golden")
    assert result["passed"] and result["ordinary_archive_opened"] is False
    assert all(c["passed"] for c in result["reference_comparisons"])
    assert len(result["repeated_replays"]) == 3
    assert all(
        r["offline_audit"]["attempts"] == {"network": 0, "database": 0}
        for r in result["repeated_replays"]
    )


@pytest.mark.parametrize(
    "change",
    [
        lambda r: r.pop("schema_version"),
        lambda r: r.update(schema_version=True),
        lambda r: r.update(template_version=2),
        lambda r: r.pop("methodology"),
        lambda r: r["methodology"].update(software_versions={"sgp4": "different"}),
        lambda r: r["validation"].update(prediction_uncertainty="quantified"),
        lambda r: r["validation"].update(independent_observation_validation="passed"),
    ],
)
def test_report_required_metadata_cannot_be_forged_into_numerical_success(
    archive, tmp_path, change
):
    root, _ = bundle(archive, tmp_path)
    report = json.loads((root / "report.json").read_bytes())
    change(report)
    rewrite(root, "report.json", report)
    result = replay.verify(root)
    assert result["status"] == "blocked" and result["replay_started_at"] is None


def test_declared_total_budget_is_checked_before_payload_reads(
    archive, tmp_path, monkeypatch
):
    root, _ = bundle(archive, tmp_path, "ground-track")
    manifest = json.loads((root / "manifest.json").read_bytes())
    for item in manifest["files"].values():
        item["bytes"] = 8 * 1024 * 1024
    (root / "manifest.json").write_bytes(replay.encoded(manifest))
    read = replay.read_file
    members = []

    def bounded(fd, name, limit):
        members.append(name)
        return read(fd, name, limit)

    monkeypatch.setattr(replay, "read_file", bounded)
    assert replay.verify(root)["status"] == "blocked"
    assert members == ["manifest.json"]


def test_ingestion_and_resource_maintenance_are_not_called(
    archive, tmp_path, monkeypatch
):
    from orbitiq.ingestion import collection
    from orbitiq.maintenance import eop

    root, _ = bundle(archive, tmp_path, "ground-track")

    def forbidden(*_, **__):
        pytest.fail("Administrative operation called during replay")

    monkeypatch.setattr(collection, "collect", forbidden)
    for name in ("prepare", "activate", "rollback"):
        monkeypatch.setattr(eop, name, forbidden)
    assert replay.verify(root)["status"] == "matched"


def test_comparison_element_units_are_checked_before_replay(archive, tmp_path):
    root, _ = bundle(archive, tmp_path, "comparison")
    report = json.loads((root / "report.json").read_bytes())
    report["calculation"]["data"]["element_differences"][0]["unit"] = "invalid"
    rewrite(root, "report.json", report)
    result = replay.verify(root)
    assert result["status"] == "blocked" and result["replay_started_at"] is None
