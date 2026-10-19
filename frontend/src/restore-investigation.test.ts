import { beforeEach, expect, it, vi } from "vitest";
import {
  explorerSource,
  getDetail,
  getSnapshotPage,
  parsePage,
  parseStored,
} from "./investigation-api";
import { restoreInvestigation } from "./restore-investigation";
import {
  parseInvestigation,
  snapshotInvestigation,
  sourceReference,
} from "./saved-investigation";
import { investigationFixtures } from "./test-fixtures/investigations";
vi.mock("./investigation-api", async (original) => ({
  ...(await original<typeof import("./investigation-api")>()),
  getDetail: vi.fn(),
  getSnapshotPage: vi.fn(),
}));
const page = vi.mocked(getSnapshotPage),
  detail = vi.mocked(getDetail);
function context() {
  const data = investigationFixtures(),
    row = parseStored(data.itrs.first),
    summary = explorerSource(row)!;
  return { data, row, value: snapshotInvestigation(summary) };
}
beforeEach(() => {
  vi.resetAllMocks();
  detail.mockResolvedValue({ values: {}, units: {} });
});
it("resolves only the exact snapshot and checks detail without searching latest", async () => {
  const { data, row, value } = context();
  page.mockResolvedValue(
    parsePage({ ...data.page, snapshots: [row], returned_count: 1 }),
  );
  const result = await restoreInvestigation(
    value,
    new AbortController().signal,
  );
  expect(result.sources[0].id).toBe(value.source.snapshot_id);
  expect(page.mock.calls[0][0].toString()).toBe("snapshot_id=1&limit=1");
  expect(detail).toHaveBeenCalledWith(row, expect.any(AbortSignal));
});
it("restores both fixed sources, timestamp, frame and filter for comparison", async () => {
  const { data } = context(),
    first = parseStored(data.itrs.first),
    second = parseStored(data.itrs.second);
  const value = parseInvestigation({
    schema_version: 1,
    mode: "comparison",
    source: sourceReference(explorerSource(first)!),
    comparison_source: sourceReference(explorerSource(second)!),
    at: data.itrs.state_comparison.evaluation_at,
    frame: "ITRS",
    category: "shared",
  });
  page.mockImplementation(async (params) =>
    parsePage({
      ...data.page,
      snapshots: [params.get("snapshot_id") === "1" ? first : second],
      returned_count: 1,
    }),
  );
  const result = await restoreInvestigation(
    value,
    new AbortController().signal,
  );
  expect(result.investigation).toEqual(value);
  expect(result.sources.map((s) => s.id)).toEqual([1, 2]);
  expect(page.mock.calls.map((c) => c[0].get("snapshot_id"))).toEqual([
    "1",
    "2",
  ]);
});
it("reports missing records without substituting another source", async () => {
  const { data, value } = context();
  page.mockResolvedValue(
    parsePage({ ...data.page, snapshots: [], returned_count: 0 }),
  );
  await expect(
    restoreInvestigation(value, new AbortController().signal),
  ).rejects.toThrow(/missing.*No newer snapshot/);
  expect(detail).not.toHaveBeenCalled();
  expect(page).toHaveBeenCalledOnce();
});
it.each(["catalog_id", "response_sha256", "orbital_epoch", "retrieved_at"])(
  "rejects saved %s mismatches before calculation",
  async (field) => {
    const { data, row, value } = context();
    page.mockResolvedValue(
      parsePage({ ...data.page, snapshots: [row], returned_count: 1 }),
    );
    const source = {
      ...value.source,
      [field]:
        field === "catalog_id"
          ? 12345
          : field === "response_sha256"
            ? "a".repeat(64)
            : "2020-01-01T00:00:00Z",
    };
    await expect(
      restoreInvestigation(
        parseInvestigation({ ...value, source }),
        new AbortController().signal,
      ),
    ).rejects.toThrow(/does not match/);
    expect(detail).not.toHaveBeenCalled();
  },
);
it("preserves scientific-detail failure without producing replacement coordinates", async () => {
  const { data, row, value } = context();
  page.mockResolvedValue(
    parsePage({ ...data.page, snapshots: [row], returned_count: 1 }),
  );
  detail.mockRejectedValue(
    new Error("Stored scientific provenance is unavailable"),
  );
  await expect(
    restoreInvestigation(value, new AbortController().signal),
  ).rejects.toThrow(/provenance is unavailable/);
});
it("stops cancelled restoration before further requests", async () => {
  const { data, row, value } = context();
  page.mockResolvedValue(
    parsePage({ ...data.page, snapshots: [row], returned_count: 1 }),
  );
  const c = new AbortController();
  c.abort();
  await expect(restoreInvestigation(value, c.signal)).rejects.toMatchObject({
    name: "AbortError",
  });
  expect(detail).not.toHaveBeenCalled();
});
