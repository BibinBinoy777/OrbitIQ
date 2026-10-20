"""Validate scientific identities and result semantics before orbital replay."""

import math
from datetime import timedelta
from importlib.metadata import version

from astropy.time import Time

from orbitiq.orbits.earth_orientation import parameters
from orbitiq.orbits.elements import ELEMENT_UNITS
from orbitiq.orbits.freshness import utc
from orbitiq.orbits.sampling import SamplingPolicy, sample_times
from orbitiq.replay_contract import BundleError
from orbitiq.services import reports
from orbitiq.services.replay import expected_projection


def invalid(field, message="Recorded calculation metadata is contradictory"):
    raise BundleError(message, "scientific_input_invalid", field=field)


def vector(value, field):
    if (
        not isinstance(value, list)
        or len(value) != 3
        or not all(type(v) in (int, float) and math.isfinite(v) for v in value)
    ):
        invalid(field, "Expected three finite numeric vector components")


def preflight(manifest, report, definition, captured, resource):
    """No propagation/coordinate transformation here; no fallback resources."""
    d = definition
    if report.status == "partial":
        if report.calculation.status != "unavailable":
            invalid("calculation.status")
        return None, []
    clocks = []

    def state(value, reference, at, frame, field):
        expected_units = {
            "position": "km",
            "velocity": "km/s",
            **(
                {"angles": "deg", "altitude": "km"}
                if frame == "ITRS"
                else {"epoch_offset": "days"}
            ),
        }
        if (
            not isinstance(value, dict)
            or value.get("frame") != frame
            or value.get("units") != expected_units
            or utc(value.get("at")) != at
            or value.get("time_system") != "UTC"
            or value.get("kind") != "calculated"
            or value.get("origin") != "Earth center"
        ):
            invalid(field, "Result frame, units, identity or evaluation time differs")
        for name in ("position_km", "velocity_km_s"):
            vector(value.get(name), field + "." + name)
        if abs((at - reference.orbital_epoch).total_seconds()) > 7 * 86400:
            invalid(field + ".at", "Requested time exceeds supported epoch window")
        if frame == "TEME":
            if (
                not reports.same_reference(reference, value)
                or type(value.get("snapshot_id")) is not int
                or type(value.get("catalog_id")) is not int
                or value.get("model") != "SGP4"
                or value.get("gravity_model") != "WGS72"
                or value.get("sgp4_version") != version("sgp4")
            ):
                invalid(field, "TEME model or exact archived source identity differs")
            clock = utc(value.get("calculated_at"))
            if (
                clock is None
                or not utc(report.generated_at) <= clock <= manifest.captured_at
            ):
                invalid(
                    field + ".calculated_at", "Original execution timestamp is invalid"
                )
            clocks.append(clock.isoformat())
        else:
            if resource is None:
                invalid(
                    field + ".earth_orientation",
                    "Required EOP/leap resource is missing",
                )
            # Check every recorded EOP field/hash/quality flag against exact bytes
            # at the fixed historical evaluation clock, before orbital calculations.
            expected_eop = parameters(
                resource, Time(at, scale="utc"), manifest.settings.eop_policy
            )
            if value.get("earth_orientation") != expected_eop:
                raise BundleError(
                    "Recorded EOP/leap identities or parameters differ "
                    "from exact resources",
                    "resource_identity_mismatch",
                    field=field + ".earth_orientation",
                )
            if (
                value.get("astropy_version") != version("astropy")
                or value.get("pyerfa_version") != version("pyerfa")
                or value.get("transformation_status")
                != (
                    "predicted_eop"
                    if expected_eop["status"] == "predicted"
                    else "measured_eop"
                )
            ):
                invalid(field, "Transformation software or EOP status differs")
            vector(value.get("ground_position_km"), field + ".ground_position_km")
            geodetic = value.get("geodetic", {})
            if not isinstance(geodetic, dict):
                invalid(field + ".geodetic")
            for key in ("latitude_deg", "longitude_deg", "altitude_km"):
                if type(geodetic.get(key)) not in (float, int) or not math.isfinite(
                    geodetic[key]
                ):
                    invalid(field + ".geodetic." + key)
            if (
                not -90 <= geodetic["latitude_deg"] <= 90
                or not -180 <= geodetic["longitude_deg"] < 180
                or geodetic.get("height_reference") != "WGS84 ellipsoid"
            ):
                invalid(field + ".geodetic")
            state(value.get("teme"), reference, at, "TEME", field + ".teme")

    data = report.calculation.data
    if d.mode == "comparison":
        rows = data.get("element_differences") if isinstance(data, dict) else None
        shared = d.source.catalog_id == d.comparison_source.catalog_id
        fields = [f for f in ELEMENT_UNITS if f != "EPOCH"] if shared else []
        if not isinstance(rows, list) or len(rows) != len(fields):
            invalid("calculation.data.element_differences")
        for row, field in zip(rows, fields, strict=True):
            if (
                not isinstance(row, dict)
                or row.get("field") != field
                or row.get("unit") != ELEMENT_UNITS[field]
            ):
                invalid(
                    "calculation.data.element_differences",
                    "Element units or identity differ",
                )
    if d.mode == "position":
        state(data, d.source, d.at, "TEME", "calculation.data")
    elif d.mode == "ground-track":
        t = d.track
        times = sample_times(
            t.start,
            t.start + timedelta(minutes=t.duration_minutes),
            t.step_seconds,
            captured[0][1].epoch,
            SamplingPolicy(
                manifest.settings.max_samples, manifest.settings.max_duration_seconds
            ),
        )
        if (
            not isinstance(data, dict)
            or not isinstance(data.get("points"), list)
            or len(data["points"]) != len(times)
        ):
            invalid(
                "calculation.data.points", "Track count differs from requested interval"
            )
        for i, (point, at) in enumerate(zip(data["points"], times, strict=True)):
            state(point, d.source, at, "ITRS", f"calculation.data.points.{i}")
    elif d.mode == "comparison" and d.at is not None:
        if d.source.catalog_id != d.comparison_source.catalog_id:
            invalid(
                "investigation.definition",
                "Common-time comparison requires shared identity",
            )
        comparison = data.get("state_comparison", {}) if isinstance(data, dict) else {}
        if (
            comparison.get("status") != "complete"
            or comparison.get("frame") != d.frame
            or utc(comparison.get("evaluation_at")) != d.at
            or comparison.get("units") != {"position": "km", "velocity": "km/s"}
        ):
            invalid("calculation.data.state_comparison")
        for side, ref in (("first", d.source), ("second", d.comparison_source)):
            state(
                comparison.get(side),
                ref,
                d.at,
                d.frame,
                "calculation.data.state_comparison." + side,
            )
    elif d.mode == "snapshot" and data is not None:
        invalid(
            "calculation.data", "Snapshot-only report cannot claim calculated states"
        )
    try:
        projection = expected_projection(report)
    except (ValueError, KeyError, TypeError, AttributeError, IndexError):
        invalid("calculation.data", "Recorded result shape is invalid")
    return projection, list(dict.fromkeys(clocks))
