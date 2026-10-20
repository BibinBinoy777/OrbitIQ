"""Explicit operator CLI; capture is read-only, verification needs no database."""

import argparse
import os
from pathlib import Path

from orbitiq import replay
from orbitiq.database import configured_path
from orbitiq.reporting import parse_definition
from orbitiq.services.analysis import AnalysisError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    capture = commands.add_parser(
        "capture", help="Create a new private evidence directory"
    )
    capture.add_argument("--definition", required=True, type=Path)
    capture.add_argument("--directory", required=True, type=Path)
    for command in ("validate", "verify"):
        operation = commands.add_parser(
            command, help="Validate locally; verify also replays"
        )
        operation.add_argument("--directory", required=True, type=Path)
        operation.add_argument("--expected-manifest-sha256")
        operation.add_argument(
            "--result", type=Path, help="New result file outside the bundle"
        )
    args = parser.parse_args(argv)
    try:
        if args.command == "capture":
            with args.definition.open("rb") as stream:
                raw = stream.read(2049)
            definition = parse_definition(raw.decode("utf-8"))
            result = replay.capture(configured_path(), definition, args.directory)
            code = 0
        else:
            if args.result and (
                not args.result.is_absolute()
                or args.result.resolve().is_relative_to(args.directory.resolve())
                or os.path.lexists(args.result)
            ):
                raise replay.BundleError(
                    "Result must be a new absolute file outside the bundle"
                )
            result = replay.verify(
                args.directory,
                args.expected_manifest_sha256,
                validation_only=args.command == "validate",
            )
            code = {
                "validated": 0,
                "matched": 0,
                "verified_source_only": 0,
                "mismatch": 2,
            }.get(result["status"], 3)
            if args.result:
                with args.result.open("xb") as stream:
                    os.fchmod(stream.fileno(), 0o600)
                    stream.write(replay.encoded(result))
                    stream.flush()
                    os.fsync(stream.fileno())
    except (
        replay.BundleError,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        RecursionError,
        AnalysisError,
    ):
        result = {
            "status": "error",
            "reason": "Invalid or unavailable input, configuration or destination; "
            "nothing overwritten",
        }
        code = 1
    print(replay.encoded(result).decode(), end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
