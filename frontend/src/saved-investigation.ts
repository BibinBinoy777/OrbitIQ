import { formatUtc } from "./time-presentation";
import type { SnapshotSummary } from "./scientific-api";
import type { Category } from "./investigation-api";

export const LIMITS = { url: 2048, state: 4096, title: 120, description: 1000 };
export interface SourceReference {
  snapshot_id: number;
  catalog_id: number;
  orbital_epoch: string;
  retrieved_at: string;
  response_sha256: string;
}
export interface TrackView {
  start: string;
  duration_minutes: number;
  step_seconds: number;
  selected_index: number;
}
interface Base {
  schema_version: 1;
  source: SourceReference;
}
export type Investigation = Base &
  (
    | { mode: "snapshot"; frame: "TEME" }
    | { mode: "position"; frame: "TEME"; at: string }
    | { mode: "ground-track"; frame: "ITRS"; at: string; track: TrackView }
    | {
        mode: "comparison";
        frame: "TEME" | "ITRS";
        at: string | null;
        comparison_source: SourceReference;
        category: Category;
      }
  );
const categories = ["all", "shared", "added", "removed", "incompatible"];
export function object(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}
export function bytes(v: string): number {
  return new TextEncoder().encode(v).length;
}
function invalid(
  message = "Investigation parameters are invalid or incomplete.",
): never {
  throw new Error(message);
}
export function keys(v: Record<string, unknown>, expected: string[]): void {
  if (
    Object.keys(v).length !== expected.length ||
    expected.some((k) => !Object.hasOwn(v, k))
  )
    invalid();
}
export function positiveId(v: unknown, max = Number.MAX_SAFE_INTEGER): number {
  if (typeof v !== "number" || !Number.isSafeInteger(v) || v < 1 || v > max)
    invalid("Use supported positive satellite and snapshot identifiers.");
  return v;
}
export function canonicalTime(v: unknown): string {
  if (typeof v !== "string" || v.length > 40)
    invalid(
      "Use a valid ISO timestamp with an explicit timezone and at most six fractional digits.",
    );
  const formatted = formatUtc(v).replace(" (UTC)", "");
  if (!/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3,6}Z$/.test(formatted))
    invalid(
      "Use a valid ISO timestamp with an explicit timezone and at most six fractional digits.",
    );
  return formatted.replace(
    /\.(\d+)Z$/,
    (_, fraction: string) => `.${fraction.padEnd(6, "0")}Z`,
  );
}
export function shiftTime(value: string, seconds: number): string {
  const start = canonicalTime(value);
  const fraction = /\.(\d{6})Z$/.exec(start)![1];
  return canonicalTime(
    new Date(Date.parse(start) + seconds * 1000)
      .toISOString()
      .replace(/\.\d{3}Z$/, `.${fraction}Z`),
  );
}
function source(v: unknown): SourceReference {
  if (!object(v)) return invalid();
  keys(v, [
    "snapshot_id",
    "catalog_id",
    "orbital_epoch",
    "retrieved_at",
    "response_sha256",
  ]);
  if (
    typeof v.response_sha256 !== "string" ||
    !/^[a-f0-9]{64}$/.test(v.response_sha256)
  )
    return invalid(
      "Source provenance is incomplete; a verified snapshot hash is required.",
    );
  return {
    snapshot_id: positiveId(v.snapshot_id),
    catalog_id: positiveId(v.catalog_id, 339999),
    orbital_epoch: canonicalTime(v.orbital_epoch),
    retrieved_at: canonicalTime(v.retrieved_at),
    response_sha256: v.response_sha256,
  };
}
export function sourceReference(s: SnapshotSummary): SourceReference {
  if (s.frame !== "TEME")
    return invalid(
      "A supported TEME source and complete provenance are required to save this view.",
    );
  return source({
    snapshot_id: s.id,
    catalog_id: s.catalog_id,
    orbital_epoch: s.orbital_epoch,
    retrieved_at: s.retrieved_at,
    response_sha256: s.response_sha256,
  });
}
export function verifySource(
  expected: SourceReference,
  s: SnapshotSummary,
): void {
  if (JSON.stringify(sourceReference(s)) !== JSON.stringify(source(expected)))
    invalid(
      `Snapshot #${expected.snapshot_id} does not match the saved satellite or provenance. This link may belong to another archive. No newer source was substituted.`,
    );
}
export function parseInvestigation(v: unknown): Investigation {
  if (!object(v) || bytes(JSON.stringify(v)) > LIMITS.state)
    return invalid("Investigation state is invalid or too large.");
  if (v.schema_version !== 1)
    return invalid(
      "Unsupported investigation schema version. No saved data were changed.",
    );
  const base = { schema_version: 1 as const, source: source(v.source) };
  const required = ["schema_version", "source", "mode", "frame"];
  if (v.mode === "snapshot") {
    keys(v, required);
    if (v.frame !== "TEME")
      return invalid("Unsupported snapshot coordinate frame.");
    return { ...base, mode: v.mode, frame: v.frame };
  }
  if (v.mode === "position") {
    keys(v, [...required, "at"]);
    if (v.frame !== "TEME") return invalid("Position inspection uses TEME.");
    return { ...base, mode: v.mode, frame: v.frame, at: canonicalTime(v.at) };
  }
  if (v.mode === "ground-track") {
    keys(v, [...required, "at", "track"]);
    if (v.frame !== "ITRS" || !object(v.track))
      return invalid(
        "Ground tracks require ITRS and explicit sampling parameters.",
      );
    keys(v.track, [
      "start",
      "duration_minutes",
      "step_seconds",
      "selected_index",
    ]);
    const {
      duration_minutes: duration,
      step_seconds: step,
      selected_index: index,
    } = v.track;
    if (
      typeof duration !== "number" ||
      !Number.isInteger(duration) ||
      duration < 1 ||
      duration > 1440 ||
      typeof step !== "number" ||
      !Number.isInteger(step) ||
      step < 10 ||
      step > 3600 ||
      typeof index !== "number" ||
      !Number.isInteger(index) ||
      index < 0
    )
      return invalid(
        "Use duration 1–1440 minutes, step 10–3600 seconds and a valid selected sample.",
      );
    const count = Math.floor((duration * 60) / step) + 1;
    if (count > 361 || index >= count)
      return invalid(
        "Saved tracks support at most 361 samples; the selected sample must be in range.",
      );
    const start = canonicalTime(v.track.start),
      at = canonicalTime(v.at);
    if (at !== shiftTime(start, index * step))
      return invalid(
        "Selected track time does not match its sampling parameters.",
      );
    return {
      ...base,
      mode: v.mode,
      frame: v.frame,
      at,
      track: {
        start,
        duration_minutes: duration,
        step_seconds: step,
        selected_index: index,
      },
    };
  }
  if (v.mode === "comparison") {
    keys(v, [...required, "at", "comparison_source", "category"]);
    if (
      (v.frame !== "TEME" && v.frame !== "ITRS") ||
      typeof v.category !== "string" ||
      !categories.includes(v.category)
    )
      return invalid("Unsupported comparison frame or filter.");
    return {
      ...base,
      mode: v.mode,
      frame: v.frame,
      at: v.at === null ? null : canonicalTime(v.at),
      comparison_source: source(v.comparison_source),
      category: v.category as Category,
    };
  }
  return invalid("Unsupported investigation mode.");
}
export function snapshotInvestigation(s: SnapshotSummary): Investigation {
  return parseInvestigation({
    schema_version: 1,
    mode: "snapshot",
    source: sourceReference(s),
    frame: "TEME",
  });
}
export function titleFor(v: Investigation): string {
  return `NORAD ${v.source.catalog_id} · ${v.mode} · #${v.source.snapshot_id}${v.mode === "comparison" ? ` / #${v.comparison_source.snapshot_id}` : ""}`;
}
export function shareLink(value: Investigation, base: string): string {
  const v = parseInvestigation(value),
    url = new URL(base);
  if (
    !["https:", "http:"].includes(url.protocol) ||
    url.username ||
    url.password
  )
    return invalid("A valid application origin is required.");
  const params = new URLSearchParams({ v: "1", mode: v.mode, frame: v.frame });
  const put = (s: SourceReference, prefix = "") => {
    for (const [key, val] of Object.entries({
      catalog: s.catalog_id,
      snapshot: s.snapshot_id,
      epoch: s.orbital_epoch,
      retrieved: s.retrieved_at,
      sha: s.response_sha256,
    }))
      params.set(prefix + key, String(val));
  };
  put(v.source);
  if ("at" in v && v.at) params.set("at", v.at);
  if (v.mode === "comparison") {
    put(v.comparison_source, "b_");
    params.set("category", v.category);
  }
  if (v.mode === "ground-track")
    for (const [key, val] of Object.entries(v.track))
      params.set(key, String(val));
  url.search = "";
  url.hash = `/investigation?${params}`;
  if (url.href.length > LIMITS.url)
    return invalid("The share link exceeds the supported URL length.");
  return url.href;
}
export function parseShareLink(href: string): Investigation | null {
  if (href.length > LIMITS.url)
    return invalid("Investigation URL is too long (maximum 2048 characters).");
  const url = new URL(href);
  if (
    !["http:", "https:"].includes(url.protocol) ||
    url.username ||
    url.password
  )
    return invalid("Unsupported investigation URL origin.");
  if (!url.hash) return null;
  if (!url.hash.startsWith("#/investigation?"))
    return invalid("Unrecognized investigation link. No source was selected.");
  const params = new URLSearchParams(url.hash.slice("#/investigation?".length));
  const allowed = [
    "v",
    "mode",
    "frame",
    "catalog",
    "snapshot",
    "epoch",
    "retrieved",
    "sha",
    "at",
    "b_catalog",
    "b_snapshot",
    "b_epoch",
    "b_retrieved",
    "b_sha",
    "category",
    "start",
    "duration_minutes",
    "step_seconds",
    "selected_index",
  ];
  if ([...params].length > allowed.length)
    return invalid("Too many investigation URL parameters.");
  for (const key of params.keys())
    if (!allowed.includes(key) || params.getAll(key).length !== 1)
      return invalid("Unknown or duplicated investigation URL parameter.");
  if (params.get("v") !== "1")
    return invalid("Unsupported investigation link version.");
  const get = (key: string) => params.get(key);
  const number = (key: string) => {
    const value = get(key);
    if (value === null || !/^\d{1,16}$/.test(value))
      return invalid("Invalid or missing numeric investigation URL parameter.");
    return Number(value);
  };
  const read = (prefix = "") => ({
    catalog_id: number(prefix + "catalog"),
    snapshot_id: number(prefix + "snapshot"),
    orbital_epoch: get(prefix + "epoch"),
    retrieved_at: get(prefix + "retrieved"),
    response_sha256: get(prefix + "sha"),
  });
  const value: Record<string, unknown> = {
    schema_version: 1,
    mode: get("mode"),
    frame: get("frame"),
    source: read(),
  };
  const mode = value.mode;
  if (mode !== "snapshot") value.at = get("at");
  if (mode === "comparison") {
    value.comparison_source = read("b_");
    value.category = get("category");
  }
  if (mode === "ground-track")
    value.track = {
      start: get("start"),
      duration_minutes: number("duration_minutes"),
      step_seconds: number("step_seconds"),
      selected_index: number("selected_index"),
    };
  const result = parseInvestigation(value);
  // Reject irrelevant-but-known parameters rather than silently ignoring state.
  const canonical = new URL(shareLink(result, url.origin + url.pathname)).hash;
  const expected = new URLSearchParams(
    canonical.slice("#/investigation?".length),
  );
  if (
    [...params.keys()].some((k) => !expected.has(k)) ||
    [...expected.keys()].some((k) => !params.has(k))
  )
    return invalid(
      "URL parameters do not match the selected investigation mode.",
    );
  return result;
}
