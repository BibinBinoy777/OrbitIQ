"""Read-only actual archive audit, deterministic report and detached comparison replay.

The output directory must be new. No ingestion, initialization or migration occurs.
An existing archive is required. Test fixtures are not genuine history.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient
from orbitiq import replay
from orbitiq.main import create_app
from orbitiq.maintenance.recovery import fingerprint
from orbitiq.reporting import parse_definition
from orbitiq.runtime import Settings
from orbitiq.services import analysis, history


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--catalog", type=int, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    path, out = args.database, args.directory
    if not path.is_absolute() or not path.is_file() or not out.is_absolute():
        raise ValueError(
            "Use an existing absolute database and new absolute output directory"
        )
    out.mkdir(mode=0o700)
    before = fingerprint(path)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    os.environ["ORBITIQ_DATABASE_PATH"] = str(path)
    pages, summaries = [], []
    with TestClient(create_app(Settings(environment="test"))) as client:
        params = {"limit": 1}
        for _ in range(1000):
            response = client.get("/api/snapshots", params=params)
            response.raise_for_status()
            page = response.json()
            pages.append(page)
            summaries.extend(page["snapshots"])
            if not page["has_more"]:
                break
            params.update(anchor_id=page["anchor_id"], before_id=page["next_before_id"])
        else:
            raise ValueError(
                "Bounded 1000-record audit exhausted; do not infer complete coverage"
            )
        response = client.get(
            "/api/historical-analysis", params={"catalog_id": args.catalog}
        )
        response.raise_for_status()
        report = response.json()
    (out / "report.json").write_bytes(replay.encoded(report))
    deterministic = history.historical_analysis(
        path, args.catalog, now=datetime.fromisoformat(report["generated_at"])
    )
    assert deterministic == report
    records = []
    for summary in summaries:
        item, elements = analysis.load_snapshot(path, summary["id"])
        records.append(
            {
                "reference": history.reference(summary),
                "insertion_at": item.get("snapshot_inserted_at"),
                "identity_consistent": summary["identity_consistent"],
                "elements": elements.model_dump(mode="json", by_alias=True),
            }
        )
    comparisons = []
    for i, pair in enumerate(report["comparisons"]):
        definition = pair["evidence"]["definition"]
        if definition is None:
            continue
        target = out / f"comparison-{i}"
        capture = replay.capture(path, parse_definition(json.dumps(definition)), target)
        package = json.loads((target / "report.json").read_bytes())
        assert pair["differences"] == [
            d
            for d in package["calculation"]["data"]["element_differences"]
            if d["field"] in history.FIELDS
        ]
        runs = []
        for repeat in range(3):
            command = [
                sys.executable,
                "scripts/verify_replay_offline.py",
                "--directory",
                str(target),
                "--expected-manifest-sha256",
                capture["manifest_sha256"],
            ]
            process = subprocess.run(
                command, capture_output=True, text=True, check=False
            )
            result = json.loads(process.stdout)
            runs.append(
                {"command": command, "exit_code": process.returncode, "result": result}
            )
            assert process.returncode == 0, result
            (out / f"comparison-{i}-repeat-{repeat}.json").write_bytes(
                replay.encoded(result)
            )
        comparisons.append(
            {
                "pair_id": pair["id"],
                "capture": capture,
                "runs": runs,
                "finding_scope": (
                    "Underlying calculations replayed; finding rules reproduced "
                    "separately at identical recorded inputs/clock"
                ),
            }
        )
    assert (
        before == fingerprint(path)
        and sha == hashlib.sha256(path.read_bytes()).hexdigest()
    )
    evidence = {
        "kind": "orbitiq_phase11_archive_audit",
        "catalog_id": args.catalog,
        "complete_archive_pagination": True,
        "total_snapshots": len(records),
        "archive_pages": pages,
        "validated_records": records,
        "report": report,
        "deterministic_repeat_equal": True,
        "comparison_evidence": comparisons,
        "database_before": before,
        "database_after": fingerprint(path),
        "database_sha256": sha,
        "acquisition_attempts": 0,
    }
    (out / "evidence.json").write_bytes(replay.encoded(evidence))
    print(
        json.dumps(
            {
                "records": len(records),
                "comparisons": len(comparisons),
                "report_id": report["report_id"],
                "archive_preserved": True,
            }
        )
    )


if __name__ == "__main__":
    main()
