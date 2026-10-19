import { afterEach, expect, it, vi } from "vitest";
import {
  comparisonMarkers,
  explorerSource,
  getComparison,
  getDetail,
  getSnapshotPage,
  parseComparison,
  parsePage,
  parseStored,
} from "./investigation-api";
import { investigationFixtures } from "./test-fixtures/investigations";
afterEach(() => vi.unstubAllGlobals());
it("accepts bounded pages and retains per-source context and stale freshness", () => {
  const raw = investigationFixtures();
  const page = parsePage(raw.page);
  expect(page.total_count).toBe(3);
  expect(page.snapshots[0].membership).toBe("historical_only");
  expect(page.snapshots[1].membership).toBe(
    "historical_record_also_in_selected",
  );
  expect(page.snapshots[2].freshness_info.state).toBe("stale");
});
it("keeps unknown metadata explicit and refuses unreliable explorer sources", () => {
  const s = investigationFixtures().page.snapshots[0];
  const missing = parseStored({
    ...s,
    catalog_id: null,
    identity_consistent: false,
    object_name: null,
    retrieved_at: null,
    source_url: null,
    metadata_issues: ["Identifier missing"],
  });
  expect(missing.catalog_id).toBeNull();
  expect(explorerSource(missing)).toBeNull();
});
it.each([
  { has_more: true, next_before_id: null },
  { scanned_count: 251 },
  { total_count: -1 },
  { order: "retrieved_at" },
  { anchor_id: 1 },
  { snapshots: [] },
])("rejects invalid page contract %o", (mutation) => {
  expect(() =>
    parsePage({ ...investigationFixtures().page, ...mutation }),
  ).toThrow(/Unexpected/);
});
it("rejects duplicate and unordered records", () => {
  const p = investigationFixtures().page;
  expect(() =>
    parsePage({
      ...p,
      snapshots: [p.snapshots[0], p.snapshots[0], p.snapshots[2]],
    }),
  ).toThrow();
});
it.each([
  "javascript:alert(1)",
  "https://user:secret@celestrak.org/NORAD/elements/gp.php",
  "https://example.test/data",
])("rejects unsafe source links %s", (source_url) => {
  expect(() =>
    parseStored({ ...investigationFixtures().page.snapshots[0], source_url }),
  ).toThrow();
});
it.each(["teme", "itrs"] as const)(
  "validates %s common-time states against exact sources",
  (key) => {
    const data = investigationFixtures()[key];
    const result = parseComparison(
      data,
      1,
      2,
      data.state_comparison.evaluation_at,
      key.toUpperCase(),
    );
    expect(result.state_comparison.status).toBe("complete");
    expect(comparisonMarkers(result)).toHaveLength(key === "itrs" ? 2 : 0);
  },
);
it.each([
  "identity",
  "frame",
  "units",
  "time",
  "submillisecond",
  "nan",
  "checksum",
])("rejects mismatched state %s", (key) => {
  const d = investigationFixtures().itrs;
  const state = d.state_comparison;
  let input: unknown = d;
  if (key === "identity") state.second.teme.snapshot_id = 999;
  if (key === "frame") state.second.frame = "TEME";
  if (key === "units") state.second.units.position = "m";
  if (key === "time") state.second.at = "2000-01-01T00:00:00Z";
  if (key === "submillisecond")
    input = {
      ...d,
      state_comparison: {
        ...state,
        evaluation_at: state.evaluation_at.replace("980096", "980097"),
      },
    };
  if (key === "nan") state.second.position_km[0] = NaN;
  if (key === "checksum") state.second.teme.response_sha256 = "a".repeat(64);
  expect(() =>
    parseComparison(input, 1, 2, state.evaluation_at, "ITRS"),
  ).toThrow(/Unexpected/);
});
it("does not turn a missing element unit into a numerical comparison", () => {
  const d = investigationFixtures().noState;
  d.element_differences[0].unit = "unknown";
  expect(() => parseComparison(d, 1, 2, "", "TEME")).toThrow();
});
it("rejects a comparison for other selected snapshot IDs", () => {
  expect(() =>
    parseComparison(investigationFixtures().noState, 2, 1, "", "TEME"),
  ).toThrow();
});
it("passes exact query, selection, timezone and no-store to backend", async () => {
  const f = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => investigationFixtures().page,
  });
  vi.stubGlobal("fetch", f);
  const p = new URLSearchParams({
    q: "REFERENCE",
    context_snapshot_id: "1",
    match: "partial",
    before_id: "20",
    anchor_id: "30",
  });
  await getSnapshotPage(p, new AbortController().signal);
  const [url, options] = f.mock.calls[0];
  expect(url).toContain("context_snapshot_id=1");
  expect(options.cache).toBe("no-store");
  f.mockResolvedValue({
    ok: true,
    json: async () => investigationFixtures().teme,
  });
  const at = investigationFixtures().teme.state_comparison.evaluation_at;
  await getComparison(1, 2, at, "TEME", "all", new AbortController().signal);
  expect(
    new URL(f.mock.calls[1][0], "https://example.test").searchParams.get("at"),
  ).toBe(at);
});
it("checks strict detail identity and element units", async () => {
  const f = investigationFixtures();
  const source = parseStored(f.page.snapshots[2]);
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: true, json: async () => f.detail }),
  );
  expect(
    (await getDetail(source, new AbortController().signal)).units.INCLINATION,
  ).toBe("deg");
  f.detail.element_units.INCLINATION = "rad";
  await expect(getDetail(source, new AbortController().signal)).rejects.toThrow(
    /Unexpected/,
  );
});
it("returns safe structured API errors", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({
        error: { code: "snapshot_not_found", message: "Snapshot not found" },
      }),
    }),
  );
  await expect(
    getSnapshotPage(new URLSearchParams(), new AbortController().signal),
  ).rejects.toThrow("Snapshot not found");
});
it("propagates cancellation", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockImplementation(
        (_url, o) =>
          new Promise((_resolve, reject) =>
            o.signal.addEventListener("abort", () => reject(o.signal.reason)),
          ),
      ),
  );
  const c = new AbortController();
  const request = getSnapshotPage(new URLSearchParams(), c.signal);
  c.abort();
  await expect(request).rejects.toMatchObject({ name: "AbortError" });
});
it("retains numerical results when states exceed the existing globe extent", () => {
  const raw = investigationFixtures().itrs;
  raw.state_comparison.first.position_km = [400 * 6378.137, 0, 0];
  const parsed = parseComparison(
    raw,
    1,
    2,
    raw.state_comparison.evaluation_at,
    "ITRS",
  );
  expect(parsed.state_comparison.status).toBe("complete");
  expect(comparisonMarkers(parsed)).toEqual([]);
});
it("does not expose raw invalid-response exception details", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => {
        throw new Error("/private/server/path");
      },
    }),
  );
  await expect(
    getSnapshotPage(new URLSearchParams(), new AbortController().signal),
  ).rejects.toThrow("Stored-data API returned an unreadable response. Retry.");
});

it("preserves separate insertion time through exact-source handoff", () => {
  const raw = investigationFixtures().page.snapshots[0];
  const source = parseStored({
    ...raw,
    snapshot_created_at: "2026-10-19T07:58:23.415+00:00",
  });
  expect(explorerSource(source)?.snapshot_created_at).toBe(
    "2026-10-19T07:58:23.415+00:00",
  );
  expect(() =>
    parseStored({ ...raw, snapshot_created_at: "unknown" }),
  ).toThrow();
});
