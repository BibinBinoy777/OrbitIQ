import type { TrackPoint } from "./ground-track-api";
import { formatUtc } from "./time-presentation";
export const EARTH_RADIUS_KM = 6378.137;
export const EARTH_POLAR_RATIO = 1 - 1 / 298.257223563;
export function displayVector(
  vector: readonly number[],
): [number, number, number] {
  // Presentation basis only: ITRS (x,y,z) -> Three (x,z,-y), uniform km scale.
  if (vector.length !== 3 || !vector.every(Number.isFinite))
    throw new Error("Invalid display vector");
  return [
    vector[0] / EARTH_RADIUS_KM,
    vector[2] / EARTH_RADIUS_KM,
    -vector[1] / EARTH_RADIUS_KM,
  ];
}
export function canRenderPoint(point?: TrackPoint): boolean {
  return (
    !!point &&
    point.frame === "ITRS" &&
    formatUtc(point.at) !== "Unavailable" &&
    [point.position_km, point.ground_position_km].every(
      (v) =>
        Array.isArray(v) &&
        v.length === 3 &&
        v.every(Number.isFinite) &&
        Math.hypot(...v) > 0 &&
        Math.hypot(...v) / EARTH_RADIUS_KM < 400,
    )
  );
}
export function canConnect(a: TrackPoint, b: TrackPoint): boolean {
  return (
    a.segment_id === b.segment_id &&
    Date.parse(b.at) - Date.parse(a.at) <= 60000
  );
}
