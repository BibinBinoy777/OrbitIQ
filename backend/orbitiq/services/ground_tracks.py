"""Read-only Earth-fixed and ground-track orchestration from one fixed snapshot."""

from datetime import UTC
from pathlib import Path

from orbitiq.orbits.coordinates import earth_fixed
from orbitiq.orbits.earth_orientation import TransformationError
from orbitiq.orbits.sampling import SamplingPolicy, sample_times
from orbitiq.services import analysis


def terrestrial_position(path: Path, snapshot_id: int, at):
    try:
        return earth_fixed(analysis.position(path, snapshot_id, at))
    except TransformationError as error:
        raise analysis.AnalysisError(error.status, error.code, str(error)) from None


def track(path: Path, catalog_id: int, snapshot_id: int, start, end, step_seconds: int):
    item, elements = analysis.load_snapshot(path, snapshot_id)
    if item["catalog_id"] != catalog_id:
        raise analysis.AnalysisError(
            404,
            "satellite_not_found",
            "Snapshot does not belong to the requested satellite",
        )
    try:
        policy = SamplingPolicy.configured()
        times = sample_times(start, end, step_seconds, elements.epoch, policy)
        points, segment = [], 0
        for at in times:
            # Fail the entire response on any sample failure. No synthetic or
            # partial coordinates escape; no stored result is modified.
            result = earth_fixed(analysis.position_from_snapshot(item, elements, at))
            if (
                points
                and abs(
                    result["geodetic"]["longitude_deg"]
                    - points[-1]["geodetic"]["longitude_deg"]
                )
                > 180
            ):
                segment += 1
            points.append(
                {**result, "sample_index": len(points), "segment_id": segment}
            )
    except TransformationError as error:
        raise analysis.AnalysisError(error.status, error.code, str(error)) from None
    return {
        "status": "complete",
        "failure_policy": "reject_entire_request",
        "catalog_id": catalog_id,
        "snapshot_id": snapshot_id,
        "response_sha256": item["response_sha256"],
        "orbital_epoch": item["orbital_epoch"],
        "retrieved_at": item["retrieved_at"],
        "requested_start": start.astimezone(UTC).isoformat(),
        "requested_end": end.astimezone(UTC).isoformat(),
        "actual_start": points[0]["at"],
        "actual_end": points[-1]["at"],
        "step_seconds": step_seconds,
        "sample_count": len(points),
        "limits": {
            "max_samples": policy.max_samples,
            "max_duration_seconds": policy.max_duration_seconds,
            "min_step_seconds": 10,
            "max_step_seconds": 3600,
        },
        "input_frame": "TEME",
        "frame": "ITRS",
        "kind": "calculated",
        "points": points,
        "warnings": [
            (
                "Fixed source snapshot throughout the track; samples are "
                "calculated, not observed."
            ),
            "Only aligned sample times at or before the requested end are included.",
            (
                "Segments break across the antimeridian; lines between samples are"
                " a visualization, not a continuous ephemeris."
            ),
        ],
    }
