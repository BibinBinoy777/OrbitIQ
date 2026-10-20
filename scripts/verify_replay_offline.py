"""Verify an existing replay bundle with DB access/network connections forbidden."""

import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True)
    parser.add_argument("--expected-manifest-sha256", required=True)
    args = parser.parse_args()
    os.environ.pop("ORBITIQ_DATABASE_PATH", None)
    attempts = {"network": 0, "database": 0}

    def audit(event, _):
        if event in {"socket.connect", "socket.getaddrinfo", "socket.sendto"}:
            attempts["network"] += 1
            raise RuntimeError("Offline verification forbids network access")
        if event == "sqlite3.connect":
            attempts["database"] += 1
            raise RuntimeError("Offline verification forbids database access")

    sys.addaudithook(audit)
    # Audit starts before importing scientific libraries or reading the bundle.
    from orbitiq import replay

    result = replay.verify(args.directory, args.expected_manifest_sha256)
    result["offline_audit"] = {
        "attempts": attempts,
        "database_configuration_present": False,
    }
    print(replay.encoded(result).decode(), end="")
    return (
        0
        if result["status"] in {"matched", "verified_source_only"}
        and not any(attempts.values())
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
