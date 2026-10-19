"""Offline geodesy assessment against frozen independent GeographicLib results.

No reference downloads, database access or compiled reference dependency is
needed. --reference-executable optionally rechecks the fixture using the recorded
GeographicLib wrapper, explicitly supplied by an operator (see the phase report).
"""

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

from astropy import units as u
from astropy.coordinates import EarthLocation
from orbitiq.orbits.coordinates import geodetic, wrap_longitude

FIXTURE = (
    Path(__file__).resolve().parents[1] / "backend/tests/fixtures/phase611-geodesy.json"
)


def unrefined_geodetic(position):
    """The actual prior ERFA path, not an independent reference implementation."""
    lon, lat, height = EarthLocation.from_geocentric(*position, unit=u.km).to_geodetic(
        ellipsoid="WGS84"
    )
    return {
        "latitude_deg": float(lat.to_value(u.deg)),
        "longitude_deg": wrap_longitude(float(lon.to_value(u.deg))),
        "altitude_km": float(height.to_value(u.km)),
    }


def forward(ground):
    """Explicit ellipsoid equations; round-trip consistency only, not observations."""
    phi = math.radians(ground["latitude_deg"])
    lam = math.radians(ground["longitude_deg"])
    h = ground["altitude_km"]
    a, f = 6378.137, 1 / 298.257223563
    e2 = f * (2 - f)
    n = a / math.sqrt(1 - e2 * math.sin(phi) ** 2)
    return [
        (n + h) * math.cos(phi) * math.cos(lam),
        (n + h) * math.cos(phi) * math.sin(lam),
        (n * (1 - e2) + h) * math.sin(phi),
    ]


def errors(actual, expected):
    result = {key: abs(actual[key] - expected[key]) for key in expected}
    result["longitude_deg"] = abs(
        math.remainder(actual["longitude_deg"] - expected["longitude_deg"], 360)
    )
    return result


def evaluate(case):
    xyz = case["position_km"]
    before, actual = unrefined_geodetic(xyz), geodetic(xyz)
    error = errors(actual, case["expected"])
    roundtrip = {}
    for name, value in [("before", before), ("after", actual)]:
        reconstructed = forward(value)
        delta = [a - b for a, b in zip(reconstructed, xyz, strict=True)]
        roundtrip[name] = {
            "reconstructed_position_km": reconstructed,
            "signed_residual_km": delta,
            "vector_norm_km": math.hypot(*delta),
        }
    return {
        "reference": case,
        "before": before,
        "actual": actual,
        "absolute_errors_before": errors(before, case["expected"]),
        "absolute_errors_after": error,
        "independent_component_comparison_passed": all(
            error[k] <= case["tolerances"][k] for k in error
        ),
        "algebraic_roundtrip_consistency": roundtrip,
        "roundtrip_passed": roundtrip["after"]["vector_norm_km"]
        <= case["roundtrip_vector_norm_tolerance_km"],
    }


def audit(reference_executable=None):
    fixture = json.loads(FIXTURE.read_text())
    cases = [evaluate(case) for case in fixture["cases"]]
    rerun = None
    if reference_executable:
        text = "".join(
            "R " + " ".join(map(repr, c["position_km"])) + "\n"
            for c in fixture["cases"]
        )
        completed = subprocess.run(
            [str(reference_executable.resolve())],
            input=text,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        lines = completed.stdout.splitlines()
        if len(lines) != len(cases):
            raise ValueError("Independent reference returned an unexpected case count")
        rerun = {
            "executable": str(reference_executable),
            "stderr": completed.stderr,
            "decimal_outputs": lines,
            "matches_frozen_decimal_outputs": all(
                line.split() == case["reference_decimal_output"]
                for line, case in zip(lines, fixture["cases"], strict=True)
            ),
        }
    return {
        "kind": "independent_numerical_geodesy_not_satellite_observations",
        "fixture_sha256": hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
        "provenance": fixture["provenance"],
        "cases": cases,
        "independent_component_cases_passed": sum(
            c["independent_component_comparison_passed"] for c in cases
        ),
        "algebraic_roundtrip_cases_passed": sum(c["roundtrip_passed"] for c in cases),
        "case_count": len(cases),
        "reference_rerun": rerun,
        "observations_used": 0,
        "uncertainty_quantified": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference-executable", type=Path)
    args = parser.parse_args()
    result = audit(args.reference_executable)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    passed = (
        result["independent_component_cases_passed"] == result["case_count"]
        and result["algebraic_roundtrip_cases_passed"] == result["case_count"]
        and (
            result["reference_rerun"] is None
            or result["reference_rerun"]["matches_frozen_decimal_outputs"]
        )
    )
    print(
        f"Geodesy: {result['independent_component_cases_passed']}/"
        f"{result['case_count']} independent cases; "
        f"{result['algebraic_roundtrip_cases_passed']} separate round-trips"
    )
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
