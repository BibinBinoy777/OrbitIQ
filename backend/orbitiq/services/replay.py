"""Replay existing backend calculations; no alternative orbital mathematics."""

import math
from datetime import timedelta
from numbers import Real

from orbitiq.orbits.coordinates import earth_fixed
from orbitiq.orbits.freshness import FreshnessPolicy, utc
from orbitiq.orbits.sampling import SamplingPolicy, sample_times
from orbitiq.replay_contract import TOLERANCES
from orbitiq.services import analysis, investigations


def state_projection(value):
    """Execution clocks/freshness/warnings are not numerical reproducibility."""
    projected = {
        k: value[k]
        for k in (
            "kind",
            "frame",
            "origin",
            "time_system",
            "position_km",
            "velocity_km_s",
            "units",
        )
    }
    projected["at"] = utc(value["at"]).isoformat()
    if value["frame"] == "ITRS":
        projected.update(
            {
                k: value[k]
                for k in (
                    "ground_position_km",
                    "geodetic",
                    "transformation_status",
                    "method",
                    "astropy_version",
                    "pyerfa_version",
                    "earth_orientation",
                )
            }
        )
        projected["teme"] = state_projection(value["teme"])
    elif value["frame"] == "TEME":
        projected.update(
            {
                k: value[k]
                for k in (
                    "snapshot_id",
                    "catalog_id",
                    "response_sha256",
                    "model",
                    "gravity_model",
                    "epoch_offset_days",
                    "sgp4_version",
                )
            }
        )
        for k in ("orbital_epoch", "retrieved_at"):
            projected[k] = utc(value[k]).isoformat()
    else:
        raise ValueError("Unsupported result frame")
    return projected


def comparison_projection(data):
    result = {k: data[k] for k in ("element_comparison_status", "element_differences")}
    state = data["state_comparison"]
    result["state_comparison"] = {
        **{k: v for k, v in state.items() if k not in {"first", "second"}},
        **{k: state_projection(state[k]) for k in ("first", "second") if state.get(k)},
    }
    return result


def expected_projection(report):
    d, c = report.investigation.definition, report.calculation
    if d.mode == "snapshot":
        return {}
    if d.mode == "position":
        return state_projection(c.data)
    if d.mode == "ground-track":
        data = c.data
        count = d.track.duration_minutes * 60 // d.track.step_seconds + 1
        if len(data["points"]) != count or data["sample_count"] != count:
            raise ValueError("Track shape mismatch")
        for i, p in enumerate(data["points"]):
            if p["sample_index"] != i or utc(p["at"]) != (
                d.track.start + timedelta(seconds=i * d.track.step_seconds)
            ):
                raise ValueError("Track sample identity mismatch")
        return {"points": [state_projection(p) for p in data["points"]]}
    return comparison_projection(c.data)


def recalculate(definition, captured, settings):
    freshness = FreshnessPolicy(settings.fresh_hours, settings.stale_hours)

    def positioner(item, elements, at):
        return analysis.position_from_snapshot(
            item, elements, at, freshness_policy=freshness
        )

    d = definition
    if d.mode == "snapshot":
        return {}
    if d.mode == "position":
        return state_projection(positioner(*captured[0], d.at))
    if d.mode == "ground-track":
        t = d.track
        times = sample_times(
            t.start,
            t.start + timedelta(minutes=t.duration_minutes),
            t.step_seconds,
            captured[0][1].epoch,
            SamplingPolicy(settings.max_samples, settings.max_duration_seconds),
        )
        return {
            "points": [
                state_projection(earth_fixed(positioner(*captured[0], at)))
                for at in times
            ]
        }
    shared = captured[0][0]["catalog_id"] == captured[1][0]["catalog_id"]
    differences = (
        investigations.element_differences(captured[0][1], captured[1][1])
        if shared
        else []
    )
    state = {"status": "not_requested", "evaluation_at": None, "frame": d.frame}
    if d.at is not None:
        if not shared:
            raise ValueError("No compatible common-time states")
        sources = [(item, item, elements, None) for item, elements in captured]
        state = investigations.common_state(
            sources, d.at, d.frame, positioner=positioner
        )
        if state["status"] != "complete":
            raise analysis.AnalysisError(
                422, "replay_calculation_unavailable", "Replay calculation unavailable"
            )
    return comparison_projection(
        {
            "element_comparison_status": "complete"
            if shared
            else "incompatible_or_no_shared_record",
            "element_differences": differences,
            "state_comparison": state,
        }
    )


def absolute_tolerance(path):
    parts = path.split(".")
    if any(
        k in parts
        for k in ("velocity_km_s", "difference_velocity_km_s", "relative_speed_km_s")
    ):
        return TOLERANCES["velocity_km_s"]
    if any(k in parts for k in ("latitude_deg", "longitude_deg")):
        return TOLERANCES["geodetic_angle_deg"]
    if "altitude_km" in parts:
        return TOLERANCES["altitude_km"]
    if any(
        k in parts
        for k in (
            "position_km",
            "ground_position_km",
            "difference_position_km",
            "separation_km",
        )
    ):
        return TOLERANCES["position_km"]
    return 0


def comparison_unit(path, row_unit=None):
    parts = path.split(".")
    if any(
        k in parts
        for k in ("velocity_km_s", "difference_velocity_km_s", "relative_speed_km_s")
    ):
        return "km/s"
    if any(
        k in parts
        for k in (
            "position_km",
            "ground_position_km",
            "difference_position_km",
            "separation_km",
            "altitude_km",
        )
    ):
        return "km"
    if any(k in parts for k in ("latitude_deg", "longitude_deg")):
        return "deg"
    if parts[-1] in {"first_value", "second_value", "difference"}:
        return row_unit
    if parts[-1].endswith("_days") or parts[-1] in {
        "first_mjd",
        "last_mjd",
        "predictive_mjd",
    }:
        return "days"
    if parts[-1].endswith("_seconds"):
        return "s"
    if parts[-1].endswith("_arcsec"):
        return "arcsec"
    return None


def compare_values(expected, actual):
    """Compare decoded binary64 numbers, preserving signed zero for exactness.

    JSON whitespace/key order and equivalent UTC spellings are outside the
    numerical projection. Longitude residuals use remainder, never add 180.
    """
    differences, agreements = [], []
    count, numbers, nonidentical, agreement_count = 0, 0, 0, 0

    def display(value):
        if isinstance(value, str):
            return value[:160]
        if isinstance(value, Real) and not math.isfinite(value):
            return None
        return value

    def mismatch(path, a, b):
        nonlocal count
        count += 1
        if len(differences) < 20:
            differences.append(
                {
                    "path": path,
                    "expected": display(a),
                    "actual": display(b),
                    "absolute_tolerance": 0,
                    "absolute_difference": None,
                    "relative_difference": None,
                    "unit": None,
                    "passed": False,
                }
            )

    def visit(a, b, path, row_unit=None):
        nonlocal numbers, count, nonidentical, agreement_count
        if isinstance(a, dict) and isinstance(b, dict):
            if a.keys() != b.keys():
                return mismatch(path, "record fields", "different record fields")
            for k in a:
                visit(a[k], b[k], path + "." + k, a.get("unit", row_unit))
        elif isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                return mismatch(path, len(a), len(b))
            for i, (x, y) in enumerate(zip(a, b, strict=True)):
                visit(x, y, path + "." + str(i), row_unit)
        elif (
            isinstance(a, Real)
            and isinstance(b, Real)
            and not isinstance(a, bool)
            and not isinstance(b, bool)
        ):
            numbers += 1
            finite = math.isfinite(a) and math.isfinite(b)
            identical = finite and float(a).hex() == float(b).hex()
            if identical:
                return
            nonidentical += 1
            tolerance, unit = absolute_tolerance(path), comparison_unit(path, row_unit)
            raw = float(b) - float(a) if finite else math.inf
            angular = path.endswith(".longitude_deg")
            residual = (
                math.remainder(raw, 360) if angular and math.isfinite(raw) else raw
            )
            absolute = abs(residual)
            passed = finite and absolute <= tolerance
            relative = absolute / abs(a) if unit and unit != "deg" and a != 0 else None
            if relative is not None and not math.isfinite(relative):
                relative = None
            detail = {
                "path": path,
                "expected": display(a),
                "actual": display(b),
                "signed_difference": residual if math.isfinite(residual) else None,
                "absolute_difference": absolute if math.isfinite(absolute) else None,
                "relative_difference": relative,
                "unit": unit,
                "difference_method": "wrapped_remainder_360"
                if angular
                else "actual_minus_expected",
                "absolute_tolerance": tolerance,
                "relative_tolerance": 0,
                "passed": passed,
            }
            if passed:
                agreement_count += 1
                if len(agreements) < 20:
                    agreements.append(detail)
            else:
                count += 1
                if len(differences) < 20:
                    differences.append(detail)
        elif type(a) is not type(b) or a != b:
            mismatch(path, a, b)

    visit(expected, actual, "calculation")
    return {
        "outcome": "mismatch"
        if count
        else "tolerance_agreement"
        if nonidentical
        else "exact_output_reproduction",
        "mismatch_count": count,
        "differences": differences,
        "numeric_values_checked": numbers,
        "nonidentical_numeric_values": nonidentical,
        "tolerance_agreement_count": agreement_count,
        "agreements_within_tolerance": agreements,
        "exact_comparison": "decoded_binary64_hex_including_signed_zero_"
        "and_exact_metadata_v1",
    }
