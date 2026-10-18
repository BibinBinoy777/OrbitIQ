import { useCallback, useEffect, useId, useState } from "react";
import type { TrackPoint } from "./ground-track-api";
import useReducedMotion from "./use-reduced-motion";
import { formatUtc } from "./time-presentation";
export default function Timeline({
  points,
  index,
  onSelect,
}: {
  points: TrackPoint[];
  index: number;
  onSelect: (index: number) => void;
}) {
  const [playing, setPlaying] = useState(false);
  const pause = useCallback(() => setPlaying(false), []);
  const reduced = useReducedMotion(pause);
  const sliderId = useId();
  useEffect(() => {
    if (!playing || reduced) return;
    const timer = window.setTimeout(() => {
      if (index >= points.length - 1) setPlaying(false);
      else {
        onSelect(index + 1);
        if (index + 1 >= points.length - 1) setPlaying(false);
      }
    }, 1000);
    return () => window.clearTimeout(timer);
  }, [playing, reduced, index, points.length, onSelect]);
  useEffect(() => {
    const hide = () => {
      if (document.hidden) setPlaying(false);
    };
    document.addEventListener("visibilitychange", hide);
    return () => document.removeEventListener("visibilitychange", hide);
  }, []);
  function select(value: number) {
    setPlaying(false);
    onSelect(value);
  }
  return (
    <section className="timeline" aria-label="Orbital timeline">
      <div className="timeline-header">
        <h4>Orbital timeline</h4>
        <span>
          {index + 1} / {points.length} samples
        </span>
      </div>
      <p className="selected-time" role="status" aria-live="polite">
        Selected time: {formatUtc(points[index]?.at)}
      </p>
      <label htmlFor={sliderId}>Calculated sample</label>
      <input
        id={sliderId}
        type="range"
        min="0"
        max={points.length - 1}
        step="1"
        value={index}
        aria-valuetext={formatUtc(points[index]?.at)}
        onChange={(e) => select(Number(e.target.value))}
      />
      <div className="toolbar">
        <button
          type="button"
          disabled={index === 0}
          onClick={() => select(index - 1)}
        >
          Previous sample
        </button>
        <button
          type="button"
          disabled={reduced || points.length < 2 || index >= points.length - 1}
          aria-pressed={playing && !reduced}
          onClick={() => setPlaying(!playing)}
        >
          {playing && !reduced ? "Pause" : "Play"}
        </button>
        <button
          type="button"
          disabled={index >= points.length - 1}
          onClick={() => select(index + 1)}
        >
          Next sample
        </button>
        <button type="button" onClick={() => select(0)}>
          Reset timeline
        </button>
      </div>
      <p>
        {reduced
          ? "Reduced motion: playback is disabled; use the sample controls."
          : "Playback advances one calculated sample each second and stops at the end."}{" "}
        No interpolated positions or playback API requests.
      </p>
    </section>
  );
}
