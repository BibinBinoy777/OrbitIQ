import { useEffect, useId, useRef, useState } from "react";
import GroundTrack from "./GroundTrack";
import Globe from "./Globe";
import type { FormEvent } from "react";
import { getPosition, getSnapshots } from "./scientific-api";
import type { PositionResult, SnapshotSummary } from "./scientific-api";
import { formatUtc } from "./time-presentation";
import InvestigationActions from "./InvestigationActions";
import {
  canonicalTime,
  snapshotInvestigation,
  sourceReference,
  verifySource,
} from "./saved-investigation";
import type { Investigation } from "./saved-investigation";
export { formatUtc } from "./time-presentation";

function message(error: unknown): string {
  return error instanceof Error ? error.message : "Request failed";
}
function sourceLink(value?: string): string | undefined {
  try {
    const url = new URL(value ?? "");
    return url.protocol === "https:" &&
      ["celestrak.org", "www.celestrak.org"].includes(url.hostname) &&
      !url.username &&
      !url.password
      ? url.href
      : undefined;
  } catch {
    return undefined;
  }
}
const labels = {
  fresh: "Fresh",
  aging: "Aging",
  stale: "Stale",
  unknown: "Unknown",
  future_epoch: "Future epoch",
};
export default function ScientificExplorer({
  initialSource,
  initialInvestigation,
  readOnly = false,
  active = true,
}: {
  initialSource?: SnapshotSummary;
  initialInvestigation?: Investigation;
  readOnly?: boolean;
  active?: boolean;
} = {}) {
  const headingId = useId();
  const [catalog, setCatalog] = useState(
    initialSource ? String(initialSource.catalog_id) : "25544",
  );
  const [snapshots, setSnapshots] = useState<SnapshotSummary[] | null>(
    initialSource ? [initialSource] : null,
  );
  const [selectedId, setSelectedId] = useState<number | null>(
    initialSource?.id ?? null,
  );
  const [at, setAt] = useState(
    initialInvestigation?.mode === "position"
      ? initialInvestigation.at
      : (initialSource?.orbital_epoch ?? ""),
  );
  const [loading, setLoading] = useState(false);
  const [calculating, setCalculating] = useState(
    initialInvestigation?.mode === "position",
  );
  const [loadError, setLoadError] = useState("");
  const [historyNotice, setHistoryNotice] = useState("");
  const [calculationError, setCalculationError] = useState("");
  const [position, setPosition] = useState<PositionResult | null>(null);
  const listRequest = useRef<AbortController | null>(null);
  const positionRequest = useRef<AbortController | null>(null);
  useEffect(() => {
    if (initialInvestigation?.mode !== "position" || !initialSource) return;
    const c = new AbortController();
    positionRequest.current = c;
    getPosition(initialSource.id, initialInvestigation.at, c.signal)
      .then((result) => {
        verifySource(initialInvestigation.source, {
          ...result,
          id: result.snapshot_id,
        });
        if (canonicalTime(result.at) !== initialInvestigation.at)
          throw new Error(
            "Restored calculation time does not match the requested time.",
          );
        if (!c.signal.aborted) setPosition(result);
      })
      .catch((e) => {
        if (!c.signal.aborted) setCalculationError(message(e));
      })
      .finally(() => {
        if (!c.signal.aborted) setCalculating(false);
      });
    return () => c.abort();
  }, [initialInvestigation, initialSource]);
  useEffect(
    () => () => {
      listRequest.current?.abort();
      positionRequest.current?.abort();
    },
    [],
  );
  const selected = snapshots?.find((s) => s.id === selectedId);
  const state = selected?.freshness_info?.state ?? "unknown";
  const href = sourceLink(selected?.source_url);
  function clearCalculation() {
    positionRequest.current?.abort();
    setCalculating(false);
    setPosition(null);
    setCalculationError("");
  }
  async function load(event: FormEvent) {
    event.preventDefault();
    listRequest.current?.abort();
    clearCalculation();
    setLoadError("");
    setHistoryNotice("");
    setSnapshots(null);
    setSelectedId(null);
    setAt("");
    const id = Number(catalog);
    if (!/^\d{1,6}$/.test(catalog) || id < 1 || id > 339999) {
      setLoading(false);
      setLoadError("Enter a catalog ID from 1 to 339999.");
      return;
    }
    const controller = new AbortController();
    listRequest.current = controller;
    setLoading(true);
    try {
      const items = await getSnapshots(id, controller.signal);
      if (!controller.signal.aborted) {
        const retained = selected?.catalog_id === id ? selected : undefined;
        const onPage = retained && items.find((s) => s.id === retained.id);
        const chosen = onPage || retained || items[0];
        setSnapshots(retained && !onPage ? [...items, retained] : items);
        setSelectedId(chosen?.id ?? null);
        setAt(retained ? at : (chosen?.orbital_epoch ?? ""));
        if (retained && !onPage)
          setHistoryNotice(
            "The selected historical source is retained separately from this bounded history page. Detail and calculation requests recheck its availability.",
          );
      }
    } catch (error) {
      if (!controller.signal.aborted) setLoadError(message(error));
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
  }
  async function calculate(event: FormEvent) {
    event.preventDefault();
    if (!selected) return;
    clearCalculation();
    const controller = new AbortController();
    positionRequest.current = controller;
    setCalculating(true);
    try {
      const result = await getPosition(selected.id, at, controller.signal);
      if (
        result.catalog_id !== selected.catalog_id ||
        (selected.response_sha256 &&
          result.response_sha256 !== selected.response_sha256)
      ) {
        throw new Error(
          "Calculation source does not match the selected snapshot",
        );
      }
      if (!controller.signal.aborted) setPosition(result);
    } catch (error) {
      if (!controller.signal.aborted) setCalculationError(message(error));
    } finally {
      if (!controller.signal.aborted) setCalculating(false);
    }
  }
  return (
    <section className="science" aria-labelledby={headingId}>
      <h2 id={headingId}>Stored orbital data</h2>
      <p>
        Inspect source snapshots and calculate a position on the backend. Search
        stored data by NORAD catalog ID. This is not a global catalog search;
        loading snapshots does not download new orbital elements.
      </p>
      <form onSubmit={load} className="controls">
        <fieldset className="controls input-boundary" disabled={readOnly}>
          <label>
            Catalog ID
            <input
              inputMode="numeric"
              value={catalog}
              onChange={(e) => setCatalog(e.target.value)}
              required
            />
          </label>
          <button type="submit">Load snapshots</button>
        </fieldset>
      </form>
      {loading && <p role="status">Loading saved snapshots…</p>}
      {loadError && <p role="alert">Snapshot load failed: {loadError}</p>}
      {historyNotice && <p className="notice">{historyNotice}</p>}
      {snapshots?.length === 0 && (
        <p role="status">
          No stored snapshots for this catalog ID. No current data is available.
        </p>
      )}
      {!selected && <Globe />}
      {selected && (
        <>
          <label>
            Saved snapshot
            <select
              disabled={readOnly}
              value={selectedId ?? ""}
              onChange={(e) => {
                const id = Number(e.target.value);
                clearCalculation();
                setHistoryNotice("");
                setSelectedId(id);
                setAt(snapshots?.find((s) => s.id === id)?.orbital_epoch ?? "");
              }}
            >
              {snapshots?.map((s, index) => (
                <option key={s.id} value={s.id}>
                  Snapshot #{s.id} ·{" "}
                  {index === 0
                    ? "Newest insertion on this page"
                    : "Stored historical record"}
                </option>
              ))}
            </select>
          </label>
          <h3>
            {selected.object_name ?? "Unnamed object"} · Catalog{" "}
            {selected.catalog_id}
          </h3>
          <p className={`freshness ${state}`}>
            Element freshness: <strong>{labels[state]}</strong>
          </p>
          {state !== "fresh" && (
            <p className="notice">
              {state === "stale"
                ? "Stale orbital elements: treat this as historical input."
                : state === "aging"
                  ? "Aging orbital elements: predictions have unquantified limitations."
                  : "Element age is unknown or its epoch is in the future."}
            </p>
          )}
          <p>
            Latest stored does not mean current or accurate. Recent retrieval
            does not refresh an older orbital epoch.
          </p>
          <InvestigationActions
            readOnly={readOnly}
            build={() =>
              position
                ? {
                    schema_version: 1,
                    mode: "position",
                    source: sourceReference(selected),
                    frame: "TEME",
                    at: canonicalTime(position.at),
                  }
                : snapshotInvestigation(selected)
            }
          />
          <GroundTrack
            key={selected.id}
            source={selected}
            initialTime={selected.orbital_epoch ?? ""}
            initialInvestigation={
              initialInvestigation?.mode === "ground-track"
                ? initialInvestigation
                : undefined
            }
            readOnly={readOnly}
            active={active}
          />
          <details
            className="source-details"
            open={initialInvestigation?.mode === "position" ? true : undefined}
          >
            <summary>Source provenance and TEME inspection</summary>
            <dl className="metadata">
              <dt>Orbital epoch</dt>
              <dd>{formatUtc(selected.orbital_epoch)}</dd>
              <dt>First retrieved</dt>
              <dd>{formatUtc(selected.retrieved_at)}</dd>
              <dt>Age evaluated</dt>
              <dd>{formatUtc(selected.freshness_info?.evaluated_at)}</dd>
              <dt>Snapshot creation time</dt>
              <dd>
                {selected.snapshot_created_at
                  ? formatUtc(selected.snapshot_created_at)
                  : "Not recorded separately for this legacy source"}
              </dd>
              <dt>Source frame</dt>
              <dd>
                {selected.frame === "TEME"
                  ? "TEME · Earth-centered"
                  : "Unknown / unsupported"}
              </dd>
              <dt>Source</dt>
              <dd>
                {href ? (
                  <a href={href} target="_blank" rel="noreferrer">
                    CelesTrak GP record
                  </a>
                ) : (
                  "Unavailable"
                )}
              </dd>
              <dt>Snapshot #{selected.id} SHA-256</dt>
              <dd className="hash">
                {/^[a-f0-9]{64}$/.test(selected.response_sha256 ?? "")
                  ? selected.response_sha256
                  : "Unavailable"}
              </dd>
              <dt>Input validation</dt>
              <dd>
                {selected.validation_status ===
                "structural_and_epoch_propagation_passed"
                  ? "Format and epoch propagation checks passed; not observational accuracy."
                  : "Unavailable"}
              </dd>
            </dl>
            <form onSubmit={calculate} className="controls">
              <fieldset className="controls input-boundary" disabled={readOnly}>
                <label>
                  Requested propagation time (UTC or explicit offset)
                  <input
                    value={at}
                    onChange={(e) => {
                      clearCalculation();
                      setAt(e.target.value);
                    }}
                    required
                    spellCheck={false}
                  />
                </label>
                <button type="submit" disabled={!at || calculating}>
                  Calculate position
                </button>
              </fieldset>
            </form>
            <p>
              Time must include a timezone and be within ±7 days of this
              snapshot’s epoch. This position calculation returns TEME;
              Earth-fixed tracks are available below.
            </p>
            {calculating && (
              <p role="status">Calculating backend SGP4 state…</p>
            )}
            {calculationError && (
              <p role="alert">Calculation failed: {calculationError}</p>
            )}
            {position && (
              <div className="result" aria-label="Calculated orbital state">
                <h3>Calculated position · {position.frame}</h3>
                <p>
                  Not a direct observation. Uncertainty is not quantified; no
                  collision or safety conclusion is provided.
                </p>
                <dl className="metadata">
                  <dt>Requested time</dt>
                  <dd>{formatUtc(position.at)}</dd>
                  <dt>Calculated at</dt>
                  <dd>{formatUtc(position.calculated_at)}</dd>
                  <dt>Result orbital epoch</dt>
                  <dd>{formatUtc(position.orbital_epoch)}</dd>
                  <dt>Result source retrieval</dt>
                  <dd>{formatUtc(position.retrieved_at)}</dd>
                  <dt>Model</dt>
                  <dd>
                    SGP4 / WGS72 · library{" "}
                    {position.sgp4_version ?? "Unavailable"}
                  </dd>
                  <dt>Calculation validation scope</dt>
                  <dd>
                    {position.validation_status ===
                    "reference_tested_engine_not_observation_validated"
                      ? "Published reference cases tested; this orbit is not observation-validated."
                      : "Validation metadata unavailable"}
                  </dd>
                  <dt>Result source SHA-256</dt>
                  <dd className="hash">
                    {position.response_sha256 ?? "Unavailable"}
                  </dd>
                </dl>
                <table>
                  <caption>
                    TEME Cartesian vectors, Earth center. Not Earth-fixed
                    coordinates.
                  </caption>
                  <thead>
                    <tr>
                      <th scope="col">Axis</th>
                      <th scope="col">Position (km)</th>
                      <th scope="col">Velocity (km/s)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {["x", "y", "z"].map((axis, i) => (
                      <tr key={axis}>
                        <th scope="row">{axis}</th>
                        <td>{position.position_km[i].toFixed(3)}</td>
                        <td>{position.velocity_km_s[i].toFixed(6)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p>
                  Values are rounded for display. Displayed precision is not
                  prediction accuracy.
                </p>
                {position.warnings.length > 0 && (
                  <ul>
                    {position.warnings.map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </details>
        </>
      )}
    </section>
  );
}
