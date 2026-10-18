import { useEffect, useRef, useState } from "react";
import type { TrackPoint } from "./ground-track-api";
import type { GlobeEngine, CameraAction } from "./globe-renderer";
import { canRenderPoint } from "./globe-geometry";
const EMPTY: TrackPoint[] = [];
export default function Globe({
  points = EMPTY,
  selected = 0,
  onInspect = () => {},
}: {
  points?: TrackPoint[];
  selected?: number;
  onInspect?: () => void;
}) {
  const host = useRef<HTMLDivElement>(null),
    engine = useRef<GlobeEngine | null>(null);
  const current = useRef({ points, selected, onInspect });
  useEffect(() => {
    current.current = { points, selected, onInspect };
    engine.current?.setData(points, selected);
  }, [points, selected, onInspect]);
  const [status, setStatus] = useState<"loading" | "ready" | "failed" | "lost">(
    "loading",
  );
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let cancelled = false;
    if (typeof window.WebGL2RenderingContext === "undefined") return;
    import("./globe-renderer")
      .then(({ createGlobe }) => {
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
        } catch {
          if (!cancelled) setStatus("failed");
        }
      })
      .catch(() => {
        if (!cancelled) setStatus("failed");
      });
    return () => {
      cancelled = true;
      engine.current?.dispose();
      engine.current = null;
    };
  }, [attempt]);
  const unavailable = typeof window.WebGL2RenderingContext === "undefined";
  const ready = status === "ready" && !unavailable;
  const compatible = points.length > 0 && points.every(canRenderPoint);
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
            ? "3D graphics are unavailable. The 2D map, timeline and coordinate information remain usable."
            : status === "lost"
              ? "Graphics context lost. Use the 2D map and information, or retry 3D."
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
          disabled={!ready || !compatible}
          onClick={() => engine.current?.camera("focus")}
        >
          Focus satellite
        </button>
        <button type="button" disabled={!compatible} onClick={onInspect}>
          Inspect satellite
        </button>
      </div>
      <p className="globe-legend">
        <span className="legend-satellite">●</span> Calculated satellite{" "}
        <span className="legend-ground">●</span> Surface track{" "}
        <span>○ Selected surface point</span>
      </p>
      {!compatible && (
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
