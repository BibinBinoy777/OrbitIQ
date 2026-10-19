import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  deleteInvestigation,
  loadSaved,
  parseSaved,
  saveInvestigation,
  STORAGE_KEY,
  STORAGE_LIMITS,
  updateInvestigation,
} from "./investigation-storage";
import { savedContext } from "./test-fixtures/saved-investigations";
function memory() {
  const values = new Map<string, string>();
  return {
    values,
    getItem: vi.fn((key: string) => values.get(key) ?? null),
    setItem: vi.fn((key: string, value: string) => {
      values.set(key, value);
    }),
  };
}
beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date("2026-10-19T12:00:00Z"));
});
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});
it("creates a validated local save and survives a fresh storage reader", async () => {
  const store = memory(),
    v = savedContext("comparison");
  const saved = await saveInvestigation(v, "Comparison", "Private note", store);
  expect(saved.investigation).toEqual(v);
  expect(loadSaved(store)).toEqual([saved]);
  expect(JSON.parse(store.values.get(STORAGE_KEY)!)).toMatchObject({
    schema_version: 1,
  });
  expect(saved.created_at).toBe("2026-10-19T12:00:00.000000Z");
});
it("renames, updates parameters and deletes only the selected local record", async () => {
  const store = memory(),
    a = await saveInvestigation(savedContext("position"), "A", "", store);
  const b = await saveInvestigation(savedContext(), "B", "", store);
  vi.setSystemTime(new Date("2026-10-19T12:01:00Z"));
  const next = await updateInvestigation(
    a,
    {
      title: "Renamed",
      description: "Notes",
      investigation: {
        ...savedContext("position"),
        at: "2024-01-01T00:02:00Z",
      } as ReturnType<typeof savedContext>,
    },
    store,
  );
  expect(next.created_at).toBe(a.created_at);
  expect(next.updated_at).not.toBe(a.updated_at);
  expect(loadSaved(store).map((v) => v.title)).toEqual(["B", "Renamed"]);
  await deleteInvestigation(next, store);
  expect(loadSaved(store)).toEqual([b]);
});
it("rejects stale edits and deletions even when timestamps share a millisecond", async () => {
  const store = memory(),
    original = await saveInvestigation(savedContext(), "Original", "", store);
  const newer = await updateInvestigation(
    original,
    {
      title: "Other tab",
      description: "",
      investigation: original.investigation,
    },
    store,
  );
  expect(newer.updated_at).toBe(original.updated_at);
  await expect(
    updateInvestigation(
      original,
      {
        title: "Stale",
        description: "",
        investigation: original.investigation,
      },
      store,
    ),
  ).rejects.toThrow(/another tab/);
  await expect(deleteInvestigation(original, store)).rejects.toThrow(
    /another tab/,
  );
  expect(loadSaved(store)).toEqual([newer]);
});
it.each(["", " ", "x".repeat(121), "bad\nname", "bad\u0000name"])(
  "rejects unsupported title without changing storage",
  async (title) => {
    const store = memory();
    await expect(
      saveInvestigation(savedContext(), title, "", store),
    ).rejects.toThrow();
    expect(store.values.size).toBe(0);
  },
);
it("bounds description text and individual record size", async () => {
  const store = memory();
  await expect(
    saveInvestigation(savedContext(), "Title", "x".repeat(1001), store),
  ).rejects.toThrow();
  expect(() => parseSaved({ huge: "x".repeat(9000) })).toThrow(/oversized/);
});
it.each([
  "{broken",
  JSON.stringify({ schema_version: 2, records: [] }),
  JSON.stringify({ schema_version: 1, records: [{}] }),
  " ".repeat(STORAGE_LIMITS.bytes + 1),
])("preserves corrupt or unsupported data and refuses writes", async (raw) => {
  const store = memory();
  store.values.set(STORAGE_KEY, raw);
  expect(() => loadSaved(store)).toThrow(/not been overwritten/);
  await expect(
    saveInvestigation(savedContext(), "Title", "", store),
  ).rejects.toThrow();
  expect(store.values.get(STORAGE_KEY)).toBe(raw);
  expect(store.setItem).not.toHaveBeenCalled();
});
it("refuses quota errors and an unconfirmed read-back without claiming a save", async () => {
  const store = memory();
  store.setItem.mockImplementation(() => {
    throw new DOMException("quota", "QuotaExceededError");
  });
  await expect(
    saveInvestigation(savedContext(), "Title", "", store),
  ).rejects.toThrow(/No save was confirmed/);
  const blocked = { getItem: () => null, setItem: vi.fn() };
  await expect(
    saveInvestigation(savedContext(), "Title", "", blocked),
  ).rejects.toThrow(/No save was confirmed/);
});
it("handles unavailable browser storage safely", async () => {
  const store = {
    getItem: () => {
      throw new Error("sensitive internal text");
    },
    setItem: vi.fn(),
  };
  expect(() => loadSaved(store)).toThrow(/unavailable/);
  await expect(
    saveInvestigation(savedContext(), "Title", "", store),
  ).rejects.not.toThrow(/sensitive/);
});
it("enforces the local count limit without replacing previous saves", async () => {
  const store = memory();
  for (let i = 0; i < 50; i++)
    await saveInvestigation(savedContext(), `Save ${i}`, "", store);
  const before = store.values.get(STORAGE_KEY);
  await expect(
    saveInvestigation(savedContext(), "Overflow", "", store),
  ).rejects.toThrow(/limit reached/);
  expect(store.values.get(STORAGE_KEY)).toBe(before);
  expect(loadSaved(store)).toHaveLength(50);
});
it("uses a same-origin Web Lock when available", async () => {
  const request = vi.fn((_key: string, callback: () => unknown) =>
    Promise.resolve(callback()),
  );
  vi.stubGlobal("navigator", { locks: { request } });
  await saveInvestigation(savedContext(), "Serialized", "", memory());
  expect(request).toHaveBeenCalledWith(STORAGE_KEY, expect.any(Function));
});
it("rejects duplicate local identifiers instead of silently merging", async () => {
  const store = memory(),
    record = await saveInvestigation(savedContext(), "A", "", store);
  store.values.set(
    STORAGE_KEY,
    JSON.stringify({ schema_version: 1, records: [record, record] }),
  );
  expect(() => loadSaved(store)).toThrow(/corrupt/);
});
