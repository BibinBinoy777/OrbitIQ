"""Operator-only immutable EOP candidate environments and atomic selection."""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

VERSION = re.compile(r"0\.\d{4}\.\d{1,2}\.\d{1,2}(?:\.\d+){0,5}")
SOURCE_ITEMS = ("backend", "scripts", "pyproject.toml", "uv.lock", ".python-version")


class MaintenanceError(ValueError):
    pass


def stamp():
    return datetime.now(UTC).isoformat()


def read_json(path):
    if path.stat().st_size > 65536:
        raise MaintenanceError("Maintenance record is oversized")
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise MaintenanceError("Invalid maintenance record")
    return data


def write_new(path, data):
    with path.open("x") as file:
        json.dump(data, file, sort_keys=True, indent=2, allow_nan=False)
        file.write("\n")
        file.flush()
        os.fsync(file.fileno())


def atomic_json(path, data):
    temporary = path.with_name("." + path.name + "." + uuid.uuid4().hex)
    try:
        write_new(temporary, data)
        os.replace(temporary, path)
        descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        temporary.unlink(missing_ok=True)


def absolute(path):
    path = Path(path)
    if not path.is_absolute():
        raise MaintenanceError("An absolute path is required")
    return path.resolve()


def source_hash(root):
    digest = hashlib.sha256()
    for item in SOURCE_ITEMS:
        path = root / item
        files = (
            sorted(p for p in path.rglob("*") if p.is_file())
            if path.is_dir()
            else [path]
        )
        for file in files:
            if "__pycache__" in file.parts or file.suffix == ".pyc":
                continue
            digest.update(str(file.relative_to(root)).encode())
            digest.update(b"\0")
            digest.update(file.read_bytes())
    return digest.hexdigest()


def run(command, root, *, timeout=180):
    environment = {
        **os.environ,
        "PYTHONPATH": str(root / "backend"),
        "UV_PROJECT_ENVIRONMENT": str(root / ".venv"),
        "UV_HTTP_TIMEOUT": "30",
        "UV_HTTP_RETRIES": "1",
    }
    environment.setdefault("UV_CACHE_DIR", "/tmp/orbitiq-eop-cache")
    try:
        result = subprocess.run(
            command,
            cwd=root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise MaintenanceError(
            "Bounded maintenance command failed; existing environments are preserved"
        ) from None
    if result.returncode:
        raise MaintenanceError(
            "Candidate command failed validation; active environment is unchanged"
        )
    return result.stdout


def environment_probe(root, *, require_current=True):
    try:
        result = json.loads(
            run(
                [
                    str(root / ".venv/bin/python"),
                    "-m",
                    "orbitiq.maintenance.probe",
                    *([] if require_current else ["--identity-only"]),
                ],
                root,
            )
        )
        if not isinstance(result, dict):
            raise ValueError
        return result
    except (ValueError, TypeError):
        raise MaintenanceError("Candidate scientific metadata are invalid") from None


def lock_versions(root):
    lock = tomllib.loads((root / "uv.lock").read_text())
    return {p["name"]: p["version"] for p in lock["package"]}


def prepare(destination, version, *, source=None):
    destination = absolute(destination)
    source = absolute(source or Path(__file__).resolve().parents[3])
    if not VERSION.fullmatch(version):
        raise MaintenanceError("Use an exact supported astropy-iers-data version")
    if destination == source or destination.is_relative_to(source):
        raise MaintenanceError("Candidate must be outside the active source checkout")
    destination.mkdir()  # Exclusive; never replace an existing candidate.
    record = {
        "status": "acquisition_failed",
        "requested_version": version,
        "started_at": stamp(),
        "source_index": "https://pypi.org/simple",
        "source_package": "astropy-iers-data",
    }
    try:
        before = lock_versions(source)
        for name in SOURCE_ITEMS:
            item = source / name
            if item.is_dir():
                shutil.copytree(
                    item,
                    destination / name,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
                )
            else:
                shutil.copy2(item, destination / name)
        run(
            [
                "uv",
                "lock",
                "--default-index",
                "https://pypi.org/simple",
                "--upgrade-package",
                f"astropy-iers-data=={version}",
            ],
            destination,
        )
        after = lock_versions(destination)
        if after.get("astropy-iers-data") != version or {
            k: v for k, v in before.items() if k != "astropy-iers-data"
        } != {k: v for k, v in after.items() if k != "astropy-iers-data"}:
            raise MaintenanceError("Candidate changed unrelated locked dependencies")
        run(["uv", "sync", "--locked", "--python", sys.executable], destination)
        metadata = environment_probe(destination)
        if metadata["package_version"] != version:
            raise MaintenanceError(
                "Installed candidate identity differs from the exact request"
            )
        record.update(
            status="acquired",
            acquired_at=stamp(),
            metadata=metadata,
            source_sha256=source_hash(destination),
            lock_sha256=hashlib.sha256(
                (destination / "uv.lock").read_bytes()
            ).hexdigest(),
        )
        write_new(destination / "acquisition.json", record)
        return record
    except Exception:
        if not (destination / "acquisition.json").exists():
            write_new(destination / "acquisition.json", record)
        raise


def verify_candidate(root, *, require_current=True):
    root = absolute(root)
    acquired = read_json(root / "acquisition.json")
    if acquired.get("status") != "acquired" or acquired.get(
        "source_sha256"
    ) != source_hash(root):
        raise MaintenanceError(
            "Candidate source or lock differs from recorded acquisition"
        )
    metadata = environment_probe(root, require_current=require_current)
    for key in (
        "package_version",
        "sha256",
        "leap_seconds_sha256",
        "first_mjd",
        "last_mjd",
        "predictive_mjd",
    ):
        if metadata.get(key) != acquired.get("metadata", {}).get(key):
            raise MaintenanceError(
                "Candidate resource or metadata changed after acquisition"
            )
    return acquired, metadata


def validate(root):
    root = absolute(root)
    operation = uuid.uuid4().hex
    try:
        acquired, metadata = verify_candidate(root)
        python = str(root / ".venv/bin/python")
        run([python, "-m", "pytest", "-q", "--tb=short"], root)
        sgp4 = root / "sgp4-reference-results.json"
        transform = root / "transformation-reference-results.json"
        run(
            [python, "scripts/verify_scientific_references.py", "--output", str(sgp4)],
            root,
        )
        run(
            [
                python,
                "scripts/verify_earth_fixed_references.py",
                "--output",
                str(transform),
            ],
            root,
        )
        for path, expected in ((sgp4, 40), (transform, 6)):
            result = json.loads(path.read_text())
            if result.get("passed") != expected or result.get("failed") != 0:
                raise MaintenanceError("Required numerical references did not pass")
        record = {
            "status": "validated",
            "verified_at": stamp(),
            "acquired_at": acquired["acquired_at"],
            "source_sha256": acquired["source_sha256"],
            "metadata": metadata,
            "checks": {
                "backend_suite": "passed",
                "sgp4_references": 40,
                "terrestrial_references": 6,
            },
            "operation_id": operation,
        }
        write_new(root / f"validation-{operation}.json", record)
        atomic_json(root / "validation.json", record)
        return record
    except Exception:
        write_new(
            root / f"validation-failed-{operation}.json",
            {"status": "validation_failed", "at": stamp(), "operation_id": operation},
        )
        # An earlier passing record cannot authorize a new failed attempt.
        atomic_json(
            root / "validation.json", {"status": "validation_failed", "at": stamp()}
        )
        raise


@contextmanager
def operation_lock(state):
    state = absolute(state)
    state.mkdir(exist_ok=True)
    lock = state / ".operation.lock"
    with lock.open("x") as file:
        file.write("Explicit operator operation in progress\n")
    try:
        yield state
    finally:
        lock.unlink()


def selected_receipt(root, acquired, metadata, verified):
    return {
        "status": "selected",
        "candidate": str(root),
        "python": str(root / ".venv/bin/python"),
        "backend": str(root / "backend"),
        "package_version": metadata["package_version"],
        "sha256": metadata["sha256"],
        "leap_seconds_sha256": metadata["leap_seconds_sha256"],
        "acquired_at": acquired["acquired_at"],
        "verified_at": verified["verified_at"],
        "activated_at": stamp(),
        "source_sha256": acquired["source_sha256"],
    }


def verify_selection(receipt, *, require_current=False):
    root = absolute(receipt["candidate"])
    acquired, metadata = verify_candidate(root, require_current=require_current)
    verified = read_json(root / "validation.json")
    if (
        verified.get("status") != "validated"
        or verified.get("source_sha256") != acquired["source_sha256"]
    ):
        raise MaintenanceError("Candidate has no matching successful validation")
    if any(
        receipt.get(k) != metadata[k]
        for k in ("package_version", "sha256", "leap_seconds_sha256")
    ):
        raise MaintenanceError("Selected resource identity mismatch")
    return receipt


def activate(root, state):
    root = absolute(root)
    acquired, metadata = verify_candidate(root)
    verified = read_json(root / "validation.json")
    if (
        verified.get("status") != "validated"
        or verified.get("source_sha256") != acquired["source_sha256"]
    ):
        raise MaintenanceError(
            "Successful candidate validation is required before selection"
        )
    proposed = selected_receipt(root, acquired, metadata, verified)
    with operation_lock(state) as state:
        previous = (
            read_json(state / "active.json")
            if (state / "active.json").exists()
            else None
        )
        previous_history = (
            read_json(state / "previous.json")
            if (state / "previous.json").exists()
            else None
        )
        if previous:
            verify_selection(previous)
        operation = uuid.uuid4().hex
        history = state / "history"
        history.mkdir(exist_ok=True)
        write_new(
            history / f"{operation}-before.json",
            {"previous": previous, "proposed": proposed},
        )
        try:
            atomic_json(state / "active.json", proposed)
            verify_selection(read_json(state / "active.json"), require_current=True)
            atomic_json(state / "previous.json", {"previous": previous})
            write_new(history / f"{operation}-selected.json", proposed)
        except Exception:
            if previous is None:
                (state / "active.json").unlink(missing_ok=True)
            else:
                atomic_json(state / "active.json", previous)
            if previous_history is None:
                (state / "previous.json").unlink(missing_ok=True)
            else:
                atomic_json(state / "previous.json", previous_history)
            write_new(
                history / f"{operation}-failed.json",
                {"status": "selection_failed_previous_restored", "at": stamp()},
            )
            raise
    return proposed


def rollback(state):
    with operation_lock(state) as state:
        previous = read_json(state / "previous.json").get("previous")
        if not previous:
            raise MaintenanceError("No previous validated selection is recorded")
        verify_selection(previous)
        current = read_json(state / "active.json")
        operation = uuid.uuid4().hex
        write_new(
            state / "history" / f"{operation}-rollback-before.json",
            {"previous": previous, "current": current},
        )
        try:
            atomic_json(state / "active.json", previous)
            verify_selection(read_json(state / "active.json"))
        except Exception:
            atomic_json(state / "active.json", current)
            raise
        write_new(
            state / "history" / f"{operation}-rolled-back.json",
            {"status": "rolled_back", "at": stamp(), "selected": previous},
        )
    return previous


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    get = sub.add_parser("prepare")
    get.add_argument("--destination", type=Path, required=True)
    get.add_argument("--version", required=True)
    check = sub.add_parser("validate")
    check.add_argument("--candidate", type=Path, required=True)
    select = sub.add_parser("activate")
    select.add_argument("--candidate", type=Path, required=True)
    select.add_argument("--state", type=Path, required=True)
    back = sub.add_parser("rollback")
    back.add_argument("--state", type=Path, required=True)
    show = sub.add_parser("status")
    show.add_argument("--state", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = prepare(args.destination, args.version)
        elif args.command == "validate":
            result = validate(args.candidate)
        elif args.command == "activate":
            result = activate(args.candidate, args.state)
        elif args.command == "rollback":
            result = rollback(args.state)
        else:
            result = verify_selection(read_json(absolute(args.state) / "active.json"))
    except (ValueError, OSError, KeyError, TypeError, RuntimeError):
        parser.exit(
            1,
            (
                "EOP maintenance refused or failed. Existing "
                "environments are retained; inspect the operation"
                " receipts before retrying.\n"
            ),
        )
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
