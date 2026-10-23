// Public synthetic history contract; not real satellite observations.
import { afterEach, expect, it, vi } from "vitest";
import { getHistory, parseHistory } from "./history-api";
import fixture from "./test-fixtures/history.json";
import windows from "./test-fixtures/history-windows.json";
afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});
it.each([
  ["page size", { limit: "1" }],
  ["before cursor", { before_id: "2" }],
  ["history anchor", { anchor_id: "1" }],
])(
  "refuses a valid same-catalog report for another requested %s",
  async (_label, parameters) => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        headers: new Headers(),
        text: async () => JSON.stringify(fixture),
      }),
    );
    await expect(
      getHistory(
        6251,
        new URLSearchParams(parameters),
        new AbortController().signal,
      ),
    ).rejects.toThrow(/historical/i);
  },
);
it.each([
  [
    "request catalog",
    (v: typeof fixture) => {
      v.request.catalog_id = 12345;
    },
  ],
  [
    "request limit",
    (v: typeof fixture) => {
      v.request.limit = 1;
    },
  ],
  [
    "complete count",
    (v: typeof fixture) => {
      v.pagination.total_count = 3;
    },
  ],
  [
    "unknown count status",
    (v: typeof fixture) => {
      v.pagination.total_count_status = "invented";
    },
  ],
  [
    "source graph",
    (v: typeof fixture) => {
      v.sources[0].snapshot_id = 999;
    },
  ],
  [
    "anchor boundary",
    (v: typeof fixture) => {
      v.pagination.anchor_id = 1;
      v.request.anchor_id = 1;
    },
  ],
])("refuses inconsistent historical %s", (_label, mutate) => {
  const body = structuredClone(fixture);
  mutate(body);
  expect(() => parseHistory(body)).toThrow(/historical/i);
});

it.each(Object.entries(windows))(
  "accepts real API synthetic %s window",
  (_name, report) => {
    expect(parseHistory(report)).toEqual(report);
  },
);
it("accepts matching selected and server-assigned anchors with exact source clocks", async () => {
  for (const body of [
    windows.full,
    windows.first,
    windows.older,
    windows.single,
    windows.empty,
  ]) {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        headers: new Headers(),
        text: async () => JSON.stringify(body),
      }),
    );
    const params = new URLSearchParams({ limit: String(body.request.limit) });
    if (body.request.before_id !== null)
      params.set("before_id", String(body.request.before_id));
    // For a first window, the server may choose the anchor. Continuations pin it.
    if (body.request.before_id !== null)
      params.set("anchor_id", String(body.request.anchor_id));
    expect(
      await getHistory(6251, params, new AbortController().signal),
    ).toEqual(body);
  }
  expect(windows.full.sources[0].retrieved_at).toContain("123456");
});

it("binds validation to the sent query snapshot and retains equivalent offset clocks", async () => {
  const body = structuredClone(windows.first);
  body.sources[0].retrieved_at = "2026-10-18T15:00:00.123456+03:00";
  expect(parseHistory(body)).toEqual(body);
  let deliver: (value: unknown) => void = () => {};
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation(
      () =>
        new Promise((resolve) => {
          deliver = resolve;
        }),
    ),
  );
  const params = new URLSearchParams({ limit: "1" });
  const pending = getHistory(6251, params, new AbortController().signal);
  params.set("limit", "20");
  deliver({
    ok: true,
    headers: new Headers(),
    text: async () => JSON.stringify(body),
  });
  expect(await pending).toEqual(body);
});
