import type { Investigation, SourceReference } from "./saved-investigation";
import { canonicalTime, parseInvestigation } from "./saved-investigation";

export type ReportValue =
  | string
  | number
  | boolean
  | null
  | ReportValue[]
  | { [key: string]: ReportValue };
export type ReportObject = { [key: string]: ReportValue };
export interface ReportSource extends ReportObject {
  role: string;
  reference: SourceReference & ReportObject;
  source_type: string;
  object_name: string;
  source_url: string;
  source_frame: string;
  payload_hash: {
    algorithm: string;
    value: string;
    scope: string;
  } & ReportObject;
  elements: ReportObject;
  element_units: ReportObject;
}
export interface InvestigationReport {
  schema_version: 1;
  template_version: 1;
  kind: "orbitiq_investigation_report";
  report_id: string;
  generated_at: string;
  status: "complete" | "partial";
  investigation: {
    id: string;
    id_kind: "configuration_sha256";
    title: string;
    title_origin: "generated_from_verified_sources";
    definition: Investigation;
    saved_record_id: null;
    saved_title: null;
    description: null;
    created_at: null;
    saved_metadata_status: "browser_only_excluded";
  };
  sources: ReportSource[];
  calculation: {
    status: "complete" | "unavailable" | "not_requested";
    data: ReportObject | null;
    errors: { code: string; message: string }[];
  };
  validation: ReportObject;
  methodology: ReportObject;
  limitations: string[];
  warnings: string[];
}
export const MAX_REPORT_BYTES = 8 * 1024 * 1024;
export function reportObject(v: unknown): v is ReportObject {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}
function invalid(): never {
  throw new Error(
    "Report data are incomplete, unsupported or do not match this investigation. No export was generated.",
  );
}
const strings = (v: unknown): v is string[] =>
  Array.isArray(v) && v.every((s) => typeof s === "string" && s.length <= 4000);
function reference(v: unknown): SourceReference {
  return parseInvestigation({
    schema_version: 1,
    mode: "snapshot",
    frame: "TEME",
    source: v,
  }).source;
}
function matches(a: SourceReference, b: unknown): boolean {
  return JSON.stringify(reference(a)) === JSON.stringify(reference(b));
}
export function parseReport(
  data: unknown,
  expected: Investigation,
): InvestigationReport {
  if (
    !reportObject(data) ||
    data.schema_version !== 1 ||
    data.template_version !== 1 ||
    data.kind !== "orbitiq_investigation_report"
  )
    return invalid();
  if (
    typeof data.report_id !== "string" ||
    !/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(
      data.report_id,
    )
  )
    return invalid();
  canonicalTime(data.generated_at);
  const i = data.investigation;
  if (
    !reportObject(i) ||
    typeof i.id !== "string" ||
    !/^configuration-sha256:[a-f0-9]{64}$/.test(i.id) ||
    i.id_kind !== "configuration_sha256" ||
    typeof i.title !== "string" ||
    i.title.length > 300 ||
    i.title_origin !== "generated_from_verified_sources" ||
    i.saved_record_id !== null ||
    i.saved_title !== null ||
    i.description !== null ||
    i.created_at !== null ||
    i.saved_metadata_status !== "browser_only_excluded"
  )
    return invalid();
  const definition = parseInvestigation(i.definition);
  if (
    JSON.stringify(definition) !== JSON.stringify(parseInvestigation(expected))
  )
    return invalid();
  const refs =
    definition.mode === "comparison"
      ? [definition.source, definition.comparison_source]
      : [definition.source];
  if (!Array.isArray(data.sources) || data.sources.length !== refs.length)
    return invalid();
  data.sources.forEach((s, index) => {
    if (
      !reportObject(s) ||
      !matches(refs[index], s.reference) ||
      s.role !== (index === 0 ? "primary" : "comparison") ||
      s.source_frame !== "TEME" ||
      s.epoch_time_system !== "UTC" ||
      typeof s.object_name !== "string" ||
      typeof s.source_url !== "string" ||
      !reportObject(s.payload_hash) ||
      s.payload_hash.algorithm !== "SHA-256" ||
      s.payload_hash.value !== refs[index].response_sha256 ||
      s.payload_hash.integrity_status !== "verified_against_stored_bytes" ||
      typeof s.payload_hash.scope !== "string" ||
      !reportObject(s.elements) ||
      !reportObject(s.element_units) ||
      !Array.isArray(s.checks_performed_for_report) ||
      s.source_authenticity !== "not_independently_verified"
    )
      return invalid();
    let url: URL;
    try {
      url = new URL(s.source_url);
    } catch {
      return invalid();
    }
    if (
      url.protocol !== "https:" ||
      !["celestrak.org", "www.celestrak.org"].includes(url.hostname) ||
      url.username ||
      url.password ||
      url.hash ||
      (url.port && url.port !== "443") ||
      url.pathname !== "/NORAD/elements/gp.php" ||
      url.searchParams.get("CATNR") !== String(refs[index].catalog_id) ||
      url.searchParams.get("FORMAT") !== "JSON" ||
      [...url.searchParams].length !== 2
    )
      return invalid();
  });
  const c = data.calculation;
  if (
    !reportObject(c) ||
    !["complete", "unavailable", "not_requested"].includes(String(c.status)) ||
    !(c.data === null || reportObject(c.data)) ||
    !Array.isArray(c.errors) ||
    !c.errors.every(
      (e) =>
        reportObject(e) &&
        typeof e.code === "string" &&
        typeof e.message === "string",
    )
  )
    return invalid();
  if (
    data.status !== (c.status === "unavailable" ? "partial" : "complete") ||
    (c.status === "unavailable" && !c.errors.length) ||
    (c.status === "complete" && !reportObject(c.data))
  )
    return invalid();
  if (
    c.status === "not_requested" &&
    !(
      definition.mode === "snapshot" ||
      (definition.mode === "comparison" && definition.at === null)
    )
  )
    return invalid();
  if (
    !reportObject(data.validation) ||
    data.validation.status !== "validated_with_warnings" ||
    data.validation.independent_observation_validation !== "blocked" ||
    data.validation.prediction_uncertainty !== "unquantified" ||
    data.validation.report_generation_is_scientific_certification !== false ||
    !reportObject(data.methodology) ||
    data.methodology.time_system !== "UTC" ||
    !strings(data.limitations) ||
    !data.limitations.length ||
    !strings(data.warnings)
  )
    return invalid();
  let nodes = 0;
  const visit = (value: unknown, depth = 0) => {
    if (
      ++nodes > 200000 ||
      depth > 32 ||
      (typeof value === "number" && !Number.isFinite(value))
    )
      return invalid();
    if (Array.isArray(value)) {
      if (value.length > 1000) return invalid();
      value.forEach((v) => visit(v, depth + 1));
    } else if (reportObject(value)) {
      if ("snapshot_id" in value && "response_sha256" in value) {
        const ref = refs.find((r) => r.snapshot_id === value.snapshot_id);
        if (
          !ref ||
          !matches(ref, {
            snapshot_id: value.snapshot_id,
            catalog_id: value.catalog_id,
            orbital_epoch: value.orbital_epoch,
            retrieved_at: value.retrieved_at,
            response_sha256: value.response_sha256,
          })
        )
          return invalid();
      }
      for (const key of [
        "position_km",
        "velocity_km_s",
        "ground_position_km",
        "difference_position_km",
        "difference_velocity_km_s",
      ]) {
        if (
          value[key] !== undefined &&
          value[key] !== null &&
          (!Array.isArray(value[key]) ||
            value[key].length !== 3 ||
            !value[key].every(
              (n) => typeof n === "number" && Number.isFinite(n),
            ))
        )
          return invalid();
      }
      if ("position_km" in value) {
        if (
          value.kind !== "calculated" ||
          !["TEME", "ITRS"].includes(String(value.frame)) ||
          value.time_system !== "UTC" ||
          !reportObject(value.units) ||
          value.units.position !== "km" ||
          value.units.velocity !== "km/s"
        )
          return invalid();
        canonicalTime(value.at);
        if (value.frame === "TEME") canonicalTime(value.calculated_at);
        else if (
          !reportObject(value.earth_orientation) ||
          !["measured_only", "measured_or_predicted"].includes(
            String(value.earth_orientation.policy),
          ) ||
          value.earth_orientation.auto_download !== false ||
          value.earth_orientation.degraded_results_allowed !== false ||
          !/^[a-f0-9]{64}$/.test(String(value.earth_orientation.sha256)) ||
          !/^[a-f0-9]{64}$/.test(
            String(value.earth_orientation.leap_seconds_sha256),
          )
        )
          return invalid();
      }
      Object.values(value).forEach((v) => visit(v, depth + 1));
    }
  };
  visit(data);
  if (c.status === "complete" && reportObject(c.data)) {
    if (
      definition.mode === "position" &&
      (c.data.frame !== "TEME" ||
        canonicalTime(c.data.at) !== definition.at ||
        !Array.isArray(c.data.position_km))
    )
      return invalid();
    if (definition.mode === "ground-track") {
      if (
        c.data.status !== "complete" ||
        c.data.failure_policy !== "reject_entire_request" ||
        !Array.isArray(c.data.points) ||
        c.data.points.length !== c.data.sample_count ||
        c.data.step_seconds !== definition.track.step_seconds ||
        canonicalTime(c.data.requested_start) !== definition.track.start
      )
        return invalid();
      const point = c.data.points[definition.track.selected_index];
      if (
        !reportObject(point) ||
        point.sample_index !== definition.track.selected_index ||
        canonicalTime(point.at) !== definition.at
      )
        return invalid();
    }
  }
  return data as unknown as InvestigationReport;
}

export async function getInvestigationReport(
  value: Investigation,
  signal: AbortSignal,
) {
  const definition = parseInvestigation(value);
  const response = await fetch(
    `/api/investigation-reports?${new URLSearchParams({ definition: JSON.stringify(definition) })}`,
    {
      signal: AbortSignal.any([signal, AbortSignal.timeout(25000)]),
      cache: "no-store",
    },
  );
  if (
    !response.body ||
    Number(response.headers.get("Content-Length")) > MAX_REPORT_BYTES
  )
    throw new Error(
      "Report response is unavailable or exceeds the supported size.",
    );
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let text = "",
    size = 0;
  try {
    while (true) {
      const chunk = await reader.read();
      if (chunk.done) break;
      size += chunk.value.byteLength;
      if (size > MAX_REPORT_BYTES) {
        await reader.cancel();
        throw new Error("Report exceeds the supported export size.");
      }
      text += decoder.decode(chunk.value, { stream: true });
    }
    text += decoder.decode();
  } finally {
    reader.releaseLock();
  }
  let data: unknown;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error(
      "The report service returned an unreadable response. Retry generation.",
    );
  }
  if (!response.ok) {
    const message =
      reportObject(data) &&
      reportObject(data.error) &&
      typeof data.error.message === "string" &&
      data.error.message.length <= 300
        ? data.error.message
        : `Report generation failed (${response.status}).`;
    throw new Error(message);
  }
  if (signal.aborted) throw new DOMException("Cancelled", "AbortError");
  return parseReport(data, definition);
}
