"""Explicit encrypted archive export/retrieval using the established restic CLI.

Repository initialization, retention deletion and scheduling are operator actions.
"""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import stat
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

from fastapi.testclient import TestClient

from orbitiq.api.orbits import database_path
from orbitiq.database import configured_path
from orbitiq.main import create_app
from orbitiq.maintenance.monitor import atomic_state
from orbitiq.maintenance.recovery import fingerprint, rehearse
from orbitiq.runtime import Settings
from orbitiq.storage import verify_archive


class ExportError(RuntimeError):
    pass


def protected_file(path: Path):
    if (
        not path.is_absolute()
        or path.is_symlink()
        or not path.is_file()
        or path.stat().st_uid != os.getuid()
        or stat.S_IMODE(path.stat().st_mode) & 0o077
        or not 0 < path.stat().st_size <= 4096
    ):
        raise ExportError(
            "Operator files must be absolute, owned, nonempty and private"
        )


def repository_kind(path: Path, allow_local_test: bool):
    protected_file(path)
    value = path.read_text().strip()
    if value.startswith("s3:https://"):
        url = urlsplit(value[3:])
        if (
            url.hostname
            and url.path.strip("/")
            and not (url.username or url.password or url.query or url.fragment)
            and url.port in (None, 443)
        ):
            return "external"
    elif re.fullmatch(
        r"sftp:(?:[A-Za-z0-9_.-]+@)?[A-Za-z0-9][A-Za-z0-9.-]*:/[^\r\n]+", value
    ):
        return "external"
    elif Path(value).is_absolute() and allow_local_test:
        return "local_test"
    raise ExportError(
        "Select an approved SFTP/HTTPS-S3 repository; local requires test mode"
    )


def restic(binary, repository, password, *args):
    command = [
        str(binary),
        "--repository-file",
        str(repository),
        "--password-file",
        str(password),
        "--no-cache",
        *args,
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=1800,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise ExportError("Encrypted storage command could not complete") from None
    if result.returncode:
        # Never echo repository URLs, credentials, subprocess arguments or stderr.
        raise ExportError(
            "Encrypted storage command failed; no recovery success confirmed"
        )
    if len(result.stdout.encode()) > 1024 * 1024:
        raise ExportError("Encrypted storage result exceeded the supported bound")
    return result.stdout


def export_and_verify(
    source,
    directory,
    binary,
    repository,
    password,
    *,
    allow_local_test=False,
    independent_destination_approved=False,
):
    if not directory.is_absolute() or directory.exists():
        raise ExportError("Select an absolute, new working directory")
    protected_file(password)
    kind = repository_kind(repository, allow_local_test)
    if kind == "local_test" and independent_destination_approved:
        raise ExportError("A local test cannot attest off-machine independence")
    directory.mkdir(mode=0o700)
    # Existing verifier reserves new files, validates all payloads and tests APIs.
    local = rehearse(source, directory / "point")
    output = restic(
        binary,
        repository,
        password,
        "backup",
        "--json",
        "--tag",
        "orbitiq-archive-v1",
        "--",
        str(directory / "point"),
    )
    summaries = [json.loads(line) for line in output.splitlines() if line.strip()]
    if any(not isinstance(row, dict) for row in summaries):
        raise ExportError("Encrypted backup receipt was not valid")
    summaries = [row for row in summaries if row.get("message_type") == "summary"]
    if len(summaries) != 1 or not re.fullmatch(
        r"[a-f0-9]{64}", str(summaries[0].get("snapshot_id", ""))
    ):
        raise ExportError("Encrypted backup receipt was not valid")
    snapshot = summaries[0]["snapshot_id"]
    target = directory / "retrieved"
    target.mkdir(mode=0o700)
    restic(
        binary,
        repository,
        password,
        "restore",
        snapshot + ":" + str(directory / "point"),
        "--target",
        str(target),
        "--verify",
    )
    retrieved = target / "backup.sqlite3"
    if hashlib.sha256(retrieved.read_bytes()).hexdigest() != local["backup_sha256"]:
        raise ExportError("Retrieved backup checksum does not match the backup point")
    actual = fingerprint(retrieved)
    if actual != local["source_at_backup"]:
        raise ExportError("Retrieved schema or archive contents do not match")
    verified = verify_archive(retrieved)
    app = create_app(Settings(environment="test"))
    app.dependency_overrides[database_path] = lambda: retrieved
    api = []
    with TestClient(app) as client:
        listing = client.get("/api/snapshots", params={"limit": 2})
        api.append({"route": "/api/snapshots", "status": listing.status_code})
        ids = [s["id"] for s in listing.json().get("snapshots", [])]
        for sid in ids:
            response = client.get(f"/api/snapshots/{sid}")
            api.append(
                {"route": f"/api/snapshots/{sid}", "status": response.status_code}
            )
        if ids:
            response = client.get(
                "/api/comparisons",
                params={
                    "first_id": ids[0],
                    "second_id": ids[-1],
                },
            )
            api.append({"route": "/api/comparisons", "status": response.status_code})
    if any(r["status"] != 200 for r in api):
        raise ExportError("Retrieved archive API verification failed")
    # A moving live source is not silently called equal to this backup point.
    if fingerprint(source) != local["source_at_backup"]:
        raise ExportError(
            "Source changed; evaluate the preserved backup point explicitly"
        )
    result = {
        "schema_version": 1,
        "status": "passed",
        "completed_at": datetime.now(UTC).isoformat(),
        "repository_kind": kind,
        "encrypted_repository": True,
        "restic_snapshot_id": snapshot,
        "backup_sha256": local["backup_sha256"],
        "backup_bytes": local["backup_bytes"],
        "source_at_backup": actual,
        "verified_snapshots": verified,
        "api_checks": api,
        "retrieved_into_separate_target": True,
        "source_unchanged": True,
        "remote_roundtrip_verified": kind == "external",
        "independent_destination_approved": independent_destination_approved,
        "off_machine_recovery_verified": kind == "external"
        and independent_destination_approved,
        "independence_basis": "explicit operator approval; not inferred from a URL",
    }
    with (directory / "export-verification.json").open("x") as file:
        json.dump(result, file, indent=2)
        file.write("\n")
    return result


def job_status(path, result=None):
    if (
        not path.is_absolute()
        or path.is_symlink()
        or not path.parent.is_dir()
        or path.parent.stat().st_mode & 0o077
        or path.parent.stat().st_uid != os.getuid()
    ):
        raise ExportError("Backup status requires a private operator-owned directory")
    if path.exists():
        if path.stat().st_size > 65536:
            raise ExportError("Unrecognized backup status file preserved")
        existing = json.loads(path.read_text())
        if (
            not isinstance(existing, dict)
            or existing.get("kind") != "orbitiq_backup_job"
            or existing.get("schema_version") != 1
        ):
            raise ExportError("Unrecognized backup status file preserved")
    if result is not None:
        atomic_state(path, {"kind": "orbitiq_backup_job", **result})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--restic", type=Path, required=True)
    parser.add_argument("--repository-file", type=Path, required=True)
    parser.add_argument("--password-file", type=Path, required=True)
    parser.add_argument("--status-file", type=Path, required=True)
    parser.add_argument("--allow-local-test", action="store_true")
    parser.add_argument("--independent-destination-approved", action="store_true")
    args = parser.parse_args()
    os.umask(0o077)
    try:
        job_status(args.status_file)
        result = export_and_verify(
            configured_path(),
            args.directory,
            args.restic,
            args.repository_file,
            args.password_file,
            allow_local_test=args.allow_local_test,
            independent_destination_approved=args.independent_destination_approved,
        )
        job_status(args.status_file, result)
    except (
        OSError,
        ValueError,
        RuntimeError,
        sqlite3.Error,
        subprocess.SubprocessError,
    ):
        try:
            job_status(
                args.status_file,
                {
                    "schema_version": 1,
                    "status": "failed",
                    "completed_at": datetime.now(UTC).isoformat(),
                    "off_machine_recovery_verified": False,
                    "remote_roundtrip_verified": False,
                },
            )
        except (OSError, ValueError, RuntimeError):
            pass
        parser.exit(
            1, "Backup/export verification failed; inspect private job artifacts.\n"
        )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
