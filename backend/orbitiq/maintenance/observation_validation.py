"""Local operator capture/verification; no external ingestion or database writes."""

import argparse
from pathlib import Path

from orbitiq import observation_validation as science
from orbitiq import replay
from orbitiq.database import configured_path
from orbitiq.replay_contract import BundleError
from orbitiq.services import observation_validation as service
from orbitiq.services.analysis import AnalysisError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("capture")
    create.add_argument("--observations", type=Path, required=True)
    create.add_argument("--snapshot", type=int, required=True)
    create.add_argument("--directory", type=Path, required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("--directory", type=Path, required=True)
    verify.add_argument("--expected-manifest-sha256")
    args = parser.parse_args(argv)
    try:
        if args.command == "capture":
            if not args.observations.is_absolute():
                raise ValueError("Use an explicit absolute observation input path")
            with replay.directory(args.observations.parent) as fd:
                raw = replay.read_file(fd, args.observations.name, science.MAX_INPUT)
            report = service.create(
                (configured_path(), args.snapshot), raw, args.directory
            )
            result = {
                "status": "captured",
                "report_id": report["report_id"],
                "summary": report["summary"],
                "manifest_sha256": replay.digest(
                    (args.directory / "manifest.json").read_bytes()
                ),
            }
        else:
            report, manifest = service.read_package(
                args.directory, args.expected_manifest_sha256
            )
            runs = {
                name: replay.verify(args.directory / name, sha)
                for name, sha in manifest["predictions"].items()
            }
            # Recompute residuals from exact preserved inputs.
            for sample in report["samples"]:
                if sample["residual"] is not None:
                    d = science.residual(
                        sample["prediction"]["position_km"],
                        sample["normalized_observation_position_km"],
                    )
                    d["rac"] = science.rac(
                        d["xyz_km"],
                        sample["prediction"]["position_km"],
                        sample["prediction"]["velocity_km_s"],
                        sample["frame"],
                    )
                    if d != sample["residual"]:
                        raise ValueError("Residual reproduction failed")
            required = {
                s["prediction_bundle"]
                for s in report["samples"]
                if s["residual"] is not None
            }
            passed = all(
                r["status"] == "matched"
                if name in required
                else r["status"] in {"matched", "unavailable"}
                for name, r in runs.items()
            )
            result = {
                "status": (
                    "reproduced"
                    if report["summary"]["compatible_count"]
                    else "validated_no_compatible_samples"
                )
                if passed
                else "blocked",
                "report_id": report["report_id"],
                "predictions": runs,
                "scope": (
                    "Captured arithmetic plus individually reported propagation "
                    "replays; unavailable predictions do not count as matched."
                ),
                "independent_observation_validation": "not_established",
            }
        print(replay.encoded(result).decode(), end="")
        return (
            0
            if result["status"]
            in {"captured", "reproduced", "validated_no_compatible_samples"}
            else 1
        )
    except (OSError, ValueError, KeyError, TypeError, BundleError, AnalysisError):
        print(
            (
                '{"status":"blocked","reason":"Invalid, incompatible, '
                "incomplete or unavailable local evidence; nothing "
                'overwritten"}'
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
