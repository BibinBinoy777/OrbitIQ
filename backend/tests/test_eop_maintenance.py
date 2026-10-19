"""Isolated operator fault tests. No installed package is modified or downloaded."""

import json
import subprocess
from pathlib import Path

import pytest
from astropy import units as u
from orbitiq.maintenance import eop
from orbitiq.maintenance.probe import validate_tables
from orbitiq.orbits.earth_orientation import orientation

VERSION = "0.2026.10.12.1.3.27"
META = {
    "package_version": VERSION,
    "sha256": "a" * 64,
    "leap_seconds_sha256": "b" * 64,
    "first_mjd": 41684.0,
    "last_mjd": 61682.0,
    "predictive_mjd": 61315.0,
}


def source(root):
    root.mkdir()
    (root / "backend").mkdir()
    (root / "scripts").mkdir()
    (root / "pyproject.toml").write_text('[project]\nname="test"\nversion="0.1"\n')
    (root / ".python-version").write_text("3.12\n")
    (root / "uv.lock").write_text(
        'version=1\n[[package]]\nname="astropy-iers-data"\nversion="' + VERSION + '"\n'
    )
    return root


@pytest.fixture
def candidates(tmp_path, monkeypatch):
    a = tmp_path / "a"
    b = tmp_path / "b"
    acquired = {
        "status": "acquired",
        "acquired_at": "2026-10-19T00:00:00+00:00",
        "source_sha256": "d" * 64,
        "metadata": META,
    }
    for root in [a, b]:
        root.mkdir()
        (root / "validation.json").write_text(
            json.dumps(
                {
                    "status": "validated",
                    "verified_at": "2026-10-19T00:01:00+00:00",
                    "source_sha256": acquired["source_sha256"],
                }
            )
        )
    monkeypatch.setattr(
        eop, "verify_candidate", lambda root, **kwargs: (acquired, META)
    )
    return a, b, tmp_path / "state"


def test_valid_candidate_prepare_is_recorded_and_reproducible(tmp_path, monkeypatch):
    active = source(tmp_path / "source")
    before = (active / "uv.lock").read_bytes()
    commands = []
    monkeypatch.setattr(
        eop, "run", lambda command, root, **kw: commands.append(command) or ""
    )
    monkeypatch.setattr(eop, "environment_probe", lambda root: META)
    first = eop.prepare(tmp_path / "first", VERSION, source=active)
    second = eop.prepare(tmp_path / "second", VERSION, source=active)
    assert first["status"] == "acquired" and first["metadata"] == META
    assert (
        first["source_sha256"] == second["source_sha256"]
        and first["lock_sha256"] == second["lock_sha256"]
    )
    assert first["source_index"] == "https://pypi.org/simple" and first["acquired_at"]
    assert (active / "uv.lock").read_bytes() == before
    assert all(command[0] == "uv" for command in commands)
    assert any("--default-index" in command for command in commands)


@pytest.mark.parametrize(
    "version", ["latest", ">=0.2026", ";echo secret", "1.0", "0.2026.10.12 --bad"]
)
def test_version_input_is_explicit_and_safe(tmp_path, version):
    with pytest.raises(eop.MaintenanceError):
        eop.prepare(tmp_path / "candidate", version, source=tmp_path / "source")
    assert not (tmp_path / "candidate").exists()


def test_acquisition_failure_preserves_active_source_and_records_failure(
    tmp_path, monkeypatch
):
    active = source(tmp_path / "source")
    before = (active / "uv.lock").read_bytes()

    def fail(*args, **kwargs):
        raise eop.MaintenanceError("acquisition failed")

    monkeypatch.setattr(eop, "run", fail)
    with pytest.raises(eop.MaintenanceError):
        eop.prepare(tmp_path / "candidate", VERSION, source=active)
    assert (active / "uv.lock").read_bytes() == before
    assert (
        json.loads((tmp_path / "candidate/acquisition.json").read_text())["status"]
        == "acquisition_failed"
    )


def test_existing_candidate_and_active_checkout_are_not_overwritten(
    tmp_path, monkeypatch
):
    active = source(tmp_path / "source")
    existing = tmp_path / "candidate"
    existing.mkdir()
    (existing / "keep").write_text("preserve")
    with pytest.raises(OSError):
        eop.prepare(existing, VERSION, source=active)
    with pytest.raises(eop.MaintenanceError):
        eop.prepare(active / "nested", VERSION, source=active)
    assert (existing / "keep").read_text() == "preserve"


def test_full_validation_and_reference_results_are_required(tmp_path, monkeypatch):
    root = source(tmp_path / "candidate")
    acquired = {
        "source_sha256": eop.source_hash(root),
        "acquired_at": "2026-10-19T00:00:00Z",
    }
    monkeypatch.setattr(eop, "verify_candidate", lambda p, **kwargs: (acquired, META))
    commands = []

    def run(command, root, **kwargs):
        commands.append(command)
        if "--output" in command:
            path = Path(command[-1])
            path.write_text(
                json.dumps({"passed": 40 if "sgp4" in path.name else 6, "failed": 0})
            )
        return ""

    monkeypatch.setattr(eop, "run", run)
    r = eop.validate(root)
    assert r["status"] == "validated" and r["checks"]["sgp4_references"] == 40
    assert any("pytest" in command for command in commands)
    assert (
        json.loads((root / "validation.json").read_text())["verified_at"]
        == r["verified_at"]
    )


@pytest.mark.parametrize("failure", ["reference", "suite", "missing_metadata"])
def test_failed_validation_cannot_authorize_activation(tmp_path, monkeypatch, failure):
    root = source(tmp_path / "candidate")
    (root / "validation.json").write_text('{"status":"validated"}')
    acquired = {
        "source_sha256": eop.source_hash(root),
        "acquired_at": "2026-10-19T00:00:00Z",
    }
    if failure == "missing_metadata":
        monkeypatch.setattr(
            eop,
            "verify_candidate",
            lambda p: (_ for _ in ()).throw(eop.MaintenanceError("metadata absent")),
        )
    else:
        monkeypatch.setattr(
            eop, "verify_candidate", lambda p, **kwargs: (acquired, META)
        )

    def run(command, root, **kwargs):
        if failure == "suite" and "pytest" in command:
            raise eop.MaintenanceError("reference test failed")
        if "--output" in command:
            Path(command[-1]).write_text(json.dumps({"passed": 0, "failed": 1}))
        return ""

    monkeypatch.setattr(eop, "run", run)
    with pytest.raises(eop.MaintenanceError):
        eop.validate(root)
    assert (
        json.loads((root / "validation.json").read_text())["status"]
        == "validation_failed"
    )
    assert list(root.glob("validation-failed-*.json"))


def test_tampered_acquired_resource_or_metadata_is_rejected(tmp_path, monkeypatch):
    root = source(tmp_path / "candidate")
    acquired = {
        "status": "acquired",
        "source_sha256": eop.source_hash(root),
        "metadata": META,
    }
    (root / "acquisition.json").write_text(json.dumps(acquired))
    monkeypatch.setattr(
        eop, "environment_probe", lambda root, **kwargs: {**META, "sha256": "f" * 64}
    )
    with pytest.raises(eop.MaintenanceError):
        eop.verify_candidate(root)
    (root / "uv.lock").write_text("changed")
    with pytest.raises(eop.MaintenanceError):
        eop.verify_candidate(root)


def test_activation_and_explicit_rollback_preserve_previous_environment(candidates):
    a, b, state = candidates
    first = eop.activate(a, state)
    eop.activate(b, state)
    assert json.loads((state / "active.json").read_text())["candidate"] == str(b)
    restored = eop.rollback(state)
    assert restored == first
    assert json.loads((state / "active.json").read_text())["candidate"] == str(a)
    assert (
        a.exists()
        and b.exists()
        and list((state / "history").glob("*rolled-back.json"))
    )


def test_post_activation_verification_failure_restores_previous(
    candidates, monkeypatch
):
    a, b, state = candidates
    first = eop.activate(a, state)
    original = eop.verify_selection

    def verify(receipt, **kwargs):
        if receipt["candidate"] == str(b):
            raise eop.MaintenanceError("simulated post-activation failure")
        return original(receipt, **kwargs)

    monkeypatch.setattr(eop, "verify_selection", verify)
    with pytest.raises(eop.MaintenanceError):
        eop.activate(b, state)
    assert json.loads((state / "active.json").read_text()) == first
    assert list((state / "history").glob("*failed.json"))


def test_atomic_replace_failure_preserves_previous_selector(candidates, monkeypatch):
    a, b, state = candidates
    first = eop.activate(a, state)
    replace = eop.os.replace
    failed = False

    def fail_once(src, dst):
        nonlocal failed
        if Path(dst).name == "active.json" and not failed:
            failed = True
            raise OSError("simulated write failure")
        return replace(src, dst)

    monkeypatch.setattr(eop.os, "replace", fail_once)
    with pytest.raises(OSError):
        eop.activate(b, state)
    assert json.loads((state / "active.json").read_text()) == first


def test_unvalidated_candidate_does_not_replace_selection(candidates):
    a, b, state = candidates
    first = eop.activate(a, state)
    (b / "validation.json").write_text('{"status":"validation_failed"}')
    with pytest.raises(eop.MaintenanceError):
        eop.activate(b, state)
    assert json.loads((state / "active.json").read_text()) == first


def test_operation_lock_and_missing_previous_version_fail_safely(candidates):
    a, _, state = candidates
    eop.activate(a, state)
    with pytest.raises(eop.MaintenanceError):
        eop.rollback(state)
    (state / ".operation.lock").write_text("another operation")
    with pytest.raises(FileExistsError):
        eop.activate(a, state)
    assert (state / ".operation.lock").read_text() == "another operation"


@pytest.mark.parametrize("failure", ["truncated", "units", "boundary", "coverage"])
def test_incomplete_or_invalid_temporary_eop_is_rejected(failure):
    with orientation() as (data, _):
        table = data.table.copy()
        leaps = data.leaps.copy()
    if failure == "truncated":
        table = table[:20]
    elif failure == "units":
        table["PM_x"] = table["PM_x"].value * u.km
    elif failure == "boundary":
        table.meta["predictive_mjd"] = 1
    else:
        table["MJD"][5] = table["MJD"][4]
    with pytest.raises((ValueError, KeyError)):
        validate_tables(table, leaps)


def test_current_installed_tables_pass_structural_and_boundary_checks():
    with orientation() as (data, _):
        validate_tables(data.table, data.leaps)


def test_subprocess_failure_does_not_expose_output_or_remove_previous(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        eop.subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a, 1, "", "SECRET credential"),
    )
    with pytest.raises(eop.MaintenanceError) as error:
        eop.run(["uv", "lock"], tmp_path)
    assert "SECRET" not in str(error.value)


def test_bookkeeping_failure_restores_selection_and_previous_history(
    candidates, monkeypatch
):
    a, b, state = candidates
    first = eop.activate(a, state)
    previous_history = (state / "previous.json").read_bytes()
    atomic = eop.atomic_json
    failed = False

    def fail_once(path, data):
        nonlocal failed
        if path.name == "previous.json" and not failed:
            failed = True
            raise OSError("simulated bookkeeping failure")
        return atomic(path, data)

    monkeypatch.setattr(eop, "atomic_json", fail_once)
    with pytest.raises(OSError):
        eop.activate(b, state)
    assert json.loads((state / "active.json").read_text()) == first
    assert (state / "previous.json").read_bytes() == previous_history


def test_stale_previous_identity_can_be_preserved_without_weakening_new_validation(
    candidates, monkeypatch
):
    a, b, state = candidates
    eop.activate(a, state)
    original = eop.verify_candidate
    calls = []

    def verify(root, *, require_current=True):
        calls.append((root, require_current))
        if root == a and require_current:
            raise eop.MaintenanceError("previous prediction age exhausted")
        return original(root, require_current=require_current)

    monkeypatch.setattr(eop, "verify_candidate", verify)
    eop.activate(b, state)
    assert (a, False) in calls and (b, True) in calls
    assert eop.rollback(state)["candidate"] == str(a)
