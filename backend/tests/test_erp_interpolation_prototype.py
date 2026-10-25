"""SYNTHETIC ONLY: no acquired ERP, GP, SP3, database, network or spacecraft input."""

import copy
import runpy
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path

import pytest

M = runpy.run_path(
    str(Path(__file__).parents[2] / "scripts/prototype_erp_interpolation.py")
)
INTERPOLATE = M["interpolate_synthetic"]
REFUSAL = M["Refusal"]
AXIS = "SYNTHETIC:abstract-fixture-axis"
FIELDS = ("x_pole", "y_pole", "ut_offset")


def fixture():
    return {
        "synthetic": True,
        "axis": {"kind": "abstract_fractional_mjd", "id": AXIS},
        "continuous": True,
        "discontinuities": [],
        "provenance": "SYNTHETIC:exact invented series, no acquired evidence",
        "units": {
            "x_pole": "microarcsec",
            "y_pole": "arcsec",
            "ut_offset": "tenth_microsecond",
        },
        "samples": [
            {
                "epoch": "60000.500000000000000000",
                "values": {"x_pole": 1000000, "y_pole": "-3", "ut_offset": 10},
                "source_id": "SYNTHETIC:row-a",
                "quality": "SYNTHETIC:known-a",
            },
            {
                "epoch": "60001.50",
                "values": {"x_pole": 3000000, "y_pole": "1", "ut_offset": 30},
                "source_id": "SYNTHETIC:row-b",
                "quality": "SYNTHETIC:known-b",
            },
            {
                "epoch": "60003.50",
                "values": {"x_pole": 11000000, "y_pole": "5", "ut_offset": 90},
                "source_id": "SYNTHETIC:row-c",
                "quality": "SYNTHETIC:known-c",
            },
        ],
    }


def evaluate(data=None, query="60001.00", fields=FIELDS, axis=AXIS):
    return INTERPOLATE(
        fixture() if data is None else data,
        query,
        query_axis_id=axis,
        fields=fields,
    )


@pytest.mark.parametrize(
    "query,x,y,ut,indices,weight",
    [
        ("60000.50", 1, -3, Fraction(1, 1000000), (0, 0), 0),
        ("60001.00", 2, -1, Fraction(2, 1000000), (0, 1), Fraction(1, 2)),
        ("60001.50", 3, 1, Fraction(3, 1000000), (1, 1), 0),
        ("60002.00", 5, 2, Fraction(45, 10000000), (1, 2), Fraction(1, 4)),
        ("60002.50", 7, 3, Fraction(6, 1000000), (1, 2), Fraction(1, 2)),
        ("60003.50", 11, 5, Fraction(9, 1000000), (2, 2), 0),
    ],
)
def test_exact_piecewise_series_units_and_all_sample_epochs(
    query, x, y, ut, indices, weight
):
    r = evaluate(query=query)
    assert r["values"] == {"x_pole": x, "y_pole": y, "ut_offset": ut}
    assert r["bracket_indices_0based"] == indices and r["weight"] == weight
    assert all(isinstance(v, Fraction) for v in r["values"].values())
    assert r["units"] == {"x_pole": "arcsec", "y_pole": "arcsec", "ut_offset": "second"}
    assert r["source_epoch_lexemes"] == tuple(
        row["epoch"] for row in fixture()["samples"]
    )


def test_no_hidden_half_day_shift_or_equal_spacing_assumption():
    # Quarter through the unequal two-day second interval, not the previous
    # bracket and not a noon-to-midnight relabelling.
    r = evaluate(query="60002.00", fields=("x_pole",))
    assert r["values"]["x_pole"] == 5 and r["weight"] == Fraction(1, 4)
    assert r["bracket_indices_0based"] == (1, 2)


def test_fractional_precision_does_not_depend_on_decimal_context():
    q = "60000.500000000000000001"
    with localcontext() as context:
        context.prec = 6
        r = evaluate(query=q, fields=("x_pole",))
    assert r["weight"] == Fraction(1, 10**18)
    assert r["query_exact"] == Fraction(Decimal(q))
    assert r["values"]["x_pole"] == 1 + Fraction(2, 10**18)


def test_original_fixture_preserved_and_only_contributing_quality_retained():
    data = fixture()
    before = copy.deepcopy(data)
    r = evaluate(data)
    assert data == before
    assert r["contributing_source_ids"] == ("SYNTHETIC:row-a", "SYNTHETIC:row-b")
    assert r["contributing_quality"] == ("SYNTHETIC:known-a", "SYNTHETIC:known-b")
    assert evaluate(data, query="60003.50")["contributing_source_ids"] == (
        "SYNTHETIC:row-c",
    )
    assert r["provenance"] == before["provenance"]
    assert r["synthetic_only"] and r["scientific_status"] == "NOT_A_SCIENTIFIC_RESULT"
    assert r["real_epoch_scale"] == "UNQUALIFIED"
    assert not r["active_EOP_policy_changed"]
    assert not r["real_time_conversion_or_leap_handling_performed"]
    assert "UTC" not in r["axis_id"] and "GPS" not in r["axis_id"]


@pytest.mark.parametrize("q", ["60000.499999999999999999", "60003.500000000000000001"])
def test_out_of_range_never_clamps_or_extrapolates(q):
    with pytest.raises(REFUSAL, match="query_out_of_range"):
        evaluate(query=q)


@pytest.mark.parametrize(
    "q",
    [
        None,
        True,
        60001.0,
        "NaN",
        "Infinity",
        "60000/2",
        " 60001",
        Decimal("sNaN"),
        Decimal("-Infinity"),
    ],
)
def test_nonexact_or_invalid_query_refused(q):
    with pytest.raises(REFUSAL, match="invalid_exact_number"):
        evaluate(query=q)


@pytest.mark.parametrize(
    "value", [None, True, float("nan"), "NaN", "Infinity", Decimal("NaN"), "***"]
)
def test_missing_or_invalid_values_do_not_trigger_neighbor_search(value):
    d = fixture()
    d["samples"][1]["values"]["x_pole"] = value
    with pytest.raises(REFUSAL, match="invalid_exact_number"):
        evaluate(d, query="60002.50")


def test_absent_field_is_distinct_from_numeric_zero():
    d = fixture()
    d["samples"][0]["values"]["x_pole"] = 0
    assert evaluate(d, query="60000.50")["values"]["x_pole"] == 0
    del d["samples"][0]["values"]["x_pole"]
    with pytest.raises(REFUSAL, match="missing_field"):
        evaluate(d, query="60000.50")


@pytest.mark.parametrize("epoch", ["60000.50", "59999.50"])
def test_duplicate_or_unordered_epochs_never_sorted(epoch):
    d = fixture()
    d["samples"][1]["epoch"] = epoch
    with pytest.raises(REFUSAL, match="duplicate_or_unordered_epoch"):
        evaluate(d)


@pytest.mark.parametrize("axis", ["UTC", "GPS", "SYNTHETIC:other-axis", None])
def test_no_implicit_epoch_scale_conversion(axis):
    with pytest.raises(REFUSAL, match="axis_mismatch"):
        evaluate(axis=axis)


@pytest.mark.parametrize("unit", [None, "radian", "microsecond", "unknown", [], {}])
def test_no_implicit_or_unknown_unit_conversion(unit):
    d = fixture()
    d["units"]["x_pole"] = unit
    with pytest.raises(REFUSAL, match="unsupported_or_missing_unit"):
        evaluate(d)


@pytest.mark.parametrize(
    "fields",
    [
        (),
        ("x_pole", "x_pole"),
        ("Xsig",),
        ("Nr",),
        ("Xrt",),
        ("dpsi",),
        ("covariance",),
    ],
)
def test_no_automatic_interpolation_of_counts_uncertainties_rates_or_extensions(fields):
    with pytest.raises(REFUSAL, match="unsupported_fields"):
        evaluate(fields=fields)


def test_extra_fields_are_ignored_explicitly_without_converting_zero_to_missing():
    d = fixture()
    for s in d["samples"]:
        s["values"].update({"Xsig": 0, "Nr": 0, "Xrt": "unqualified", "dpsi": 0})
    r = evaluate(d)
    assert r["ignored_fields"] == ("Nr", "Xrt", "Xsig", "dpsi")
    assert set(r["values"]) == set(FIELDS)


def test_malformed_field_names_are_refused():
    d = fixture()
    d["samples"][0]["values"][0] = "SYNTHETIC:invalid field identifier"
    with pytest.raises(REFUSAL, match="invalid_field_name"):
        evaluate(d)


@pytest.mark.parametrize(
    "field",
    [
        "synthetic",
        "axis",
        "continuous",
        "discontinuities",
        "provenance",
        "units",
        "samples",
    ],
)
def test_required_fixture_scope_and_continuity_metadata(field):
    d = fixture()
    del d[field]
    with pytest.raises(REFUSAL):
        evaluate(d)


@pytest.mark.parametrize("field", ["epoch", "values", "source_id", "quality"])
def test_required_row_metadata_not_invented(field):
    d = fixture()
    del d["samples"][1][field]
    with pytest.raises(REFUSAL):
        evaluate(d)


def test_a_marked_step_is_not_interpolated_as_a_continuous_offset():
    d = fixture()
    d["discontinuities"] = ["SYNTHETIC:explicit step, no leap rule implemented"]
    with pytest.raises(REFUSAL, match="unqualified_discontinuities"):
        evaluate(d)


def test_real_scale_axis_and_unmarked_inputs_are_refused():
    d = fixture()
    d["axis"] = {"kind": "UTC", "id": AXIS}
    with pytest.raises(REFUSAL, match="abstract_axis_required"):
        evaluate(d)
    d = fixture()
    d["synthetic"] = False
    with pytest.raises(REFUSAL, match="synthetic_fixture_required"):
        evaluate(d)


def test_fraction_and_decimal_inputs_are_exact():
    d = fixture()
    d["samples"][0]["values"]["y_pole"] = Fraction(-3)
    d["samples"][1]["values"]["y_pole"] = Decimal("1")
    assert evaluate(d, query=Fraction(60001))["values"]["y_pole"] == -1


def test_installed_astropy_noon_boundary_status_is_not_a_coverage_proof():
    # Invented EOP values only. This inspects the installed interpolation
    # behavior, not a real scientific resource or any spacecraft state.
    import astropy
    from astropy import units as u
    from astropy.time import Time
    from astropy.utils import iers

    assert astropy.__version__ == "7.2.3"
    table = iers.IERS_B()
    table["MJD"] = [60000.5, 60001.5, 60003.5] * u.d
    table["PM_x"] = [0, 1, 5] * u.arcsec
    table["PM_y"] = [0, 1, 5] * u.arcsec
    xp, _, status = table.pm_xy(
        Time([60000.5, 60003.75], format="mjd", scale="utc"), return_status=True
    )
    assert status[0] == iers.TIME_BEFORE_IERS_RANGE  # Exact first noon knot.
    assert xp[0].value == 0
    assert status[1] == iers.FROM_IERS_B  # After actual final noon knot.
    assert xp[1].value == pytest.approx(5.5)  # Extrapolated invented value.
    assert evaluate(query="60000.5")["bracket_indices_0based"] == (0, 0)
    assert evaluate(query="60003.5")["bracket_indices_0based"] == (2, 2)
    with pytest.raises(REFUSAL, match="query_out_of_range"):
        evaluate(query="60003.75")
