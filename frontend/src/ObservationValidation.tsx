import { useEffect, useId, useRef, useState } from "react";
import { reportJson } from "./report-presentation";
import { formatUtc } from "./time-presentation";
import { object } from "./saved-investigation";
export interface ValidationReport {
  kind: "orbitiq_observation_validation_report";
  schema_version: 1;
  report_id: string;
  generated_at: string;
  status: string;
  prediction_source: {
    snapshot_id: number;
    catalog_id: number;
    response_sha256: string;
    orbital_epoch: string;
    retrieved_at: string;
  };
  input_sha256: string;
  input_representation: string;
  limitations: string[];
  summary: {
    requested_count: number;
    compatible_count: number;
    excluded_count: number;
    independently_verified_count: 0;
    independent_error_metrics: null;
    independent_validation_status: "not_established";
    descriptive_discrepancy_by_frame: Record<string, unknown>;
  };
  samples: {
    index: number;
    observation: Record<string, unknown> | null;
    status: string;
    reason: string;
    frame?: string;
    prediction_generated_at?: string;
    holdout_from_retrieval_seconds?: number;
    residual: { xyz_km: number[]; magnitude_km: number; rac: unknown } | null;
    independence: { status: string; eligible: false };
    checks: Record<string, boolean>;
    uncertainty: unknown;
    prediction_reference: unknown;
    prediction?: unknown;
    prediction_bundle?: string;
    prediction_manifest_sha256?: string;
  }[];
  findings: Record<string, unknown>[];
}
function invalid(): never {
  throw new Error(
    "Unexpected observation-validation response; no result is displayed.",
  );
}
export function parseValidation(v: unknown): ValidationReport {
  if (
    !object(v) ||
    v.kind !== "orbitiq_observation_validation_report" ||
    v.schema_version !== 1 ||
    typeof v.report_id !== "string" ||
    !/^[a-f0-9]{32}$/.test(v.report_id) ||
    typeof v.generated_at !== "string" ||
    formatUtc(v.generated_at) === "Unavailable" ||
    !object(v.prediction_source) ||
    !Number.isSafeInteger(v.prediction_source.snapshot_id) ||
    !Number.isSafeInteger(v.prediction_source.catalog_id) ||
    typeof v.prediction_source.response_sha256 !== "string" ||
    !/^[a-f0-9]{64}$/.test(v.prediction_source.response_sha256) ||
    typeof v.input_sha256 !== "string" ||
    !/^[a-f0-9]{64}$/.test(v.input_sha256) ||
    typeof v.status !== "string" ||
    !object(v.summary) ||
    !Array.isArray(v.samples) ||
    !v.samples.length ||
    v.samples.length > 10 ||
    !Array.isArray(v.findings) ||
    v.findings.length !== v.samples.length ||
    !Array.isArray(v.limitations) ||
    !v.limitations.every((x) => typeof x === "string")
  )
    invalid();
  const summary = v.summary;
  if (
    summary.requested_count !== v.samples.length ||
    summary.independently_verified_count !== 0 ||
    summary.independent_error_metrics !== null ||
    summary.independent_validation_status !== "not_established" ||
    !object(summary.descriptive_discrepancy_by_frame)
  )
    invalid();
  let compatible = 0;
  for (let i = 0; i < v.samples.length; i++) {
    const s = v.samples[i];
    if (
      !object(s) ||
      s.index !== i ||
      typeof s.status !== "string" ||
      typeof s.reason !== "string" ||
      !object(s.independence) ||
      s.independence.eligible !== false ||
      typeof s.independence.status !== "string" ||
      !object(s.checks) ||
      !(s.observation === null || object(s.observation))
    )
      invalid();
    if (s.residual !== null) {
      if (
        s.status !== "compatible_with_warnings" ||
        !object(s.residual) ||
        !Array.isArray(s.residual.xyz_km) ||
        s.residual.xyz_km.length !== 3 ||
        !s.residual.xyz_km.every(
          (x) => typeof x === "number" && Number.isFinite(x),
        ) ||
        typeof s.residual.magnitude_km !== "number" ||
        !Number.isFinite(s.residual.magnitude_km) ||
        s.residual.magnitude_km < 0 ||
        !["TEME", "ITRS"].includes(String(s.frame)) ||
        !Object.values(s.checks).every((x) => x === true)
      )
        invalid();
      compatible++;
    } else if (s.status === "compatible_with_warnings") invalid();
  }
  if (
    summary.compatible_count !== compatible ||
    summary.excluded_count !== v.samples.length - compatible
  )
    invalid();
  for (const f of v.findings)
    if (
      !object(f) ||
      f.rule_version !== 1 ||
      typeof f.finding_id !== "string" ||
      typeof f.explanation !== "string" ||
      f.confidence !== null ||
      f.severity !== null
    )
      invalid();
  return v as unknown as ValidationReport;
}
async function read(url: string, signal: AbortSignal) {
  const response = await fetch(url, {
    signal: AbortSignal.any([signal, AbortSignal.timeout(30000)]),
    cache: "no-store",
  });
  if (!response.ok)
    throw new Error(
      `Observation validation evidence unavailable (${response.status}). Ask the local operator to verify the configured package.`,
    );
  const text = await response.text();
  if (text.length > 2 * 1024 * 1024) invalid();
  return JSON.parse(text) as unknown;
}
export default function ObservationValidation() {
  const heading = useId(),
    request = useRef<AbortController | null>(null);
  const [listing, setListing] = useState<{
      status: string;
      message: string;
      runs: string[];
    } | null>(null),
    [report, setReport] = useState<ValidationReport | null>(null);
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [run, setRun] = useState(""),
    [selected, setSelected] = useState("0"),
    [notice, setNotice] = useState("");
  useEffect(() => () => request.current?.abort(), []);
  async function load(id?: string) {
    request.current?.abort();
    const c = new AbortController();
    request.current = c;
    setBusy(true);
    setError("");
    setReport(null);
    setNotice("");
    try {
      if (id) {
        if (!/^[a-f0-9]{32}$/.test(id)) invalid();
        const v = parseValidation(
          await read(`/api/observation-validations/${id}`, c.signal),
        );
        if (v.report_id !== id) invalid();
        if (!c.signal.aborted) {
          setReport(v);
          setSelected("0");
        }
      } else {
        const v = await read("/api/observation-validations", c.signal);
        if (
          !object(v) ||
          typeof v.status !== "string" ||
          typeof v.message !== "string" ||
          !Array.isArray(v.runs) ||
          v.runs.length > 100 ||
          !v.runs.every(
            (x) => typeof x === "string" && /^[a-f0-9]{32}$/.test(x),
          )
        )
          invalid();
        if (!c.signal.aborted) {
          setListing(v as { status: string; message: string; runs: string[] });
          setRun("");
        }
      }
    } catch (e) {
      if (!c.signal.aborted)
        setError(
          e instanceof Error ? e.message : "Evidence request failed. Retry.",
        );
    } finally {
      if (!c.signal.aborted) setBusy(false);
    }
  }
  function download() {
    if (!report) return;
    try {
      const url = URL.createObjectURL(
        new Blob([reportJson(report)], { type: "application/json" }),
      );
      const a = document.createElement("a");
      a.href = url;
      a.download = `orbitiq-observation-validation-${report.report_id}.json`;
      document.body.append(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setNotice(
        "Captured JSON download requested; no calculations or ingestion were performed.",
      );
    } catch {
      setError("Download unavailable. Retry.");
    }
  }
  const sample = report?.samples[Number(selected)];
  return (
    <section aria-labelledby={heading} className="historical-analysis">
      <h3 id={heading}>Independent observation validation</h3>
      <p>
        Compare archived-input SGP4 predictions with operator-supplied position
        records. Historical element changes are a separate analysis. No
        observations are acquired by this view.
      </p>
      <p className="notice">
        Independent observation-based prediction accuracy remains unverified.
        Numerical discrepancies alone do not establish independence, uncertainty
        or physical causes.
      </p>
      <button type="button" disabled={busy} onClick={() => void load()}>
        Inspect available validation evidence
      </button>
      {busy && <p role="status">Loading captured observation evidence…</p>}
      {error && (
        <p role="alert">
          {error}
          <button type="button" onClick={() => void load(run || undefined)}>
            Retry observation evidence
          </button>
        </p>
      )}
      {notice && <p role="status">{notice}</p>}
      {listing && (
        <>
          <p role="status">
            {listing.message} Status: {listing.status}.
          </p>
          {listing.runs.length > 0 && (
            <form
              className="controls"
              onSubmit={(e) => {
                e.preventDefault();
                void load(run);
              }}
            >
              <label>
                Captured prediction / observation run
                <select
                  value={run}
                  onChange={(e) => {
                    request.current?.abort();
                    setBusy(false);
                    setRun(e.target.value);
                    setReport(null);
                    setError("");
                  }}
                >
                  <option value="">Choose recorded evidence</option>
                  {listing.runs.map((id) => (
                    <option key={id}>{id}</option>
                  ))}
                </select>
              </label>
              <button type="submit" disabled={!run || busy}>
                Open captured validation
              </button>
            </form>
          )}
        </>
      )}
      {report && (
        <>
          <h4>
            Captured validation · NORAD {report.prediction_source.catalog_id}
          </h4>
          <p>
            Prediction source snapshot #{report.prediction_source.snapshot_id}.
            Source epoch: {formatUtc(report.prediction_source.orbital_epoch)}.
            Retrieval: {formatUtc(report.prediction_source.retrieved_at)}.
            Generated: {formatUtc(report.generated_at)}.
          </p>
          <p className="source-hash">
            Input snapshot SHA-256: {report.prediction_source.response_sha256}.
            Observation input SHA-256: {report.input_sha256}.
          </p>
          <p>
            {report.summary.requested_count} requested records;{" "}
            {report.summary.compatible_count} compatible discrepancies;{" "}
            {report.summary.excluded_count} excluded;{" "}
            {report.summary.independently_verified_count} independently verified
            observations. Status: {report.status}.
          </p>
          <p>
            Retrospective propagation from archived input is not a historically
            issued forecast. Unavailable values are not zero. This captured run
            contains operator-normalized observations whose upstream
            authenticity has not been verified.
          </p>
          <div
            className="history-table"
            role="region"
            aria-label="Observation discrepancy samples"
            tabIndex={0}
          >
            <table>
              <caption>
                Available error samples only; no interpolation or error forecast
              </caption>
              <thead>
                <tr>
                  <th>Observation</th>
                  <th>Epoch</th>
                  <th>Frame</th>
                  <th>Discrepancy (km)</th>
                  <th>Seconds after input retrieval</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {report.samples.map((s) => (
                  <tr key={s.index}>
                    <th scope="row">
                      {String(
                        s.observation?.observation_id ??
                          `Invalid record ${s.index}`,
                      )}
                    </th>
                    <td>
                      {formatUtc(
                        typeof s.observation?.observed_at === "string"
                          ? s.observation.observed_at
                          : undefined,
                      )}
                    </td>
                    <td>{s.frame ?? "Unavailable"}</td>
                    <td>{s.residual?.magnitude_km ?? "Unavailable"}</td>
                    <td>{s.holdout_from_retrieval_seconds ?? "Unavailable"}</td>
                    <td>{s.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <label>
            Observation evidence detail
            <select
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
            >
              {report.samples.map((s) => (
                <option key={s.index} value={s.index}>
                  {String(
                    s.observation?.observation_id ??
                      `Invalid record ${s.index}`,
                  )}
                </option>
              ))}
            </select>
          </label>
          {sample && (
            <>
              <p>{sample.reason}</p>
              <p>
                Independence: {sample.independence.status}. Joint
                prediction/observation uncertainty is unavailable.
              </p>
              <details>
                <summary>
                  Source, prediction, compatibility and uncertainty evidence
                </summary>
                <pre>{JSON.stringify(sample, null, 2)}</pre>
              </details>
            </>
          )}
          <h4>Descriptive discrepancy metrics</h4>
          <p>
            Two compatible samples per frame are required. These unweighted
            statistics are not independent prediction-accuracy measurements or
            confidence bounds.
          </p>
          <pre>
            {JSON.stringify(
              report.summary.descriptive_discrepancy_by_frame,
              null,
              2,
            )}
          </pre>
          <h4>Explainable validation findings</h4>
          {report.findings.map((f) => (
            <details key={String(f.finding_id)}>
              <summary>
                {String(f.rule_id)} · record {String(f.observation_index)}
              </summary>
              <p>{String(f.explanation)}</p>
              <pre>{JSON.stringify(f, null, 2)}</pre>
            </details>
          ))}
          <h4>Scientific limitations</h4>
          <ul>
            {report.limitations.map((x) => (
              <li key={x}>{x}</li>
            ))}
          </ul>
          <button type="button" onClick={download}>
            Export captured observation validation JSON
          </button>
          <p>
            Export records exact original-input and nested prediction
            references. The operator retains the complete package for offline
            replay; JSON alone is not the complete replay package.
          </p>
        </>
      )}
    </section>
  );
}
