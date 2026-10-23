import { formatUtc } from "./time-presentation";
import { canonicalTime } from "./saved-investigation";
export type FreshnessState =
  "fresh" | "aging" | "stale" | "unknown" | "future_epoch";
export interface SnapshotSummary {
  id: number;
  catalog_id: number;
  object_name?: string;
  orbital_epoch?: string;
  retrieved_at?: string;
  snapshot_created_at?: string;
  source_url?: string;
  response_sha256?: string;
  frame?: string;
  validation_status?: string;
  freshness_info?: { state: FreshnessState; evaluated_at?: string };
}
export interface PositionResult {
  snapshot_id: number;
  catalog_id: number;
  kind: "calculated";
  model: "SGP4";
  gravity_model: "WGS72";
  time_system: "UTC";
  frame: "TEME";
  position_km: number[];
  velocity_km_s: number[];
  units: { position: "km"; velocity: "km/s" };
  at?: string;
  calculated_at?: string;
  orbital_epoch?: string;
  retrieved_at?: string;
  response_sha256?: string;
  validation_status?: string;
  sgp4_version?: string;
  warnings: string[];
}
function object(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
function integer(value: unknown): value is number {
  return typeof value === "number" && Number.isSafeInteger(value) && value > 0;
}
function string(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}
function freshness(value: unknown): SnapshotSummary["freshness_info"] {
  if (!object(value)) return undefined;
  const states: unknown[] = [
    "fresh",
    "aging",
    "stale",
    "unknown",
    "future_epoch",
  ];
  return states.includes(value.state)
    ? {
        state: value.state as FreshnessState,
        evaluated_at: string(value.evaluated_at),
      }
    : undefined;
}
async function request(path: string, signal: AbortSignal): Promise<unknown> {
  const response = await fetch(path, {
    signal: AbortSignal.any([signal, AbortSignal.timeout(5000)]),
  });
  let data: unknown;
  try {
    data = await response.json();
  } catch {
    throw new Error(`API returned an unreadable response (${response.status})`);
  }
  if (!response.ok) {
    const message =
      object(data) && object(data.error) ? data.error.message : undefined;
    throw new Error(
      typeof message === "string" && message.length <= 300
        ? message
        : `Request failed (${response.status})`,
    );
  }
  return data;
}
export async function getSnapshots(
  catalog: number,
  signal: AbortSignal,
): Promise<SnapshotSummary[]> {
  const data = await request(
    `/api/satellites/${catalog}/snapshots?limit=20`,
    signal,
  );
  if (
    !object(data) ||
    !Array.isArray(data.snapshots) ||
    data.snapshots.length > 100
  )
    throw new Error("Unexpected snapshot response");
  return data.snapshots.map((item: unknown) => {
    if (!object(item) || !integer(item.id) || item.catalog_id !== catalog)
      throw new Error("Snapshot identity is missing or mismatched");
    return {
      id: item.id,
      catalog_id: catalog,
      object_name: string(item.object_name),
      orbital_epoch: string(item.orbital_epoch),
      retrieved_at: string(item.retrieved_at),
      snapshot_created_at:
        typeof item.snapshot_created_at === "string" &&
        formatUtc(item.snapshot_created_at) !== "Unavailable"
          ? item.snapshot_created_at
          : undefined,
      source_url: string(item.source_url),
      response_sha256: string(item.response_sha256),
      frame: string(item.frame),
      validation_status: string(item.validation_status),
      freshness_info: freshness(item.freshness_info),
    };
  });
}
function vector(value: unknown): value is number[] {
  return (
    Array.isArray(value) &&
    value.length === 3 &&
    value.every((x: unknown) => typeof x === "number" && Number.isFinite(x))
  );
}
export async function getPosition(
  snapshot: number,
  at: string,
  signal: AbortSignal,
): Promise<PositionResult> {
  const data = await request(
    `/api/snapshots/${snapshot}/position?${new URLSearchParams({ at, frame: "TEME" })}`,
    signal,
  );
  if (
    !object(data) ||
    data.snapshot_id !== snapshot ||
    !integer(data.catalog_id) ||
    data.kind !== "calculated" ||
    data.model !== "SGP4" ||
    data.gravity_model !== "WGS72" ||
    data.time_system !== "UTC" ||
    data.frame !== "TEME" ||
    !vector(data.position_km) ||
    !vector(data.velocity_km_s) ||
    !object(data.units) ||
    data.units.position !== "km" ||
    data.units.velocity !== "km/s"
  )
    throw new Error(
      "Calculation response has invalid identity, frame, units or numbers",
    );
  // Missing legacy metadata remains unknown. If a time is supplied, it must
  // identify the requested instant, including all supported microseconds.
  if (data.at !== undefined) {
    try {
      if (canonicalTime(data.at) !== canonicalTime(at)) throw new Error();
    } catch {
      throw new Error("Calculation time does not match the requested time");
    }
  }
  return {
    snapshot_id: snapshot,
    catalog_id: data.catalog_id,
    kind: "calculated",
    model: "SGP4",
    gravity_model: "WGS72",
    time_system: "UTC",
    frame: "TEME",
    position_km: data.position_km,
    velocity_km_s: data.velocity_km_s,
    units: { position: "km", velocity: "km/s" },
    at: string(data.at),
    calculated_at: string(data.calculated_at),
    orbital_epoch: string(data.orbital_epoch),
    retrieved_at: string(data.retrieved_at),
    response_sha256: string(data.response_sha256),
    validation_status: string(data.validation_status),
    sgp4_version: string(data.sgp4_version),
    warnings: Array.isArray(data.warnings)
      ? data.warnings.filter((w): w is string => typeof w === "string")
      : [],
  };
}
