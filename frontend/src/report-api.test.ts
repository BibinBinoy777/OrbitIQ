import { afterEach, expect, it, vi } from "vitest";
import {
  getInvestigationReport,
  MAX_REPORT_BYTES,
  parseReport,
} from "./report-api";
import { parseInvestigation } from "./saved-investigation";
import { reportFixture } from "./test-fixtures/reports";
afterEach(() => vi.unstubAllGlobals());

it.each(["snapshot", "position", "ground-track", "comparison"])(
  "accepts the actual backend %s contract",
  (mode) => {
    const r = reportFixture(mode);
    expect(parseReport(r, r.investigation.definition)).toBe(r);
  },
);
it("fetches a fresh canonical definition with no local metadata and a bounded response", async () => {
  const r = reportFixture();
  const fetcher = vi.fn().mockResolvedValue(
    new Response(JSON.stringify(r), {
      headers: { "Content-Type": "application/json" },
    }),
  );
  vi.stubGlobal("fetch", fetcher);
  const result = await getInvestigationReport(
    r.investigation.definition,
    new AbortController().signal,
  );
  expect(result.report_id).toBe(r.report_id);
  const [url, init] = fetcher.mock.calls[0];
  expect(String(url)).toMatch(/^\/api\/investigation-reports\?/);
  expect(init.cache).toBe("no-store");
  const params = new URL(String(url), "http://localhost").searchParams;
  expect(parseInvestigation(JSON.parse(params.get("definition")!))).toEqual(
    parseInvestigation(r.investigation.definition),
  );
  expect(String(url)).not.toContain("description");
});
it.each([
  [
    "schema version",
    (r: ReturnType<typeof reportFixture>) => {
      r.schema_version = 99 as 1;
    },
  ],
  [
    "source hash",
    (r: ReturnType<typeof reportFixture>) => {
      r.sources[0].payload_hash.value = "b".repeat(64);
    },
  ],
  [
    "source identity",
    (r: ReturnType<typeof reportFixture>) => {
      r.sources[0].reference.catalog_id = 123;
    },
  ],
  [
    "unsafe source URL",
    (r: ReturnType<typeof reportFixture>) => {
      r.sources[0].source_url = "https://user:password@celestrak.org/private";
    },
  ],
  [
    "scientific certification",
    (r: ReturnType<typeof reportFixture>) => {
      r.validation.report_generation_is_scientific_certification = true;
    },
  ],
  [
    "nonfinite number",
    (r: ReturnType<typeof reportFixture>) => {
      r.calculation.data!.position_km = [Infinity, 0, 0];
    },
  ],
  [
    "wrong evaluation time",
    (r: ReturnType<typeof reportFixture>) => {
      r.calculation.data!.at = "2020-01-01T00:00:00Z";
    },
  ],
  [
    "wrong units",
    (r: ReturnType<typeof reportFixture>) => {
      r.calculation.data!.units = { position: "m", velocity: "m/s" };
    },
  ],
  [
    "calculation lineage",
    (r: ReturnType<typeof reportFixture>) => {
      r.calculation.data!.response_sha256 = "b".repeat(64);
    },
  ],
])("rejects %s rather than exporting misleading facts", (_, change) => {
  const r = reportFixture(),
    expected = structuredClone(r.investigation.definition);
  change(r);
  expect(() => parseReport(r, expected)).toThrow();
});
it("rejects a response belonging to an older investigation selection", () => {
  const r = reportFixture();
  const different = parseInvestigation({
    ...r.investigation.definition,
    source: { ...r.investigation.definition.source, snapshot_id: 99 },
  });
  expect(() => parseReport(r, different)).toThrow(/match/);
});
it("rejects invalid EOP policy and payload identity in a terrestrial sample", () => {
  const r = reportFixture("ground-track");
  const points = r.calculation.data!.points as Record<string, unknown>[];
  (points[0].earth_orientation as Record<string, unknown>).policy =
    "ignore_errors";
  expect(() => parseReport(r, r.investigation.definition)).toThrow();
});
it("represents an unavailable result explicitly and rejects contradictory success", () => {
  const r = reportFixture();
  r.status = "partial";
  r.calculation = {
    status: "unavailable",
    data: null,
    errors: [
      {
        code: "eop_unavailable",
        message: "Required local resources unavailable",
      },
    ],
  };
  expect(parseReport(r, r.investigation.definition).status).toBe("partial");
  r.status = "complete";
  expect(() => parseReport(r, r.investigation.definition)).toThrow();
});
it("refuses oversized content lengths and streamed bodies", async () => {
  const r = reportFixture();
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      new Response("{}", {
        headers: { "Content-Length": String(MAX_REPORT_BYTES + 1) },
      }),
    ),
  );
  await expect(
    getInvestigationReport(
      r.investigation.definition,
      new AbortController().signal,
    ),
  ).rejects.toThrow(/size/);
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(new Response(" ".repeat(MAX_REPORT_BYTES + 1))),
  );
  await expect(
    getInvestigationReport(
      r.investigation.definition,
      new AbortController().signal,
    ),
  ).rejects.toThrow(/size/);
});
it("shows safe service refusals and unreadable responses", async () => {
  const r = reportFixture();
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          error: {
            code: "snapshot_not_found",
            message: "Snapshot not found",
          },
        }),
        { status: 404 },
      ),
    ),
  );
  await expect(
    getInvestigationReport(
      r.investigation.definition,
      new AbortController().signal,
    ),
  ).rejects.toThrow("Snapshot not found");
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("not JSON")));
  await expect(
    getInvestigationReport(
      r.investigation.definition,
      new AbortController().signal,
    ),
  ).rejects.toThrow(/unreadable/);
});
