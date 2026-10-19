import { expect, it } from "vitest";
import {
  canonicalTime,
  LIMITS,
  parseInvestigation,
  parseShareLink,
  shareLink,
  shiftTime,
  sourceReference,
  verifySource,
} from "./saved-investigation";
import { savedContext } from "./test-fixtures/saved-investigations";

it.each(["snapshot", "position", "ground-track", "comparison"] as const)(
  "round-trips versioned %s parameters without orbital payloads",
  (mode) => {
    const context = savedContext(mode),
      link = shareLink(
        context,
        "https://example.test/orbit/?private=do-not-copy#old",
      );
    expect(parseShareLink(link)).toEqual(context);
    expect(link).not.toContain("private");
    expect(link).not.toContain("position_km");
    expect(link.length).toBeLessThan(LIMITS.url);
  },
);
it("preserves microseconds through offsets and sampling arithmetic", () => {
  expect(canonicalTime("2024-02-29T23:00:00.123456+05:30")).toBe(
    "2024-02-29T17:30:00.123456Z",
  );
  expect(shiftTime("2024-12-31T23:59:00.123456Z", 120)).toBe(
    "2025-01-01T00:01:00.123456Z",
  );
});
it.each([0, -1, 339999 + 1, Number.MAX_SAFE_INTEGER, true, "25544"])(
  "rejects invalid satellite identifier %s",
  (catalog_id) => {
    const v = savedContext();
    expect(() =>
      parseInvestigation({ ...v, source: { ...v.source, catalog_id } }),
    ).toThrow();
  },
);
it.each([0, -1, Number.MAX_SAFE_INTEGER + 1, 1.2, null, "7"])(
  "rejects invalid snapshot identifier %s",
  (snapshot_id) => {
    const v = savedContext();
    expect(() =>
      parseInvestigation({ ...v, source: { ...v.source, snapshot_id } }),
    ).toThrow();
  },
);
it.each([
  "2024-02-30T00:00:00Z",
  "2024-01-01T00:00:00",
  "2016-12-31T23:59:60Z",
  "2024-01-01T00:00:00.1234567Z",
  "2024-01-01T00:00:00+25:00",
  "bad",
  "",
])("rejects unsupported time %s", (at) => {
  expect(() =>
    parseInvestigation({ ...savedContext("position"), at }),
  ).toThrow();
});
it.each([undefined, 0, 2, "1"])(
  "rejects unsupported/missing schema version %s",
  (schema_version) => {
    expect(() =>
      parseInvestigation({ ...savedContext(), schema_version }),
    ).toThrow(/version/);
  },
);
it.each(["GCRS", "ECEF", "itrs", "", null])(
  "rejects unsupported coordinate frame %s",
  (frame) => {
    expect(() =>
      parseInvestigation({ ...savedContext("comparison"), frame }),
    ).toThrow();
  },
);
it("enforces mode-specific fields rather than dropping injected or irrelevant state", () => {
  expect(() =>
    parseInvestigation({ ...savedContext(), at: "2024-01-01T00:00:00Z" }),
  ).toThrow();
  expect(() =>
    parseInvestigation({ ...savedContext(), admin: true }),
  ).toThrow();
  expect(() =>
    parseInvestigation({ ...savedContext(), huge: "x".repeat(5000) }),
  ).toThrow(/large/);
  expect(() =>
    parseInvestigation({ ...savedContext("position"), frame: "ITRS" }),
  ).toThrow();
});
it.each([
  { duration_minutes: 1440, step_seconds: 10 },
  { step_seconds: 0 },
  { selected_index: 4 },
  { selected_index: -1 },
  { duration_minutes: 0 },
])("bounds track context %j", (change) => {
  const v = savedContext("ground-track");
  if (v.mode !== "ground-track") throw new Error();
  expect(() =>
    parseInvestigation({ ...v, track: { ...v.track, ...change } }),
  ).toThrow();
});
it("rejects mismatched selected time and requested sampling", () => {
  expect(() =>
    parseInvestigation({
      ...savedContext("ground-track"),
      at: "2024-01-01T00:00:00Z",
    }),
  ).toThrow(/sampling/);
});
it("allows explicit elements-only comparison without inventing evaluation time", () => {
  const v = parseInvestigation({ ...savedContext("comparison"), at: null });
  expect(parseShareLink(shareLink(v, "https://example.test"))).toEqual(v);
});
it.each([
  "&v=1",
  "&at=2024-01-01T00%3A00%3A00Z",
  "&admin=true",
  "&b_snapshot=1",
  "&method=POST",
  "&eop_policy=ignore",
])("rejects duplicated, irrelevant or injected link parameters %s", (extra) => {
  const link = shareLink(savedContext(), "https://example.test");
  expect(() => parseShareLink(link + extra)).toThrow();
});
it("rejects malformed, missing, oversized and future-version links before fetching", () => {
  const link = shareLink(savedContext("position"), "https://example.test");
  expect(() => parseShareLink(link.replace("v=1", "v=2"))).toThrow(/version/);
  expect(() =>
    parseShareLink(link.replace(/snapshot=7/, "snapshot=%FF")),
  ).toThrow();
  expect(() =>
    parseShareLink("https://example.test/#/investigation?v=1"),
  ).toThrow();
  expect(() => parseShareLink("https://example.test/#unknown")).toThrow(
    /Unrecognized/,
  );
  expect(() => parseShareLink(link + "x".repeat(2048))).toThrow(/long/);
  expect(parseShareLink("https://example.test/")).toBeNull();
});
it("requires hash, epoch, retrieval and supported source frame", () => {
  expect(() =>
    sourceReference({ id: 7, catalog_id: 25544, frame: "TEME" }),
  ).toThrow();
  expect(() =>
    sourceReference({ id: 7, catalog_id: 25544, frame: "GCRS" }),
  ).toThrow(/TEME/);
});
it("detects an identifier collision or wrong source provenance", () => {
  const expected = savedContext().source;
  const actual = {
    ...expected,
    id: expected.snapshot_id,
    frame: "TEME",
    response_sha256: "b".repeat(64),
  };
  expect(() => verifySource(expected, actual)).toThrow(/No newer source/);
});
