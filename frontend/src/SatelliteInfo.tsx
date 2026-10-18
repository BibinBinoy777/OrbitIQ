import { useEffect, useId, useState } from "react";
import type { RefObject } from "react";
import type { SnapshotSummary } from "./scientific-api";
import type { TrackPoint } from "./ground-track-api";
import { getOrbitalElements } from "./snapshot-api";
import type { OrbitalElements } from "./snapshot-api";
import { formatUtc } from "./time-presentation";
export default function SatelliteInfo({
  source,
  point,
  panelRef,
}: {
  source: SnapshotSummary;
  point?: TrackPoint;
  panelRef: RefObject<HTMLElement | null>;
}) {
  const [elements, setElements] = useState<OrbitalElements | null>(null);
  const [error, setError] = useState("");
  const title = useId();
  useEffect(() => {
    const controller = new AbortController();
    getOrbitalElements(source, controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setElements(data);
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setError(
            "Source element details unavailable. Reselect the snapshot to retry.",
          );
      });
    return () => controller.abort();
  }, [source]);
  return (
    <section
      className="satellite-info"
      ref={panelRef}
      tabIndex={-1}
      aria-labelledby={title}
    >
      <span className="eyebrow">SELECTED SOURCE</span>
      <h4 id={title}>Satellite information</h4>
      <p className="satellite-name">{source.object_name ?? "Unnamed object"}</p>
      <p>
        NORAD {source.catalog_id} · snapshot #{source.id}
      </p>
      <p className={`freshness ${source.freshness_info?.state ?? "unknown"}`}>
        Freshness: {source.freshness_info?.state ?? "unknown"}
      </p>
      <h5>Source mean elements</h5>
      {elements ? (
        <dl className="element-values">
          <dt>Inclination</dt>
          <dd>{elements.inclination_deg.toFixed(4)}°</dd>
          <dt>Eccentricity</dt>
          <dd>{elements.eccentricity.toFixed(7)} · dimensionless</dd>
          <dt>Mean motion</dt>
          <dd>{elements.mean_motion_rev_day.toFixed(8)} rev/day</dd>
          <dt>International identifier</dt>
          <dd>{elements.object_id || "Not provided"}</dd>
        </dl>
      ) : (
        <p role="status">{error || "Loading source element details…"}</p>
      )}
      <p>Element epoch: {formatUtc(source.orbital_epoch)}</p>
      <p>First retrieval: {formatUtc(source.retrieved_at)}</p>
      <h5>Selected calculated sample</h5>
      {point ? (
        <>
          <p>Propagation time: {formatUtc(point.at)}</p>
          <p>Calculated at: {formatUtc(point.teme?.calculated_at)}</p>
          <p>ITRS · Earth center · position in km</p>
          {point.position_km ? (
            <dl className="element-values">
              {["x", "y", "z"].map((axis, i) => (
                <div key={axis}>
                  <dt>{axis} (km)</dt>
                  <dd>{point.position_km![i].toFixed(3)}</dd>
                </div>
              ))}
            </dl>
          ) : (
            <p>No validated Cartesian position available for the 3D marker.</p>
          )}
          <p>
            EOP: {point.earth_orientation.status}.{" "}
            {point.transformation_status === "predicted_eop"
              ? "Predictions, not final measurements."
              : "Measured Earth-orientation input."}
          </p>
        </>
      ) : (
        <p>
          No calculated position selected. Generate a track using this snapshot.
        </p>
      )}
      <p className="notice">
        Calculated positions are not direct observations. Orbital uncertainty is
        unquantified; numerical reference agreement is not an accuracy
        guarantee.
      </p>
      <details>
        <summary>Scientific limits</summary>
        <p>
          No visibility or collision assessment. Leap-crossing propagation is
          unsupported. Earth-orientation resources have finite coverage and
          require maintenance. The approximately 1.32 cm fixed-EOP reference
          residual is case-specific.
        </p>
      </details>
    </section>
  );
}
