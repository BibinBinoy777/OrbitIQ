"""Offline scientific references and accuracy probes, never satellite observations."""

import importlib.util
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pytest
from astropy import units as u
from astropy.time import Time, TimeDelta
from fastapi.testclient import TestClient
from orbitiq.main import create_app
from orbitiq.orbits import earth_orientation as eo
from orbitiq.orbits.coordinates import earth_fixed, geodetic
from orbitiq.orbits.earth_orientation import (
    TransformationError,
    orientation,
    parameters,
)
from orbitiq.orbits.elements import Elements
from orbitiq.orbits.engine import propagate, propagate_satellite
from sgp4.api import Satrec
from sgp4.conveniences import sat_epoch_datetime

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "phase61_audit", ROOT / "scripts/verify_phase61_science.py"
)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)
FIXTURES = Path(__file__).parent / "fixtures"
SGP = json.loads((FIXTURES / "phase61-sgp4.json").read_text())
TERRESTRIAL = json.loads((FIXTURES / "phase61-terrestrial.json").read_text())
PUBLISHED = [(source, case) for source in SGP["inputs"] for case in source["cases"]]


@pytest.mark.parametrize("source,case", PUBLISHED)
@pytest.mark.parametrize("kind", ["tle", "omm"])
def test_additional_published_branch_vectors(source, case, kind):
    sat = Satrec.twoline2rv(*source["tle"])
    at = sat_epoch_datetime(sat) + timedelta(minutes=case["minutes"])
    actual = (
        propagate_satellite(sat, at)
        if kind == "tle"
        else propagate(Elements.model_validate(source["omm"]), at)
    )
    for key in ["position_km", "velocity_km_s"]:
        assert actual[key] == pytest.approx(
            case[key], abs=SGP["tolerances"][key], rel=0
        )
    if kind == "omm":
        assert actual["uncertainty"] == {
            "status": "not_quantified",
            "covariance_available": False,
            "observation_validated": False,
        }
        assert actual["frame"] == "TEME" and actual["gravity_model"] == "WGS72"


@pytest.mark.parametrize("case", TERRESTRIAL["transforms"], ids=lambda c: c["id"])
def test_independent_explicit_rotation_references(case, monkeypatch):
    resource = AUDIT.controlled_resources(case)
    monkeypatch.setattr(eo, "resources", lambda: resource)
    actual = earth_fixed(AUDIT.state(case))
    for key in ["position_km", "velocity_km_s"]:
        assert actual[key] == pytest.approx(
            case["expected"][key], abs=case["tolerances"][key], rel=0
        )
    assert actual["earth_orientation"]["auto_download"] is False


# Phase 6.1.1 resolves the original latitude target. Keep its input/threshold
# unchanged and run every coordinate assertion without an expected-failure mark.
GEODESY = [
    pytest.param(anchor, coordinate, id=anchor["id"] + "-" + coordinate)
    for anchor in TERRESTRIAL["geodesy"]
    for coordinate in ["latitude_deg", "longitude_deg", "altitude_km"]
]


@pytest.mark.parametrize("anchor,coordinate", GEODESY)
def test_independent_mathematical_wgs84_anchors(anchor, coordinate):
    actual = geodetic(anchor["position_km"])
    assert actual[coordinate] == pytest.approx(
        anchor["expected"][coordinate], abs=anchor["tolerances"][coordinate], rel=0
    )


@pytest.mark.parametrize("case", TERRESTRIAL["time_components"], ids=lambda c: c["id"])
def test_published_sofa_component_constants(case):
    with eo.orientation():
        if case["id"] == "SOFA_GMST82":
            import erfa

            assert erfa.gmst82(*case["input_jd_parts"]) == pytest.approx(
                case["expected_rad"], abs=case["tolerance_rad"], rel=0
            )
            return
        t = Time(*case["input_jd_parts"], format="jd", scale=case["input_scale"])
        if "dut1_seconds" in case:
            t.delta_ut1_utc = case["dut1_seconds"]
        actual = getattr(t, case["output_scale"])
        expected = case["expected_jd_parts"]
        error = abs((actual.jd1 - expected[0]) + (actual.jd2 - expected[1])) * 86400
        assert error <= case["tolerance_seconds"]


@pytest.fixture(scope="module")
def residual():
    return AUDIT.residual_investigation()


def test_original_residual_reproduced_without_rounding_or_new_tolerance(residual):
    original = residual["variants"]["orbitIQ_current_two_part"]["position_residual_km"]
    assert 1.3e-5 < original["max_absolute_component"] < 1.4e-5
    assert (
        original["max_absolute_component"]
        <= residual["existing_tolerances_unchanged"]["position_km"]
    )
    assert residual["existing_tolerances_unchanged"] == {
        "position_km": 2e-5,
        "velocity_km_s": 1e-6,
    }
    assert (
        residual["orbital_elements"] is None
    )  # standalone paper state, not invented TLE


def test_independent_high_precision_equation_agrees_with_two_part_transform(residual):
    assert abs(residual["independent_GMST_minus_erfa_rad"]) < 1e-12
    assert (
        residual["independent_decimal_vs_current_position_km"]["max_absolute_component"]
        < 1e-7
    )


def test_single_jd_precision_order_explains_dominant_paper_difference(residual):
    value = residual["variants"]["single_UTC_JD_plus_DUT1_then_polynomial"]
    assert value["position_residual_km"]["max_absolute_component"] < 1e-7
    assert residual["UTC_plus_DUT1_rounding_error_microseconds"] > 20
    assert residual["single_UT1_rounding_error_microseconds"] < -15
    # Merely collapsing the final UT1 JD is a different order and makes it worse.
    assert (
        residual["variants"]["single_UT1_JD_then_polynomial"]["position_residual_km"][
            "max_absolute_component"
        ]
        > 2e-5
    )


@pytest.mark.parametrize("channel", ["ut1", "polar"])
@pytest.mark.parametrize("support_index", [0, 2])
def test_any_velocity_support_prediction_triggers_strict_policy(
    monkeypatch, channel, support_index
):
    original = eo.resources()
    table = original.table.copy()
    method = "ut1_utc" if channel == "ut1" else "pm_xy"
    real = getattr(table, method)

    def controlled(*args, **kwargs):
        values = list(real(*args, **kwargs))
        status = np.array([0, 0, 0])
        status[support_index] = 2
        values[-1] = status
        return tuple(values)

    monkeypatch.setattr(table, method, controlled)
    resource = replace(original, table=table)
    at = Time("2004-04-06T07:51:28.386", scale="utc")
    with orientation():
        result = parameters(
            resource,
            at,
            "measured_or_predicted",
            now=datetime(2026, 10, 19, tzinfo=UTC),
        )
        assert result["status"] == "predicted"
        key = (
            "velocity_support_ut1"
            if channel == "ut1"
            else "velocity_support_polar_motion"
        )
        assert result["source_quality"][key][support_index] == "prediction"
        assert (
            result["source_quality"]["ut1" if channel == "ut1" else "polar_motion"]
            == "final"
        )
        with pytest.raises(TransformationError) as caught:
            parameters(resource, at, "measured_only")
    assert caught.value.code == "eop_prediction_disallowed"


@pytest.mark.parametrize("seconds,allowed", [(0.500001, True), (0.499999, False)])
def test_leap_expiry_applies_to_entire_velocity_support(seconds, allowed):
    resource = eo.resources()
    with orientation():
        at = resource.leaps.expires - TimeDelta(seconds, format="sec")
        now = Time(
            resource.metadata["predictive_mjd"] + 5, format="mjd", scale="utc"
        ).to_datetime(timezone=UTC)
        if allowed:
            assert (
                parameters(resource, at, "measured_or_predicted", now=now)["status"]
                == "predicted"
            )
        else:
            with pytest.raises(TransformationError) as caught:
                parameters(resource, at, "measured_or_predicted", now=now)
            assert caught.value.code == "leap_seconds_out_of_range"


@pytest.mark.parametrize(
    "epoch,at,allowed",
    [
        ("2016-12-31T23:59:58Z", "2016-12-31T23:59:59Z", True),
        ("2017-01-01T00:00:00Z", "2017-01-01T00:00:01Z", True),
        ("2016-12-31T23:59:59Z", "2017-01-01T00:00:00Z", False),
        ("2017-01-01T00:00:00Z", "2016-12-31T23:59:59Z", False),
    ],
)
def test_leap_crossing_limit_forward_reverse_and_adjacent(epoch, at, allowed):
    case = TERRESTRIAL["transforms"][0]
    test_state = {**AUDIT.state(case), "at": at, "orbital_epoch": epoch}
    if allowed:
        assert earth_fixed(test_state)["frame"] == "ITRS"
    else:
        with pytest.raises(TransformationError) as caught:
            earth_fixed(test_state)
        assert caught.value.code == "leap_crossing_unsupported"


def test_nominal_utc_sgp4_day_is_distinct_from_tai_across_leap():
    arguments = []

    class Capture:
        def sgp4(self, jd, fraction):
            arguments.append((jd, fraction))
            return 0, [1, 2, 3], [4, 5, 6]

    first = datetime(2016, 12, 31, 23, 59, 59, tzinfo=UTC)
    second = datetime(2017, 1, 1, tzinfo=UTC)
    sat = Capture()
    propagate_satellite(sat, first)
    propagate_satellite(sat, second)
    nominal = (
        (arguments[1][0] - arguments[0][0]) + (arguments[1][1] - arguments[0][1])
    ) * 86400
    with orientation():
        physical = (Time(second).tai - Time(first).tai).to_value(u.s)
    assert nominal == pytest.approx(1, abs=1e-8, rel=0)
    assert physical == pytest.approx(2, abs=1e-8, rel=0)


def test_invalid_leap_second_spelling_is_rejected_by_actual_api(tmp_path, monkeypatch):
    missing = tmp_path / "never-create.sqlite3"
    monkeypatch.setenv("ORBITIQ_DATABASE_PATH", str(missing))
    with TestClient(create_app()) as client:
        response = client.get(
            "/api/snapshots/1/position", params={"at": "2016-12-31T23:59:60Z"}
        )
    assert response.status_code == 422
    assert not missing.exists()


@pytest.mark.parametrize(
    "flag,expected", [(0, "final"), (1, "rapid_nonprediction"), (2, "prediction")]
)
def test_eop_quality_distinguishes_final_rapid_and_prediction(
    monkeypatch, flag, expected
):
    resource = eo.resources()
    table = resource.table.copy()
    for method in ["ut1_utc", "pm_xy"]:
        original = getattr(table, method)

        def returned(*args, _original=original, **kwargs):
            values = list(_original(*args, **kwargs))
            values[-1] = np.array([flag] * 3)
            return tuple(values)

        monkeypatch.setattr(table, method, returned)
    with orientation():
        result = parameters(
            replace(resource, table=table),
            Time("2004-04-06", scale="utc"),
            "measured_or_predicted",
            now=datetime(2026, 10, 19, tzinfo=UTC),
        )
    assert result["source_quality"]["ut1"] == expected
    assert result["source_quality"]["polar_motion"] == expected
    assert result["status"] == ("predicted" if flag == 2 else "measured")
    assert (
        result["ut1_source"]
        == ["IERS_B_final", "IERS_A_measured", "IERS_A_prediction"][flag]
    )
