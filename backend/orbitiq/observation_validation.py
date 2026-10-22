"Bounded observation contract and residual arithmetic, never fabricated measurements."

import hashlib
import json
import math
from collections import Counter
from statistics import median
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from orbitiq.orbits.freshness import utc
from orbitiq.reporting import ReportTime

MAX_SAMPLES = 10
MAX_INPUT = 65536
MAX_REPORT = 1024 * 1024
VERSION = 1
Number = Annotated[float, Field(strict=True, allow_inf_nan=False, ge=-1e9, le=1e9)]
Text = Annotated[str, Field(strict=True, min_length=1, max_length=256)]
Hash = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Uncertainty(Contract):
    kind: Literal["axis_standard_deviation"]
    values: tuple[Number, Number, Number]
    unit: Literal["km", "m"]
    provenance: Text

    @field_validator("values")
    @classmethod
    def nonnegative(cls, value):
        if any(v < 0 for v in value):
            raise ValueError("Standard deviations cannot be negative")
        return value


class Observation(Contract):
    observation_id: Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$")]
    catalog_id: Annotated[int, Field(strict=True, ge=1, le=339999)]
    source_id: Text
    source_organization: Text | None = None
    source_record_reference: Text
    upstream_payload_sha256: Hash | None = None
    retrieved_at: ReportTime | None = None
    observed_at: ReportTime
    time_scale: Text
    frame: Text
    origin: Text
    unit: Text
    measurement_type: Text
    data_kind: Literal[
        "measurement", "observation_derived_state", "model_output", "unknown"
    ]
    position: tuple[Number, Number, Number]
    quality: Literal["accepted", "unknown", "rejected"]
    quality_reference: Text | None = None
    uncertainty: Uncertainty | None = None


LIMITATIONS = [
    "Residuals are observed minus predicted, after explicit time/frame/unit checks.",
    "Operator-normalized observations are not independently authenticated by OrbitIQ. "
    "Their original input bytes are retained; upstream hashes are declarations only.",
    (
        "CelesTrak GP fitting-observation lineage is unavailable. "
        "Different IDs/providers do not establish independence. "
        "Temporal holdout is conditional on truthful clocks."
    ),
    (
        "Retrospective propagation from archived input is not a "
        "historically issued forecast."
    ),
    (
        "Prediction uncertainty is unquantified. Observation sigmas "
        "are retained without joint covariance, significance tests, "
        "confidence intervals or weighted statistics."
    ),
    "Descriptive discrepancy statistics do not establish model accuracy, causes, "
    "maneuvers, anomalies, collision risk or operational safety.",
    "No interpolation, extrapolated error trend or outlier removal is performed.",
]


def encoded(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def identity(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def parse_input(raw):
    from orbitiq.replay_json import decoded

    # Existing bounded/duplicate-key/nonfinite parser; original bytes remain separate.
    if len(raw) > MAX_INPUT:
        raise ValueError("Observation input exceeds limit")
    value = decoded(raw)
    if (
        not isinstance(value, dict)
        or set(value) != {"kind", "schema_version", "observations"}
        or value["kind"] != "orbitiq_observation_input"
        or type(value["schema_version"]) is not int
        or value["schema_version"] != VERSION
        or not isinstance(value["observations"], list)
        or not 1 <= len(value["observations"]) <= MAX_SAMPLES
    ):
        raise ValueError("Expected version-1 observation input with 1–10 records")
    return value["observations"]


def duplicate_indices(records):
    ids, sources = [], []
    for r in records:
        if isinstance(r, dict):
            ids.append(str(r.get("observation_id")))
            sources.append(
                (str(r.get("source_id")), str(r.get("source_record_reference")))
            )
        else:
            ids.append(None)
            sources.append(None)
    payload_keys = [
        (r.get("upstream_payload_sha256"), str(r.get("source_record_reference")))
        if isinstance(r, dict) and isinstance(r.get("upstream_payload_sha256"), str)
        else (None, i)
        for i, r in enumerate(records)
    ]
    payload_counts = Counter(payload_keys)
    id_counts, source_counts = Counter(ids), Counter(sources)
    return {
        i
        for i in range(len(records))
        if id_counts[ids[i]] > 1
        or source_counts[sources[i]] > 1
        or payload_counts[payload_keys[i]] > 1
    }


def compatible(observation, source, now):
    checks = {
        "target_identity": observation.catalog_id == source["catalog_id"],
        "time_scale": observation.time_scale == "UTC",
        "coordinate_frame": observation.frame in {"TEME", "ITRS"},
        "origin": observation.origin == "Earth center",
        "unit": observation.unit in {"km", "m"},
        "measurement_type": observation.measurement_type
        == "geocentric_cartesian_position",
        "measurement_kind": observation.data_kind
        in {"measurement", "observation_derived_state"},
        "quality": observation.quality != "rejected",
        "observed_not_future": observation.observed_at <= now,
        "retrieval_chronology": observation.retrieved_at is None
        or (observation.observed_at <= observation.retrieved_at <= now),
    }
    return checks


def independence(observation, source):
    if observation.upstream_payload_sha256 == source["response_sha256"]:
        return {
            "status": "reused_prediction_payload",
            "eligible": False,
            "basis": (
                "Declared observation payload equals the prediction input payload."
            ),
        }
    after = observation.observed_at > utc(source["retrieved_at"])
    return {
        "status": "temporal_holdout_candidate_unverified"
        if after
        else "unverified_input_lineage",
        "eligible": False,
        "basis": (
            "Observation time is after archived input retrieval; "
            "conditional holdout only, not authenticated independent "
            "evidence."
        )
        if after
        else (
            "Prediction fitting-observation lineage is not available; "
            "input reuse cannot be excluded."
        ),
    }


def residual(predicted, observed):
    if (
        len(predicted) != 3
        or len(observed) != 3
        or not all(
            type(v) in (float, int) and math.isfinite(v)
            for v in (*predicted, *observed)
        )
    ):
        raise ValueError("Three finite numeric components required")
    delta = [o - p for o, p in zip(observed, predicted, strict=True)]
    magnitude = math.hypot(*delta)
    if not all(math.isfinite(v) and abs(v) <= 1e12 for v in (*delta, magnitude)):
        raise ValueError("Residual is outside finite numeric range")
    return {
        "xyz_km": delta,
        "magnitude_km": magnitude,
        "sign": "observed_minus_predicted",
    }


def rac(delta, position, velocity, frame):
    if frame != "TEME":
        return {
            "status": "unavailable",
            "reason": (
                "RAC requires supported inertial TEME state; no rotating-"
                "frame basis is substituted."
            ),
        }
    cross = [
        position[1] * velocity[2] - position[2] * velocity[1],
        position[2] * velocity[0] - position[0] * velocity[2],
        position[0] * velocity[1] - position[1] * velocity[0],
    ]
    radius, momentum = math.hypot(*position), math.hypot(*cross)
    scale = radius * math.hypot(*velocity)
    if (
        not all(math.isfinite(v) for v in (radius, momentum, scale))
        or radius == 0
        or scale == 0
        or momentum <= 1e-12 * scale
    ):
        return {
            "status": "unavailable",
            "reason": "Degenerate or ill-conditioned radial/transverse/normal basis.",
        }
    r, c = [v / radius for v in position], [v / momentum for v in cross]
    a = [
        c[1] * r[2] - c[2] * r[1],
        c[2] * r[0] - c[0] * r[2],
        c[0] * r[1] - c[1] * r[0],
    ]
    values = [
        math.fsum(x * y for x, y in zip(delta, axis, strict=True)) for axis in (r, a, c)
    ]
    if not all(math.isfinite(v) for v in values):
        raise ValueError("Nonfinite RAC residual")
    return {
        "status": "complete",
        "radial_km": values[0],
        "along_track_km": values[1],
        "cross_track_km": values[2],
        "definition": (
            "R=r/|r|, C=(r×v)/|r×v|, A=C×R; along-track is transverse, "
            "not generally velocity direction."
        ),
    }


def statistics(samples):
    n = len(samples)
    if n < 2:
        return {
            "status": "insufficient_samples",
            "sample_count": n,
            "minimum_samples": 2,
            "values": None,
        }

    def scalar(values):
        bias = math.fsum(values) / n
        return {
            "bias": bias,
            "mae": math.fsum(abs(v) for v in values) / n,
            "rmse": math.hypot(*values) / math.sqrt(n),
            "maximum_absolute": max(abs(v) for v in values),
            "median_absolute": median(abs(v) for v in values),
            "population_standard_deviation": math.hypot(*(v - bias for v in values))
            / math.sqrt(n),
        }

    axes = {
        name: scalar([s["xyz_km"][i] for s in samples])
        for i, name in enumerate(("x", "y", "z"))
    }
    norms = [s["magnitude_km"] for s in samples]
    return {
        "status": "descriptive_only",
        "sample_count": n,
        "unit": "km",
        "axes": axes,
        "position_norm": {
            "mean": math.fsum(norms) / n,
            "rmse": math.hypot(*norms) / math.sqrt(n),
            "maximum": max(norms),
            "median": median(norms),
        },
        "aggregation": (
            "Equal-weight compatible samples; denominator N for "
            "RMS/dispersion. No independent/IID population inference."
        ),
    }
