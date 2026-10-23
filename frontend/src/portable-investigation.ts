import { parseSaved } from "./investigation-storage";
import type { SavedInvestigation } from "./investigation-storage";
import { bytes, canonicalTime, keys, object } from "./saved-investigation";

export const PORTABLE_MAX_BYTES = 16 * 1024;
export interface PortableBundle {
  kind: "orbitiq_saved_investigation_bundle";
  schema_version: 1;
  exported_at: string;
  record: SavedInvestigation;
}
const invalid = () =>
  new Error(
    "Invalid or unsupported portable bundle. Use a version-1 file exported from Saved investigations; no local data were changed.",
  );
export function exportBundle(
  value: SavedInvestigation,
  includeNotes = false,
  now = new Date().toISOString(),
): { bundle: PortableBundle; json: string; filename: string } {
  const record = parseSaved(value);
  const bundle: PortableBundle = {
    kind: "orbitiq_saved_investigation_bundle",
    schema_version: 1,
    exported_at: canonicalTime(now),
    record: { ...record, description: includeNotes ? record.description : "" },
  };
  const json = JSON.stringify(bundle, null, 2) + "\n";
  if (bytes(json) > PORTABLE_MAX_BYTES)
    throw new Error(
      "Portable file exceeds 16 KiB. Existing saves were not changed.",
    );
  return {
    bundle,
    json,
    filename: `orbitiq-investigation-${record.investigation.mode}-${record.id}.json`,
  };
}
function uniqueKeys(raw: string) {
  // JSON.parse validates syntax first. Inspect string/punctuation tokens only,
  // detecting escaped-equivalent keys without writing another JSON value parser.
  const tokens = [...raw.matchAll(/"(?:\\.|[^"\\])*"|[{}[\]:,]/g)].map(
    (m) => m[0],
  );
  const stack: (Set<string> | null)[] = [];
  tokens.forEach((token, i) => {
    if (token === "{" || token === "[") {
      stack.push(token === "{" ? new Set() : null);
      if (stack.length > 32) throw invalid();
    } else if (token === "}" || token === "]") stack.pop();
    else if (token.startsWith('"') && tokens[i + 1] === ":") {
      const key: string = JSON.parse(token);
      const seen = stack.at(-1);
      if (!seen || seen.has(key)) throw invalid();
      seen.add(key);
    }
  });
}
export function parseBundle(raw: string): PortableBundle {
  if (bytes(raw) > PORTABLE_MAX_BYTES)
    throw new Error(
      "File exceeds 16 KiB. Choose one portable investigation bundle.",
    );
  try {
    const value: unknown = JSON.parse(raw);
    uniqueKeys(raw);
    if (!object(value)) throw invalid();
    keys(value, ["kind", "schema_version", "exported_at", "record"]);
    if (
      value.kind !== "orbitiq_saved_investigation_bundle" ||
      value.schema_version !== 1
    )
      throw invalid();
    return {
      kind: value.kind,
      schema_version: 1,
      exported_at: canonicalTime(value.exported_at),
      record: parseSaved(value.record),
    };
  } catch {
    throw invalid();
  }
}
export async function readBundleFile(
  file: Pick<File, "size" | "arrayBuffer">,
): Promise<PortableBundle> {
  if (file.size > PORTABLE_MAX_BYTES)
    throw new Error(
      "File exceeds 16 KiB. Choose one portable investigation bundle.",
    );
  if (!file.size)
    throw new Error(
      "The file is empty. Choose an exported portable investigation bundle.",
    );
  let raw: string;
  try {
    const buffer = await file.arrayBuffer();
    if (buffer.byteLength > PORTABLE_MAX_BYTES) throw invalid();
    raw = new TextDecoder("utf-8", { fatal: true }).decode(buffer);
  } catch {
    throw new Error(
      "The file could not be read as bounded UTF-8 JSON. Choose another file and retry.",
    );
  }
  return parseBundle(raw);
}
