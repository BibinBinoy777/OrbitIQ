// Synthetic browser model fixtures only; never inserted into the orbital archive.
import { canonicalTime, parseInvestigation } from "../saved-investigation";
import type { Investigation } from "../saved-investigation";
export function savedContext(
  mode: Investigation["mode"] = "snapshot",
): Investigation {
  const source = {
    snapshot_id: 7,
    catalog_id: 25544,
    orbital_epoch: "2024-01-01T00:00:00Z",
    retrieved_at: "2024-01-01T01:00:00Z",
    response_sha256: "a".repeat(64),
  };
  const base = { schema_version: 1, source, mode, frame: "TEME" };
  if (mode === "position")
    return parseInvestigation({ ...base, at: source.orbital_epoch });
  if (mode === "comparison")
    return parseInvestigation({
      ...base,
      frame: "ITRS",
      at: source.orbital_epoch,
      comparison_source: {
        ...source,
        snapshot_id: 8,
        response_sha256: "b".repeat(64),
      },
      category: "all",
    });
  if (mode === "ground-track")
    return parseInvestigation({
      ...base,
      frame: "ITRS",
      at: "2024-01-01T00:01:00Z",
      track: {
        start: canonicalTime(source.orbital_epoch),
        duration_minutes: 2,
        step_seconds: 60,
        selected_index: 1,
      },
    });
  return parseInvestigation(base);
}
