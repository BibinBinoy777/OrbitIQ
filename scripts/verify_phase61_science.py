"""Offline Phase 6.1 reference investigation; never reads an application database.

Independent mathematical reference generation uses Decimal + explicit rotations,
not OrbitIQ/Astropy/ERFA transformation outputs. It is verification code only.
"""

import argparse
import hashlib
import json
import math
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, localcontext
from pathlib import Path
from unittest.mock import patch

import astropy
import erfa
import sgp4
from astropy import units as u
from astropy.time import Time
from astropy.utils import iers
from orbitiq.orbits import earth_orientation as eo
from orbitiq.orbits.coordinates import earth_fixed, geodetic
from orbitiq.orbits.elements import Elements
from orbitiq.orbits.engine import propagate, propagate_satellite
from sgp4.api import Satrec
from sgp4.conveniences import sat_epoch_datetime

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "backend/tests/fixtures"


def exact_utc_jd(value):
    """Nominal UTC date away from leap-second spellings, as an exact Decimal."""
    at = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    seconds = Decimal(at.hour * 3600 + at.minute * 60 + at.second) + Decimal(
        at.microsecond
    ) / Decimal(1000000)
    return (
        Decimal("2451544.5")
        + Decimal((at.date() - date(2000, 1, 1)).days)
        + seconds / Decimal(86400)
    )


def reference_sidereal(at, dut1):
    """Vallado C-1, 50-digit time/polynomial; double sin/cos only afterwards."""
    with localcontext() as context:
        context.prec = 50
        jd = exact_utc_jd(at) + Decimal(str(dut1)) / Decimal(86400)
        t = (jd - Decimal(2451545)) / Decimal(36525)
        coefficient = Decimal(876600 * 3600) + Decimal("8640184.812866")
        seconds = (
            Decimal("67310.54841")
            + coefficient * t
            + Decimal("0.093104") * t * t
            - Decimal("0.0000062") * t * t * t
        )
        turns = (seconds / Decimal(86400)) % 1
        if turns < 0:
            turns += 1
        derivative = (
            coefficient + Decimal("0.186208") * t - Decimal("0.0000186") * t * t
        )
        rate = float(derivative / (Decimal(36525) * Decimal(86400))) * math.pi / 43200
        return float(turns) * math.tau, rate


def single_jd_sidereal(jd):
    """Controlled legacy double-precision evaluation, not a runtime alternative."""
    t = (jd - 2451545) / 36525
    seconds = (
        -6.2e-6 * t * t * t
        + 0.093104 * t * t
        + (876600 * 3600 + 8640184.812866) * t
        + 67310.54841
    )
    return (seconds * math.pi / 43200) % math.tau


def reference_transform(case, *, angle=None, rate=None):
    """Explicit R3/IAU-1980 polar rotations + analytic fixed-EOP derivative.

    Parameters are controlled mathematical inputs, not historical measurements.
    sp=0 is the existing Vallado TEME convention; no GCRS precession is added.
    """
    e = case["eop"]
    theta, omega = reference_sidereal(case["at"], e["ut1_minus_utc_seconds"])
    if angle is not None:
        theta = angle
    if rate is not None:
        omega = rate
    c, s = math.cos(theta), math.sin(theta)

    def rotate(vector):
        x, y, z = vector
        return [c * x + s * y, -s * x + c * y, z]

    xp = math.radians(e["polar_motion_x_arcsec"] / 3600)
    yp = math.radians(e["polar_motion_y_arcsec"] / 3600)
    cx, sx, cy, sy = math.cos(xp), math.sin(xp), math.cos(yp), math.sin(yp)
    matrix = [[cx, 0, sx], [sx * sy, cy, -cx * sy], [-sx * cy, sy, cx * cy]]

    def polar(vector):
        return [sum(a * b for a, b in zip(row, vector, strict=True)) for row in matrix]

    p = rotate(case["position_km"])
    v = rotate(case["velocity_km_s"])
    v = [v[0] + omega * p[1], v[1] - omega * p[0], v[2]]
    return {
        "position_km": polar(p),
        "velocity_km_s": polar(v),
        "gmst82_rad": theta,
        "rotation_rate_rad_s": omega,
    }


def reference_cartesian(latitude, longitude, height):
    """Independent WGS84 forward ellipsoid equation, not ERFA's inverse routine."""
    a = 6378.137
    f = 1 / 298.257223563
    e2 = f * (2 - f)
    phi, lam = math.radians(latitude), math.radians(longitude)
    n = a / math.sqrt(1 - e2 * math.sin(phi) ** 2)
    return [
        (n + height) * math.cos(phi) * math.cos(lam),
        (n + height) * math.cos(phi) * math.sin(lam),
        (n * (1 - e2) + height) * math.sin(phi),
    ]


def state(case):
    return {
        "at": case["at"],
        "orbital_epoch": case["at"],
        "frame": "TEME",
        "time_system": "UTC",
        "units": {"position": "km", "velocity": "km/s"},
        "position_km": case["position_km"],
        "velocity_km_s": case["velocity_km_s"],
    }


def controlled_resources(case):
    """Reference-only table. Never installed/selected by normal API requests."""
    data = eo.resources()
    e = case["eop"]
    with eo.orientation():
        mjd = math.floor(Time(case["at"], scale="utc").mjd)
    table = iers.IERS_B()
    table["MJD"] = [mjd - 1, mjd, mjd + 1, mjd + 2] * u.d
    table["UT1_UTC"] = [e["ut1_minus_utc_seconds"]] * 4 * u.s
    table["PM_x"] = [e["polar_motion_x_arcsec"]] * 4 * u.arcsec
    table["PM_y"] = [e["polar_motion_y_arcsec"]] * 4 * u.arcsec
    return replace(
        data,
        table=table,
        metadata={
            **data.metadata,
            "source": (
                "Controlled mathematical verification parameters; not "
                "historical EOP observations"
            ),
            "first_mjd": mjd - 1,
            "last_mjd": mjd + 2,
        },
    )


def vector_errors(actual, expected):
    residual = [a - b for a, b in zip(actual, expected, strict=True)]
    return {
        "signed": residual,
        "max_absolute_component": max(abs(v) for v in residual),
        "euclidean_norm": math.hypot(*residual),
    }


def residual_investigation():
    original = json.loads((FIXTURES / "earth-fixed.json").read_text())["vallado"]
    case = {**original, "eop": original["published_eop"]}
    with patch.object(eo, "resources", return_value=controlled_resources(case)):
        actual = earth_fixed(state(case))
    exact = reference_transform(case)
    e = case["eop"]
    with eo.orientation():
        t = Time(case["at"], scale="utc")
        t.precision = 9
        t.delta_ut1_utc = e["ut1_minus_utc_seconds"]
        ut1 = t.ut1
        jd1, jd2 = float(ut1.jd1), float(ut1.jd2)
        collapsed = float(ut1.jd)
        utc_then_dut1 = float(t.jd) + e["ut1_minus_utc_seconds"] / 86400
        scales = {
            "utc": t.isot,
            "tai": t.tai.isot,
            "tt": t.tt.isot,
            "ut1": ut1.isot,
            "ut1_jd_parts": [jd1, jd2],
            "tai_minus_utc_seconds": 32,
            "tt_minus_tai_seconds": 32.184,
        }
        erfa_angle = float(erfa.gmst82(jd1, jd2))
    cases = {
        "orbitIQ_current_two_part": {
            key: actual[key] for key in ["position_km", "velocity_km_s"]
        },
        "independent_decimal_equation": exact,
        "single_UT1_JD_then_polynomial": reference_transform(
            case, angle=single_jd_sidereal(collapsed)
        ),
        "single_UTC_JD_plus_DUT1_then_polynomial": reference_transform(
            case, angle=single_jd_sidereal(utc_then_dut1)
        ),
    }
    # Constant omega/LOD ablations use the archived Vallado example conventions;
    # the paper itself does not supply LOD, so these do not prove its exact run.
    velocity_variants = []
    for omega in [7.292115e-5, 7.29211514670698e-5]:
        for lod in [0, 0.0015563]:
            value = reference_transform(
                case,
                angle=single_jd_sidereal(utc_then_dut1),
                rate=omega * (1 - lod / 86400),
            )
            velocity_variants.append(
                {
                    "nominal_omega_rad_s": omega,
                    "lod_seconds": lod,
                    "actual_velocity_km_s": value["velocity_km_s"],
                    "residual_km_s": vector_errors(
                        value["velocity_km_s"], original["expected_velocity_km_s"]
                    ),
                }
            )
    variants = {}
    for name, value in cases.items():
        variants[name] = {
            **value,
            "position_residual_km": vector_errors(
                value["position_km"], original["expected_position_km"]
            ),
            "velocity_residual_km_s": vector_errors(
                value["velocity_km_s"], original["expected_velocity_km_s"]
            ),
        }
    old = variants["orbitIQ_current_two_part"]["position_residual_km"]
    return {
        "reference": original,
        "orbital_elements": None,
        "orbital_epoch": None,
        "orbital_input_explanation": (
            "Published standalone TEME Cartesian state, not an SGP4 "
            "propagation case; epoch=transform evaluation time; no "
            "TLE/OMM is specified by the paper for this vector."
        ),
        "time_scales": scales,
        "variants": variants,
        "single_UT1_rounding_error_microseconds": ((collapsed - jd1) - jd2)
        * 86400
        * 1e6,
        "UTC_plus_DUT1_rounding_error_microseconds": ((utc_then_dut1 - jd1) - jd2)
        * 86400
        * 1e6,
        "independent_GMST_minus_erfa_rad": exact["gmst82_rad"] - erfa_angle,
        "independent_decimal_vs_current_position_km": vector_errors(
            exact["position_km"], actual["position_km"]
        ),
        "velocity_convention_ablations": velocity_variants,
        "existing_tolerances_unchanged": original["fixed_eop_tolerances"],
        "original_position_max_component_cm": old["max_absolute_component"] * 1e5,
        "original_position_vector_norm_cm": old["euclidean_norm"] * 1e5,
        "conclusion": (
            "Dominant reference-evaluation precision/order mismatch "
            "reproduced; no OrbitIQ position transformation defect "
            "demonstrated. The exact historical paper runtime and "
            "remaining submillimetre terms are not certified."
        ),
        "observation_based_accuracy_demonstrated": False,
    }


def additional_sgp4():
    fixture = json.loads((FIXTURES / "phase61-sgp4.json").read_text())
    results = []
    for source in fixture["inputs"]:
        sat = Satrec.twoline2rv(*source["tle"])
        elements = Elements.model_validate(source["omm"])
        epoch = sat_epoch_datetime(sat)
        for vector in source["cases"]:
            at = epoch + timedelta(minutes=vector["minutes"])
            for kind in ["tle", "omm"]:
                actual = (
                    propagate_satellite(sat, at)
                    if kind == "tle"
                    else propagate(elements, at)
                )
                errors = {
                    key: vector_errors(actual[key], vector[key])
                    for key in ["position_km", "velocity_km_s"]
                }
                results.append(
                    {
                        "catalog_id": source["catalog_id"],
                        "input_format": kind,
                        "source_line": vector["source_line"],
                        "epoch": epoch.isoformat(),
                        "at": at.isoformat(),
                        "offset_minutes": vector["minutes"],
                        "expected": vector,
                        "actual": {key: actual[key] for key in errors},
                        "residuals": errors,
                        "passed": all(
                            errors[key]["max_absolute_component"]
                            <= fixture["tolerances"][key]
                            for key in errors
                        ),
                    }
                )
    return {
        "reference": fixture,
        "distinct_published_vectors": sum(len(s["cases"]) for s in fixture["inputs"]),
        "comparisons": results,
    }


def additional_terrestrial():
    fixture = json.loads((FIXTURES / "phase61-terrestrial.json").read_text())
    transforms = []
    geometry = []
    times = []
    for case in fixture["transforms"]:
        with patch.object(eo, "resources", return_value=controlled_resources(case)):
            actual = earth_fixed(state(case))
        expected = case["expected"]
        errors = {
            key: vector_errors(actual[key], expected[key])
            for key in ["position_km", "velocity_km_s"]
        }
        transforms.append(
            {
                "reference": case,
                "actual": {key: actual[key] for key in errors},
                "residuals": errors,
                "passed": all(
                    errors[key]["max_absolute_component"] <= case["tolerances"][key]
                    for key in errors
                ),
            }
        )
    for case in fixture["geodesy"]:
        actual = geodetic(case["position_km"])
        expected = case["expected"]
        errors = {key: abs(actual[key] - expected[key]) for key in expected}
        geometry.append(
            {
                "reference": case,
                "actual": actual,
                "absolute_residuals": errors,
                "passed": all(errors[key] <= case["tolerances"][key] for key in errors),
            }
        )
    with eo.orientation():
        for case in fixture["time_components"]:
            if case["id"] == "SOFA_GMST82":
                actual = float(erfa.gmst82(*case["input_jd_parts"]))
                error = abs(actual - case["expected_rad"])
                times.append(
                    {
                        "reference": case,
                        "actual_rad": actual,
                        "absolute_residual_rad": error,
                        "passed": error <= case["tolerance_rad"],
                    }
                )
                continue
            t = Time(*case["input_jd_parts"], format="jd", scale=case["input_scale"])
            if "dut1_seconds" in case:
                t.delta_ut1_utc = case["dut1_seconds"]
            actual = getattr(t, case["output_scale"])
            expected = case["expected_jd_parts"]
            error = (
                abs(
                    (float(actual.jd1) - expected[0])
                    + (float(actual.jd2) - expected[1])
                )
                * 86400
            )
            times.append(
                {
                    "reference": case,
                    "actual_jd_parts": [float(actual.jd1), float(actual.jd2)],
                    "absolute_residual_seconds": error,
                    "passed": error <= case["tolerance_seconds"],
                }
            )
    return {
        "reference_metadata": fixture["provenance"],
        "mathematical_transform_cases": transforms,
        "mathematical_geodesy_cases": geometry,
        "published_component_cases": times,
    }


def geodesy_precision_assessment():
    """Reassess the unchanged target; preserve historical failures in old reports."""
    case = json.loads((FIXTURES / "phase61-terrestrial.json").read_text())["geodesy"][
        -1
    ]
    actual = geodetic(case["position_km"])
    x, y, z = case["position_km"]
    rho = math.hypot(x, y)
    a, f = 6378.137, 1 / 298.257223563
    e2 = f * (2 - f)
    phi = math.atan2(z, rho * (1 - e2))
    for _ in range(20):
        normal = a / math.sqrt(1 - e2 * math.sin(phi) ** 2)
        phi = math.atan2(z + e2 * normal * math.sin(phi), rho)
    forward = reference_cartesian(
        actual["latitude_deg"], actual["longitude_deg"], actual["altitude_km"]
    )
    errors = vector_errors(forward, case["position_km"])
    scan = []
    for height in [0, 400, 1000, 10000, 20000, 35786, 100000]:
        observed = geodetic(reference_cartesian(45, -120, height))
        scan.append(
            {
                "height_km": height,
                "latitude_error_deg": observed["latitude_deg"] - 45,
                "height_error_km": observed["altitude_km"] - height,
            }
        )
    error = abs(actual["latitude_deg"] - case["expected"]["latitude_deg"])
    return {
        "status": "FAIL" if error > case["tolerances"]["latitude_deg"] else "PASS",
        "reference": case,
        "actual": actual,
        "latitude_error_deg": error,
        "unchanged_target_deg": case["tolerances"]["latitude_deg"],
        "independent_fixed_point_inverse_latitude_deg": math.degrees(phi),
        "independent_forward_reprojection_error_km": errors,
        "altitude_scan": scan,
        "source_algorithm": (
            "ERFA finite Halley seed + residual-checked exterior Newton step"
        ),
        "source_scope": (
            "Source below describes the seed; see Phase 6.1.1 for refinement"
        ),
        "source_url": (
            "https://raw.githubusercontent.com/liberfa/erfa/v2.0.1/src/gc2gde.c"
        ),
        "source_sha256": (
            "402b00e018605f574cfa5471113519e3de2a3e1b360aa8604e82465112caaae3"
        ),
        "conclusion": (
            "Phase 6.1.1 meets the unchanged latitude target using a checked "
            "exterior Newton correction of the ERFA seed. Historical Phase 6.1 "
            "failure evidence is preserved; this is not prediction accuracy."
            if error <= case["tolerances"]["latitude_deg"]
            else "The unchanged high-altitude latitude target is not met."
        ),
        "production_regression": False,
    }


def audit():
    sgp = additional_sgp4()
    terrestrial = additional_terrestrial()
    residual = residual_investigation()
    checks = (
        sgp["comparisons"]
        + terrestrial["mathematical_transform_cases"]
        + terrestrial["mathematical_geodesy_cases"]
        + terrestrial["published_component_cases"]
    )
    return {
        "kind": "numerical_verification_not_observational_accuracy",
        "versions": {
            "astropy": astropy.__version__,
            "pyerfa": erfa.__version__,
            "sgp4": sgp4.__version__,
        },
        "fixture_sha256": {
            name: hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest()
            for name in [
                "earth-fixed.json",
                "phase61-sgp4.json",
                "phase61-terrestrial.json",
            ]
        },
        "sgp4": sgp,
        "terrestrial": terrestrial,
        "vallado_residual": residual,
        "geodesy_precision_assessment": geodesy_precision_assessment(),
        "passed": sum(c["passed"] for c in checks),
        "failed": sum(not c["passed"] for c in checks),
        "counts_are_comparisons_not_independent_observations": True,
        "observation_validation": {
            "status": "BLOCKED",
            "observations_used": 0,
            "reason": (
                "No suitable identified, contemporaneous independent "
                "measurements with verified frame/time/uncertainty and "
                "paired orbital inputs available in the archive."
            ),
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit()
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(
        f"Phase 6.1 audit: {result['passed']} comparisons passed, "
        f"{result['failed']} failed; observation validation BLOCKED"
    )
    raise SystemExit(bool(result["failed"]))


if __name__ == "__main__":
    main()
