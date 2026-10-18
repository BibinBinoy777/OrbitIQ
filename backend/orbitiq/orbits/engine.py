"""WGS72 SGP4 propagation. All output is calculated, geocentric TEME."""

import math
from datetime import UTC, datetime

import sgp4
from sgp4.api import SGP4_ERRORS, Satrec, jday

from orbitiq.orbits.elements import Elements


class PropagationError(ValueError):
    def __init__(self, message: str, code: str = "propagation_failed"):
        super().__init__(message)
        self.code = code


def propagate_satellite(satellite: Satrec, at: datetime) -> dict:
    if not isinstance(at, datetime) or at.tzinfo is None or at.utcoffset() is None:
        raise PropagationError("Calculation time must include a timezone")
    try:
        at = at.astimezone(UTC)
    except (ValueError, OverflowError):
        raise PropagationError("Calculation time is not representable in UTC") from None
    jd, fraction = jday(
        at.year,
        at.month,
        at.day,
        at.hour,
        at.minute,
        at.second + at.microsecond / 1_000_000,
    )
    try:
        code, position, velocity = satellite.sgp4(jd, fraction)
    except (ValueError, OverflowError, ArithmeticError):
        raise PropagationError("SGP4 could not calculate a finite state") from None
    if code:
        raise PropagationError(f"SGP4 error {code}: {SGP4_ERRORS.get(code, 'unknown')}")
    try:
        valid = (
            len(position) == 3
            and len(velocity) == 3
            and all(
                not isinstance(x, bool) and math.isfinite(x)
                for x in (*position, *velocity)
            )
        )
    except (TypeError, OverflowError):
        valid = False
    if not valid:
        raise PropagationError("SGP4 returned non-finite or malformed results")
    return {"position_km": list(position), "velocity_km_s": list(velocity)}


def propagate(elements: Elements, at: datetime) -> dict:
    if not isinstance(at, datetime) or at.tzinfo is None or at.utcoffset() is None:
        raise PropagationError("Calculation time must include a timezone")
    try:
        at = at.astimezone(UTC)
    except (ValueError, OverflowError):
        raise PropagationError("Calculation time is not representable in UTC") from None
    offset_days = (at - elements.epoch).total_seconds() / 86400
    # A product safety bound, not an accuracy guarantee within the window.
    if abs(offset_days) > 7:
        raise PropagationError(
            "Requested time exceeds the supported ±7-day epoch window",
            code="epoch_window_exceeded",
        )
    try:
        satellite = elements.satellite()
    except (ValueError, OverflowError, ArithmeticError):
        raise PropagationError("Orbital elements cannot initialize SGP4") from None
    result = propagate_satellite(satellite, at)
    return {
        **result,
        "kind": "calculated",
        "frame": "TEME",
        "origin": "Earth center",
        "time_system": "UTC",
        "at": at.isoformat(),
        "calculated_at": datetime.now(UTC).isoformat(),
        "orbital_epoch": elements.epoch.isoformat(),
        "epoch_offset_days": offset_days,
        "model": "SGP4",
        "gravity_model": "WGS72",
        "units": {"position": "km", "velocity": "km/s", "epoch_offset": "days"},
        "uncertainty": {
            "status": "not_quantified",
            "covariance_available": False,
            "observation_validated": False,
        },
        "validation_scope": "Published numerical cases; not observed orbit accuracy",
        "sgp4_version": sgp4.__version__,
        "validation_status": "reference_tested_engine_not_observation_validated",
        "warnings": [
            "Calculated from mean elements, not a direct observation.",
            "No position uncertainty or collision assessment is provided.",
            *(
                ["Calculation is more than 24 hours from the orbital epoch."]
                if abs(offset_days) > 1
                else []
            ),
        ],
    }
