"""Independent geodesy references and separate algebraic consistency checks."""

import importlib.util
import json
import math
from pathlib import Path

import pytest
from orbitiq.orbits.coordinates import (
    _refine_exterior_latitude,
    geodetic,
)
from orbitiq.orbits.earth_orientation import TransformationError

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "phase611_geodesy", ROOT / "scripts/verify_phase611_geodesy.py"
)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)
CASES = json.loads(AUDIT.FIXTURE.read_text())["cases"]


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_independent_geographiclib_components(case):
    actual = geodetic(case["position_km"])
    residuals = AUDIT.errors(actual, case["expected"])
    for key, error in residuals.items():
        assert error <= case["tolerances"][key], (key, error, actual)
    assert -90 <= actual["latitude_deg"] <= 90
    assert -180 <= actual["longitude_deg"] < 180
    assert actual["height_reference"] == "WGS84 ellipsoid"


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_separate_forward_reconstruction_consistency(case):
    result = AUDIT.evaluate(case)
    error = result["algebraic_roundtrip_consistency"]["after"]["vector_norm_km"]
    assert error <= case["roundtrip_vector_norm_tolerance_km"]


@pytest.mark.parametrize("position", [[1, 0, 0], [20, 0, 1], [0, 0, 100]])
def test_deep_interior_branch_is_preserved(position):
    before = AUDIT.unrefined_geodetic(position)
    actual = geodetic(position)
    assert {key: actual[key] for key in before} == before


def test_inaccurate_exterior_seed_cannot_silently_return_unconverged_result():
    with pytest.raises(TransformationError, match="did not converge"):
        _refine_exterior_latitude([6778.137, 0, 0], 45, 400)


def test_invalid_exterior_seed_derivative_fails_explicitly():
    with pytest.raises(TransformationError, match="ill-conditioned"):
        _refine_exterior_latitude([0, 0, 6778.137], -45, 400)


def test_longitude_residual_keeps_tiny_differences_and_wraps_antimeridian():
    expected = {"latitude_deg": 0, "longitude_deg": -120, "altitude_km": 0}
    actual = {**expected, "longitude_deg": math.nextafter(-120, math.inf)}
    assert AUDIT.errors(actual, expected)["longitude_deg"] == math.ulp(120)
    expected["longitude_deg"] = -179.9
    actual["longitude_deg"] = 179.9
    assert AUDIT.errors(actual, expected)["longitude_deg"] == pytest.approx(0.2)
