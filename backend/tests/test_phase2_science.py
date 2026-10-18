"""Published-vector comparisons and distinct time/numeric consistency tests."""

import json
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest
from astropy.time import Time
from orbitiq.orbits.elements import Elements
from orbitiq.orbits.engine import PropagationError, propagate, propagate_satellite
from orbitiq.orbits.freshness import FreshnessPolicy, classify
from sgp4.api import Satrec
from sgp4.conveniences import sat_epoch_datetime

FIXTURES = json.loads((Path(__file__).parent / "fixtures/vallado-leo.json").read_text())
CASES = [(f, c) for f in FIXTURES for c in f["cases"]]


@pytest.mark.parametrize("fixture,case", CASES)
@pytest.mark.parametrize("input_format", ["tle", "omm"])
def test_additional_published_leo_vectors(fixture, case, input_format):
    satellite = Satrec.twoline2rv(*fixture["tle"])
    at = sat_epoch_datetime(satellite) + timedelta(minutes=case["minutes"])
    if input_format == "tle":
        result = propagate_satellite(satellite, at)
    else:
        result = propagate(Elements.model_validate(fixture["omm"]), at)
        assert result["units"] == {
            "position": "km",
            "velocity": "km/s",
            "epoch_offset": "days",
        }
        assert result["uncertainty"]["status"] == "not_quantified"
    assert result["position_km"] == pytest.approx(case["position_km"], abs=1e-5, rel=0)
    assert result["velocity_km_s"] == pytest.approx(
        case["velocity_km_s"], abs=1e-8, rel=0
    )


@pytest.mark.parametrize(
    "at",
    [
        datetime(2000, 1, 1, 12, tzinfo=UTC),
        datetime(2024, 2, 29, 23, 59, 59, 123456, tzinfo=UTC),
    ],
)
def test_julian_day_call_matches_independent_astropy_time(at):
    calls = []

    class CapturingSatellite:
        def sgp4(self, jd, fraction):
            calls.append(jd + fraction)
            return 0, (1, 2, 3), (4, 5, 6)

    propagate_satellite(CapturingSatellite(), at)
    # This verifies time input, not a second orbital-accuracy reference.
    assert calls[0] == pytest.approx(Time(at, scale="utc").jd, abs=1e-9, rel=0)
    if at.year == 2000:
        assert calls[0] == 2451545.0  # Standard Julian-date noon anchor.


@pytest.mark.parametrize("seconds", [-86400.25, -1.000001, 0, 0.000001, 86400.25])
def test_timezone_and_fractional_offset_consistency(seconds):
    elements = Elements.model_validate(FIXTURES[0]["omm"])
    at = elements.epoch + timedelta(seconds=seconds)
    utc_result = propagate(elements, at)
    offset_result = propagate(
        elements, at.astimezone(timezone(timedelta(hours=5, minutes=30)))
    )
    assert offset_result["at"] == utc_result["at"]
    assert offset_result["position_km"] == utc_result["position_km"]
    assert utc_result["epoch_offset_days"] == pytest.approx(seconds / 86400, abs=1e-12)


@pytest.mark.parametrize(
    "at",
    [
        None,
        "not a timestamp",
        datetime(2020, 1, 1),
        datetime(1, 1, 1, tzinfo=timezone(timedelta(hours=14))),
    ],
)
def test_invalid_time_is_rejected(at):
    with pytest.raises(PropagationError):
        propagate(Elements.model_validate(FIXTURES[0]["omm"]), at)


@pytest.mark.parametrize("bad", [float("inf"), float("nan")])
def test_nonfinite_velocity_is_rejected(bad):
    class BadSatellite:
        def sgp4(self, jd, fraction):
            return 0, (1, 2, 3), (0, bad, 0)

    with pytest.raises(PropagationError, match="non-finite"):
        propagate_satellite(BadSatellite(), datetime.now(UTC))


def test_propagator_overflow_is_sanitized():
    class OverflowingSatellite:
        def sgp4(self, jd, fraction):
            raise OverflowError("INTERNAL_PATH_MUST_NOT_LEAK")

    with pytest.raises(PropagationError) as caught:
        propagate_satellite(OverflowingSatellite(), datetime.now(UTC))
    assert "MUST_NOT_LEAK" not in str(caught.value)


NOW = datetime(2026, 10, 18, 12, tzinfo=UTC)


@pytest.mark.parametrize(
    "hours,state",
    [
        (0, "fresh"),
        (24, "fresh"),
        (24.000001, "aging"),
        (72, "aging"),
        (72.000001, "stale"),
        (-1, "future_epoch"),
    ],
)
def test_freshness_threshold_boundaries(hours, state):
    result = classify(NOW - timedelta(hours=hours), NOW, as_of=NOW)
    assert result["state"] == state
    assert result["epoch_age_seconds"] == pytest.approx(hours * 3600)
    assert result["accuracy_guarantee"] is False


@pytest.mark.parametrize(
    "epoch,retrieved",
    [
        (None, NOW),
        ("bad", NOW),
        (datetime(2026, 10, 18), NOW),
        (NOW, None),
        (NOW, NOW + timedelta(seconds=1)),
    ],
)
def test_unknown_age_and_clock_inconsistency(epoch, retrieved):
    assert classify(epoch, retrieved, as_of=NOW)["state"] == "unknown"


def test_recent_retrieval_does_not_refresh_old_epoch():
    result = classify(NOW - timedelta(days=30), NOW, as_of=NOW)
    assert result["state"] == "stale"
    assert result["retrieval_age_seconds"] == 0


def test_configurable_freshness_is_deterministic(monkeypatch):
    monkeypatch.setenv("ORBITIQ_FRESH_HOURS", "1")
    monkeypatch.setenv("ORBITIQ_STALE_HOURS", "3")
    policy = FreshnessPolicy.configured()
    assert (
        classify(NOW - timedelta(hours=2), NOW, as_of=NOW, policy=policy)["state"]
        == "aging"
    )
    assert classify(
        NOW - timedelta(hours=2), NOW, as_of=NOW, policy=policy
    ) == classify(NOW - timedelta(hours=2), NOW, as_of=NOW, policy=policy)


@pytest.mark.parametrize(
    "fresh,stale",
    [(0, 72), (24, 24), (24, 169), (float("nan"), 72), (24, float("inf"))],
)
def test_invalid_threshold_policy(fresh, stale):
    with pytest.raises(ValueError):
        FreshnessPolicy(fresh, stale)


@pytest.mark.parametrize(
    "position,velocity",
    [
        ((1, 2), (1, 2, 3)),
        ((1, 2, 3), (1, 2)),
        ((True, 2, 3), (1, 2, 3)),
        ((10**1000, 2, 3), (1, 2, 3)),
    ],
)
def test_malformed_or_overflowing_state_vectors_are_rejected(position, velocity):
    class InvalidState:
        def sgp4(self, jd, fraction):
            return 0, position, velocity

    with pytest.raises(PropagationError, match="malformed"):
        propagate_satellite(InvalidState(), NOW)


@pytest.mark.parametrize("days", [-7, 7])
def test_epoch_window_includes_its_documented_boundary(days):
    elements = Elements.model_validate(FIXTURES[1]["omm"])
    assert (
        propagate(elements, elements.epoch + timedelta(days=days))["epoch_offset_days"]
        == days
    )
    with pytest.raises(PropagationError, match="7-day"):
        propagate(
            elements,
            elements.epoch + timedelta(days=days, seconds=1 if days > 0 else -1),
        )
