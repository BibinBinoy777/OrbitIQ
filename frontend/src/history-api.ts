import { object, parseStored } from "./investigation-api";
import type { StoredSnapshot } from "./investigation-api";
import type { Investigation } from "./saved-investigation";
import { canonicalTime } from "./saved-investigation";
interface HistoricalReference {
  snapshot_id: number;
  catalog_id: number | null;
  orbital_epoch: string | null;
  retrieved_at: string | null;
  response_sha256: string | null;
}
export interface HistoryPoint {
  metadata: StoredSnapshot;
  reference: HistoricalReference;
  usable: boolean;
  elements: Record<string, string | number> | null;
  element_units: Record<string, string>;
  freshness: { state: string };
}
export interface HistoryPair {
  id: string;
  first: HistoricalReference;
  second: HistoricalReference;
  chronology_status: string;
  status: string;
  retrieval_interval_seconds: number | null;
  differences: {
    field: string;
    unit: string;
    first_value: number;
    second_value: number;
    difference: number;
    convention: string;
  }[];
  evidence: {
    status: string;
    definition: Extract<Investigation, { mode: "comparison" }> | null;
    scope: string;
  };
}
export interface HistoryFinding {
  finding_id: string;
  rule_id: string;
  rule_version: number;
  category: string;
  title: string;
  explanation: string;
  sources: HistoricalReference[];
  inputs: Record<string, unknown>;
  result: unknown;
  reproduction_status: string;
}
export interface HistoricalReport {
  kind: "orbitiq_historical_analysis";
  schema_version: 1;
  rule_set_version: 1;
  report_id: string;
  generated_at: string;
  catalog_id: number;
  pagination: {
    anchor_id: number | null;
    has_more: boolean;
    next_before_id: number | null;
    page_size: number;
    total_count: number | null;
    total_count_status: string;
  };
  coverage: {
    inspected_count: number;
    validated_record_count: number;
    complete_anchored_history: boolean;
    oldest_verifiable_retrieval: string | null;
    newest_verifiable_retrieval: string | null;
    retrieval_span_seconds: number | null;
    chronology: string;
    summary: string;
    trend_statistic: null;
    interpolation: false;
    extrapolation: false;
  };
  points: HistoryPoint[];
  comparisons: HistoryPair[];
  findings: HistoryFinding[];
  limitations: string[];
}
const id = (v: unknown): v is number =>
  typeof v === "number" && Number.isSafeInteger(v) && v > 0;
const finite = (v: unknown): v is number =>
  typeof v === "number" && Number.isFinite(v);
const strings = (v: unknown): v is string[] =>
  Array.isArray(v) && v.every((x) => typeof x === "string" && x.length <= 2000);
function time(v: unknown): boolean {
  if (v === null) return true;
  try {
    canonicalTime(v);
    return true;
  } catch {
    return false;
  }
}
function invalid(): never {
  throw new Error(
    "Unexpected historical analysis response; source identity or bounded contract is invalid.",
  );
}
const units: Record<string, string> = {
  INCLINATION: "deg",
  ECCENTRICITY: "dimensionless",
  MEAN_MOTION: "rev/day",
};
export function parseHistory(v: unknown): HistoricalReport {
  if (
    !object(v) ||
    v.kind !== "orbitiq_historical_analysis" ||
    v.schema_version !== 1 ||
    v.rule_set_version !== 1 ||
    !id(v.catalog_id) ||
    v.catalog_id > 339999 ||
    typeof v.report_id !== "string" ||
    !/^history-report-sha256:[a-f0-9]{64}$/.test(v.report_id) ||
    !time(v.generated_at) ||
    v.generated_at === null ||
    !strings(v.limitations) ||
    !object(v.pagination) ||
    !object(v.coverage) ||
    !Array.isArray(v.points) ||
    v.points.length > 20 ||
    !Array.isArray(v.comparisons) ||
    v.comparisons.length > 19 ||
    !Array.isArray(v.findings) ||
    v.findings.length > 200
  )
    invalid();
  const p = v.pagination,
    c = v.coverage;
  if (
    !(p.anchor_id === null || id(p.anchor_id)) ||
    typeof p.has_more !== "boolean" ||
    !(p.next_before_id === null || id(p.next_before_id)) ||
    (p.has_more && !id(p.next_before_id)) ||
    (!p.has_more && p.next_before_id !== null) ||
    !id(p.page_size) ||
    p.page_size > 20 ||
    v.points.length > p.page_size ||
    !(
      p.total_count === null ||
      (Number.isSafeInteger(p.total_count) && Number(p.total_count) >= 0)
    ) ||
    typeof p.total_count_status !== "string" ||
    c.inspected_count !== v.points.length ||
    !Number.isInteger(c.validated_record_count) ||
    Number(c.validated_record_count) < 0 ||
    Number(c.validated_record_count) > v.points.length ||
    typeof c.complete_anchored_history !== "boolean" ||
    (c.complete_anchored_history && p.has_more) ||
    !time(c.oldest_verifiable_retrieval) ||
    !time(c.newest_verifiable_retrieval) ||
    !(
      c.retrieval_span_seconds === null ||
      (finite(c.retrieval_span_seconds) && c.retrieval_span_seconds >= 0)
    ) ||
    typeof c.chronology !== "string" ||
    typeof c.summary !== "string" ||
    c.trend_statistic !== null ||
    c.interpolation !== false ||
    c.extrapolation !== false
  )
    invalid();
  const sources = new Map<number, StoredSnapshot>();
  function checkRef(r: unknown, strict = false) {
    if (!object(r) || !id(r.snapshot_id)) invalid();
    const s = sources.get(r.snapshot_id);
    if (
      !s ||
      r.catalog_id !== s.catalog_id ||
      r.response_sha256 !== s.response_sha256 ||
      !time(r.orbital_epoch) ||
      !time(r.retrieved_at)
    )
      invalid();
    for (const key of ["orbital_epoch", "retrieved_at"] as const)
      if (
        (r[key] === null) !== (s[key] === null) ||
        (r[key] !== null && canonicalTime(r[key]) !== canonicalTime(s[key]))
      )
        invalid();
    if (
      strict &&
      (r.orbital_epoch === null ||
        r.retrieved_at === null ||
        !s.response_sha256)
    )
      invalid();
  }
  for (const point of v.points) {
    if (
      !object(point) ||
      typeof point.usable !== "boolean" ||
      !object(point.freshness) ||
      typeof point.freshness.state !== "string" ||
      !object(point.element_units)
    )
      invalid();
    const s = parseStored(point.metadata);
    if (sources.has(s.id) || s.catalog_id !== v.catalog_id) invalid();
    sources.set(s.id, s);
    checkRef(point.reference, point.usable);
    if (point.usable) {
      if (
        !object(point.elements) ||
        point.elements.NORAD_CAT_ID !== v.catalog_id
      )
        invalid();
      for (const [f, u] of Object.entries(units))
        if (!finite(point.elements[f]) || point.element_units[f] !== u)
          invalid();
    } else if (point.elements !== null) invalid();
  }
  if (
    v.points.filter((x) => object(x) && x.usable).length !==
    c.validated_record_count
  )
    invalid();
  const pairIds = new Set<string>();
  for (const pair of v.comparisons) {
    if (
      !object(pair) ||
      typeof pair.id !== "string" ||
      pairIds.has(pair.id) ||
      typeof pair.chronology_status !== "string" ||
      !["complete", "unavailable"].includes(String(pair.status)) ||
      !Array.isArray(pair.differences) ||
      pair.differences.length > 3 ||
      !object(pair.evidence) ||
      typeof pair.evidence.status !== "string" ||
      typeof pair.evidence.scope !== "string" ||
      !(
        pair.retrieval_interval_seconds === null ||
        (finite(pair.retrieval_interval_seconds) &&
          pair.retrieval_interval_seconds >= 0)
      )
    )
      invalid();
    pairIds.add(pair.id);
    checkRef(pair.first);
    checkRef(pair.second);
    if (
      pair.status === "complete" &&
      (pair.differences.length !== 3 || pair.chronology_status !== "ordered")
    )
      invalid();
    if (pair.status === "unavailable" && pair.differences.length) invalid();
    const fields = new Set();
    for (const d of pair.differences) {
      if (
        !object(d) ||
        typeof d.field !== "string" ||
        !Object.hasOwn(units, d.field) ||
        fields.has(d.field) ||
        d.unit !== units[d.field] ||
        !finite(d.first_value) ||
        !finite(d.second_value) ||
        !finite(d.difference) ||
        d.difference !== d.second_value - d.first_value ||
        d.convention !== "second_minus_first"
      )
        invalid();
      fields.add(d.field);
    }
    if (pair.evidence.definition !== null) {
      const d = pair.evidence.definition;
      if (
        !object(d) ||
        d.schema_version !== 1 ||
        d.mode !== "comparison" ||
        d.frame !== "TEME" ||
        !time(d.at) ||
        d.category !== "all"
      )
        invalid();
      checkRef(d.source, true);
      checkRef(d.comparison_source, true);
      if (
        !object(pair.first) ||
        !object(pair.second) ||
        !object(d.source) ||
        !object(d.comparison_source) ||
        d.source.snapshot_id !== pair.first.snapshot_id ||
        d.comparison_source.snapshot_id !== pair.second.snapshot_id
      )
        invalid();
    }
  }
  const findingIds = new Set<string>();
  for (const f of v.findings) {
    if (
      !object(f) ||
      typeof f.finding_id !== "string" ||
      !/^history-finding-sha256:[a-f0-9]{64}$/.test(f.finding_id) ||
      findingIds.has(f.finding_id) ||
      typeof f.rule_id !== "string" ||
      !f.rule_id.startsWith("history.") ||
      f.rule_version !== 1 ||
      ![
        "informational",
        "incomplete_data",
        "stale_source_data",
        "comparison_unavailable",
        "validation_failure",
      ].includes(String(f.category)) ||
      typeof f.title !== "string" ||
      typeof f.explanation !== "string" ||
      !Array.isArray(f.sources) ||
      !object(f.inputs) ||
      typeof f.reproduction_status !== "string"
    )
      invalid();
    findingIds.add(f.finding_id);
    f.sources.forEach((s) => checkRef(s));
  }
  return v as unknown as HistoricalReport;
}
export async function getHistory(
  catalog: number,
  params: URLSearchParams,
  signal: AbortSignal,
): Promise<HistoricalReport> {
  const query = new URLSearchParams(params);
  query.set("catalog_id", String(catalog));
  const r = await fetch(`/api/historical-analysis?${query}`, {
    signal: AbortSignal.any([signal, AbortSignal.timeout(30000)]),
    cache: "no-store",
  });
  if (!r.ok)
    throw new Error(
      `Historical analysis unavailable (${r.status}). Retry or inspect the archive configuration.`,
    );
  if (Number(r.headers.get("content-length")) > 4 * 1024 * 1024) invalid();
  const text = await r.text();
  if (text.length > 4 * 1024 * 1024) invalid();
  const value = parseHistory(JSON.parse(text));
  if (value.catalog_id !== catalog) invalid();
  return value;
}
