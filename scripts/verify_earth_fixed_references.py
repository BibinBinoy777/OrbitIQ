"""Reproduce Phase 3 numerical evidence. No download, database or app startup."""

import argparse
import hashlib
import json
import math
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import astropy
import erfa
from astropy import units as u
from astropy.time import Time
from astropy.utils import iers
from orbitiq.orbits import earth_orientation as eo
from orbitiq.orbits.coordinates import earth_fixed, geodetic
from orbitiq.orbits.engine import propagate_satellite
from sgp4.api import Satrec

FIXTURE = (
    Path(__file__).resolve().parents[1] / "backend/tests/fixtures/earth-fixed.json"
)


def audit():
    reference = json.loads(FIXTURE.read_text())
    results = []
    c = reference["vallado"]
    state = {
        "at": c["at"],
        "orbital_epoch": c["at"],
        "frame": "TEME",
        "time_system": "UTC",
        "units": {"position": "km", "velocity": "km/s"},
        "position_km": c["position_km"],
        "velocity_km_s": c["velocity_km_s"],
    }
    data = eo.resources()
    e = c["published_eop"]
    table = iers.IERS_B()
    table["MJD"] = [53100, 53101, 53102, 53103] * u.d
    table["UT1_UTC"] = [e["ut1_minus_utc_seconds"]] * 4 * u.s
    table["PM_x"] = [e["polar_motion_x_arcsec"]] * 4 * u.arcsec
    table["PM_y"] = [e["polar_motion_y_arcsec"]] * 4 * u.arcsec
    with patch.object(
        eo,
        "resources",
        return_value=replace(
            data,
            table=table,
            metadata={
                **data.metadata,
                "source": "Vallado published fixed-EOP reference fixture (not runtime)",
                "sha256": hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
                "first_mjd": 53100.0,
                "last_mjd": 53103.0,
            },
        ),
    ):
        fixed = earth_fixed(state)
    bundled = earth_fixed(state)
    for mode, r in [("fixed", fixed), ("bundled", bundled)]:
        tol = c[mode + "_eop_tolerances"]
        errors = {
            k: [abs(a - b) for a, b in zip(r[k], c["expected_" + k], strict=True)]
            for k in ["position_km", "velocity_km_s"]
        }
        results.append(
            {
                "case": "Vallado Appendix C / " + mode + " EOP",
                "reference": c,
                "actual_position_km": r["position_km"],
                "actual_velocity_km_s": r["velocity_km_s"],
                "actual_eop": r["earth_orientation"],
                "eop_override": e if mode == "fixed" else None,
                "absolute_error": errors,
                "absolute_tolerances": tol,
                "passed": all(max(errors[k]) <= tol[k] for k in errors),
            }
        )
    c = reference["astropy_example"]
    sat = Satrec.twoline2rv(*c["tle"])
    state = {
        **state,
        "at": c["at"],
        "orbital_epoch": c["at"],
        **propagate_satellite(sat, datetime.fromisoformat(c["at"])),
    }
    r = earth_fixed(state)
    expected = c["expected"]
    actual = r["geodetic"]
    errors = {k: abs(actual[k] - v) for k, v in expected.items()}
    results.append(
        {
            "case": "Astropy official satellite example",
            "reference": c,
            "input_teme": state,
            "actual": actual,
            "actual_eop": r["earth_orientation"],
            "absolute_error": errors,
            "passed": all(
                errors[k]
                <= c["tolerances"][
                    "altitude_km" if k == "altitude_km" else "angles_deg"
                ]
                for k in errors
            ),
        }
    )
    c = reference["sofa_geodesy"]
    r = geodetic(c["position_km"])
    expected = {
        "latitude_deg": math.degrees(c["expected_latitude_rad"]),
        "longitude_deg": math.degrees(c["expected_longitude_rad"]),
        "altitude_km": c["expected_altitude_km"],
    }
    errors = {k: abs(r[k] - v) for k, v in expected.items()}
    results.append(
        {
            "case": "SOFA gc2gd WGS84",
            "reference": c,
            "expected": expected,
            "actual": r,
            "absolute_error": errors,
            "passed": all(x <= 1e-10 for x in errors.values()),
        }
    )
    c = reference["sofa_time"]
    with eo.orientation():
        t = Time(*c["utc_jd_parts"], format="jd", scale="utc")
        t.delta_ut1_utc = c["ut1_minus_utc_seconds"]
        for scale in ["tai", "ut1"]:
            actual = getattr(t, scale)
            expected = Time(*c[f"expected_{scale}_jd_parts"], format="jd", scale=scale)
            error = (
                abs((actual.jd1 - expected.jd1) + (actual.jd2 - expected.jd2)) * 86400
            )
            results.append(
                {
                    "case": "SOFA UTC -> " + scale.upper(),
                    "reference": c,
                    "at_utc": t.isot,
                    "actual_jd_parts": [float(actual.jd1), float(actual.jd2)],
                    "absolute_error_seconds": float(error),
                    "passed": error < c["tolerance_seconds"],
                }
            )
    passed = sum(bool(r["passed"]) for r in results)
    return {
        "astropy_version": astropy.__version__,
        "pyerfa_version": erfa.__version__,
        "fixture_sha256": hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
        "eop_resource": data.metadata,
        "relative_tolerance": 0,
        "cases": results,
        "passed": passed,
        "failed": len(results) - passed,
        "limitations": (
            "Finite selected numerical cases; not observational accuracy or universal "
            "frame accuracy. Fixed EOP is reference-only, "
            "never an application fallback."
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit()
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"{result['passed']} reference cases passed; {result['failed']} failed")
    raise SystemExit(bool(result["failed"]))
