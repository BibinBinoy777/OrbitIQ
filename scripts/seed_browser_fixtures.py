"""Create ONLY a fresh disposable E1 fixture volume; never read an operator DB.

Reference-derived elements and deliberately altered second record are synthetic
UI inputs, not genuine archive history. Observation offsets are arithmetic tests.
"""

import argparse
import copy
import hashlib
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from orbitiq.database import initialize
from orbitiq.orbits.elements import Elements
from orbitiq.services import analysis
from orbitiq.services.observation_validation import create
from orbitiq.storage import save_snapshot


def seed(directory: Path, reference: Path, *, local_owner: bool = False):
    if not directory.is_absolute() or directory.is_symlink():
        raise ValueError("Explicit absolute fresh fixture directory required")
    if any(directory.iterdir()):
        raise ValueError("Refusing to overwrite a nonempty fixture directory")
    database = directory / "archive.sqlite3"
    initialize(database)
    first = json.loads(reference.read_text())[0]["omm"]
    first["OBJECT_NAME"] = "E1 SYNTHETIC UI FIXTURE - NOT OBSERVED HISTORY"
    second = copy.deepcopy(first)
    second["EPOCH"] = (
        Elements.model_validate(first).epoch + timedelta(hours=6)
    ).isoformat()
    second["MEAN_MOTION"] += 0.001
    second["INCLINATION"] += 0.01
    second["ECCENTRICITY"] += 0.00001
    ids = []
    for index, record in enumerate([first, second]):
        # The immutable application schema requires this URL shape. No network
        # request occurs, and this is NOT a receipt from the named provider.
        ids.append(
            save_snapshot(
                database,
                json.dumps([record]).encode(),
                record,
                Elements.model_validate(record),
                "https://celestrak.org/NORAD/elements/gp.php?CATNR=6251&FORMAT=JSON",
                datetime(2026, 10, 17 + index, tzinfo=UTC),
            )
        )
    records = []
    for i in range(2):
        at = Elements.model_validate(first).epoch + timedelta(minutes=i)
        position = analysis.position(database, ids[0], at)["position_km"]
        records.append(
            {
                "observation_id": f"SYNTHETIC-ONLY-{i}",
                "catalog_id": 6251,
                "source_id": "isolated-reference-fixture-not-observation-provider",
                "source_record_reference": f"synthetic-arithmetic-record-{i}",
                "observed_at": at.isoformat(),
                "time_scale": "UTC",
                "frame": "TEME",
                "origin": "Earth center",
                "unit": "km",
                "measurement_type": "geocentric_cartesian_position",
                "data_kind": "measurement",
                "quality": "accepted",
                "position": [position[0] + 3, position[1] - 4, position[2]],
            }
        )
    archive = directory / "validation"
    archive.mkdir(mode=0o700)
    run_id = "e1" * 16
    report = create(
        (database, ids[0]),
        json.dumps(
            {
                "kind": "orbitiq_observation_input",
                "schema_version": 1,
                "observations": records,
            }
        ).encode(),
        archive / run_id,
        now=datetime(2026, 10, 20, tzinfo=UTC),
    )
    assert report["summary"]["independently_verified_count"] == 0
    assert all(s["residual"]["magnitude_km"] == 5 for s in report["samples"])
    database.chmod(0o444)
    if not local_owner:
        for path in [archive, *archive.rglob("*")]:
            os.chown(path, 10001, 10001)  # Existing release API UID; read-only mount.
    return {
        "fixture": "SYNTHETIC UI INPUTS; NOT SATELLITE OBSERVATIONS",
        "catalog": 6251,
        "first": ids[0],
        "second": ids[1],
        "run_id": run_id,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path("/fixtures"))
    parser.add_argument(
        "--local-owner",
        action="store_true",
        help="Use the bundled synthetic fixture and retain current-user ownership",
    )
    args = parser.parse_args(argv)
    reference = (
        Path(__file__).resolve().parents[1] / "backend/tests/fixtures/vallado-leo.json"
        if args.local_owner
        else Path("/reference.json")
    )
    result = seed(args.directory, reference, local_owner=args.local_owner)
    if args.local_owner:
        result.update(
            synthetic_only=True,
            database=str(args.directory / "archive.sqlite3"),
            database_sha256=hashlib.sha256(
                (args.directory / "archive.sqlite3").read_bytes()
            ).hexdigest(),
        )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
