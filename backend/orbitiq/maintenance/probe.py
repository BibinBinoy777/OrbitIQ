"""Validate the installed, package-managed IERS resources without downloading."""

import json
import math
from pathlib import Path

import astropy
import astropy_iers_data
import numpy as np
from astropy import units as u
from astropy.time import Time

from orbitiq.orbits.earth_orientation import orientation, parameters


def validate_tables(table, leaps):
    if not 366 <= len(table) <= 100000:
        raise ValueError("Incomplete or oversized EOP table")
    for key, unit in (
        ("MJD", u.d),
        ("UT1_UTC", u.s),
        ("PM_x", u.arcsec),
        ("PM_y", u.arcsec),
    ):
        values = table[key].to_value(unit)
        if np.ma.is_masked(values) or not np.all(np.isfinite(values)):
            raise ValueError("Incomplete or invalid EOP numeric column")
    dates = table["MJD"].to_value(u.d)
    if not np.allclose(np.diff(dates), 1, rtol=0, atol=1e-8):
        raise ValueError("EOP coverage is not a coherent daily sequence")
    predicted = np.zeros(len(table), dtype=bool)
    for key in ("UT1Flag", "PolPMFlag"):
        flags = np.asarray(table[key])
        if not np.all(np.isin(flags, ["B", "I", "P"])):
            raise ValueError("Unknown EOP provenance flag")
        predicted |= flags == "P"
    if not np.any(predicted):
        raise ValueError("Prediction boundary unavailable")
    first_prediction = float(dates[np.flatnonzero(predicted)[0]])
    if (
        not math.isfinite(float(table.meta["predictive_mjd"]))
        or float(table.meta["predictive_mjd"]) != first_prediction
    ):
        raise ValueError("Prediction boundary metadata mismatch")
    if len(leaps) < 10 or not isinstance(leaps.expires, Time):
        raise ValueError("Leap-second resource is incomplete")
    if not np.all(np.isfinite(leaps["mjd"])) or not np.all(np.diff(leaps["mjd"]) > 0):
        raise ValueError("Leap-second chronology is invalid")
    if not np.all(np.isfinite(leaps["tai_utc"])) or float(leaps.expires.mjd) <= float(
        leaps["mjd"][-1]
    ):
        raise ValueError("Leap-second validity is incoherent")
    for date in (dates[0] - 1, dates[-1] + 1):
        time = Time(date, format="mjd", scale="utc")
        _, status = table.ut1_utc(time, return_status=True)
        _, _, polar = table.pm_xy(time, return_status=True)
        if int(status) >= 0 or int(polar) >= 0:
            raise ValueError("Out-of-coverage policy is not strict")


def describe(*, require_current=True):
    for filename, maximum in (
        (astropy_iers_data.IERS_A_FILE, 16 * 1024 * 1024),
        (astropy_iers_data.IERS_LEAP_SECOND_FILE, 65536),
    ):
        if not 0 < Path(filename).stat().st_size <= maximum:
            raise ValueError("Resource size is invalid")
    with orientation() as (data, mode):
        validate_tables(data.table, data.leaps)
        now = Time.now()
        # A maintenance candidate must support current-time operation under the
        # existing configured policy, not just a historical numerical reference.
        if require_current:
            parameters(data, now, mode)
        for date in ("2004-04-06T07:51:28.386", "2019-12-09T20:42:09.071993"):
            parameters(data, Time(date, scale="utc"), mode)
        return {
            **data.metadata,
            "astropy_version": astropy.__version__,
            "rows": len(data.table),
            "leap_rows": len(data.leaps),
            "validation_policy": mode,
            "strict_out_of_coverage": True,
            "current_time_resources_usable": True if require_current else None,
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--identity-only", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            describe(require_current=not args.identity_only),
            sort_keys=True,
            allow_nan=False,
        )
    )
