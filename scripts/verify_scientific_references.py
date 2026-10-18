"""Audit published vectors. Run with PYTHONPATH=backend; no network or DB access."""

import argparse
import hashlib
import json
import math
from datetime import timedelta
from pathlib import Path

import sgp4
from orbitiq.orbits.elements import Elements
from orbitiq.orbits.engine import propagate, propagate_satellite
from sgp4.api import Satrec
from sgp4.conveniences import sat_epoch_datetime


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = {
        "reference": "Vallado AIAA 2006-6753; SGP4-VER.TLE/tcppver.out",
        "source_url": "https://celestrak.org/publications/AIAA/2006-6753/",
        "sgp4_version": sgp4.__version__,
        "frame": "TEME",
        "origin": "Earth center",
        "position_unit": "km",
        "velocity_unit": "km/s",
        "time_system": "UTC",
        "absolute_tolerances": {"position_km": 1e-5, "velocity_km_s": 1e-8},
        "relative_tolerance": 0,
        "inputs": {},
        "comparisons": [],
    }
    for name in ["vallado.json", "vallado-leo.json"]:
        path = root / "backend/tests/fixtures" / name
        for fixture in json.loads(path.read_text()):
            input_id = f"{name}:{fixture['catalog_id']}"
            satellite = Satrec.twoline2rv(*fixture["tle"])
            epoch = sat_epoch_datetime(satellite)
            elements = Elements.model_validate(fixture["omm"])
            output["inputs"][input_id] = {
                "fixture": str(path.relative_to(root)),
                "fixture_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "tle": fixture["tle"],
                "omm": fixture["omm"],
                "reference_epoch_utc": epoch.isoformat(),
            }
            for case in fixture["cases"]:
                at = epoch + timedelta(minutes=case["minutes"])
                for input_format in ["tle", "omm"]:
                    result = (
                        propagate_satellite(satellite, at)
                        if input_format == "tle"
                        else propagate(elements, at)
                    )
                    errors = {
                        key: [
                            abs(a - b)
                            for a, b in zip(result[key], case[key], strict=True)
                        ]
                        for key in ["position_km", "velocity_km_s"]
                    }
                    passed = all(
                        math.isclose(a, b, rel_tol=0, abs_tol=tolerance)
                        for key, tolerance in [
                            ("position_km", 1e-5),
                            ("velocity_km_s", 1e-8),
                        ]
                        for a, b in zip(result[key], case[key], strict=True)
                    )
                    output["comparisons"].append(
                        {
                            "input_ref": input_id,
                            "input_format": input_format,
                            "offset_minutes": case["minutes"],
                            "requested_time_utc": at.isoformat(),
                            "expected": {key: case[key] for key in errors},
                            "actual": {key: result[key] for key in errors},
                            "absolute_error": errors,
                            "passed": passed,
                        }
                    )
    output["passed"] = sum(c["passed"] for c in output["comparisons"])
    output["failed"] = len(output["comparisons"]) - output["passed"]
    args.output.write_text(json.dumps(output, indent=2) + "\n")
    print(f"Reference audit: {output['passed']} passed, {output['failed']} failed")
    if output["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
