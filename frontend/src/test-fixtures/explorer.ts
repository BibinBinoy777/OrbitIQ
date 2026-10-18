// Synthetic graphics/timeline contract fixtures. Never actual satellite observations.
import { fixture, source } from "./ground-track";
import { parseTrack } from "../ground-track-api";
export function explorerTrack() {
  const data = fixture();
  return parseTrack(
    {
      ...data,
      points: data.points.map((p, i) => ({
        ...p,
        position_km: [-6778.137, i * 5, 0],
        ground_position_km: [-6378.137, i * 4, 0],
        teme: { ...p.teme, calculated_at: "2026-10-18T18:00:00+00:00" },
      })),
    },
    source,
  );
}
