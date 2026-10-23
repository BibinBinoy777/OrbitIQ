import {
  bytes,
  canonicalTime,
  keys,
  LIMITS,
  object,
  parseInvestigation,
} from "./saved-investigation";
import type { Investigation } from "./saved-investigation";

export const STORAGE_KEY = "orbitiq.saved-investigations.v1";
export const SAVED_CHANGED = "orbitiq:saved-investigations-changed";
export const STORAGE_LIMITS = {
  count: 50,
  bytes: 256 * 1024,
  recordBytes: 8192,
};
export interface SavedInvestigation {
  schema_version: 1;
  id: string;
  title: string;
  description: string;
  created_at: string;
  updated_at: string;
  investigation: Investigation;
}
export type BrowserStorage = Pick<Storage, "getItem" | "setItem">;
const uuid =
  /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const unavailable = () =>
  new Error(
    "Browser storage is unavailable or full. No save was confirmed; existing orbital data are unaffected.",
  );
function storage(): BrowserStorage {
  try {
    return window.localStorage;
  } catch {
    throw unavailable();
  }
}
export function text(value: unknown, max: number, required = false): string {
  if (
    typeof value !== "string" ||
    value.length > max ||
    [...value].some((c) => {
      const code = c.codePointAt(0)!;
      return code === 127 || (code < 32 && ![9, 10, 13].includes(code));
    }) ||
    (required && !value.trim())
  )
    throw new Error(
      "Use a nonempty title up to 120 characters and a description up to 1000 characters.",
    );
  if (required && /[\r\n\t]/.test(value))
    throw new Error("Investigation titles must fit on one line.");
  return value.trim();
}
export function parseSaved(v: unknown): SavedInvestigation {
  if (!object(v) || bytes(JSON.stringify(v)) > STORAGE_LIMITS.recordBytes)
    throw new Error("Invalid or oversized local investigation.");
  keys(v, [
    "schema_version",
    "id",
    "title",
    "description",
    "created_at",
    "updated_at",
    "investigation",
  ]);
  if (v.schema_version !== 1 || typeof v.id !== "string" || !uuid.test(v.id))
    throw new Error(
      "Unsupported or invalid local investigation version/identifier.",
    );
  const created = canonicalTime(v.created_at),
    updated = canonicalTime(v.updated_at);
  if (updated < created)
    throw new Error(
      "Investigation timestamps are inconsistent. Check the browser clock.",
    );
  return {
    schema_version: 1,
    id: v.id,
    title: text(v.title, LIMITS.title, true),
    description: text(v.description, LIMITS.description),
    created_at: created,
    updated_at: updated,
    investigation: parseInvestigation(v.investigation),
  };
}
export function loadSaved(
  target: BrowserStorage = storage(),
): SavedInvestigation[] {
  let raw: string | null;
  try {
    raw = target.getItem(STORAGE_KEY);
  } catch {
    throw unavailable();
  }
  if (raw === null) return [];
  try {
    if (bytes(raw) > STORAGE_LIMITS.bytes) throw new Error();
    const data: unknown = JSON.parse(raw);
    if (!object(data)) throw new Error();
    keys(data, ["schema_version", "records"]);
    if (
      data.schema_version !== 1 ||
      !Array.isArray(data.records) ||
      data.records.length > STORAGE_LIMITS.count
    )
      throw new Error();
    const records = data.records.map(parseSaved);
    if (new Set(records.map((r) => r.id)).size !== records.length)
      throw new Error();
    return records;
  } catch {
    throw new Error(
      "Local saved data are corrupt or use an unsupported version. They have not been overwritten. Restore a browser-storage backup or use another browser profile.",
    );
  }
}
function persist(records: SavedInvestigation[], target: BrowserStorage): void {
  const value = JSON.stringify({
    schema_version: 1,
    records: records.map(parseSaved),
  });
  if (
    records.length > STORAGE_LIMITS.count ||
    bytes(value) > STORAGE_LIMITS.bytes
  )
    throw new Error(
      "Local save limit reached (50 investigations / 256 KiB). Delete an existing local investigation first.",
    );
  try {
    target.setItem(STORAGE_KEY, value);
    if (target.getItem(STORAGE_KEY) !== value) throw new Error();
  } catch {
    throw unavailable();
  }
  if (typeof window !== "undefined")
    window.dispatchEvent(new Event(SAVED_CHANGED));
}
async function locked<T>(operation: () => T): Promise<T> {
  // Web Locks serialize same-origin tabs where available. Storage remains local.
  if (typeof navigator !== "undefined" && navigator.locks?.request)
    return navigator.locks.request(STORAGE_KEY, operation);
  return operation();
}
export async function saveInvestigation(
  investigation: Investigation,
  title: string,
  description: string,
  target: BrowserStorage = storage(),
): Promise<SavedInvestigation> {
  return locked(() => {
    const records = loadSaved(target),
      now = new Date().toISOString();
    if (!globalThis.crypto?.randomUUID)
      throw new Error(
        "Secure browser identifiers are unavailable. Use a current browser in a secure context; sharing parameters remains available.",
      );
    const record = parseSaved({
      schema_version: 1,
      id: crypto.randomUUID(),
      title,
      description,
      created_at: now,
      updated_at: now,
      investigation,
    });
    persist([record, ...records], target);
    return record;
  });
}
export async function updateInvestigation(
  previous: SavedInvestigation,
  changes: Pick<SavedInvestigation, "title" | "description" | "investigation">,
  target: BrowserStorage = storage(),
): Promise<SavedInvestigation> {
  return locked(() => {
    const expected = parseSaved(previous),
      id = expected.id;
    const records = loadSaved(target),
      existing = records.find((r) => r.id === id);
    if (!existing)
      throw new Error(
        "This local investigation no longer exists. Refresh the list.",
      );
    if (JSON.stringify(existing) !== JSON.stringify(expected))
      throw new Error(
        "This save changed in another tab. Refresh before editing or deleting it.",
      );
    const record = parseSaved({
      ...existing,
      ...changes,
      updated_at: new Date().toISOString(),
    });
    persist(
      records.map((r) => (r.id === id ? record : r)),
      target,
    );
    return record;
  });
}
export async function deleteInvestigation(
  previous: SavedInvestigation,
  target: BrowserStorage = storage(),
): Promise<void> {
  return locked(() => {
    const expected = parseSaved(previous),
      id = expected.id;
    const records = loadSaved(target);
    const existing = records.find((r) => r.id === id);
    if (!existing)
      throw new Error(
        "This local investigation no longer exists. Refresh the list.",
      );
    if (JSON.stringify(existing) !== JSON.stringify(expected))
      throw new Error(
        "This save changed in another tab. Refresh before editing or deleting it.",
      );
    persist(
      records.filter((r) => r.id !== id),
      target,
    );
  });
}

export interface ImportPreview {
  record: SavedInvestigation;
  expectedStorage: string | null;
  status: "new" | "already_saved" | "collision";
  existingId?: string;
}
function sameContent(a: SavedInvestigation, b: SavedInvestigation): boolean {
  return JSON.stringify({ ...a, id: "" }) === JSON.stringify({ ...b, id: "" });
}
export function previewImport(
  value: SavedInvestigation,
  target: BrowserStorage = storage(),
): ImportPreview {
  const record = parseSaved(value);
  let expectedStorage: string | null;
  try {
    expectedStorage = target.getItem(STORAGE_KEY);
  } catch {
    throw unavailable();
  }
  const records = loadSaved(target);
  try {
    if (target.getItem(STORAGE_KEY) !== expectedStorage) throw new Error();
  } catch {
    throw new Error(
      "Local saves changed or became unavailable. Preview the file again.",
    );
  }
  const duplicate = records.find((r) => sameContent(r, record));
  return {
    record,
    expectedStorage,
    status: duplicate
      ? "already_saved"
      : records.some((r) => r.id === record.id)
        ? "collision"
        : "new",
    existingId: duplicate?.id,
  };
}
export async function confirmImport(
  preview: ImportPreview,
  copy: boolean,
  target: BrowserStorage = storage(),
): Promise<{ record: SavedInvestigation; inserted: boolean }> {
  // Import shares the existing writers' lock and requires it for cross-tab safety.
  // Unsupported clients may still export; there is no unsafe overwrite fallback.
  if (typeof navigator === "undefined" || !navigator.locks?.request)
    throw new Error(
      "Safe import requires Web Locks. Use a current browser in a secure context; existing saves were not changed.",
    );
  return locked(() => {
    const current = previewImport(parseSaved(preview.record), target);
    if (current.expectedStorage !== preview.expectedStorage)
      throw new Error(
        "Local saves changed since preview. Preview the file again before importing.",
      );
    const records = loadSaved(target);
    if (current.status === "already_saved")
      return {
        record: records.find((r) => r.id === current.existingId)!,
        inserted: false,
      };
    let record = current.record;
    if (current.status === "collision") {
      if (!copy)
        throw new Error(
          "This identifier already exists. Cancel or explicitly import a separate copy.",
        );
      if (!globalThis.crypto?.randomUUID)
        throw new Error(
          "Secure identifiers are unavailable. No import was performed.",
        );
      record = parseSaved({ ...record, id: crypto.randomUUID() });
      if (records.some((r) => r.id === record.id))
        throw new Error(
          "A unique identifier could not be created. No import was performed.",
        );
    }
    // Recheck immediately before the single atomic localStorage write. Cooperating
    // tabs use this lock; direct devtools/older application writers are not covered.
    try {
      if (target.getItem(STORAGE_KEY) !== current.expectedStorage)
        throw new Error();
    } catch {
      throw new Error(
        "Local saves changed or became unavailable. Preview the file again.",
      );
    }
    persist([record, ...records], target);
    return { record, inserted: true };
  });
}
