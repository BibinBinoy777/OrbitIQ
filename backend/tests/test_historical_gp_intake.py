"""Synthetic format/readiness tests only; no genuine historical Swarm-A GP."""

import builtins
import json
import os
import runpy
import stat
import sys
from pathlib import Path

import pytest
from orbitiq import replay
from orbitiq.ingestion import celestrak
from orbitiq.orbits import engine
from orbitiq.orbits.elements import Elements
from orbitiq.services import analysis

ROOT = Path(__file__).resolve().parents[2]
TOOL = runpy.run_path(str(ROOT / "scripts/inspect_historical_gp.py"))
GLOBALS = TOOL["capture"].__globals__


def synthetic(**changes):
    # Reuse the existing mathematical reference format, explicitly relabelled.
    value = json.loads((ROOT / "backend/tests/fixtures/vallado-leo.json").read_text())[
        0
    ]["omm"]
    value.update(
        NORAD_CAT_ID=39452,
        OBJECT_NAME="SYNTHETIC FORMAT TEST ONLY",
        OBJECT_ID="2013-067B",
        EPOCH="2014-01-01T00:00:00",
    )
    value.update(changes)
    return value


def inspect(value, provenance=None):
    return TOOL["inspect_attachment"](replay.encoded(value), provenance)


def test_single_object_and_original_hash_scope():
    raw = json.dumps(synthetic(), separators=(",", ":")).encode()
    report = TOOL["inspect_attachment"](raw)
    item = report["records"][0]
    assert report["attachment_sha256"] == replay.digest(raw)
    assert report["attachment_bytes"] == len(raw)
    assert item["source_index"] == 0 and item["status"] == "CANDIDATE"
    assert item["attachment_sha256"] == replay.digest(raw)
    assert item["parsed_record_sha256"] == replay.digest(replay.encoded(synthetic()))
    assert item["parsed_record_sha256"] != replay.digest(raw)
    assert "NOT original record bytes" in report["parsed_record_hash_scope"]
    assert report["selected_source_index"] is None


def test_multi_record_source_order_and_mixed_invalid_records_are_not_discarded():
    records = [
        synthetic(EPOCH="2014-01-02T00:00:00"),
        {"NORAD_CAT_ID": 39452},
        synthetic(EPOCH="2013-12-30T00:00:00"),
        "not a record",
        synthetic(ECCENTRICITY=2),
    ]
    report = inspect(records)
    assert report["counts"] == {"enumerated": 5, "candidate": 2, "excluded": 3}
    assert [r["source_index"] for r in report["records"]] == list(range(5))
    assert report["records"][1]["reasons"]
    assert report["records"][3]["reasons"] == ["record_must_be_object"]
    assert report["records"][4]["field_failures"]
    assert report["selected_source_index"] is None


@pytest.mark.parametrize(
    "raw",
    [
        b"[]",
        b"",
        b"{",
        b"null",
        b"42",
        b'"a"',
        b"true",
        b"\xff",
        b'{"a":1,"a":2}',
        b'[{"EPOCH":NaN}]',
        b'[{"EPOCH":Infinity}]',
        b'[{"MEAN_MOTION":1e999}]',
        b"[" * 34 + b"0" + b"]" * 34,
        b"[" + b"{}," * 512 + b"{}]",
    ],
)
def test_malformed_unsupported_nonfinite_or_over_budget_document_fails_closed(raw):
    result = TOOL["inspect_attachment"](raw)
    assert result["document_errors"] and result["records"] == []
    assert result["qualification_gates"]["input_structure_and_numbers"]["status"] == (
        "BLOCKED"
    )
    assert result["comparison_ready"] is False and result["residuals"] is None


@pytest.mark.parametrize(
    "changes",
    [
        {"EPOCH": None},
        {"EPOCH": "not time"},
        {"MEAN_MOTION": "15"},
        {"MEAN_MOTION": -1},
        {"ECCENTRICITY": 1.0},
        {"INCLINATION": 181.0},
        {"NORAD_CAT_ID": 25544},
        {"NORAD_CAT_ID": "39452"},
        {"OBJECT_ID": "wrong"},
        {"REF_FRAME": "ITRS"},
        {"TIME_SYSTEM": "TAI"},
        {"MEAN_ELEMENT_THEORY": "other"},
        {"EPOCH": "2014-01-01T00:00:00.1234567"},
        {"EPOCH": "2014-01-01T00:00:00+01:00"},
        {"EPOCH": "2014-01-01T00:00:60"},
        {"EPOCH": "0001-01-01T00:00:00"},
    ],
)
def test_invalid_or_incompatible_record_is_individually_excluded(changes):
    result = inspect([synthetic(), synthetic(**changes)])
    assert result["records"][1]["status"] == "EXCLUDED"
    assert result["records"][1]["reasons"]
    assert result["records"][0]["status"] == "CANDIDATE"


def test_missing_required_fields_reported_without_exception_input_values():
    item = synthetic()
    del item["EPOCH"]
    del item["BSTAR"]
    result = inspect(item)["records"][0]
    assert result["epoch_source_text"] is None
    assert set(result["missing_required_fields"]) >= {"EPOCH", "BSTAR"}
    assert all(set(r) == {"field", "code"} for r in result["field_failures"])


@pytest.mark.parametrize(
    "epoch",
    [
        "2014-01-01T00:00:00.12345600Z",
        "2014-01-01T00:00:00.000001",
        "2014-01-01T00:00:00+00:00",
    ],
)
def test_exact_microseconds_and_original_text_preserved(epoch):
    result = inspect(synthetic(EPOCH=epoch))["records"][0]
    assert result["status"] == "CANDIDATE" and result["epoch_source_text"] == epoch
    assert result["orbital_epoch_utc"] == TOOL["exact_epoch"](epoch).isoformat()


def test_precision_exclusion_explains_why_without_rounding():
    item = inspect(synthetic(EPOCH="2014-01-01T00:00:00.1234567"))["records"][0]
    assert item["epoch_failure"] == "epoch_submicrosecond_precision_unsupported"
    assert item["orbital_epoch_utc"] is None
    assert item["epoch_source_text"] == "2014-01-01T00:00:00.1234567"


def test_duplicates_exclude_all_copies_without_claiming_original_record_hashes():
    value = synthetic()
    report = inspect(
        [value, dict(reversed(list(value.items()))), synthetic(BSTAR=1e-6)]
    )
    assert report["counts"] == {"enumerated": 3, "candidate": 1, "excluded": 2}
    assert [r["duplicate_source_indices"] for r in report["records"][:2]] == (
        [[0, 1], [0, 1]]
    )
    assert report["records"][2]["status"] == "CANDIDATE"
    assert (
        "multiple_records_share_epoch_review_required"
        in (report["records"][2]["unresolved"])
    )
    assert report["selected_source_index"] is None


@pytest.mark.parametrize(
    "epoch,candidate,intersects",
    [
        ("2013-12-30T00:00:00", True, True),
        ("2014-01-02T23:59:59.999999", True, True),
        ("2014-01-03T00:00:00", False, True),
        ("2013-12-29T23:59:59.999999", False, True),
        ("2013-12-25T00:02:04", False, True),  # Exactly seven days at first epoch.
        ("2013-12-25T00:02:03.999999", False, False),
        ("2014-01-08T23:57:54", False, True),
        ("2014-01-08T23:57:54.000001", False, False),
    ],
)
def test_declared_scope_and_exact_seven_day_intersections(epoch, candidate, intersects):
    item = inspect(synthetic(EPOCH=epoch))["records"][0]
    assert (item["status"] == "CANDIDATE") is candidate
    assert (item["epoch_bound_intersection"] is not None) is intersects
    assert item["forecast_eligible"] is False


def test_unknown_provenance_and_creation_or_receipt_do_not_prove_availability():
    report = inspect(
        synthetic(CREATION_DATE="2013-12-31T23:00:00"),
        {
            "provider": "SYNTHETIC TEST ONLY",
            "received_at": "2026-10-21T06:10:16Z",
            "notes": "Synthetic metadata; not actual receipt or historical evidence",
        },
    )
    assert report["provenance"]["source_authenticated"] is False
    assert report["provenance"]["historically_available_at"] is None
    assert report["provenance"]["asserted"]["acquired_at"] is None
    assert report["records"][0]["available_at"] is None
    assert report["comparison_mode_if_other_gates_later_pass"] == "retrospective_only"
    assert TOOL["metadata"]()["asserted"] == dict.fromkeys(TOOL["METADATA_FIELDS"])


@pytest.mark.parametrize(
    "value",
    [
        [],
        {"password": "must not be accepted"},
        {"provider": 5},
        {"received_at": "2026-10-21T06:10:16"},
        {"received_at": "2026-10-21T06:10:16.0000001Z"},
        {"notes": "a" * 1025},
        {"original_filename": "../private.txt"},
        {"acquired_at": "2026-10-22T00:00:00Z", "received_at": "2026-10-21T00:00:00Z"},
    ],
)
def test_unsupported_or_ambiguous_metadata_refused(value):
    with pytest.raises(ValueError):
        TOOL["metadata"](value)


@pytest.fixture
def intake_paths(tmp_path):
    source = tmp_path / "synthetic-input.json"
    source.write_bytes(replay.encoded([synthetic()]))
    archive = tmp_path / "private"
    archive.mkdir(mode=0o700)
    return source, archive


def test_capture_preserves_original_before_parsing_and_manifest_hashes(
    intake_paths, monkeypatch
):
    source, archive = intake_paths
    raw = source.read_bytes()
    original = GLOBALS["inspect_attachment"]

    def inspect_after_preserving(*args):
        leaf = next(archive.iterdir())
        assert (leaf / "attachment.original").read_bytes() == raw
        receipt = json.loads((leaf / "receipt.json").read_bytes())
        assert receipt["attachment_sha256"] == replay.digest(raw)
        assert receipt["provenance"]["asserted"]["received_at"] is None
        assert not (leaf / "manifest.json").exists()
        return original(*args)

    monkeypatch.setitem(GLOBALS, "inspect_attachment", inspect_after_preserving)
    leaf, report = TOOL["capture"](source, archive, expected_sha256=replay.digest(raw))
    assert source.read_bytes() == (leaf / "attachment.original").read_bytes() == raw
    assert stat.S_IMODE(leaf.stat().st_mode) == 0o700
    assert all(stat.S_IMODE(p.stat().st_mode) == 0o600 for p in leaf.iterdir())
    manifest = json.loads((leaf / "manifest.json").read_bytes())
    for name, entry in manifest["files"].items():
        assert replay.digest((leaf / name).read_bytes()) == entry["sha256"]
        assert (leaf / name).stat().st_size == entry["bytes"]
    assert report["status"] == "BLOCKED"


def test_repeated_capture_appends_without_replacing_previous_files(intake_paths):
    source, archive = intake_paths
    first, _ = TOOL["capture"](source, archive)
    saved = {p.name: p.read_bytes() for p in first.iterdir()}
    second, _ = TOOL["capture"](source, archive)
    assert first != second and len(list(archive.iterdir())) == 2
    assert saved == {p.name: p.read_bytes() for p in first.iterdir()}


def test_collision_refuses_existing_directory_without_changing_it(
    intake_paths, monkeypatch
):
    source, archive = intake_paths
    fixed = TOOL["uuid4"]()
    monkeypatch.setitem(GLOBALS, "uuid4", lambda: fixed)
    first, _ = TOOL["capture"](source, archive)
    saved = {p.name: p.read_bytes() for p in first.iterdir()}
    with pytest.raises(FileExistsError):
        TOOL["capture"](source, archive)
    assert saved == {p.name: p.read_bytes() for p in first.iterdir()}


def test_mid_capture_failure_preserves_private_original_without_completion_manifest(
    intake_paths, monkeypatch
):
    source, archive = intake_paths

    def fail(*args):
        raise RuntimeError("synthetic interruption")

    monkeypatch.setitem(GLOBALS, "inspect_attachment", fail)
    with pytest.raises(RuntimeError):
        TOOL["capture"](source, archive)
    leaf = next(archive.iterdir())
    assert (leaf / "attachment.original").read_bytes() == source.read_bytes()
    assert (leaf / "receipt.json").exists() and not (leaf / "manifest.json").exists()


@pytest.mark.parametrize(
    "kind",
    [
        "public",
        "link_source",
        "link_parent",
        "link_archive",
        "mismatch",
        "relative",
        "oversized",
        "fifo",
    ],
)
def test_unsafe_paths_permissions_sizes_or_hashes_refused(intake_paths, tmp_path, kind):
    source, archive = intake_paths
    original = source.read_bytes()
    expected = None
    if kind == "public":
        archive.chmod(0o755)
    elif kind == "link_source":
        linked = tmp_path / "link.json"
        linked.symlink_to(source)
        source = linked
    elif kind == "link_parent":
        linked = tmp_path / "parent"
        linked.symlink_to(tmp_path, target_is_directory=True)
        source = linked / source.name
    elif kind == "link_archive":
        linked = tmp_path / "archive-link"
        linked.symlink_to(archive, target_is_directory=True)
        archive = linked
    elif kind == "mismatch":
        expected = "0" * 64
    elif kind == "relative":
        source = Path("synthetic-input.json")
    elif kind == "oversized":
        source.write_bytes(b"x" * (TOOL["MAX_BYTES"] + 1))
    elif kind == "fifo":
        source = tmp_path / "pipe"
        os.mkfifo(source)
    with pytest.raises((ValueError, OSError, replay.BundleError)):
        TOOL["capture"](source, archive, expected_sha256=expected)
    assert not list(archive.iterdir())
    if kind not in {"oversized", "relative", "fifo"}:
        assert source.read_bytes() == original


def test_malformed_json_is_preserved_and_refused_not_discarded(intake_paths):
    source, archive = intake_paths
    source.write_bytes(b"{not JSON")
    leaf, report = TOOL["capture"](source, archive)
    assert report["document_errors"]
    assert (leaf / "attachment.original").read_bytes() == b"{not JSON"
    assert (leaf / "manifest.json").exists()  # Completed diagnostic of invalid input.


def test_cli_sanitized_summary_and_failure(intake_paths, capsys):
    source, archive = intake_paths
    argv = ["--attachment", str(source), "--archive-root", str(archive)]
    assert TOOL["main"](argv) == 0
    output = capsys.readouterr().out
    assert source.name not in output and str(archive) not in output
    assert json.loads(output)["comparison_ready"] is False
    assert TOOL["main"]([*argv, "--expected-sha256", "0" * 64]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "intake_refused"


def test_intake_never_calls_existing_dynamic_parser_propagation_db_or_residuals(
    intake_paths, monkeypatch
):
    def forbidden(*args, **kwargs):
        raise AssertionError("Scientific evaluation forbidden during intake")

    monkeypatch.setattr(celestrak, "parse_response", forbidden)
    monkeypatch.setattr(celestrak, "propagate_satellite", forbidden)
    monkeypatch.setattr(engine, "propagate_satellite", forbidden)
    monkeypatch.setattr(engine, "propagate", forbidden)
    monkeypatch.setattr(Elements, "satellite", forbidden)
    monkeypatch.setattr(analysis, "position_from_snapshot", forbidden)
    monkeypatch.setattr(analysis, "load_snapshot", forbidden)
    # Publication of intake must not require the separate, unpublished Phase 11
    # observation extension. Guard imports before reloading the tool so even a
    # future top-level residual import fails in a clean checkout. If the larger
    # local suite already loaded that extension, retain its callable sentinel too.
    if module := sys.modules.get("orbitiq.observation_validation"):
        monkeypatch.setattr(module, "residual", forbidden)
    original_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.endswith(".observation_validation") or (
            name.startswith("orbitiq") and "observation_validation" in fromlist
        ):
            forbidden()
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    isolated = runpy.run_path(str(ROOT / "scripts/inspect_historical_gp.py"))
    _, report = isolated["capture"](*intake_paths)
    assert len(report["qualification_gates"]) == 9
    assert all(
        g["status"] in {"BLOCKED", "PARTIAL"}
        for g in report["qualification_gates"].values()
    )
    assert (
        report["comparison_ready"] is False and report["adapter_operational"] is False
    )
    assert report["normalized_observations"] == [] and report["residuals"] is None
    assert report["prediction_evaluations"] == 0 and report["accuracy"] is None
