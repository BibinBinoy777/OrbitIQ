"""Offline reference-fixture evidence lifecycle; never opens the ordinary archive.

The isolated SQLite adapter serializes published OMM reference inputs. Its URL and
retrieval metadata are test scaffolding, not a claim of a CelesTrak acquisition.
Published expected vectors remain separate from OrbitIQ's captured replay baseline.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path

from orbitiq import replay
from orbitiq.database import initialize
from orbitiq.orbits.elements import Elements
from orbitiq.storage import get_snapshot, save_snapshot


def run(directory):
    directory = Path(directory)
    if not directory.is_absolute():
        raise ValueError("Golden audit needs a new absolute directory")
    directory.mkdir(mode=0o700)
    fixture_path = replay.ROOT / "backend/tests/fixtures/vallado-leo.json"
    fixture = json.loads(fixture_path.read_bytes())[0]
    assert fixture["catalog_id"] == 6251
    case = fixture["cases"][0]
    assert case["minutes"] == 0
    upstream = files("sgp4").joinpath("tcppver.out").read_bytes()
    assert (
        replay.digest(upstream)
        == "687bf28dbe52df86e8e60ab5cb4a08d1aa3dbcaf4e63b1f7ab95f044fbe3833b"
    )
    record = {**fixture["omm"], "OBJECT_NAME": "REFERENCE TEST ONLY - Vallado 6251"}
    elements = Elements.model_validate(record)
    db = directory / "reference-fixture-only.sqlite3"
    initialize(db)  # Exclusively new isolated fixture, never configured ordinary DB.
    sid = save_snapshot(
        db,
        json.dumps([record]).encode(),
        record,
        elements,
        "https://celestrak.org/NORAD/elements/gp.php?CATNR=6251&FORMAT=JSON",
        datetime.now(UTC),
    )
    item = get_snapshot(db, sid)
    definition = {
        "schema_version": 1,
        "mode": "position",
        "frame": "TEME",
        "at": elements.epoch.isoformat(),
        "source": {
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
        },
    }
    (directory / "definition.json").write_bytes(replay.encoded(definition))
    source_hash = replay.digest(db.read_bytes())
    environment = {
        **os.environ,
        "PYTHONPATH": str(replay.ROOT / "backend"),
        "ORBITIQ_DATABASE_PATH": str(db),
    }
    commands = []

    def execute(args, output):
        process = subprocess.run(
            [sys.executable, *args],
            cwd=replay.ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=60,
        )
        (directory / output).write_text(process.stdout)
        (directory / (output + ".stderr")).write_text(process.stderr)
        commands.append(
            {"argv": [sys.executable, *args], "exit_code": process.returncode}
        )
        assert process.returncode == 0, process.stdout + process.stderr
        return json.loads(process.stdout)

    capture = execute(
        [
            "-m",
            "orbitiq.maintenance.replay",
            "capture",
            "--definition",
            str(directory / "definition.json"),
            "--directory",
            str(directory / "captured"),
        ],
        "capture.json",
    )
    # Export is an ordinary exclusive copy of the fixed member directory; no archive
    # extraction/import writer is introduced. Verification reads this detached copy.
    exported = directory / "exported"
    shutil.copytree(directory / "captured", exported)
    members_before = {p.name: replay.digest(p.read_bytes()) for p in exported.iterdir()}
    validation = execute(
        [
            "-m",
            "orbitiq.maintenance.replay",
            "validate",
            "--directory",
            str(exported),
            "--expected-manifest-sha256",
            capture["manifest_sha256"],
        ],
        "validation.json",
    )
    assert (
        validation["status"] == "validated" and validation["replay_started_at"] is None
    )
    replays = [
        execute(
            [
                "scripts/verify_replay_offline.py",
                "--directory",
                str(exported),
                "--expected-manifest-sha256",
                capture["manifest_sha256"],
            ],
            f"replay-{i}.json",
        )
        for i in range(3)
    ]
    assert all(r["numerical_outcome"] == "exact_output_reproduction" for r in replays)
    assert len({r["actual_projection_sha256"] for r in replays}) == 1
    report = json.loads((exported / "report.json").read_bytes())
    actual = {
        key: report["calculation"]["data"][key]
        for key in ("position_km", "velocity_km_s")
    }
    comparisons = []
    for key, tolerance, unit in (
        ("position_km", 1e-5, "km"),
        ("velocity_km_s", 1e-8, "km/s"),
    ):
        for i, (expected, value) in enumerate(zip(case[key], actual[key], strict=True)):
            delta = value - expected
            comparisons.append(
                {
                    "field": f"{key}.{i}",
                    "expected": expected,
                    "actual": value,
                    "signed_difference": delta,
                    "absolute_difference": abs(delta),
                    "unit": unit,
                    "absolute_tolerance": tolerance,
                    "relative_tolerance": 0,
                    "passed": abs(delta) <= tolerance,
                }
            )
    assert all(c["passed"] for c in comparisons)
    assert source_hash == replay.digest(db.read_bytes())
    assert members_before == {
        p.name: replay.digest(p.read_bytes()) for p in exported.iterdir()
    }
    evidence = {
        "kind": "reference_fixture_evidence_lifecycle",
        "passed": True,
        "recorded_at": datetime.now(UTC).isoformat(),
        "source_payload_kind": "reference_fixture_serialization_not_http_acquisition",
        "snapshot_metadata": "test_adapter_only_not_real_provider_retrieval",
        "reference": {
            "name": "Vallado et al. AIAA 2006-6753, tcppver.out 6251 offset 0",
            "source_url": "https://celestrak.org/publications/AIAA/2006-6753/",
            "distribution": "python-sgp4 2.27 published reference files",
            "upstream_output_sha256": replay.digest(upstream),
            "fixture": str(fixture_path.relative_to(replay.ROOT)),
            "fixture_sha256": replay.digest(fixture_path.read_bytes()),
            "input_tle": fixture["tle"],
            "input_omm": record,
            "epoch": elements.epoch.isoformat(),
            "requested_at": elements.epoch.isoformat(),
            "frame": "TEME",
            "origin": "Earth center",
            "gravity_model": "WGS72",
            "time_convention": "SGP4 nominal UTC calendar days; microsecond datetime",
            "eop": None,
            "eop_status": "not_applicable_TEME",
            "leap_resource": None,
            "leap_status": "not_used_by_nominal_UTC_SGP4",
            "expected": {k: case[k] for k in actual},
            "expected_kind": "literal_published_reference_not_OrbitIQ_output",
            "limitations": [
                "Selected published numerical vector, not satellite observation",
                "Reference precision/epoch representation limits; "
                "not universal accuracy",
            ],
        },
        "reference_comparisons": comparisons,
        "commands": commands,
        "capture": capture,
        "validation": validation,
        "repeated_replays": replays,
        "exported_members_sha256": members_before,
        "fixture_database_unchanged": True,
        "exported_bundle_unchanged": True,
        "ordinary_archive_opened": False,
    }
    (directory / "evidence.json").write_bytes(replay.encoded(evidence))
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.directory)
    print(
        "Golden lifecycle: 6 published vector components passed; "
        f"{len(result['repeated_replays'])} exact offline replays"
    )


if __name__ == "__main__":
    main()
