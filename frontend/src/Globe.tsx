import { useEffect, useRef, useState } from "react";
import type { TrackPoint } from "./ground-track-api";
import type { GlobeEngine, CameraAction } from "./globe-renderer";
import { canRenderPoint } from "./globe-geometry";
import type { ComparisonMarker } from "./globe-geometry";
const EMPTY: TrackPoint[] = [];
const NO_COMPARISON: ComparisonMarker[] = [];
export default function Globe({
  points = EMPTY,
  selected = 0,
  onInspect = () => {},
  comparison = NO_COMPARISON,
}: {
  points?: TrackPoint[];
  selected?: number;
  onInspect?: () => void;
  comparison?: ComparisonMarker[];
}) {
  const host = useRef<HTMLDivElement>(null),
    engine = useRef<GlobeEngine | null>(null);
  const current = useRef({ points, selected, onInspect, comparison });
  useEffect(() => {
    current.current = { points, selected, onInspect, comparison };
    engine.current?.setData(points, selected);
    engine.current?.setComparison?.(comparison);
  }, [points, selected, onInspect, comparison]);
  const [status, setStatus] = useState<"loading" | "ready" | "failed" | "lost">(
    "loading",
  );
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let cancelled = false;
    if (typeof window.WebGL2RenderingContext === "undefined") return;
    // Bound a stalled chunk fetch. A late import must not create a stale scene.
    const timeout = window.setTimeout(() => {
      cancelled = true;
      setStatus("failed");
    }, 15000);
    import("./globe-renderer")
      .then(({ createGlobe }) => {
        window.clearTimeout(timeout);
        if (cancelled || !host.current) return;
        try {
          engine.current = createGlobe(host.current, {
            ready: () => {
              if (!cancelled) setStatus("ready");
            },
            lost: () => {
              if (!cancelled) setStatus("lost");
            },
            inspect: () => current.current.onInspect(),
          });
          engine.current.setData(
            current.current.points,
            current.current.selected,
          );
          engine.current.setComparison?.(current.current.comparison);
        } catch (error) {
          console.error("OrbitIQ globe initialization failed", error);
          if (!cancelled) setStatus("failed");
        }
      })
      .catch((error: unknown) => {
        window.clearTimeout(timeout);
        console.error("OrbitIQ globe module failed to load", error);
        if (!cancelled) setStatus("failed");
      });
    return () => {
      cancelled = true;
      window.clearTimeout(timeout);
      engine.current?.dispose();
      engine.current = null;
    };
  }, [attempt]);
  const unavailable = typeof window.WebGL2RenderingContext === "undefined";
  const ready = status === "ready" && !unavailable;
  const compatible = points.length > 0 && points.every(canRenderPoint);
  const paired =
    comparison.length === 2 &&
    comparison.every(canRenderPoint) &&
    comparison[0].at === comparison[1].at;
  const button = (label: string, action: CameraAction) => (
    <button
      type="button"
      disabled={!ready}
      onClick={() => engine.current?.camera(action)}
    >
      {label}
    </button>
  );
  return (
    <section className="globe-card" aria-label="Interactive 3D Earth explorer">
      <div className="globe-topline">
        <span className="eyebrow">EARTH-FIXED EXPLORER</span>
        <span>ITRS · WGS84</span>
      </div>
      <div
        ref={host}
        className="globe-canvas"
        hidden={!ready}
        data-testid="globe-host"
      />
      {!ready && (
        <div className="globe-fallback" role="status">
          {unavailable || status === "failed"
            ? paired
              ? "3D graphics are unavailable. The numerical comparison and source metadata remain usable."
              : "3D graphics are unavailable. The 2D map, timeline and coordinate information remain usable."
            : status === "lost"
              ? paired
                ? "Graphics context lost. Numerical comparison remains available; retry 3D."
                : "Graphics context lost. Use the 2D map and information, or retry 3D."
              : "Loading the 3D Earth…"}
        </div>
      )}
      {!unavailable && (status === "failed" || status === "lost") && (
        <button
          type="button"
          onClick={() => {
            setStatus("loading");
            setAttempt((x) => x + 1);
          }}
        >
          Retry 3D
        </button>
      )}
      <div
        className="toolbar camera-controls"
        role="group"
        aria-label="Globe camera controls"
      >
        {button("Rotate left", "left")}
        {button("Rotate right", "right")}
        {button("Tilt up", "up")}
        {button("Tilt down", "down")}
        {button("Zoom in", "in")}
        {button("Zoom out", "out")}
        {button("Reset camera", "reset")}
        <button
          type="button"
          disabled={!ready || (!compatible && !paired)}
          onClick={() => engine.current?.camera("focus")}
        >
          {paired ? "Focus source A" : "Focus satellite"}
        </button>
        <button type="button" disabled={!compatible} onClick={onInspect}>
          Inspect satellite
        </button>
      </div>
      {!paired && (
        <p className="globe-legend">
          <span className="legend-satellite">●</span> Calculated satellite{" "}
          <span className="legend-ground">●</span> Surface track{" "}
          <span>○ Selected surface point</span>
        </p>
      )}
      {paired && (
        <p className="comparison-legend">
          A: snapshot #{comparison[0].snapshot_id} · sphere. B: snapshot #
          {comparison[1].snapshot_id} · diamond. Two calculated ITRS states at{" "}
          {comparison[0].at}; no connecting trajectory. Markers may overlap and
          their sizes are illustrative.
        </p>
      )}
      {!compatible && !paired && (
        <p className="notice">
          No validated ITRS position is available for a marker. Load a track to
          inspect calculated samples.
        </p>
      )}
      <p className="visual-note">
        Drag to rotate; scroll or pinch to zoom. Camera buttons and arrow keys
        provide keyboard navigation. Positions use one Earth-relative distance
        scale; marker size and the slightly lifted surface overlay are
        illustrative. Lighting and the static Earth image do not represent the
        selected date.
      </p>
      <details>
        <summary>Earth image credit</summary>
        <p>
          Three.js examples, MIT license.{" "}
          <a href="/assets/THREE-LICENSE.txt">Asset license</a>. Static
          geographic illustration.
        </p>
      </details>
    </section>
  );
}
