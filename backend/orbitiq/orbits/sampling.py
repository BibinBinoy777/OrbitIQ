"""Integer-second bounded, chronological sampling; no unaligned end point."""

import os
from dataclasses import dataclass
from datetime import datetime, timedelta

from orbitiq.orbits.earth_orientation import TransformationError
from orbitiq.orbits.freshness import utc


@dataclass(frozen=True)
class SamplingPolicy:
    max_samples: int = 361
    max_duration_seconds: int = 86400

    @classmethod
    def configured(cls):
        try:
            samples = int(os.environ.get("ORBITIQ_TRACK_MAX_SAMPLES", "361"))
            duration = int(
                os.environ.get("ORBITIQ_TRACK_MAX_DURATION_SECONDS", "86400")
            )
            if not 1 <= samples <= 1000 or not 10 <= duration <= 86400:
                raise ValueError
            return cls(samples, duration)
        except (ValueError, OverflowError):
            raise TransformationError(
                "sampling_configuration", "Ground-track limits are invalid", 503
            ) from None


def sample_times(
    start: datetime,
    end: datetime,
    step_seconds: int,
    epoch: datetime,
    policy: SamplingPolicy,
):
    start, end, epoch = utc(start), utc(end), utc(epoch)
    if start is None or end is None or epoch is None:
        raise TransformationError(
            "invalid_interval", "Sampling times must include timezones"
        )
    if start > end:
        raise TransformationError(
            "invalid_interval", "Interval end must not precede start"
        )
    if (
        isinstance(step_seconds, bool)
        or not isinstance(step_seconds, int)
        or not 10 <= step_seconds <= 3600
    ):
        raise TransformationError(
            "sampling_limit", "Sampling step must be an integer from 10 to 3600 seconds"
        )
    duration = (end - start).total_seconds()
    count = int(duration // step_seconds) + 1
    if duration > policy.max_duration_seconds or count > policy.max_samples:
        raise TransformationError(
            "sampling_limit",
            "Requested track exceeds configured duration or sample limits",
        )
    if any(abs((t - epoch).total_seconds()) > 7 * 86400 for t in (start, end)):
        raise TransformationError(
            "epoch_window_exceeded",
            "Requested interval exceeds the supported ±7-day epoch window",
        )
    return [start + timedelta(seconds=i * step_seconds) for i in range(count)]
