import { useEffect, useId, useRef, useState } from "react";
import Globe from "./Globe";
import Timeline from "./Timeline";
import SatelliteInfo from "./SatelliteInfo";
import type { FormEvent } from "react";
import { getGroundTrack } from "./ground-track-api";
import type { GroundTrackResult, TrackPoint } from "./ground-track-api";
import type { SnapshotSummary } from "./scientific-api";
import { formatUtc } from "./time-presentation";

export function TrackMap({
  points,
  selected,
}: {
  points: TrackPoint[];
  selected: number;
}) {
  const segments: TrackPoint[][] = [];
  for (const point of points) {
    const last = segments.at(-1);
    if (
      !last ||
      last.at(-1)?.segment_id !== point.segment_id ||
      Date.parse(point.at) - Date.parse(last.at(-1)!.at) > 300000
    )
      segments.push([point]);
    else last.push(point);
  }
  const point = points[selected];
  return (
    <figure className="track-map">
      <svg
        viewBox="-200 -110 400 220"
        role="img"
        aria-label="Calculated satellite ground track on a longitude and latitude map"
      >
        <title>Calculated ground track · ITRS to WGS84</title>
        <desc>
          East-positive longitude from minus 180 to 180 degrees; latitude from
          minus 90 to 90 degrees. Lines stop at the antimeridian. The
          highlighted point is the selected sample. No observer visibility or
          accuracy is implied.
        </desc>
        <rect
          x="-180"
          y="-90"
          width="360"
          height="180"
          fill="#142039"
          stroke="#6e91b8"
        />
        {[-90, 0, 90].map((x) => (
          <g key={x}>
            <line
              x1={x}
              y1="-90"
              x2={x}
              y2="90"
              stroke="#405873"
              strokeWidth="0.5"
            />
            <text x={x} y="103" textAnchor="middle">
              {x}°
            </text>
          </g>
        ))}
        {[-45, 0, 45].map((lat) => (
          <g key={lat}>
            <line
              x1="-180"
              y1={-lat}
              x2="180"
              y2={-lat}
              stroke="#405873"
              strokeWidth="0.5"
            />
            <text x="-184" y={-lat + 3} textAnchor="end">
              {lat}°
            </text>
          </g>
        ))}
        {segments.map((s, i) => (
          <polyline
            key={i}
            data-testid="track-segment"
            points={s
              .map(
                (p) =>
                  `${p.geodetic.longitude_deg},${-p.geodetic.latitude_deg}`,
              )
              .join(" ")}
            fill="none"
            stroke="#b6d8ff"
            strokeWidth="1.3"
          />
        ))}
        {points.map((p, i) => (
          <circle
            key={i}
            cx={p.geodetic.longitude_deg}
            cy={-p.geodetic.latitude_deg}
            r="0.7"
            fill="#b6d8ff"
          />
        ))}
        {point && (
          <circle
            cx={point.geodetic.longitude_deg}
            cy={-point.geodetic.latitude_deg}
            r="3"
            fill="#ffd782"
            stroke="#0c1424"
            strokeWidth="0.8"
          />
        )}
      </svg>
      <figcaption>
        Longitude / latitude graticule · east-positive degrees. Sampled path;
        breaks at ±180°. The highlighted point is selected below.
      </figcaption>
    </figure>
  );
}
export default function GroundTrack({
  source,
  initialTime,
}: {
  source: SnapshotSummary;
  initialTime: string;
}) {
  const infoPanel = useRef<HTMLElement | null>(null);
  const sampleControlId = useId();
  const [start, setStart] = useState(initialTime);
  const [duration, setDuration] = useState("90");
  const [step, setStep] = useState("60");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [track, setTrack] = useState<GroundTrackResult | null>(null);
  const [index, setIndex] = useState(0);
  const active = useRef<AbortController | null>(null);
  useEffect(() => () => active.current?.abort(), []);
  function clear() {
    active.current?.abort();
    setTrack(null);
    setError("");
    setLoading(false);
    setIndex(0);
  }
  async function generate(event: FormEvent) {
    event.preventDefault();
    clear();
    const time = Date.parse(start),
      minutes = Number(duration),
      seconds = Number(step);
    if (
      formatUtc(start) === "Unavailable" ||
      !Number.isFinite(time) ||
      !Number.isInteger(minutes) ||
      minutes < 1 ||
      minutes > 1440 ||
      !Number.isInteger(seconds) ||
      seconds < 10 ||
      seconds > 3600
    ) {
      setError(
        "Use an aware ISO timestamp, duration 1–1440 minutes and step 10–3600 seconds.",
      );
      return;
    }
    // Date is used only for UI interval selection, never orbital calculations.
    // Retain source sub-millisecond digits in the end-time query.
    const fraction = /\.(\d{4,6})(?:Z|[+-]\d{2}:\d{2})$/.exec(start)?.[1];
    let end = new Date(time + minutes * 60000).toISOString();
    if (fraction) end = end.replace(/\.\d{3}Z$/, `.${fraction}Z`);
    const controller = new AbortController();
    active.current = controller;
    setLoading(true);
    try {
      const result = await getGroundTrack(
        source,
        start,
        end,
        seconds,
        controller.signal,
      );
      if (!controller.signal.aborted) setTrack(result);
    } catch (e) {
      if (!controller.signal.aborted)
        setError(
          e instanceof Error ? e.message : "Ground-track request failed",
        );
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
  }
  const selected = track?.points[index];
  return (
    <section className="result" aria-labelledby="track-heading">
      <h3 id="track-heading">Earth-relative ground track</h3>
      <p>
        Calculated from this fixed saved snapshot. Historical intervals are
        supported within ±7 days of its epoch. Source freshness:{" "}
        <strong>{source.freshness_info?.state ?? "unknown"}</strong>.
      </p>
      <form className="controls" onSubmit={generate}>
        <label>
          Track start (UTC or explicit offset)
          <input
            value={start}
            required
            spellCheck={false}
            onChange={(e) => {
              clear();
              setStart(e.target.value);
            }}
          />
        </label>
        <label>
          Duration (minutes)
          <input
            type="number"
            min="1"
            max="1440"
            value={duration}
            required
            onChange={(e) => {
              clear();
              setDuration(e.target.value);
            }}
          />
        </label>
        <label>
          Sample step (seconds)
          <input
            type="number"
            min="10"
            max="3600"
            value={step}
            required
            onChange={(e) => {
              clear();
              setStep(e.target.value);
            }}
          />
        </label>
        <button
          type="button"
          onClick={() => {
            clear();
            setStart(initialTime);
            setDuration("90");
            setStep("60");
          }}
        >
          Reset track window
        </button>
        <button disabled={loading} type="submit">
          Generate ground track
        </button>
      </form>
      <p>
        Default limits: 361 samples and 24 hours; step 10–3600 seconds. Any
        failed sample rejects the entire request. Only aligned times through the
        requested end are included.
      </p>
      {loading && <p role="status">Generating backend ground track…</p>}
      {error && <p role="alert">Ground track unavailable: {error}</p>}
      {!track && !loading && !error && <p>No ground track calculated yet.</p>}
      <div className="explorer-grid">
        <div className="earth-workspace">
          <Globe
            points={track?.points}
            selected={index}
            onInspect={() => infoPanel.current?.focus()}
          />
          {track && (
            <Timeline
              key={track.actual_start + track.actual_end}
              points={track.points}
              index={index}
              onSelect={setIndex}
            />
          )}
        </div>
        <SatelliteInfo source={source} point={selected} panelRef={infoPanel} />
      </div>
      {track && selected && (
        <div aria-label="Calculated ground-track result">
          <h4>
            {track.points.length} calculated samples · TEME → ITRS → WGS84
          </h4>
          <p>
            Not direct observations. Prediction uncertainty is not quantified.
            Lines between samples do not establish visibility, collision risk or
            orbital safety.
          </p>
          <TrackMap points={track.points} selected={index} />
          <label htmlFor={sampleControlId}>Selected track sample</label>
          <select
            id={sampleControlId}
            value={index}
            onChange={(e) => setIndex(Number(e.target.value))}
          >
            {track.points.map((p, i) => (
              <option key={p.at} value={i}>
                {i + 1} · {formatUtc(p.at)}
              </option>
            ))}
          </select>
          <dl className="metadata">
            <dt>Selected propagation time</dt>
            <dd>{formatUtc(selected.at)}</dd>
            <dt>Track orbital epoch</dt>
            <dd>{formatUtc(track.orbital_epoch)}</dd>
            <dt>Track source retrieval</dt>
            <dd>{formatUtc(track.retrieved_at)}</dd>
            <dt>Requested interval</dt>
            <dd>
              {formatUtc(track.requested_start)} through{" "}
              {formatUtc(track.requested_end)}
            </dd>
            <dt>Actual sample interval</dt>
            <dd>
              {formatUtc(track.actual_start)} through{" "}
              {formatUtc(track.actual_end)} · step {track.step_seconds} s
            </dd>
            <dt>Transformation status</dt>
            <dd>
              {selected.transformation_status === "predicted_eop"
                ? "Completed using predicted EOP"
                : "Completed using measured EOP"}
              ; no degraded fallback
            </dd>
            <dt>Earth-orientation data</dt>
            <dd>
              {selected.earth_orientation.status} ·{" "}
              {selected.earth_orientation.source} ·{" "}
              {selected.earth_orientation.package_version}
            </dd>
            <dt>EOP policy</dt>
            <dd>
              {selected.earth_orientation.policy} · local data, automatic
              downloads disabled
            </dd>
            <dt>EOP SHA-256</dt>
            <dd className="hash">{selected.earth_orientation.sha256}</dd>
            <dt>Track source</dt>
            <dd>
              Catalog {track.catalog_id} · snapshot #{track.snapshot_id}
            </dd>
            <dt>Track source SHA-256</dt>
            <dd className="hash">{track.response_sha256}</dd>
          </dl>
          <table>
            <caption>
              Selected calculated point · WGS84 ellipsoid, angles in degrees
            </caption>
            <thead>
              <tr>
                <th scope="col">Latitude (°)</th>
                <th scope="col">Longitude (° east)</th>
                <th scope="col">Height (km)</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>{selected.geodetic.latitude_deg.toFixed(5)}</td>
                <td>{selected.geodetic.longitude_deg.toFixed(5)}</td>
                <td>{selected.geodetic.altitude_km.toFixed(3)}</td>
              </tr>
            </tbody>
          </table>
          <p>
            Height is above the WGS84 ellipsoid, not terrain or mean sea level.
            Display rounding does not indicate accuracy.
          </p>
          <ul>
            {[...track.warnings, ...selected.warnings].map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
