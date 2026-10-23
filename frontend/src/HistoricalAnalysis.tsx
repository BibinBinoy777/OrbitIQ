import { useEffect, useId, useRef, useState } from "react";
import type { FormEvent } from "react";
import { getHistory } from "./history-api";
import type { HistoricalReport } from "./history-api";
import type { StoredSnapshot } from "./investigation-api";
import { formatUtc } from "./time-presentation";
export default function HistoricalAnalysis({
  onInspect,
  onCompare,
}: {
  onInspect: (s: StoredSnapshot) => void;
  onCompare: (a: number, b: number) => void;
}) {
  const heading = useId(),
    request = useRef<AbortController | null>(null);
  const retryWindow = useRef<{
    params: URLSearchParams;
    back: URLSearchParams[];
  } | null>(null);
  const [catalog, setCatalog] = useState("25544"),
    [size, setSize] = useState("20");
  const [report, setReport] = useState<HistoricalReport | null>(null),
    [error, setError] = useState("");
  const [busy, setBusy] = useState(false),
    [notice, setNotice] = useState("");
  const [params, setParams] = useState(new URLSearchParams({ limit: "20" })),
    [back, setBack] = useState<URLSearchParams[]>([]);
  const [first, setFirst] = useState(""),
    [second, setSecond] = useState("");
  useEffect(() => () => request.current?.abort(), []);
  function clear() {
    retryWindow.current = null;
    request.current?.abort();
    setReport(null);
    setError("");
    setNotice("");
    setBusy(false);
    setBack([]);
  }
  async function load(p: URLSearchParams, previous: URLSearchParams[] = []) {
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    // Capture the attempted window, not just the most recent successful result.
    const attempted = new URLSearchParams(p);
    const previousWindows = previous.map((value) => new URLSearchParams(value));
    retryWindow.current = { params: attempted, back: previousWindows };
    setReport(null);
    setError("");
    setNotice("");
    setBusy(true);
    try {
      if (
        !/^\d{1,6}$/.test(catalog) ||
        Number(catalog) < 1 ||
        Number(catalog) > 339999
      )
        throw new Error("Use a NORAD catalog identifier from 1 to 339999.");
      const value = await getHistory(
        Number(catalog),
        attempted,
        controller.signal,
      );
      if (!controller.signal.aborted) {
        setReport(value);
        const resolved = new URLSearchParams(attempted);
        if (value.pagination.anchor_id !== null)
          resolved.set("anchor_id", String(value.pagination.anchor_id));
        setParams(resolved);
        setBack(previousWindows);
        const ids = value.points
          .filter((x) => x.usable)
          .map((x) => String(x.metadata.id));
        setFirst(ids[0] ?? "");
        setSecond(ids[1] ?? "");
      }
    } catch (e) {
      if (!controller.signal.aborted)
        setError(
          e instanceof Error ? e.message : "Historical analysis failed. Retry.",
        );
    } finally {
      if (!controller.signal.aborted) setBusy(false);
    }
  }
  function submit(e: FormEvent) {
    e.preventDefault();
    void load(new URLSearchParams({ limit: size }));
  }
  function download(value: unknown, filename: string) {
    try {
      const url = URL.createObjectURL(
        new Blob([JSON.stringify(value, null, 2) + "\n"], {
          type: "application/json",
        }),
      );
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.append(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setNotice(
        "Download requested from this captured report; no recalculation or ingestion occurred.",
      );
    } catch {
      setError("Download could not be prepared. Retry.");
    }
  }
  return (
    <section aria-labelledby={heading} className="historical-analysis">
      <h3 id={heading}>Historical change analysis</h3>
      <p>
        Inspect persisted source estimates by NORAD identity. This read-only
        tool never collects data. Each page contains at most 20 records.
      </p>
      <form className="controls" onSubmit={submit}>
        <label>
          Historical satellite NORAD ID
          <input
            inputMode="numeric"
            value={catalog}
            onChange={(e) => {
              setCatalog(e.target.value);
              clear();
            }}
          />
        </label>
        <label>
          Timeline page size
          <select
            value={size}
            onChange={(e) => {
              setSize(e.target.value);
              clear();
            }}
          >
            {[1, 2, 5, 10, 20].map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>
        </label>
        <button type="submit" disabled={busy}>
          Analyze archived history
        </button>
      </form>
      {busy && <p role="status">Analyzing archived records…</p>}
      {error && (
        <p role="alert">
          {error}{" "}
          <button
            type="button"
            onClick={() => {
              const target = retryWindow.current;
              if (target) void load(target.params, target.back);
            }}
          >
            Retry historical analysis
          </button>
        </p>
      )}
      {notice && <p role="status">{notice}</p>}
      {report && (
        <>
          <h4>Historical coverage · NORAD {report.catalog_id}</h4>
          <p className="notice">{report.coverage.summary}</p>
          <p>
            {report.coverage.validated_record_count} provenance-validated
            persisted records in this page; {report.coverage.inspected_count}{" "}
            inspected. Anchored archive count:{" "}
            {report.pagination.total_count ?? "unknown (bounded count)"}{" "}
            metadata records.{" "}
            {report.coverage.complete_anchored_history
              ? "Complete anchored satellite history inspected."
              : "Partial window: other records may be outside this page."}
          </p>
          <p>
            Retrieval span in this window:{" "}
            {formatUtc(
              report.coverage.oldest_verifiable_retrieval ?? undefined,
            )}{" "}
            to{" "}
            {formatUtc(
              report.coverage.newest_verifiable_retrieval ?? undefined,
            )}
            . Order: {report.coverage.chronology}. Generated:{" "}
            {formatUtc(report.generated_at)}.
          </p>
          <nav className="toolbar" aria-label="Historical timeline pages">
            <button
              type="button"
              disabled={!back.length}
              onClick={() =>
                void load(back[back.length - 1], back.slice(0, -1))
              }
            >
              Previous timeline page
            </button>
            <button
              type="button"
              disabled={!report.pagination.has_more || back.length >= 100}
              onClick={() => {
                const p = new URLSearchParams(params);
                p.set("anchor_id", String(report.pagination.anchor_id));
                p.set("before_id", String(report.pagination.next_before_id));
                void load(p, [...back, params]);
              }}
            >
              Next timeline page
            </button>
            <button
              type="button"
              onClick={() => void load(new URLSearchParams({ limit: size }))}
            >
              Refresh history anchor
            </button>
          </nav>
          {back.length >= 100 && (
            <p>Navigation limit reached. Refresh the anchor to restart.</p>
          )}
          <h4>Recorded snapshot timeline</h4>
          <p>
            Only archived points are shown. No intermediate element sets,
            observations, or future trend are inferred. Intervals describe this
            window only.
          </p>
          {!report.points.length && (
            <p>No archived records found for this NORAD identifier.</p>
          )}
          <ol className="history-points">
            {report.points.map((p) => (
              <li key={p.metadata.id}>
                <h5>
                  Snapshot #{p.metadata.id} ·{" "}
                  {p.metadata.object_name ?? "Name unavailable"}
                </h5>
                <dl>
                  <dt>Retrieval time</dt>
                  <dd>{formatUtc(p.metadata.retrieved_at ?? undefined)}</dd>
                  <dt>Element epoch</dt>
                  <dd>{formatUtc(p.metadata.orbital_epoch ?? undefined)}</dd>
                  <dt>Separate insertion time</dt>
                  <dd>
                    {p.metadata.snapshot_created_at
                      ? formatUtc(p.metadata.snapshot_created_at)
                      : "Not recorded (legacy); not inferred"}
                  </dd>
                  <dt>Validation / freshness</dt>
                  <dd>
                    {p.usable
                      ? "Full stored provenance validated"
                      : "Unusable for calculation"}{" "}
                    / {p.freshness.state}
                  </dd>
                  <dt>Payload SHA-256</dt>
                  <dd className="source-hash">
                    {p.metadata.response_sha256 ?? "Unavailable"}
                  </dd>
                  <dt>Provider</dt>
                  <dd>
                    {p.metadata.source_url ? (
                      <a href={p.metadata.source_url}>
                        CelesTrak source for NORAD {report.catalog_id}
                      </a>
                    ) : (
                      "Provenance unavailable"
                    )}
                  </dd>
                </dl>
                {p.elements && (
                  <details>
                    <summary>
                      Inspect archived orbital elements #{p.metadata.id}
                    </summary>
                    <div
                      className="history-table"
                      tabIndex={0}
                      role="region"
                      aria-label={`Snapshot ${p.metadata.id} element values`}
                    >
                      <table>
                        <caption>Actual normalized source fields</caption>
                        <thead>
                          <tr>
                            <th>Field</th>
                            <th>Value</th>
                            <th>Unit</th>
                          </tr>
                        </thead>
                        <tbody>
                          {Object.entries(p.elements).map(([k, v]) => (
                            <tr key={k}>
                              <th scope="row">{k}</th>
                              <td>{String(v)}</td>
                              <td>
                                {p.element_units[k] ??
                                  "Identifier / convention"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </details>
                )}
                <button type="button" onClick={() => onInspect(p.metadata)}>
                  Open existing snapshot detail #{p.metadata.id}
                </button>
              </li>
            ))}
          </ol>
          <h4>Choose two records for existing comparison</h4>
          <div className="controls">
            {(["A", "B"] as const).map((side) => (
              <label key={side}>
                History source {side}
                <select
                  value={side === "A" ? first : second}
                  onChange={(e) =>
                    side === "A"
                      ? setFirst(e.target.value)
                      : setSecond(e.target.value)
                  }
                >
                  <option value="">Choose a validated snapshot</option>
                  {report.points
                    .filter((p) => p.usable)
                    .map((p) => (
                      <option key={p.metadata.id} value={p.metadata.id}>
                        #{p.metadata.id} /{" "}
                        {formatUtc(p.metadata.retrieved_at ?? undefined)}
                      </option>
                    ))}
                </select>
              </label>
            ))}
            <button
              type="button"
              disabled={!first || !second || first === second}
              onClick={() => onCompare(Number(first), Number(second))}
            >
              Open selected historical comparison
            </button>
          </div>
          {report.comparisons.map((pair) => (
            <section
              key={pair.id}
              aria-label={`Selected records ${pair.first.snapshot_id} and ${pair.second.snapshot_id}`}
            >
              <h4>
                {pair.status === "complete"
                  ? "Recorded change"
                  : "Comparison unavailable"}{" "}
                #{pair.first.snapshot_id} / #{pair.second.snapshot_id}
              </h4>
              <p>
                Chronology: {pair.chronology_status}. Status: {pair.status}.
                Retrieval interval:{" "}
                {pair.retrieval_interval_seconds ?? "unavailable"} seconds. This
                interval is not evidence of an outage. Values use later
                retrieval minus earlier retrieval only where ordered;
                inclination is linear, not wrapped.
              </p>
              <p>
                Retrievals: {formatUtc(pair.first.retrieved_at ?? undefined)} /{" "}
                {formatUtc(pair.second.retrieved_at ?? undefined)}. Element
                epochs: {formatUtc(pair.first.orbital_epoch ?? undefined)} /{" "}
                {formatUtc(pair.second.orbital_epoch ?? undefined)}.
              </p>
              <div
                className="history-table"
                tabIndex={0}
                role="region"
                aria-label="Recorded element differences"
              >
                <table>
                  <caption>
                    Differences between published mean-element sets
                  </caption>
                  <thead>
                    <tr>
                      <th>Field</th>
                      <th>Earlier value</th>
                      <th>Later value</th>
                      <th>Difference</th>
                      <th>Unit</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pair.differences.map((d) => (
                      <tr key={d.field}>
                        <th scope="row">{d.field}</th>
                        <td>{d.first_value}</td>
                        <td>{d.second_value}</td>
                        <td>{d.difference}</td>
                        <td>{d.unit}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p>
                {pair.evidence.scope} Status: {pair.evidence.status}. No package
                has been captured by this page.
              </p>
              {pair.evidence.definition && (
                <button
                  type="button"
                  onClick={() =>
                    download(
                      pair.evidence.definition,
                      `orbitiq-comparison-${pair.id}-definition.json`,
                    )
                  }
                >
                  Download existing replay capture definition {pair.id}
                </button>
              )}
            </section>
          ))}
          <h4>Explainable data-quality findings</h4>
          <p>
            Rule set version {report.rule_set_version}. Categories describe
            evidence quality, with no physical-event severity or confidence
            score.
          </p>
          {report.findings.map((f) => (
            <details key={f.finding_id}>
              <summary>
                {f.title} · {f.category}
              </summary>
              <p>{f.explanation}</p>
              <p>
                Rule {f.rule_id} v{f.rule_version}. {f.reproduction_status}
              </p>
              <p className="source-hash">Finding: {f.finding_id}</p>
              <pre>
                {JSON.stringify(
                  { sources: f.sources, inputs: f.inputs, result: f.result },
                  null,
                  2,
                )}
              </pre>
            </details>
          ))}
          <h4>Methodological limitations</h4>
          <ul>
            {report.limitations.map((x) => (
              <li key={x}>{x}</li>
            ))}
          </ul>
          <button
            type="button"
            onClick={() =>
              download(report, `orbitiq-history-${report.catalog_id}.json`)
            }
          >
            Export historical analysis JSON
          </button>
          <p>
            The JSON preserves this captured analysis, all findings, exact
            references, inputs, units, rules and limitations. It is a
            historical-analysis schema, not a Phase 10 replay bundle.
          </p>
        </>
      )}
    </section>
  );
}
