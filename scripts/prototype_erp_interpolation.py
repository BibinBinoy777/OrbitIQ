"""E8.7.10 synthetic-only fractional-MJD interpolation feasibility.

No file/network input, real epoch-scale conversion, leap-second handling, EOP
adapter or active policy integration. Explicit fixture labels are an audit
boundary, not proof that arbitrary caller-supplied numbers are synthetic.
Passing these tests does not qualify the acquired ERP or any scientific result.
"""

import re
from bisect import bisect_left
from collections.abc import Mapping
from decimal import Decimal
from fractions import Fraction

SCALES = {
    "x_pole": {"arcsec": Fraction(1), "microarcsec": Fraction(1, 1_000_000)},
    "y_pole": {"arcsec": Fraction(1), "microarcsec": Fraction(1, 1_000_000)},
    "ut_offset": {"second": Fraction(1), "tenth_microsecond": Fraction(1, 10_000_000)},
}
OUTPUT_UNITS = {"x_pole": "arcsec", "y_pole": "arcsec", "ut_offset": "second"}


class Refusal(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise Refusal(code)


def exact_number(value):
    """Accept exact fixture numbers only; no float conversion or silent rounding."""
    require(not isinstance(value, bool), "invalid_exact_number")
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, str):
        require(
            len(value) <= 80 and re.fullmatch(r"[+-]?\d+(?:\.\d+)?", value),
            "invalid_exact_number",
        )
        value = Decimal(value)
    require(isinstance(value, Decimal) and value.is_finite(), "invalid_exact_number")
    return Fraction(value)


def interpolate_synthetic(fixture, query, *, query_axis_id, fields):
    """Interpolate selected synthetic continuous fields on one abstract MJD axis.

    Epochs are never shifted or relabelled UTC/GPS. Exact knots return the
    original scaled value. Outside queries are refused; missing values never
    cause a search for a more distant knot. Unsupported fields (including
    rates, counts, formal errors and covariance) cannot be requested.
    """
    require(isinstance(fixture, Mapping), "synthetic_fixture_required")
    require(fixture.get("synthetic") is True, "synthetic_fixture_required")
    axis = fixture.get("axis")
    require(isinstance(axis, Mapping), "abstract_axis_required")
    require(
        axis.get("kind") == "abstract_fractional_mjd"
        and isinstance(axis.get("id"), str)
        and axis["id"].startswith("SYNTHETIC:"),
        "abstract_axis_required",
    )
    require(query_axis_id == axis["id"], "axis_mismatch")
    require(
        fixture.get("continuous") is True and fixture.get("discontinuities") == [],
        "unqualified_discontinuities",
    )
    require(
        isinstance(fields, tuple)
        and fields
        and all(isinstance(f, str) and f in SCALES for f in fields)
        and len(set(fields)) == len(fields),
        "unsupported_fields",
    )
    provenance = fixture.get("provenance")
    require(
        isinstance(provenance, str) and provenance.startswith("SYNTHETIC:"),
        "synthetic_provenance_required",
    )
    units = fixture.get("units")
    require(isinstance(units, Mapping), "missing_units")
    for name in fields:
        require(
            isinstance(units.get(name), str) and units[name] in SCALES[name],
            "unsupported_or_missing_unit",
        )
    samples = fixture.get("samples")
    require(isinstance(samples, list) and 2 <= len(samples) <= 4096, "sample_count")
    knots = []
    values = []
    quality = []
    source_ids = []
    for sample in samples:
        require(isinstance(sample, Mapping) and "epoch" in sample, "missing_epoch")
        epoch = exact_number(sample["epoch"])
        require(not knots or epoch > knots[-1], "duplicate_or_unordered_epoch")
        row = sample.get("values")
        require(isinstance(row, Mapping), "missing_values")
        require(all(isinstance(name, str) for name in row), "invalid_field_name")
        require(all(name in row for name in fields), "missing_field")
        source_id = sample.get("source_id")
        label = sample.get("quality")
        require(
            isinstance(source_id, str) and source_id.startswith("SYNTHETIC:"),
            "synthetic_source_required",
        )
        require(
            isinstance(label, str) and label.startswith("SYNTHETIC:"),
            "synthetic_quality_required",
        )
        knots.append(epoch)
        values.append(
            {
                name: exact_number(row[name]) * SCALES[name][units[name]]
                for name in fields
            }
        )
        quality.append(label)
        source_ids.append(source_id)
    target = exact_number(query)
    require(knots[0] <= target <= knots[-1], "query_out_of_range")
    right = bisect_left(knots, target)
    if knots[right] == target:
        left = right
        weight = Fraction(0)
    else:
        left = right - 1
        weight = (target - knots[left]) / (knots[right] - knots[left])
    result = {
        name: values[left][name] + weight * (values[right][name] - values[left][name])
        for name in fields
    }
    contributing = (left,) if left == right else (left, right)
    return {
        "synthetic_only": True,
        "scientific_status": "NOT_A_SCIENTIFIC_RESULT",
        "real_epoch_scale": "UNQUALIFIED",
        "axis_id": axis["id"],
        "source_epoch_lexemes": tuple(sample["epoch"] for sample in samples),
        "query_exact": target,
        "bracket_indices_0based": (left, right),
        "weight": weight,
        "values": result,
        "units": {name: OUTPUT_UNITS[name] for name in fields},
        "contributing_source_ids": tuple(source_ids[i] for i in contributing),
        "contributing_quality": tuple(quality[i] for i in contributing),
        "provenance": provenance,
        "interpolation_model": "piecewise_linear_synthetic_continuous_values_only",
        "ignored_fields": tuple(
            sorted({name for row in samples for name in row["values"]} - set(fields))
        ),
        "active_EOP_policy_changed": False,
        "real_time_conversion_or_leap_handling_performed": False,
    }
