import { formatUtc } from "./time-presentation";
import type { SnapshotSummary, FreshnessState } from "./scientific-api";
import type { ComparisonMarker } from "./globe-geometry";
import { canRenderPoint } from "./globe-geometry";
export interface StoredSnapshot {
  id: number;
  catalog_id: number | null;
  object_name: string | null;
  object_id: string | null;
  identity_consistent: boolean;
  orbital_epoch: string | null;
  retrieved_at: string | null;
  snapshot_created_at?: string | null;
  source_url: string | null;
  provider: string | null;
  response_sha256: string | null;
  validation_status: string | null;
  validator_version: string | null;
  ingestion_sgp4_version: string | null;
  frame: string | null;
  record_count: number;
  metadata_issues: string[];
  membership: string;
  freshness_info: {
    state: FreshnessState;
    evaluated_at: string;
    epoch_age_seconds?: number | null;
  };
}
export interface SnapshotPage {
  snapshots: StoredSnapshot[];
  anchor_id: number | null;
  has_more: boolean;
  next_before_id: number | null;
  returned_count: number;
  scanned_count: number;
  scan_limit: number;
  total_count: number | null;
  total_count_status: string;
  evaluated_at: string;
  order: string;
  warnings: string[];
}
export type Category = "all" | "shared" | "added" | "removed" | "incompatible";
export interface ComparedState {
  at: string;
  calculated_at?: string;
  frame: "TEME" | "ITRS";
  position_km: [number, number, number];
  velocity_km_s: [number, number, number];
  ground_position_km?: [number, number, number];
  teme?: { calculated_at: string };
}
export interface Comparison {
  kind: "stored_snapshot_comparison";
  evaluated_at: string;
  first: StoredSnapshot;
  second: StoredSnapshot;
  is_self_comparison: boolean;
  chronology: {
    status: string;
    basis: string;
    older_snapshot_id: number | null;
    newer_snapshot_id: number | null;
  };
  counts: Record<Exclude<Category, "all">, number>;
  records: {
    category: Exclude<Category, "all">;
    catalog_id: number | null;
    first_snapshot_id: number | null;
    second_snapshot_id: number | null;
  }[];
  element_differences: {
    field: string;
    unit: string;
    first_value: number;
    second_value: number;
    difference: number;
    convention: string;
  }[];
  element_comparison_status: string;
  source_errors: ({ code: string; message: string } | null)[];
  provenance_differences: {
    field: string;
    first_value: string | null;
    second_value: string | null;
    status: string;
  }[];
  state_comparison: {
    status: "complete" | "unavailable" | "not_requested";
    evaluation_at: string | null;
    frame: "TEME" | "ITRS";
    first?: ComparedState | null;
    second?: ComparedState | null;
    errors?: ({ code: string; message: string } | null)[];
    difference_position_km?: number[] | null;
    difference_velocity_km_s?: number[] | null;
    separation_km?: number | null;
    relative_speed_km_s?: number | null;
  };
  caution: string;
  assumptions: string[];
}
export const elementUnits: Record<string, string> = {
  REV_AT_EPOCH: "rev",
  MEAN_MOTION: "rev/day",
  ECCENTRICITY: "dimensionless",
  INCLINATION: "deg",
  RA_OF_ASC_NODE: "deg",
  ARG_OF_PERICENTER: "deg",
  MEAN_ANOMALY: "deg",
  BSTAR: "1/Earth-radii",
  MEAN_MOTION_DOT: "rev/day^2",
  MEAN_MOTION_DDOT: "rev/day^3",
};
export function object(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null;
}
const id = (v: unknown): v is number =>
  typeof v === "number" && Number.isSafeInteger(v) && v > 0;
const finite = (v: unknown): v is number =>
  typeof v === "number" && Number.isFinite(v);
const vector = (v: unknown): v is [number, number, number] =>
  Array.isArray(v) && v.length === 3 && v.every(finite);
const strings = (v: unknown): v is string[] =>
  Array.isArray(v) && v.every((x) => typeof x === "string" && x.length <= 1000);
const time = (v: unknown): v is string =>
  typeof v === "string" && formatUtc(v) !== "Unavailable";
function canonicalTime(v: string): string {
  return formatUtc(v).replace(
    /\.(\d{3,6})Z \(UTC\)$/,
    (_all, fraction: string) => `.${fraction.padEnd(6, "0")}Z`,
  );
}
function invalid(): never {
  throw new Error(
    "Unexpected investigation response: identity, metadata or scientific contract is invalid.",
  );
}
export function parseStored(value: unknown): StoredSnapshot {
  if (
    !object(value) ||
    !id(value.id) ||
    !(
      value.catalog_id === null ||
      (id(value.catalog_id) && value.catalog_id <= 339999)
    ) ||
    typeof value.identity_consistent !== "boolean" ||
    !strings(value.metadata_issues) ||
    !object(value.freshness_info) ||
    !["fresh", "aging", "stale", "unknown", "future_epoch"].includes(
      String(value.freshness_info.state),
    ) ||
    !time(value.freshness_info.evaluated_at) ||
    value.record_count !== 1
  )
    return invalid();
  for (const key of [
    "object_name",
    "object_id",
    "orbital_epoch",
    "retrieved_at",
    "source_url",
    "provider",
    "response_sha256",
    "validation_status",
    "validator_version",
    "ingestion_sgp4_version",
    "frame",
  ]) {
    if (!(value[key] === null || typeof value[key] === "string"))
      return invalid();
  }
  if (
    (value.orbital_epoch !== null && !time(value.orbital_epoch)) ||
    (value.retrieved_at !== null && !time(value.retrieved_at)) ||
    (value.response_sha256 !== null &&
      !/^[a-f0-9]{64}$/.test(String(value.response_sha256)))
  )
    return invalid();
  if (value.snapshot_created_at != null && !time(value.snapshot_created_at))
    return invalid();
  if (value.source_url !== null) {
    try {
      const u = new URL(String(value.source_url));
      if (
        u.protocol !== "https:" ||
        !["celestrak.org", "www.celestrak.org"].includes(u.hostname) ||
        u.username ||
        u.password ||
        (u.port && u.port !== "443") ||
        u.pathname !== "/NORAD/elements/gp.php" ||
        u.hash ||
        u.searchParams.get("CATNR") !== String(value.catalog_id) ||
        u.searchParams.get("FORMAT") !== "JSON" ||
        [...u.searchParams].length !== 2
      )
        return invalid();
    } catch {
      return invalid();
    }
  }
  return value as unknown as StoredSnapshot;
}
export function explorerSource(value: StoredSnapshot): SnapshotSummary | null {
  if (
    !value.catalog_id ||
    !value.identity_consistent ||
    value.frame !== "TEME" ||
    !value.retrieved_at ||
    !value.source_url ||
    !value.orbital_epoch ||
    !value.response_sha256
  )
    return null;
  return {
    id: value.id,
    catalog_id: value.catalog_id,
    object_name: value.object_name ?? undefined,
    orbital_epoch: value.orbital_epoch,
    retrieved_at: value.retrieved_at ?? undefined,
    snapshot_created_at: value.snapshot_created_at ?? undefined,
    source_url: value.source_url ?? undefined,
    response_sha256: value.response_sha256,
    frame: value.frame ?? undefined,
    validation_status: value.validation_status ?? undefined,
    freshness_info: value.freshness_info,
  };
}
export function parsePage(data: unknown): SnapshotPage {
  if (
    !object(data) ||
    !Array.isArray(data.snapshots) ||
    data.snapshots.length > 100 ||
    typeof data.has_more !== "boolean" ||
    !(data.anchor_id === null || id(data.anchor_id)) ||
    !(data.next_before_id === null || id(data.next_before_id)) ||
    (data.has_more && !id(data.next_before_id)) ||
    !Number.isInteger(data.scanned_count) ||
    Number(data.scanned_count) < 0 ||
    Number(data.scanned_count) > 250 ||
    data.scan_limit !== 250 ||
    ![
      "exact_within_anchor",
      "unknown_exceeds_bounded_count",
      "not_computed_for_search",
    ].includes(String(data.total_count_status)) ||
    !(
      data.total_count === null ||
      (Number.isInteger(data.total_count) && Number(data.total_count) >= 0)
    ) ||
    !strings(data.warnings) ||
    !time(data.evaluated_at) ||
    data.order !== "insertion_id_desc_not_retrieval_chronology" ||
    data.returned_count !== data.snapshots.length
  )
    return invalid();
  const snapshots = data.snapshots.map(parseStored);
  if (
    new Set(snapshots.map((s) => s.id)).size !== snapshots.length ||
    snapshots.some(
      (s, i) =>
        (id(data.anchor_id) && s.id > data.anchor_id) ||
        (i > 0 && s.id >= snapshots[i - 1].id),
    )
  )
    return invalid();
  return { ...data, snapshots } as unknown as SnapshotPage;
}
function parseState(
  value: unknown,
  source: StoredSnapshot,
  at: string,
  frame: string,
): ComparedState {
  if (
    !object(value) ||
    value.at !== at ||
    value.frame !== frame ||
    value.kind !== "calculated" ||
    value.time_system !== "UTC" ||
    value.origin !== "Earth center" ||
    !vector(value.position_km) ||
    !vector(value.velocity_km_s) ||
    !object(value.units) ||
    value.units.position !== "km" ||
    value.units.velocity !== "km/s"
  )
    return invalid();
  const origin = frame === "ITRS" ? value.teme : value;
  if (
    !object(origin) ||
    origin.snapshot_id !== source.id ||
    origin.catalog_id !== source.catalog_id ||
    origin.response_sha256 !== source.response_sha256 ||
    origin.orbital_epoch !== source.orbital_epoch ||
    origin.retrieved_at !== source.retrieved_at ||
    origin.at !== at ||
    origin.frame !== "TEME" ||
    origin.model !== "SGP4" ||
    origin.gravity_model !== "WGS72" ||
    !time(origin.calculated_at)
  )
    return invalid();
  if (
    frame === "ITRS" &&
    (!vector(value.ground_position_km) ||
      !object(value.earth_orientation) ||
      !["measured", "predicted"].includes(
        String(value.earth_orientation.status),
      ) ||
      value.earth_orientation.auto_download !== false ||
      value.earth_orientation.degraded_results_allowed !== false ||
      !/^[a-f0-9]{64}$/.test(String(value.earth_orientation.sha256)) ||
      value.transformation_status !==
        (value.earth_orientation.status === "predicted"
          ? "predicted_eop"
          : "measured_eop"))
  )
    return invalid();
  return value as unknown as ComparedState;
}
export function parseComparison(
  data: unknown,
  firstId: number,
  secondId: number,
  requestedAt: string,
  requestedFrame: string,
): Comparison {
  if (
    !object(data) ||
    data.kind !== "stored_snapshot_comparison" ||
    !time(data.evaluated_at) ||
    !object(data.chronology) ||
    !object(data.counts) ||
    !Array.isArray(data.records) ||
    data.records.length > 2 ||
    !Array.isArray(data.element_differences) ||
    data.element_differences.length > 10 ||
    !Array.isArray(data.provenance_differences) ||
    !Array.isArray(data.source_errors) ||
    data.source_errors.length !== 2 ||
    !data.source_errors.every(
      (e) =>
        e === null ||
        (object(e) &&
          typeof e.code === "string" &&
          typeof e.message === "string"),
    ) ||
    !strings(data.assumptions) ||
    typeof data.caution !== "string" ||
    !object(data.state_comparison) ||
    typeof data.is_self_comparison !== "boolean"
  )
    return invalid();
  const first = parseStored(data.first),
    second = parseStored(data.second);
  if (
    first.id !== firstId ||
    second.id !== secondId ||
    data.is_self_comparison !== (firstId === secondId)
  )
    return invalid();
  if (
    !["ordered", "ambiguous_equal_retrieval_times", "unknown"].includes(
      String(data.chronology.status),
    ) ||
    data.chronology.basis !== "stored_retrieval_time" ||
    ![
      data.chronology.older_snapshot_id,
      data.chronology.newer_snapshot_id,
    ].every((v) => v === null || v === firstId || v === secondId)
  )
    return invalid();
  for (const key of ["shared", "added", "removed", "incompatible"])
    if (
      !Number.isInteger(data.counts[key]) ||
      Number(data.counts[key]) < 0 ||
      Number(data.counts[key]) > 2
    )
      return invalid();
  for (const row of data.element_differences) {
    if (
      !object(row) ||
      typeof row.field !== "string" ||
      row.unit !== elementUnits[row.field] ||
      !finite(row.first_value) ||
      !finite(row.second_value) ||
      !finite(row.difference) ||
      typeof row.convention !== "string"
    )
      return invalid();
  }
  for (const row of data.records)
    if (
      !object(row) ||
      !["shared", "added", "removed", "incompatible"].includes(
        String(row.category),
      )
    )
      return invalid();
  for (const row of data.provenance_differences)
    if (
      !object(row) ||
      typeof row.field !== "string" ||
      ![row.first_value, row.second_value].every(
        (v) => v === null || typeof v === "string",
      ) ||
      typeof row.status !== "string"
    )
      return invalid();
  const s = data.state_comparison;
  if (
    !["complete", "unavailable", "not_requested"].includes(String(s.status)) ||
    s.frame !== requestedFrame ||
    (requestedAt
      ? !time(s.evaluation_at) ||
        canonicalTime(s.evaluation_at) !== canonicalTime(requestedAt)
      : s.status !== "not_requested")
  )
    return invalid();
  if (s.status === "complete") {
    if (
      !requestedAt ||
      first.catalog_id !== second.catalog_id ||
      !object(s.units) ||
      s.units.position !== "km" ||
      s.units.velocity !== "km/s" ||
      !vector(s.difference_position_km) ||
      !vector(s.difference_velocity_km_s) ||
      !finite(s.separation_km) ||
      s.separation_km < 0 ||
      !finite(s.relative_speed_km_s) ||
      s.relative_speed_km_s < 0
    )
      return invalid();
    parseState(s.first, first, String(s.evaluation_at), requestedFrame);
    parseState(s.second, second, String(s.evaluation_at), requestedFrame);
  }
  if (
    s.errors !== undefined &&
    (!Array.isArray(s.errors) ||
      !s.errors.every(
        (e) =>
          e === null ||
          (object(e) &&
            typeof e.code === "string" &&
            typeof e.message === "string"),
      ))
  )
    return invalid();
  return { ...data, first, second } as unknown as Comparison;
}
async function request(path: string, signal: AbortSignal) {
  const response = await fetch(path, {
    signal: AbortSignal.any([signal, AbortSignal.timeout(10000)]),
    cache: "no-store",
  });
  let data: unknown;
  try {
    data = await response.json();
  } catch {
    throw new Error("Stored-data API returned an unreadable response. Retry.");
  }
  if (!response.ok) {
    const message =
      object(data) &&
      object(data.error) &&
      typeof data.error.message === "string" &&
      data.error.message.length <= 300
        ? data.error.message
        : `Stored-data request failed (${response.status}). Retry.`;
    throw new Error(message);
  }
  return data;
}
export async function getSnapshotPage(
  params: URLSearchParams,
  signal: AbortSignal,
) {
  return parsePage(await request(`/api/snapshots?${params}`, signal));
}
export async function getComparison(
  first: number,
  second: number,
  at: string,
  frame: string,
  category: Category,
  signal: AbortSignal,
) {
  const params = new URLSearchParams({
    first_id: String(first),
    second_id: String(second),
    frame,
    category,
  });
  if (at) params.set("at", at);
  return parseComparison(
    await request(`/api/comparisons?${params}`, signal),
    first,
    second,
    at,
    frame,
  );
}
export async function getDetail(source: StoredSnapshot, signal: AbortSignal) {
  const data = await request(`/api/snapshots/${source.id}`, signal);
  if (
    !object(data) ||
    data.id !== source.id ||
    data.catalog_id !== source.catalog_id ||
    data.response_sha256 !== source.response_sha256 ||
    !object(data.normalized_record) ||
    !object(data.element_units)
  )
    return invalid();
  const values = data.normalized_record,
    units = data.element_units;
  for (const [field, unit] of Object.entries(elementUnits))
    if (!finite(values[field]) || units[field] !== unit) return invalid();
  return {
    values: values as Record<string, number | string>,
    units: units as Record<string, string>,
  };
}
export function comparisonMarkers(data: Comparison): ComparisonMarker[] {
  const s = data.state_comparison;
  if (s.status !== "complete" || s.frame !== "ITRS" || !s.first || !s.second)
    return [];
  const markers: ComparisonMarker[] = [s.first, s.second].map((p, i) => ({
    at: p.at,
    frame: "ITRS",
    position_km: p.position_km,
    ground_position_km: p.ground_position_km,
    snapshot_id: i === 0 ? data.first.id : data.second.id,
  }));
  return markers.every(canRenderPoint) ? markers : [];
}
