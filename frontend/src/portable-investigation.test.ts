// Deterministic local recovery inputs, not orbital observations or private saves.
import { readFileSync } from "node:fs";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  exportBundle,
  parseBundle,
  PORTABLE_MAX_BYTES,
  readBundleFile,
} from "./portable-investigation";
import {
  confirmImport,
  loadSaved,
  parseSaved,
  previewImport,
  saveInvestigation,
  STORAGE_KEY,
  updateInvestigation,
} from "./investigation-storage";
import type { SavedInvestigation } from "./investigation-storage";
import { savedContext } from "./test-fixtures/saved-investigations";
import type { Investigation } from "./saved-investigation";
type Draft = {
  schema_version: unknown;
  exported_at?: unknown;
  record: {
    id: unknown;
    schema_version: unknown;
    created_at: unknown;
    updated_at: unknown;
    title: unknown;
    description: unknown;
    investigation: { mode: unknown; source: Record<string, unknown> };
    [key: string]: unknown;
  };
  [key: string]: unknown;
};
const uuid = "c7fcaa37-5da9-4bd5-8000-582c07b6683b";
function record(mode: Investigation["mode"] = "snapshot"): SavedInvestigation {
  return parseSaved({
    schema_version: 1,
    id: uuid,
    title: "E6 SYNTHETIC RECOVERY",
    description: "TEST NOTE ONLY",
    created_at: "2026-10-19T12:00:00Z",
    updated_at: "2026-10-19T12:00:00Z",
    investigation: savedContext(mode),
  });
}
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
  vi.stubGlobal("navigator", {
    locks: {
      request: vi.fn((_key: string, fn: () => unknown) =>
        Promise.resolve(fn()),
      ),
    },
  });
  vi.stubGlobal(
    "fetch",
    vi.fn(() => {
      throw new Error("Network forbidden for portability");
    }),
  );
});
afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});
it.each(["snapshot", "position", "ground-track", "comparison"] as const)(
  "round-trips %s into independent storage, preserving exact inputs/timestamps/notes with explicit opt-in",
  async (mode) => {
    const original = record(mode),
      before = structuredClone(original);
    const { json, filename } = exportBundle(original, true);
    expect(filename).toBe(`orbitiq-investigation-${mode}-${uuid}.json`);
    const bundle = parseBundle(json),
      target = memory();
    const preview = previewImport(bundle.record, target);
    expect(target.setItem).not.toHaveBeenCalled();
    const restored = await confirmImport(preview, false, target);
    expect(restored.inserted).toBe(true);
    expect(loadSaved(target)).toEqual([original]);
    expect(
      parseBundle(exportBundle(restored.record, true).json).record,
    ).toEqual(original);
    expect(original).toEqual(before);
    expect(fetch).not.toHaveBeenCalled();
  },
);
it("excludes optional private notes by default without editing the original", () => {
  const original = record();
  expect(parseBundle(exportBundle(original).json).record.description).toBe("");
  expect(original.description).toBe("TEST NOTE ONLY");
});
it("treats title/notes as text and generates a filename without user text", () => {
  const value = {
    ...record(),
    title: "<img src=x onerror=alert(1)>/../file",
    description: "=SUM(1,2) <script>alert(1)</script>",
  };
  const file = exportBundle(value, true);
  expect(file.filename).not.toMatch(/[<>/]/);
  expect(parseBundle(file.json).record).toEqual(value);
});
it.each([
  "",
  " ",
  "{bad",
  "null",
  "[]",
  '{"kind":"orbitiq_investigation_report"}',
])("rejects invalid or non-portable JSON %s", (raw) => {
  expect(() => parseBundle(raw)).toThrow(/version-1/);
});
it.each([
  (v: Draft) => {
    v.schema_version = 2;
  },
  (v: Draft) => {
    delete v.exported_at;
  },
  (v: Draft) => {
    v.exported_at = "2026-02-30T00:00:00Z";
  },
  (v: Draft) => {
    v.record.id = "missing";
  },
  (v: Draft) => {
    v.record.schema_version = 2;
  },
  (v: Draft) => {
    v.record.created_at = "bad";
  },
  (v: Draft) => {
    v.record.updated_at = "2000-01-01T00:00:00Z";
  },
  (v: Draft) => {
    v.record.title = 42;
  },
  (v: Draft) => {
    v.record.description = "x".repeat(1001);
  },
  (v: Draft) => {
    v.record.investigation.mode = "unsupported";
  },
  (v: Draft) => {
    v.record.investigation.source.snapshot_id = -1;
  },
  (v: Draft) => {
    v.record.investigation.source.response_sha256 = "bad";
  },
  (v: Draft) => {
    v.record.investigation.source.orbital_epoch = "2026-10-01T00:00:00";
  },
  (v: Draft) => {
    v.scientifically_qualified = true;
  },
  (v: Draft) => {
    v.record.results = { trusted: true };
  },
  (v: Draft) => {
    v.record.investigation.source.url = "javascript:alert(1)";
  },
])(
  "rejects unsupported fields, types, modes, versions, clocks and provenance",
  (change) => {
    const value = JSON.parse(exportBundle(record(), true).json);
    change(value);
    expect(() => parseBundle(JSON.stringify(value))).toThrow(
      /no local data were changed/,
    );
  },
);
it.each([
  '"schema_version":1,"schema_version":1',
  '"schema_version":1,"schema_vers\\u0069on":1',
])("rejects duplicate and escaped-equivalent JSON keys", (duplicate) => {
  const raw = JSON.stringify(exportBundle(record(), true).bundle).replace(
    '"schema_version":1',
    duplicate,
  );
  expect(() => parseBundle(raw)).toThrow(/unsupported/);
});
it("bounds raw UTF-8 bytes and checks file size before reading", async () => {
  expect(() => parseBundle("é".repeat(PORTABLE_MAX_BYTES))).toThrow(/16 KiB/);
  const read = vi.fn();
  await expect(
    readBundleFile({ size: PORTABLE_MAX_BYTES + 1, arrayBuffer: read }),
  ).rejects.toThrow(/16 KiB/);
  expect(read).not.toHaveBeenCalled();
  await expect(readBundleFile({ size: 0, arrayBuffer: read })).rejects.toThrow(
    /empty/,
  );
  expect(read).not.toHaveBeenCalled();
});
it("reads real UTF-8 bytes and rejects invalid encoding or failed file IO", async () => {
  const original = record(),
    raw = new TextEncoder().encode(exportBundle(original, true).json);
  expect(
    (
      await readBundleFile({
        size: raw.byteLength,
        arrayBuffer: async () => raw.buffer,
      })
    ).record,
  ).toEqual(original);
  await expect(
    readBundleFile({
      size: 1,
      arrayBuffer: async () => new Uint8Array([255]).buffer,
    }),
  ).rejects.toThrow(/UTF-8/);
  await expect(
    readBundleFile({
      size: 1,
      arrayBuffer: async () => {
        throw new Error("private path");
      },
    }),
  ).rejects.not.toThrow(/private path/);
});
it("no-ops repeated imports, including an earlier collision copy", async () => {
  const target = memory(),
    original = record();
  await confirmImport(previewImport(original, target), false, target);
  const bytes = target.values.get(STORAGE_KEY),
    writes = target.setItem.mock.calls.length;
  const second = await confirmImport(
    previewImport(original, target),
    false,
    target,
  );
  expect(second.inserted).toBe(false);
  expect(target.values.get(STORAGE_KEY)).toBe(bytes);
  expect(target.setItem).toHaveBeenCalledTimes(writes);
  const conflict = { ...original, title: "DIFFERENT TEST CONTENT" };
  const preview = previewImport(conflict, target);
  expect(preview.status).toBe("collision");
  await expect(confirmImport(preview, false, target)).rejects.toThrow(
    /identifier already exists/,
  );
  expect(target.values.get(STORAGE_KEY)).toBe(bytes);
  const copied = await confirmImport(preview, true, target);
  expect(copied.record.id).not.toBe(original.id);
  expect(loadSaved(target).find((r) => r.id === original.id)).toEqual(original);
  const repeated = await confirmImport(
    previewImport(conflict, target),
    true,
    target,
  );
  expect(repeated.inserted).toBe(false);
  expect(repeated.record).toEqual(copied.record);
  expect(loadSaved(target)).toHaveLength(2);
});
it("rechecks newer state under the same-origin write lock before confirmation", async () => {
  const target = memory(),
    preview = previewImport(record(), target);
  await saveInvestigation(savedContext(), "OTHER TAB TEST SAVE", "", target);
  const before = target.values.get(STORAGE_KEY);
  await expect(confirmImport(preview, false, target)).rejects.toThrow(
    /changed since preview/,
  );
  expect(target.values.get(STORAGE_KEY)).toBe(before);
  expect(navigator.locks.request).toHaveBeenCalledWith(
    STORAGE_KEY,
    expect.any(Function),
  );
});
it("detects a same-ID edit while the preview is open", async () => {
  const target = memory();
  await confirmImport(previewImport(record(), target), false, target);
  const preview = previewImport(record(), target),
    original = loadSaved(target)[0];
  await updateInvestigation(
    original,
    { ...original, title: "NEWER CONTENT" },
    target,
  );
  await expect(confirmImport(preview, false, target)).rejects.toThrow(
    /changed since preview/,
  );
  expect(loadSaved(target)[0].title).toBe("NEWER CONTENT");
});
it("refuses unavailable Web Locks, corrupt destination and quota failures without changing originals", async () => {
  const target = memory();
  await saveInvestigation(savedContext(), "ORIGINAL", "", target);
  const before = target.values.get(STORAGE_KEY),
    preview = previewImport(record(), target);
  vi.stubGlobal("navigator", {});
  await expect(confirmImport(preview, false, target)).rejects.toThrow(
    /Web Locks/,
  );
  expect(target.values.get(STORAGE_KEY)).toBe(before);
  vi.stubGlobal("navigator", {
    locks: { request: (_: string, fn: () => unknown) => Promise.resolve(fn()) },
  });
  target.setItem.mockImplementation(() => {
    throw new DOMException("quota", "QuotaExceededError");
  });
  await expect(confirmImport(preview, false, target)).rejects.toThrow(
    /No save was confirmed/,
  );
  expect(target.values.get(STORAGE_KEY)).toBe(before);
  target.values.set(STORAGE_KEY, "corrupt");
  expect(() => previewImport(record(), target)).toThrow(/not been overwritten/);
  expect(target.values.get(STORAGE_KEY)).toBe("corrupt");
});
it("refuses the existing count limit instead of discarding records", async () => {
  const target = memory();
  for (let i = 0; i < 50; i++)
    await saveInvestigation(savedContext(), `TEST ${i}`, "", target);
  const before = target.values.get(STORAGE_KEY);
  await expect(
    confirmImport(previewImport(record(), target), false, target),
  ).rejects.toThrow(/limit reached/);
  expect(target.values.get(STORAGE_KEY)).toBe(before);
});

it("validates the documented synthetic bundle example with the production parser", () => {
  const guide = readFileSync("../docs/engineering-e6-guide.md", "utf8");
  const example = /```json\n([\s\S]*?)\n```/.exec(guide)?.[1];
  expect(example).toBeDefined();
  const bundle = parseBundle(example!);
  expect(bundle.record.title).toContain("SYNTHETIC FORMAT EXAMPLE");
  expect(bundle.record.investigation.mode).toBe("snapshot");
});
