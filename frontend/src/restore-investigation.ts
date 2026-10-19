import {
  explorerSource,
  getDetail,
  getSnapshotPage,
} from "./investigation-api";
import type { Investigation, SourceReference } from "./saved-investigation";
import { parseInvestigation, verifySource } from "./saved-investigation";
import type { SnapshotSummary } from "./scientific-api";

async function resolve(
  ref: SourceReference,
  signal: AbortSignal,
): Promise<SnapshotSummary> {
  const page = await getSnapshotPage(
    new URLSearchParams({ snapshot_id: String(ref.snapshot_id), limit: "1" }),
    signal,
  );
  if (signal.aborted) throw new DOMException("Cancelled", "AbortError");
  const stored = page.snapshots.find((s) => s.id === ref.snapshot_id);
  if (!stored)
    throw new Error(
      `Snapshot #${ref.snapshot_id} is missing from this archive. Its saved satellite and source cannot be restored. No newer snapshot was substituted.`,
    );
  const summary = explorerSource(stored);
  if (!summary)
    throw new Error(
      `Snapshot #${ref.snapshot_id} has unavailable or unsupported source provenance. No replacement was selected.`,
    );
  verifySource(ref, summary);
  await getDetail(stored, signal); // Existing service revalidates the persisted source.
  return summary;
}
export async function restoreInvestigation(
  value: Investigation,
  signal: AbortSignal,
) {
  const investigation = parseInvestigation(value);
  const references =
    investigation.mode === "comparison"
      ? [investigation.source, investigation.comparison_source]
      : [investigation.source];
  const sources = await Promise.all(
    references.map((ref) => resolve(ref, signal)),
  );
  if (signal.aborted) throw new DOMException("Cancelled", "AbortError");
  return { investigation, sources };
}
