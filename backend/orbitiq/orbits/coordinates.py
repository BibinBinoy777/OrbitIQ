"""Astropy Vallado TEME -> geocentric ITRS -> WGS84 geodetic coordinates."""

import math
import warnings

import astropy
import erfa
from astropy import units as u
from astropy.coordinates import (
    ITRS,
    TEME,
    CartesianDifferential,
    CartesianRepresentation,
    EarthLocation,
)
from astropy.time import Time
from astropy.utils.exceptions import AstropyWarning

from orbitiq.orbits.earth_orientation import (
    TransformationError,
    orientation,
    parameters,
)
from orbitiq.orbits.freshness import utc


def finite_vector(value):
    try:
        valid = len(value) == 3 and all(
            not isinstance(x, bool) and isinstance(x, (int, float)) and math.isfinite(x)
            for x in value
        )
    except (TypeError, OverflowError):
        valid = False
    if not valid:
        raise TransformationError(
            "invalid_coordinates",
            "Coordinates must contain three finite numeric components",
        )
    return value


def wrap_longitude(longitude: float) -> float:
    if isinstance(longitude, bool) or not math.isfinite(longitude):
        raise TransformationError("invalid_coordinates", "Longitude must be finite")
    return (longitude + 180) % 360 - 180


def geodetic(position_km):
    position_km = finite_vector(position_km)
    if math.hypot(*position_km) < 1:
        raise TransformationError(
            "invalid_coordinates", "Geodetic position is undefined near Earth's center"
        )
    location = EarthLocation.from_geocentric(*position_km, unit=u.km)
    lon, lat, height = location.to_geodetic(ellipsoid="WGS84")
    result = {
        "latitude_deg": float(lat.to_value(u.deg)),
        "longitude_deg": wrap_longitude(float(lon.to_value(u.deg))),
        "altitude_km": float(height.to_value(u.km)),
        "height_reference": "WGS84 ellipsoid",
    }
    if (
        not all(
            math.isfinite(result[k])
            for k in ("latitude_deg", "longitude_deg", "altitude_km")
        )
        or not -90 <= result["latitude_deg"] <= 90
    ):
        raise TransformationError(
            "invalid_coordinates", "Geodetic result is outside valid numeric ranges"
        )
    return result


def surface_position(ground: dict) -> list[float]:
    """WGS84 normal footpoint at zero ellipsoidal height, in ITRS km."""
    latitude, longitude = ground["latitude_deg"], ground["longitude_deg"]
    if (
        any(isinstance(x, bool) or not math.isfinite(x) for x in (latitude, longitude))
        or not -90 <= latitude <= 90
        or not -180 <= longitude < 180
    ):
        raise TransformationError("invalid_coordinates", "Invalid geodetic footpoint")
    location = EarthLocation.from_geodetic(
        longitude * u.deg, latitude * u.deg, 0 * u.km, ellipsoid="WGS84"
    )
    return finite_vector([float(v.to_value(u.km)) for v in location.to_geocentric()])


def earth_fixed(teme: dict) -> dict:
    if not isinstance(teme, dict) or not isinstance(teme.get("units"), dict):
        raise TransformationError(
            "invalid_coordinates", "TEME state and units are required"
        )
    at = utc(teme.get("at"))
    if (
        at is None
        or teme.get("frame") != "TEME"
        or teme.get("time_system") != "UTC"
        or teme.get("units", {}).get("position") != "km"
        or teme.get("units", {}).get("velocity") != "km/s"
    ):
        raise TransformationError(
            "invalid_coordinates",
            "Transformation requires a TEME state in km and km/s at an aware UTC time",
        )
    p = finite_vector(teme.get("position_km"))
    v = finite_vector(teme.get("velocity_km_s"))
    try:
        with orientation() as (data, mode), warnings.catch_warnings():
            warnings.simplefilter("error", AstropyWarning)
            warnings.simplefilter("error", erfa.ErfaWarning)
            t = Time(at, scale="utc")
            eop = parameters(data, t, mode)
            # Keep inherited SGP4 nominal-UTC-day convention explicit: do not
            # offer new terrestrial results spanning an unvalidated leap step.
            epoch = utc(teme.get("orbital_epoch"))
            if epoch is not None:
                epoch_time = Time(epoch, scale="utc")
                elapsed = (t.tai - epoch_time.tai).to_value(u.s)
                if abs(elapsed - (at - epoch).total_seconds()) > 1e-4:
                    raise TransformationError(
                        "leap_crossing_unsupported",
                        (
                            "Earth-fixed calculations spanning a leap second "
                            "are not validated"
                        ),
                    )
            representation = CartesianRepresentation(p * u.km).with_differentials(
                CartesianDifferential(v * u.km / u.s)
            )
            transformed = TEME(representation, obstime=t).transform_to(ITRS(obstime=t))
            xyz = transformed.cartesian.xyz.to_value(u.km).tolist()
            velocity = (
                transformed.cartesian.differentials["s"]
                .d_xyz.to_value(u.km / u.s)
                .tolist()
            )
            finite_vector(xyz)
            finite_vector(velocity)
            ground = geodetic(xyz)
            ground_xyz = surface_position(ground)
    except TransformationError:
        raise
    except (ValueError, TypeError, ArithmeticError, AstropyWarning, erfa.ErfaWarning):
        raise TransformationError(
            "transformation_failed",
            "Coordinate transformation could not produce a validated finite result",
        ) from None
    return {
        "teme": teme,
        "at": at.isoformat(),
        "kind": "calculated",
        "input_frame": "TEME",
        "frame": "ITRS",
        "origin": "Earth center",
        "time_system": "UTC",
        "position_km": xyz,
        "ground_position_km": ground_xyz,
        "velocity_km_s": velocity,
        "units": {
            "position": "km",
            "velocity": "km/s",
            "angles": "deg",
            "altitude": "km",
        },
        "geodetic": ground,
        "transformation_status": "predicted_eop"
        if eop["status"] == "predicted"
        else "measured_eop",
        "method": (
            "Astropy TEME -> ITRS at same obstime; "
            "Vallado 2006 GMST82 and polar motion; WGS84 geodetic"
        ),
        "astropy_version": astropy.__version__,
        "pyerfa_version": erfa.__version__,
        "earth_orientation": eop,
        "warnings": [
            *teme.get("warnings", []),
            (
                "WGS84 ellipsoidal height is not terrain clearance or mean-sea-"
                "level height."
            ),
            "A ground track does not establish observer visibility or orbital safety.",
            (
                "Transformation reference agreement does not quantify satellite "
                "prediction uncertainty."
            ),
            *(
                [
                    (
                        "Predicted Earth-orientation parameters are used; they are not "
                        "final measurements."
                    )
                ]
                if eop["status"] == "predicted"
                else []
            ),
        ],
    }
