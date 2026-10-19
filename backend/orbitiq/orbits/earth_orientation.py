"""Explicit, offline IERS resources; no IERS-Auto or assumed EOP fallback."""

import hashlib
import os
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from threading import RLock

import astropy_iers_data
import numpy as np
from astropy import units as u
from astropy.time import Time, TimeDelta
from astropy.utils import iers


class TransformationError(ValueError):
    def __init__(self, code: str, message: str, status: int = 422):
        super().__init__(message)
        self.code, self.status = code, status


@dataclass(frozen=True)
class Resources:
    table: iers.IERS_A
    leaps: iers.LeapSeconds
    metadata: dict


LOCK = RLock()  # Astropy ScienceState and configuration contexts are process-global.


@lru_cache(maxsize=1)
def resources() -> Resources:
    try:
        eop = Path(astropy_iers_data.IERS_A_FILE)
        leap = Path(astropy_iers_data.IERS_LEAP_SECOND_FILE)
        table = iers.IERS_A.open(str(eop))
        leaps = iers.LeapSeconds.open(str(leap))
        return Resources(
            table,
            leaps,
            {
                "source": "astropy-iers-data bundled IERS-A finals2000A.all",
                "package_version": astropy_iers_data.__version__,
                "sha256": hashlib.sha256(eop.read_bytes()).hexdigest(),
                "leap_seconds_sha256": hashlib.sha256(leap.read_bytes()).hexdigest(),
                "leap_seconds_expires": leaps.expires.isot,
                "first_mjd": float(table["MJD"][0].value),
                "last_mjd": float(table["MJD"][-1].value),
                "predictive_mjd": float(table.meta["predictive_mjd"]),
            },
        )
    except (OSError, ValueError, KeyError, TypeError):
        raise TransformationError(
            "eop_unavailable",
            "Required local Earth-orientation resources are unavailable",
            503,
        ) from None


@contextmanager
def orientation():
    mode = os.environ.get("ORBITIQ_EOP_POLICY", "measured_or_predicted")
    if mode not in {"measured_only", "measured_or_predicted"}:
        raise TransformationError(
            "eop_configuration", "Earth-orientation policy is invalid", 503
        )
    with (
        LOCK,
        iers.conf.set_temp("auto_download", False),
        iers.conf.set_temp("iers_degraded_accuracy", "error"),
        iers.conf.set_temp("iers_leap_second_auto_url", ""),
        iers.conf.set_temp("ietf_leap_second_auto_url", ""),
        iers.conf.set_temp(
            "system_leap_second_file", astropy_iers_data.IERS_LEAP_SECOND_FILE
        ),
    ):
        data = resources()
        try:
            data.leaps.update_erfa_leap_seconds(initialize_erfa=True)
        except (ValueError, OSError):
            raise TransformationError(
                "eop_unavailable", "Leap-second resource is invalid", 503
            ) from None
        with iers.earth_orientation_table.set(data.table):
            yield data, mode


def parameters(data: Resources, at: Time, mode: str, *, now: datetime | None = None):
    """Preflight all EOP used by Astropy's one-second velocity difference."""
    support = at + TimeDelta([-0.5, 0, 0.5], format="sec")
    if np.any(support >= data.leaps.expires):
        raise TransformationError(
            "leap_seconds_out_of_range",
            "Requested date exceeds the local leap-second validity",
        )
    try:
        dut1, ut_status = data.table.ut1_utc(support, return_status=True)
        xp, yp, pm_status = data.table.pm_xy(support, return_status=True)
    except (ValueError, IndexError, TypeError):
        raise TransformationError(
            "eop_unavailable", "Earth-orientation data cannot be evaluated", 503
        ) from None
    statuses = np.concatenate([np.atleast_1d(ut_status), np.atleast_1d(pm_status)])
    if np.any(statuses < 0):
        raise TransformationError(
            "eop_out_of_range",
            "Requested date is outside local Earth-orientation coverage",
        )
    if not np.all(
        np.isin(
            statuses, [iers.FROM_IERS_B, iers.FROM_IERS_A, iers.FROM_IERS_A_PREDICTION]
        )
    ):
        raise TransformationError(
            "eop_unavailable", "Earth-orientation status is invalid", 503
        )
    if not all(np.all(np.isfinite(x.value)) for x in (dut1, xp, yp)):
        raise TransformationError(
            "eop_unavailable", "Earth-orientation parameters are not finite", 503
        )
    predicted = np.any(statuses == iers.FROM_IERS_A_PREDICTION)
    now = now or datetime.now(UTC)
    age = float(Time(now, scale="utc").mjd - data.metadata["predictive_mjd"])
    if predicted and mode == "measured_only":
        raise TransformationError(
            "eop_prediction_disallowed",
            "Policy requires measured Earth-orientation data",
        )
    if predicted and age > 30:
        raise TransformationError(
            "eop_predictions_expired",
            "Local Earth-orientation predictions need an explicit data update",
            503,
        )
    labels = {0: "IERS_B_final", 1: "IERS_A_measured", 2: "IERS_A_prediction"}
    # Preserve wire labels, but do not imply rapid IERS-A estimates are final.
    # Finite-difference velocity can require predicted support around a final
    # central epoch, so expose all contributing quality flags as well.
    quality = {0: "final", 1: "rapid_nonprediction", 2: "prediction"}
    return {
        **data.metadata,
        "policy": mode,
        "status": "predicted" if predicted else "measured",
        "ut1_source": labels[int(ut_status[1])],
        "polar_motion_source": labels[int(pm_status[1])],
        "source_quality": {
            "ut1": quality[int(ut_status[1])],
            "polar_motion": quality[int(pm_status[1])],
            "velocity_support_ut1": [quality[int(s)] for s in ut_status],
            "velocity_support_polar_motion": [quality[int(s)] for s in pm_status],
            "scope": (
                "IERS resource flags; rapid nonprediction values are not "
                "asserted final. They are not satellite observations."
            ),
        },
        "ut1_minus_utc_seconds": float(dut1[1].to_value(u.s)),
        "polar_motion_x_arcsec": float(xp[1].to_value(u.arcsec)),
        "polar_motion_y_arcsec": float(yp[1].to_value(u.arcsec)),
        "prediction_table_age_days": age,
        "max_prediction_table_age_days": 30,
        "auto_download": False,
        "degraded_results_allowed": False,
        "velocity_support_seconds": [-0.5, 0.5],
    }
