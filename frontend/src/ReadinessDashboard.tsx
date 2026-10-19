import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { getReadiness, readinessKeys } from "./readiness-api";
import type { ReadinessComponent, ReadinessResult } from "./readiness-api";
import { formatUtc } from "./time-presentation";
const titles = {
  database: "Database availability",
  orbital_data: "Orbital snapshot freshness",
  eop: "Earth orientation",
  leap_seconds: "Leap seconds",
};
function text(v: unknown): string | undefined {
  return typeof v === "string" ? v : undefined;
}
function numeric(v: unknown, unit: string) {
  return typeof v === "number" && Number.isFinite(v)
    ? `${v.toFixed(2)} ${unit}`
    : "Unknown";
}
function moment(v: unknown) {
  return formatUtc(text(v));
}
function Details({
  type,
  data,
}: {
  type: (typeof readinessKeys)[number];
  data: ReadinessComponent;
}) {
  if (type === "database")
    return (
      <dl className="readiness-facts">
        <dt>Reachable</dt>
        <dd>
          {data.reachable === true
            ? "Yes"
            : data.reachable === false
              ? "No"
              : "Unknown"}
        </dd>
        <dt>Schema / metadata reads</dt>
        <dd>
          {data.schema_available === true && data.reads_available === true
            ? "Available"
            : "Unavailable or unknown"}
        </dd>
        <dt>Latest stored snapshot retrieval</dt>
        <dd>{moment(data.latest_stored_retrieved_at)}</dd>
        <dt>Separate insertion timestamp</dt>
        <dd>Not recorded</dd>
      </dl>
    );
  if (type === "orbital_data") {
    const f =
      typeof data.freshness === "object" && data.freshness !== null
        ? (data.freshness as Record<string, unknown>)
        : {};
    return (
      <dl className="readiness-facts">
        <dt>Stored data</dt>
        <dd>
          {data.snapshots_present === true
            ? "Snapshots present"
            : data.snapshots_present === false
              ? "No snapshots"
              : "Unknown"}
        </dd>
        <dt>Global latest retrieval</dt>
        <dd>
          {data.global_latest_known === false
            ? "Unknown — bounded history assessment"
            : moment(data.latest_retrieval_at)}
        </dd>
        <dt>Source element epoch</dt>
        <dd>{moment(data.orbital_epoch)}</dd>
        <dt>Element age</dt>
        <dd>{numeric(f.epoch_age_seconds, "seconds")}</dd>
        <dt>Retrieval age</dt>
        <dd>{numeric(data.retrieval_age_seconds, "seconds")}</dd>
        <dt>Epoch-age category</dt>
        <dd>{text(f.state) ?? "Unknown"}</dd>
        <dt>Fresh / stale thresholds</dt>
        <dd>
          {numeric(f.fresh_hours, "hours")} / {numeric(f.stale_hours, "hours")}
        </dd>
        <dt>Ingestion failure history</dt>
        <dd>Not recorded; absence is not evidence of successful ingestion</dd>
      </dl>
    );
  }
  if (type === "eop") {
    const m =
      typeof data.maintenance === "object" && data.maintenance !== null
        ? (data.maintenance as Record<string, unknown>)
        : {};
    return (
      <dl className="readiness-facts">
        <dt>Source / version</dt>
        <dd>
          {text(data.source) ?? "Unknown"} ·{" "}
          {text(data.package_version) ?? "Unknown"}
        </dd>
        <dt>Coverage starts</dt>
        <dd>{moment(data.first_covered_at)}</dd>
        <dt>Coverage ends</dt>
        <dd>{moment(data.last_covered_at)}</dd>
        <dt>First predicted region</dt>
        <dd>{moment(data.prediction_starts_at)}</dd>
        <dt>Requested epoch coverage</dt>
        <dd>
          {data.covered === true
            ? "Inside file range; support and policy checks also apply"
            : data.covered === false
              ? "Outside or unusable"
              : "Unknown"}
        </dd>
        <dt>Requested EOP type</dt>
        <dd>{text(data.requested_eop_type) ?? "Unavailable or unknown"}</dd>
        <dt>Prediction-region age / limit</dt>
        <dd>
          {numeric(data.prediction_table_age_days, "days")} /{" "}
          {numeric(data.max_prediction_table_age_days, "days")}
        </dd>
        <dt>Package release age</dt>
        <dd>Unknown — release timestamp is not recorded</dd>
        <dt>Last controlled acquisition</dt>
        <dd>{moment(m.acquired_at)}</dd>
        <dt>Last verified / selected</dt>
        <dd>
          {moment(m.verified_at)} / {moment(m.activated_at)}
        </dd>
        <dt>Resource SHA-256</dt>
        <dd className="hash">{text(data.sha256) ?? "Unknown"}</dd>
      </dl>
    );
  }
  return (
    <dl className="readiness-facts">
      <dt>Source / version</dt>
      <dd>
        {text(data.source) ?? "Unknown"} ·{" "}
        {text(data.package_version) ?? "Unknown"}
      </dd>
      <dt>Effective expiry cutoff (UTC)</dt>
      <dd>
        {data.expiry_known === true
          ? moment(data.expires_at)
          : "Unknown — validity cannot be asserted"}
      </dd>
      <dt>Source expiry label / scale</dt>
      <dd>
        {text(data.source_expiry_label) ?? "Unknown"} /{" "}
        {text(data.source_expiry_scale) ?? "Unknown"}
      </dd>
      <dt>Time until expiry</dt>
      <dd>{numeric(data.expires_in_days, "days")}</dd>
      <dt>Resource SHA-256</dt>
      <dd className="hash">{text(data.sha256) ?? "Unknown"}</dd>
    </dl>
  );
}
export default function ReadinessDashboard({
  onExplore,
}: {
  onExplore: () => void;
}) {
  const [target, setTarget] = useState("");
  const [result, setResult] = useState<ReadinessResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const active = useRef<AbortController | null>(null);
  useEffect(() => {
    const c = new AbortController();
    active.current = c;
    getReadiness("", c.signal)
      .then((r) => {
        if (!c.signal.aborted) setResult(r);
      })
      .catch(() => {
        if (!c.signal.aborted)
          setError(
            "Readiness API could not be reached. Check the backend and retry.",
          );
      })
      .finally(() => {
        if (!c.signal.aborted) setLoading(false);
      });
    return () => active.current?.abort();
  }, []);
  async function refresh(e: FormEvent) {
    e.preventDefault();
    active.current?.abort();
    setResult(null);
    setError("");
    if (target && formatUtc(target) === "Unavailable") {
      setLoading(false);
      setError(
        "Enter an ISO timestamp with timezone or leave it empty for the assessment time.",
      );
      return;
    }
    const c = new AbortController();
    active.current = c;
    setLoading(true);
    try {
      const r = await getReadiness(target, c.signal);
      if (!c.signal.aborted) setResult(r);
    } catch (e) {
      if (!c.signal.aborted)
        setError(
          e instanceof Error ? e.message : "Readiness request failed. Retry.",
        );
    } finally {
      if (!c.signal.aborted) setLoading(false);
    }
  }
  return (
    <section className="readiness" aria-labelledby="readiness-title">
      <h2 id="readiness-title">Scientific-data readiness</h2>
      <p>
        A calculated assessment of resources and stored metadata, not a current
        satellite observation, orbit-accuracy measurement or liveness check.
      </p>
      <button type="button" onClick={onExplore}>
        Return to satellite explorer
      </button>
      <form className="controls" onSubmit={refresh}>
        <label>
          Calculation time to assess (optional, UTC or offset)
          <input
            value={target}
            onChange={(e) => {
              active.current?.abort();
              setResult(null);
              setError("");
              setLoading(false);
              setTarget(e.target.value);
            }}
            spellCheck={false}
          />
        </label>
        <button type="submit">Refresh readiness</button>
      </form>
      {loading && <p role="status">Assessing scientific resources…</p>}
      {error && <p role="alert">{error}</p>}
      {!loading && !error && !result && (
        <p role="status">Refresh to assess this requested time.</p>
      )}
      {result && (
        <>
          <div className="readiness-summary" role="status">
            <strong>Overall readiness: {result.status}</strong>
            <p>Last status refresh: {formatUtc(result.evaluated_at)}</p>
            <p>Requested calculation time: {formatUtc(result.requested_at)}</p>
            <p>{result.scope}</p>
          </div>
          <div className="readiness-grid">
            {readinessKeys.map((key) => (
              <section
                className="readiness-card"
                key={key}
                aria-labelledby={`readiness-${key}`}
              >
                <h3 id={`readiness-${key}`}>{titles[key]}</h3>
                <p
                  className={`readiness-badge status-${result.components[key].status}`}
                >
                  Status: <strong>{result.components[key].status}</strong>
                </p>
                <p>{result.components[key].message}</p>
                <Details type={key} data={result.components[key]} />
              </section>
            ))}
          </div>
          <p>
            Maintenance is an explicit operator action. This read-only page does
            not update resources. Unknown or stale current data may still permit
            supported historical calculations; each calculation enforces its own
            strict checks.
          </p>
        </>
      )}
    </section>
  );
}
