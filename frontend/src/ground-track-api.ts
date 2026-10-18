import type { SnapshotSummary } from "./scientific-api";
import { formatUtc } from "./time-presentation";

export interface TrackPoint {
  at: string;
  sample_index: number;
  segment_id: number;
  geodetic: {
    latitude_deg: number;
    longitude_deg: number;
    altitude_km: number;
    height_reference: "WGS84 ellipsoid";
  };
  transformation_status: "measured_eop" | "predicted_eop";
  earth_orientation: {
    status: "measured" | "predicted";
    source: string;
    package_version: string;
    sha256: string;
    policy: string;
  };
  warnings: string[];
}
export interface GroundTrackResult {
  status: "complete";
  snapshot_id: number;
  catalog_id: number;
  response_sha256: string;
  orbital_epoch: string;
  retrieved_at: string;
  requested_start: string;
  requested_end: string;
  actual_start: string;
  actual_end: string;
  step_seconds: number;
  frame: "ITRS";
  input_frame: "TEME";
  kind: "calculated";
  points: TrackPoint[];
  warnings: string[];
}
function record(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null;
}
function finite(v: unknown): v is number {
  return typeof v === "number" && Number.isFinite(v);
}
function text(v: unknown): v is string {
  return typeof v === "string";
}
function strings(v: unknown): v is string[] {
  return Array.isArray(v) && v.every(text);
}
function timestamp(v: unknown): v is string {
  return (
    text(v) && /T.*(?:Z|\+00:00)$/.test(v) && formatUtc(v) !== "Unavailable"
  );
}
export function parseTrack(
  data: unknown,
  source: SnapshotSummary,
): GroundTrackResult {
  const invalid = () =>
    new Error(
      "Ground-track response has invalid coordinates, provenance, timing or scientific metadata",
    );
  if (
    !record(data) ||
    data.status !== "complete" ||
    data.failure_policy !== "reject_entire_request"
  )
    throw new Error(
      "Incomplete or partial track received. No track is displayed.",
    );
  if (
    data.snapshot_id !== source.id ||
    data.catalog_id !== source.catalog_id ||
    data.response_sha256 !== source.response_sha256 ||
    !text(data.response_sha256) ||
    !/^[a-f0-9]{64}$/.test(data.response_sha256) ||
    data.orbital_epoch !== source.orbital_epoch ||
    data.retrieved_at !== source.retrieved_at ||
    data.frame !== "ITRS" ||
    data.input_frame !== "TEME" ||
    data.kind !== "calculated" ||
    !Array.isArray(data.points) ||
    data.points.length === 0 ||
    data.points.length > 1000 ||
    data.sample_count !== data.points.length ||
    !strings(data.warnings) ||
    !timestamp(data.requested_start) ||
    !timestamp(data.requested_end) ||
    !timestamp(data.actual_start) ||
    !timestamp(data.actual_end) ||
    !Number.isInteger(data.step_seconds) ||
    !finite(data.step_seconds) ||
    data.step_seconds < 10 ||
    data.step_seconds > 3600
  )
    throw invalid();
  let previous = -Infinity;
  let previousSegment = 0;
  let previousLongitude: number | null = null;
  const points: TrackPoint[] = data.points.map((p: unknown, i: number) => {
    if (
      !record(p) ||
      !record(p.geodetic) ||
      !record(p.earth_orientation) ||
      !record(p.teme) ||
      !record(p.units) ||
      p.units.angles !== "deg" ||
      p.units.altitude !== "km" ||
      p.units.position !== "km" ||
      p.units.velocity !== "km/s" ||
      p.frame !== "ITRS" ||
      p.input_frame !== "TEME" ||
      p.kind !== "calculated" ||
      p.time_system !== "UTC" ||
      p.teme.snapshot_id !== source.id ||
      p.teme.catalog_id !== source.catalog_id ||
      p.teme.response_sha256 !== source.response_sha256 ||
      p.teme.orbital_epoch !== source.orbital_epoch ||
      p.teme.retrieved_at !== source.retrieved_at ||
      p.teme.at !== p.at ||
      p.teme.frame !== "TEME" ||
      !timestamp(p.at) ||
      p.sample_index !== i ||
      !finite(p.segment_id) ||
      !Number.isInteger(p.segment_id) ||
      !finite(p.geodetic.latitude_deg) ||
      Math.abs(p.geodetic.latitude_deg) > 90 ||
      !finite(p.geodetic.longitude_deg) ||
      p.geodetic.longitude_deg < -180 ||
      p.geodetic.longitude_deg >= 180 ||
      !finite(p.geodetic.altitude_km) ||
      p.geodetic.height_reference !== "WGS84 ellipsoid" ||
      !strings(p.warnings) ||
      !text(p.earth_orientation.source) ||
      !text(p.earth_orientation.package_version) ||
      !text(p.earth_orientation.sha256) ||
      !/^[a-f0-9]{64}$/.test(p.earth_orientation.sha256) ||
      !["measured_only", "measured_or_predicted"].includes(
        String(p.earth_orientation.policy),
      ) ||
      !["measured", "predicted"].includes(String(p.earth_orientation.status)) ||
      p.earth_orientation.auto_download !== false ||
      p.earth_orientation.degraded_results_allowed !== false ||
      p.transformation_status !==
        (p.earth_orientation.status === "predicted"
          ? "predicted_eop"
          : "measured_eop")
    )
      throw invalid();
    const time = Date.parse(p.at);
    const expectedSegment =
      previousSegment +
      (previousLongitude !== null &&
      Math.abs(p.geodetic.longitude_deg - previousLongitude) > 180
        ? 1
        : 0);
    if (
      time <= previous ||
      p.segment_id !== expectedSegment ||
      time < Date.parse(data.requested_start as string) ||
      time > Date.parse(data.requested_end as string) ||
      (i > 0 &&
        Math.abs(time - previous - Number(data.step_seconds) * 1000) > 1)
    )
      throw invalid();
    previous = time;
    previousSegment = p.segment_id;
    previousLongitude = p.geodetic.longitude_deg;
    return p as unknown as TrackPoint;
  });
  if (
    points[0].at !== data.actual_start ||
    points.at(-1)?.at !== data.actual_end ||
    Date.parse(data.actual_start) !== Date.parse(data.requested_start)
  )
    throw invalid();
  return { ...data, points } as unknown as GroundTrackResult;
}
export async function getGroundTrack(
  source: SnapshotSummary,
  start: string,
  end: string,
  step: number,
  signal: AbortSignal,
): Promise<GroundTrackResult> {
  const params = new URLSearchParams({
    snapshot_id: String(source.id),
    start,
    end,
    step_seconds: String(step),
    frame: "ITRS",
  });
  const response = await fetch(
    `/api/satellites/${source.catalog_id}/ground-track?${params}`,
    { signal: AbortSignal.any([signal, AbortSignal.timeout(20000)]) },
  );
  let data: unknown;
  try {
    data = await response.json();
  } catch {
    throw new Error("Unreadable ground-track response");
  }
  if (!response.ok) {
    const message =
      record(data) && record(data.error) ? data.error.message : undefined;
    throw new Error(
      text(message) && message.length <= 300
        ? message
        : `Ground-track request failed (${response.status})`,
    );
  }
  const result = parseTrack(data, source);
  if (
    Date.parse(result.requested_start) !== Date.parse(start) ||
    Date.parse(result.requested_end) !== Date.parse(end) ||
    result.step_seconds !== step
  )
    throw new Error("Ground-track times do not match the requested interval");
  return result;
}
