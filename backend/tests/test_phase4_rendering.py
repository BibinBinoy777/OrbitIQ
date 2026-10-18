"""Additive WGS84 surface geometry; no change to orbital or EOP conventions."""

import hashlib
import math

import pytest
from orbitiq.orbits.coordinates import surface_position
from orbitiq.orbits.earth_orientation import TransformationError

pytest_plugins = ["test_phase2_api"]


@pytest.mark.parametrize(
    "lat,lon,expected",
    [
        (0, 0, [6378.137, 0, 0]),
        (0, 90, [0, 6378.137, 0]),
        (0, -180, [-6378.137, 0, 0]),
        (90, 0, [0, 0, 6356.752314245179]),
        (-90, 0, [0, 0, -6356.752314245179]),
    ],
)
def test_surface_analytic_wgs84_axes(lat, lon, expected):
    result = surface_position({"latitude_deg": lat, "longitude_deg": lon})
    assert result == pytest.approx(expected, rel=0, abs=1e-9)


@pytest.mark.parametrize(
    "lat,lon", [(91, 0), (0, 180), (math.nan, 0), (0, math.inf), (True, 0)]
)
def test_invalid_surface_coordinates(lat, lon):
    with pytest.raises(TransformationError):
        surface_position({"latitude_deg": lat, "longitude_deg": lon})


def test_ground_track_returns_authoritative_footpoints_without_db_writes(setup_api):
    client, path, sid, record = setup_api
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    r = client.get(
        f"/api/snapshots/{sid}/earth-fixed", params={"at": record["EPOCH"] + "Z"}
    )
    assert r.status_code == 200
    data = r.json()
    v = data["ground_position_km"]
    assert len(v) == 3 and all(math.isfinite(x) for x in v)
    a, b = 6378.137, 6356.752314245179
    assert (v[0] ** 2 + v[1] ** 2) / a**2 + v[2] ** 2 / b**2 == pytest.approx(
        1, rel=0, abs=1e-12
    )
    assert v != data["position_km"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest


def test_sofa_surface_reference_with_analytic_height_removal():
    # Official SOFA/ERFA t_gd2gc: lon=3.1 rad, lat=-0.5 rad, h=2500 m.
    # Remove the known ellipsoidal height along the independently specified
    # geodetic normal; expected original Cartesian values are published constants.
    lon, lat, height = 3.1, -0.5, 2.5
    reference = [-5599.0005577049947, 233.01167223479203, -3040.9094706983363]
    normal = [
        math.cos(lat) * math.cos(lon),
        math.cos(lat) * math.sin(lon),
        math.sin(lat),
    ]
    expected = [r - height * n for r, n in zip(reference, normal, strict=True)]
    actual = surface_position(
        {"latitude_deg": math.degrees(lat), "longitude_deg": math.degrees(lon)}
    )
    assert actual == pytest.approx(expected, rel=0, abs=1e-9)
