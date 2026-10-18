// Explicitly synthetic wire fixtures for UI contract tests, never live data.
import type { SnapshotSummary } from "../scientific-api";
export const source: SnapshotSummary = {
  id: 7,
  catalog_id: 25544,
  object_name: "TEST FIXTURE ONLY",
  orbital_epoch: "2024-01-01T00:00:00+00:00",
  retrieved_at: "2024-01-01T01:00:00+00:00",
  response_sha256: "a".repeat(64),
  freshness_info: { state: "stale" },
};
export function fixture() {
  const points = [179, -179, -178].map((longitude, i) => {
    const at = `2024-01-01T00:0${i}:00+00:00`;
    return {
      at,
      sample_index: i,
      segment_id: i === 0 ? 0 : 1,
      frame: "ITRS",
      input_frame: "TEME",
      kind: "calculated",
      time_system: "UTC",
      units: {
        angles: "deg",
        altitude: "km",
        position: "km",
        velocity: "km/s",
      },
      geodetic: {
        latitude_deg: i * 5,
        longitude_deg: longitude,
        altitude_km: 400,
        height_reference: "WGS84 ellipsoid",
      },
      teme: {
        snapshot_id: 7,
        catalog_id: 25544,
        response_sha256: source.response_sha256,
        orbital_epoch: source.orbital_epoch,
        retrieved_at: source.retrieved_at,
        at,
        frame: "TEME",
      },
      transformation_status: "predicted_eop",
      earth_orientation: {
        status: "predicted",
        source: "BUNDLED EOP TEST FIXTURE",
        package_version: "fixture-version",
        sha256: "b".repeat(64),
        policy: "measured_or_predicted",
        auto_download: false,
        degraded_results_allowed: false,
      },
      warnings: ["Predicted EOP fixture warning"],
    };
  });
  return {
    status: "complete",
    failure_policy: "reject_entire_request",
    snapshot_id: 7,
    catalog_id: 25544,
    response_sha256: source.response_sha256,
    orbital_epoch: source.orbital_epoch,
    retrieved_at: source.retrieved_at,
    requested_start: points[0].at,
    requested_end: points[2].at,
    actual_start: points[0].at,
    actual_end: points[2].at,
    step_seconds: 60,
    sample_count: 3,
    frame: "ITRS",
    input_frame: "TEME",
    kind: "calculated",
    points,
    warnings: ["Synthetic UI fixture, not actual observations"],
  };
}
