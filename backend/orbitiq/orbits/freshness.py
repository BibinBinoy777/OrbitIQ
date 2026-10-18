"""Deterministic presentation policy; age is not a position uncertainty model."""

import math
import os
from dataclasses import dataclass
from datetime import UTC, datetime


def utc(value: str | datetime | None) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value) if isinstance(value, str) else value
        if not isinstance(parsed, datetime) or parsed.tzinfo is None:
            return None
        return parsed.astimezone(UTC)
    except (ValueError, OverflowError):
        return None


@dataclass(frozen=True)
class FreshnessPolicy:
    fresh_hours: float = 24
    stale_hours: float = 72

    def __post_init__(self):
        if not (
            math.isfinite(self.fresh_hours)
            and math.isfinite(self.stale_hours)
            and 0 < self.fresh_hours < self.stale_hours <= 168
        ):
            raise ValueError(
                "Freshness thresholds must satisfy 0 < fresh < stale <= 168h"
            )

    @classmethod
    def configured(cls):
        return cls(
            float(os.environ.get("ORBITIQ_FRESH_HOURS", "24")),
            float(os.environ.get("ORBITIQ_STALE_HOURS", "72")),
        )


def classify(
    epoch: str | datetime | None,
    retrieved_at: str | datetime | None,
    *,
    as_of: datetime,
    policy: FreshnessPolicy | None = None,
) -> dict:
    policy = policy or FreshnessPolicy()
    now = utc(as_of)
    if now is None:
        raise ValueError("Freshness evaluation time must have a timezone")
    epoch_time, retrieval_time = utc(epoch), utc(retrieved_at)
    epoch_age = (now - epoch_time).total_seconds() if epoch_time else None
    retrieval_age = (now - retrieval_time).total_seconds() if retrieval_time else None
    if epoch_age is None or retrieval_age is None or retrieval_age < 0:
        state = "unknown"
    elif epoch_age < 0:
        state = "future_epoch"
    elif epoch_age <= policy.fresh_hours * 3600:
        state = "fresh"
    elif epoch_age <= policy.stale_hours * 3600:
        state = "aging"
    else:
        state = "stale"
    return {
        "state": state,
        "evaluated_at": now.isoformat(),
        "epoch_age_seconds": epoch_age,
        "retrieval_age_seconds": retrieval_age,
        "fresh_hours": policy.fresh_hours,
        "stale_hours": policy.stale_hours,
        "basis": "orbital_epoch",
        "accuracy_guarantee": False,
    }
