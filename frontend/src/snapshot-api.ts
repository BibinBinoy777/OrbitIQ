import type { SnapshotSummary } from "./scientific-api";
export interface OrbitalElements {
  inclination_deg: number;
  eccentricity: number;
  mean_motion_rev_day: number;
  object_id: string;
}
function object(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null;
}
function finite(v: unknown): v is number {
  return typeof v === "number" && Number.isFinite(v);
}
export async function getOrbitalElements(
  source: SnapshotSummary,
  signal: AbortSignal,
): Promise<OrbitalElements> {
  const response = await fetch(`/api/snapshots/${source.id}`, {
    signal: AbortSignal.any([signal, AbortSignal.timeout(5000)]),
  });
  if (!response.ok)
    throw new Error(
      "Source elements unavailable. Try selecting the snapshot again.",
    );
  const data: unknown = await response.json();
  if (
    !object(data) ||
    data.id !== source.id ||
    data.catalog_id !== source.catalog_id ||
    data.response_sha256 !== source.response_sha256 ||
    data.orbital_epoch !== source.orbital_epoch ||
    !object(data.normalized_record) ||
    !object(data.element_units)
  )
    throw new Error("Source element identity or provenance is invalid");
  const r = data.normalized_record,
    u = data.element_units;
  if (
    !finite(r.INCLINATION) ||
    r.INCLINATION < 0 ||
    r.INCLINATION > 180 ||
    !finite(r.ECCENTRICITY) ||
    r.ECCENTRICITY < 0 ||
    r.ECCENTRICITY >= 1 ||
    !finite(r.MEAN_MOTION) ||
    r.MEAN_MOTION <= 0 ||
    r.MEAN_MOTION > 100 ||
    typeof r.OBJECT_ID !== "string" ||
    u.INCLINATION !== "deg" ||
    u.MEAN_MOTION !== "rev/day" ||
    u.ECCENTRICITY !== "dimensionless"
  )
    throw new Error("Source element units or values are invalid");
  return {
    inclination_deg: r.INCLINATION,
    eccentricity: r.ECCENTRICITY,
    mean_motion_rev_day: r.MEAN_MOTION,
    object_id: r.OBJECT_ID,
  };
}
