import { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";
import Globe from "./Globe";
import {
  comparisonMarkers,
  elementUnits,
  explorerSource,
  getComparison,
  getDetail,
  getSnapshotPage,
} from "./investigation-api";
import type {
  Category,
  Comparison,
  SnapshotPage,
  StoredSnapshot,
} from "./investigation-api";
import type { SnapshotSummary } from "./scientific-api";
import { formatUtc } from "./time-presentation";
const message = (e: unknown) =>
  e instanceof Error ? e.message : "Stored-data request failed. Retry.";
const value = (s: unknown) =>
  s === null || s === undefined || s === "" ? "Unavailable" : String(s);
const labels = {
  shared: "Shared NORAD identity",
  added: "Only in B (added to second dataset)",
  removed: "Only in A (removed from second dataset)",
  incompatible: "Incompatible or unreliable record",
};
function identifier(s: string, optional = false): number | undefined {
  if (optional && !s.trim()) return undefined;
  const n = Number(s);
  if (!/^\d{1,16}$/.test(s) || !Number.isSafeInteger(n) || n < 1)
    throw new Error(
      "Use positive, safe integer snapshot or catalog identifiers.",
    );
  return n;
}
function Metadata({ source: s }: { source: StoredSnapshot }) {
  const pairs = [
    ["Snapshot / NORAD", `#${s.id} / ${value(s.catalog_id)}`],
    [
      "Name / international identifier",
      `${value(s.object_name)} / ${value(s.object_id)}`,
    ],
    ["Element epoch", formatUtc(s.orbital_epoch ?? undefined)],
    ["Retrieval time", formatUtc(s.retrieved_at ?? undefined)],
    ["Separate insertion time", "Not recorded"],
    [
      "Freshness / assessed at",
      `${s.freshness_info.state} / ${formatUtc(s.freshness_info.evaluated_at)}`,
    ],
    [
      "Stored record count",
      `${s.record_count} · one satellite record per schema-2 snapshot`,
    ],
    [
      "Provider / validation",
      `${value(s.provider)} / ${value(s.validation_status)}`,
    ],
    [
      "Validator / ingestion SGP4",
      `${value(s.validator_version)} / ${value(s.ingestion_sgp4_version)}`,
    ],
    ["Source SHA-256", value(s.response_sha256)],
    [
      "Metadata limitations",
      s.metadata_issues.length
        ? s.metadata_issues.join(" ")
        : "Listing metadata present; full source provenance is checked before scientific use.",
    ],
  ];
  return (
    <>
      <dl className="metadata investigation-metadata">
        {pairs.map(([k, v]) => (
          <div className="metadata-pair" key={k}>
            <dt>{k}</dt>
            <dd>{v}</dd>
          </div>
        ))}
      </dl>
      {s.source_url && (
        <a href={s.source_url} target="_blank" rel="noreferrer">
          CelesTrak source
        </a>
      )}
    </>
  );
}
export default function Investigations({
  active,
  onExplore,
}: {
  active: boolean;
  onExplore: (s: SnapshotSummary) => void;
}) {
  const [mode, setMode] = useState<"discovery" | "history" | "comparison">(
    "discovery",
  );
  const [query, setQuery] = useState("");
  const [match, setMatch] = useState("partial");
  const [catalog, setCatalog] = useState("");
  const [context, setContext] = useState("");
  const [only, setOnly] = useState(false);
  const [size, setSize] = useState("20");
  const [direct, setDirect] = useState("");
  const [page, setPage] = useState<SnapshotPage | null>(null);
  const [params, setParams] = useState<URLSearchParams | null>(null);
  const [previous, setPrevious] = useState<URLSearchParams[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<StoredSnapshot | null>(null);
  const [detail, setDetail] = useState<Awaited<
    ReturnType<typeof getDetail>
  > | null>(null);
  const [detailError, setDetailError] = useState("");
  const [detailLoading, setDetailLoading] = useState(false);
  const [first, setFirst] = useState("");
  const [second, setSecond] = useState("");
  const [at, setAt] = useState("");
  const [frame, setFrame] = useState("TEME");
  const [category, setCategory] = useState<Category>("all");
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [comparing, setComparing] = useState(false);
  const [compareError, setCompareError] = useState("");
  const listRequest = useRef<AbortController | null>(null),
    detailRequest = useRef<AbortController | null>(null),
    compareRequest = useRef<AbortController | null>(null);
  useEffect(() => {
    const abort = () => {
      listRequest.current?.abort();
      detailRequest.current?.abort();
      compareRequest.current?.abort();
    };
    if (!active) abort();
    return abort;
  }, [active]);
  const markers = useMemo(
    () => (comparison ? comparisonMarkers(comparison) : []),
    [comparison],
  );
  function clearPage() {
    listRequest.current?.abort();
    setPage(null);
    setError("");
    setLoading(false);
    setParams(null);
    setPrevious([]);
  }
  function clearComparison() {
    compareRequest.current?.abort();
    setComparison(null);
    setCompareError("");
    setComparing(false);
  }
  async function load(next: URLSearchParams, history: URLSearchParams[] = []) {
    listRequest.current?.abort();
    const c = new AbortController();
    listRequest.current = c;
    setLoading(true);
    setPage(null);
    setError("");
    setParams(next);
    setPrevious(history);
    try {
      const d = await getSnapshotPage(next, c.signal);
      if (!c.signal.aborted) setPage(d);
    } catch (e) {
      if (!c.signal.aborted) setError(message(e));
    } finally {
      if (listRequest.current === c) setLoading(false);
    }
  }
  async function search(e: FormEvent) {
    e.preventDefault();
    clearPage();
    try {
      const p = new URLSearchParams({ q: query, match, limit: size });
      const cat = identifier(catalog, true),
        ctx = identifier(context, true);
      if (cat) {
        if (cat > 339999) throw new Error("NORAD catalog ID must be 1–339999.");
        p.set("catalog_id", String(cat));
      }
      if (ctx) p.set("context_snapshot_id", String(ctx));
      if (only) {
        if (!ctx)
          throw new Error(
            "Choose a snapshot context for selected-only search.",
          );
        p.set("selected_only", "true");
      }
      await load(p);
    } catch (e) {
      setError(message(e));
    }
  }
  async function inspect(source: StoredSnapshot) {
    detailRequest.current?.abort();
    const c = new AbortController();
    detailRequest.current = c;
    setSelected(source);
    setDetail(null);
    setDetailError("");
    setDetailLoading(true);
    try {
      const d = await getDetail(source, c.signal);
      if (!c.signal.aborted) setDetail(d);
    } catch (e) {
      if (!c.signal.aborted) setDetailError(message(e));
    } finally {
      if (detailRequest.current === c) setDetailLoading(false);
    }
  }
  async function openDirect(e: FormEvent) {
    e.preventDefault();
    clearPage();
    try {
      const sid = identifier(direct);
      const p = new URLSearchParams({ snapshot_id: String(sid), limit: "1" });
      const c = new AbortController();
      listRequest.current = c;
      setLoading(true);
      setParams(p);
      try {
        const d = await getSnapshotPage(p, c.signal);
        if (!c.signal.aborted) {
          setPage(d);
          if (d.snapshots[0]) await inspect(d.snapshots[0]);
          else setError("Snapshot not found in available stored records.");
        }
      } finally {
        if (listRequest.current === c) setLoading(false);
      }
    } catch (e) {
      if (!(e instanceof DOMException && e.name === "AbortError"))
        setError(message(e));
    }
  }
  async function compare(e: FormEvent) {
    e.preventDefault();
    clearComparison();
    try {
      const a = identifier(first)!,
        b = identifier(second)!;
      if (at && formatUtc(at) === "Unavailable")
        throw new Error(
          "Use an ISO evaluation timestamp with timezone, or leave blank for elements only.",
        );
      const c = new AbortController();
      compareRequest.current = c;
      setComparing(true);
      try {
        const d = await getComparison(a, b, at, frame, category, c.signal);
        if (!c.signal.aborted) setComparison(d);
      } finally {
        if (compareRequest.current === c) setComparing(false);
      }
    } catch (e) {
      if (!(e instanceof DOMException && e.name === "AbortError"))
        setCompareError(message(e));
    }
  }
  function choose(s: StoredSnapshot, side: "A" | "B") {
    clearComparison();
    if (side === "A") setFirst(String(s.id));
    else setSecond(String(s.id));
  }
  function explore(s: StoredSnapshot) {
    const source = explorerSource(s);
    if (source) onExplore(source);
  }
  const state = comparison?.state_comparison;
  return (
    <section className="investigations" aria-labelledby="investigations-title">
      <h2 id="investigations-title">
        Stored satellite discovery & historical investigation
      </h2>
      <p>
        Search genuinely stored records. Each snapshot contains one satellite
        record; source datasets are not direct observations. Searches never
        download or ingest new elements.
      </p>
      <nav className="toolbar" aria-label="Stored-data tools">
        <button
          type="button"
          aria-current={mode === "discovery" ? "page" : undefined}
          onClick={() => setMode("discovery")}
        >
          Find satellites
        </button>
        <button
          type="button"
          aria-current={mode === "history" ? "page" : undefined}
          onClick={() => {
            setMode("history");
            void load(new URLSearchParams({ limit: size }));
          }}
        >
          Browse snapshot history
        </button>
        <button
          type="button"
          aria-current={mode === "comparison" ? "page" : undefined}
          onClick={() => setMode("comparison")}
        >
          Compare snapshots
        </button>
      </nav>
      {mode !== "comparison" && (
        <>
          {mode === "discovery" && (
            <form className="controls" onSubmit={search}>
              <label>
                Name, NORAD ID or international identifier
                <input
                  value={query}
                  maxLength={64}
                  onChange={(e) => {
                    setQuery(e.target.value);
                    clearPage();
                  }}
                />
              </label>
              <label>
                Match
                <select
                  value={match}
                  onChange={(e) => {
                    setMatch(e.target.value);
                    clearPage();
                  }}
                >
                  <option value="partial">Partial literal match</option>
                  <option value="exact">Exact match</option>
                </select>
              </label>
              <label>
                NORAD filter (optional)
                <input
                  value={catalog}
                  inputMode="numeric"
                  onChange={(e) => {
                    setCatalog(e.target.value);
                    clearPage();
                  }}
                />
              </label>
              <label>
                Selected snapshot context (optional)
                <input
                  value={context}
                  inputMode="numeric"
                  onChange={(e) => {
                    setContext(e.target.value);
                    clearPage();
                  }}
                />
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={only}
                  onChange={(e) => {
                    setOnly(e.target.checked);
                    clearPage();
                  }}
                />
                Only records in selected snapshot
              </label>
              <button type="submit">Search stored records</button>
            </form>
          )}
          <form className="controls" onSubmit={openDirect}>
            <label>
              Open snapshot ID directly
              <input
                value={direct}
                inputMode="numeric"
                onChange={(e) => setDirect(e.target.value)}
              />
            </label>
            <button type="submit">Open snapshot</button>
            <label>
              Page size
              <select
                value={size}
                onChange={(e) => {
                  setSize(e.target.value);
                  clearPage();
                }}
              >
                {[10, 20, 50, 100].map((n) => (
                  <option key={n}>{n}</option>
                ))}
              </select>
            </label>
          </form>
          {loading && <p role="status">Loading stored records…</p>}
          {error && (
            <p role="alert">
              {error}{" "}
              {params && (
                <button
                  type="button"
                  onClick={() => void load(params, previous)}
                >
                  Retry stored-data request
                </button>
              )}
            </p>
          )}
          {!page && !loading && !error && (
            <p role="status">
              Search stored records or browse snapshot history to begin.
            </p>
          )}
          {page && (
            <>
              <p>
                Page: {page.returned_count} records.{" "}
                {page.total_count === null
                  ? `Total matching count unavailable (${page.total_count_status}).`
                  : `Total within selected history anchor: ${page.total_count}.`}{" "}
                Assessed {formatUtc(page.evaluated_at)}.
              </p>
              <p>
                Insertion-ID order only; it does not establish retrieval
                chronology or globally latest/oldest epochs. Anchor #
                {page.anchor_id ?? "unavailable"}; at most {page.scan_limit}{" "}
                candidates per search page.
              </p>
              {!page.snapshots.length && (
                <p role="status">
                  No matches in this stored-data page.{" "}
                  {page.has_more
                    ? "More history remains; continue scanning."
                    : "No further matching stored records in this history view."}{" "}
                  This does not establish absence from orbit.
                </p>
              )}
              {!!page.snapshots.length && (
                <div
                  className="table-scroll"
                  role="region"
                  aria-label="Stored satellite and snapshot results"
                  tabIndex={0}
                >
                  <table>
                    <caption>
                      Stored satellite records · duplicates across snapshots are
                      retained
                    </caption>
                    <thead>
                      <tr>
                        <th scope="col">Snapshot / identity</th>
                        <th scope="col">Epoch / retrieval (UTC)</th>
                        <th scope="col">Source / status</th>
                        <th scope="col">Context / actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {page.snapshots.map((s) => (
                        <tr key={s.id}>
                          <th scope="row">
                            #{s.id} · {value(s.object_name)}
                            <br />
                            NORAD {value(s.catalog_id)}
                            <br />
                            {value(s.object_id)}
                          </th>
                          <td>
                            {formatUtc(s.orbital_epoch ?? undefined)}
                            <br />
                            {formatUtc(s.retrieved_at ?? undefined)}
                          </td>
                          <td>
                            {value(s.provider)} · {s.record_count} record
                            <br />
                            Freshness: {s.freshness_info.state}
                            <br />
                            {value(s.validation_status)}
                            {!!s.metadata_issues.length && (
                              <p className="notice">
                                {s.metadata_issues.join(" ")}
                              </p>
                            )}
                          </td>
                          <td>
                            {s.membership?.replaceAll("_", " ")}
                            <div className="toolbar">
                              <button
                                type="button"
                                onClick={() => void inspect(s)}
                              >
                                Inspect snapshot #{s.id}
                              </button>
                              <button
                                type="button"
                                onClick={() => choose(s, "A")}
                              >
                                Use #{s.id} as A
                              </button>
                              <button
                                type="button"
                                onClick={() => choose(s, "B")}
                              >
                                Use #{s.id} as B
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <div className="toolbar" aria-label="History pagination">
                <button
                  type="button"
                  disabled={!previous.length || loading}
                  onClick={() => {
                    const stack = [...previous];
                    const p = stack.pop()!;
                    void load(p, stack);
                  }}
                >
                  Previous page
                </button>
                <button
                  type="button"
                  disabled={!page.has_more || loading}
                  onClick={() => {
                    if (!params || !page.next_before_id || !page.anchor_id)
                      return;
                    const next = new URLSearchParams(params);
                    next.set("before_id", String(page.next_before_id));
                    next.set("anchor_id", String(page.anchor_id));
                    void load(next, [...previous, params].slice(-1000));
                  }}
                >
                  Continue history
                </button>
                <button
                  type="button"
                  onClick={() => {
                    if (!params) return;
                    const p = new URLSearchParams(params);
                    p.delete("before_id");
                    p.delete("anchor_id");
                    void load(p);
                  }}
                >
                  Restart history view
                </button>
              </div>
            </>
          )}
          {selected && (
            <section
              className="source-detail"
              aria-labelledby="source-detail-title"
            >
              <h3 id="source-detail-title">
                Snapshot #{selected.id}: fixed source detail
              </h3>
              <Metadata source={selected} />
              {detailLoading && <p role="status">Validating source details…</p>}
              {detailError && (
                <p role="alert">
                  {detailError} Metadata remain inspectable.{" "}
                  <button type="button" onClick={() => void inspect(selected)}>
                    Retry source detail
                  </button>
                </p>
              )}
              {detail && (
                <div
                  className="table-scroll"
                  role="region"
                  aria-label="Validated source mean elements"
                  tabIndex={0}
                >
                  <table>
                    <caption>
                      Validated mean elements; not observational accuracy
                    </caption>
                    <thead>
                      <tr>
                        <th scope="col">Element</th>
                        <th scope="col">Stored value</th>
                        <th scope="col">Unit</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(elementUnits).map(([field, unit]) => (
                        <tr key={field}>
                          <th scope="row">{field}</th>
                          <td>{value(detail.values[field])}</td>
                          <td>{unit}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <div className="toolbar">
                <button
                  type="button"
                  disabled={!explorerSource(selected)}
                  onClick={() => explore(selected)}
                >
                  Open exact source in 3D explorer
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setContext(String(selected.id));
                    setMode("discovery");
                  }}
                >
                  Use as discovery context
                </button>
                <button
                  type="button"
                  onClick={() => {
                    choose(selected, "A");
                    setMode("comparison");
                  }}
                >
                  Compare this source as A
                </button>
              </div>
            </section>
          )}
        </>
      )}
      <p>
        Selected comparison sources: A #{first || "not selected"} · B #
        {second || "not selected"}. Choices remain fixed until explicitly
        changed.
      </p>
      {mode === "comparison" && (
        <>
          <form className="controls" onSubmit={compare}>
            <label>
              Snapshot A
              <input
                value={first}
                inputMode="numeric"
                onChange={(e) => {
                  setFirst(e.target.value);
                  clearComparison();
                }}
              />
            </label>
            <label>
              Snapshot B
              <input
                value={second}
                inputMode="numeric"
                onChange={(e) => {
                  setSecond(e.target.value);
                  clearComparison();
                }}
              />
            </label>
            <label>
              Record difference filter
              <select
                value={category}
                onChange={(e) => {
                  setCategory(e.target.value as Category);
                  clearComparison();
                }}
              >
                {["all", "shared", "added", "removed", "incompatible"].map(
                  (c) => (
                    <option key={c} value={c}>
                      {c === "added"
                        ? "Only B / added"
                        : c === "removed"
                          ? "Only A / removed"
                          : c}
                    </option>
                  ),
                )}
              </select>
            </label>
            <label>
              Common evaluation time (optional, explicit timezone)
              <input
                value={at}
                onChange={(e) => {
                  setAt(e.target.value);
                  clearComparison();
                }}
                placeholder="Leave blank for element differences"
              />
            </label>
            <label>
              State frame
              <select
                value={frame}
                onChange={(e) => {
                  setFrame(e.target.value);
                  clearComparison();
                }}
              >
                <option value="TEME">TEME · numerical states</option>
                <option value="ITRS">ITRS · Earth-fixed globe</option>
              </select>
            </label>
            <button type="submit">Compare selected snapshots</button>
            <button type="button" onClick={clearComparison}>
              Cancel comparison
            </button>
          </form>
          <p>
            One explicit common evaluation time; positions in km, velocities in
            km/s. Existing ±7-day epoch and strict EOP/leap policies apply.
            Blank time requests record/element inspection only.
          </p>
          {comparing && <p role="status">Comparing fixed stored sources…</p>}
          {compareError && (
            <p role="alert">{compareError} Adjust the request and retry.</p>
          )}
          {comparison && (
            <section aria-labelledby="comparison-title">
              <h3 id="comparison-title">
                Comparison A #{comparison.first.id} / B #{comparison.second.id}
              </h3>
              {comparison.is_self_comparison && (
                <p className="notice">
                  Same snapshot selected twice: a self-check, not distinct
                  historical evidence. A distinct real source must be stored
                  explicitly to investigate historical changes.
                </p>
              )}
              <p>
                Chronology: {comparison.chronology.status.replaceAll("_", " ")}{" "}
                · {comparison.chronology.basis.replaceAll("_", " ")}.{" "}
                {comparison.chronology.older_snapshot_id
                  ? `Older retrieval #${comparison.chronology.older_snapshot_id}; newer retrieval #${comparison.chronology.newer_snapshot_id}.`
                  : "Sources remain in selected A/B order; older/newer order cannot be established."}
              </p>
              <p>
                Shared: {comparison.counts.shared} · only B:{" "}
                {comparison.counts.added} · only A: {comparison.counts.removed}{" "}
                · incompatible: {comparison.counts.incompatible}. Matching uses
                validated NORAD ID, never names alone.
              </p>
              {!comparison.records.length && (
                <p role="status">
                  No record differences in the selected category.
                </p>
              )}
              {comparison.records.map((r, i) => (
                <p key={i}>
                  {labels[r.category]} · NORAD {value(r.catalog_id)}
                </p>
              ))}
              <div className="comparison-sources">
                {[comparison.first, comparison.second].map((s, i) => (
                  <section
                    key={i}
                    aria-label={`Comparison source ${i === 0 ? "A" : "B"}`}
                  >
                    <h4>
                      {i === 0 ? "A" : "B"}: snapshot #{s.id}
                    </h4>
                    <Metadata source={s} />
                    <button
                      type="button"
                      disabled={!explorerSource(s)}
                      onClick={() => explore(s)}
                    >
                      Explore source {i === 0 ? "A" : "B"} #{s.id}
                    </button>
                  </section>
                ))}
              </div>
              <div
                className="table-scroll"
                role="region"
                aria-label="Source metadata differences"
                tabIndex={0}
              >
                <table>
                  <caption>Provenance and epoch differences</caption>
                  <thead>
                    <tr>
                      <th scope="col">Field</th>
                      <th scope="col">A</th>
                      <th scope="col">B</th>
                      <th scope="col">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {comparison.provenance_differences.map((r) => (
                      <tr key={r.field}>
                        <th scope="row">{r.field}</th>
                        <td>{value(r.first_value)}</td>
                        <td>{value(r.second_value)}</td>
                        <td>{r.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="notice">{comparison.caution}</p>
              {comparison.source_errors
                .filter((e) => e !== null)
                .map((e, i) => (
                  <p className="notice" key={i}>
                    {e.code}: {e.message}
                  </p>
                ))}
              {comparison.element_differences.length ? (
                <div
                  className="table-scroll"
                  role="region"
                  aria-label="Element differences"
                  tabIndex={0}
                >
                  <table>
                    <caption>
                      Mean elements · B minus A; cyclic angles wrapped to
                      [−180°, 180°)
                    </caption>
                    <thead>
                      <tr>
                        <th scope="col">Element / unit</th>
                        <th scope="col">A</th>
                        <th scope="col">B</th>
                        <th scope="col">Difference / convention</th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparison.element_differences.map((r) => (
                        <tr key={r.field}>
                          <th scope="row">
                            {r.field} · {r.unit}
                          </th>
                          <td>{r.first_value}</td>
                          <td>{r.second_value}</td>
                          <td>
                            {r.difference} · {r.convention}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p role="status">
                  {comparison.element_comparison_status ===
                  "unavailable_numeric_range"
                    ? "Element subtraction unavailable: the numerical range is not finite. Source records remain inspectable."
                    : "Element differences unavailable: no common validated record with compatible definitions and units."}
                </p>
              )}
              {state?.status === "not_requested" && (
                <p role="status">Common-time state comparison not requested.</p>
              )}
              {state?.status === "unavailable" && (
                <div role="status">
                  <p>
                    Common-time state comparison unavailable. Record-level
                    inspection remains available.
                  </p>
                  {state.errors
                    ?.filter((e) => e !== null)
                    .map((e, i) => (
                      <p key={i}>
                        {e.code}: {e.message}
                      </p>
                    ))}
                </div>
              )}
              {state?.status === "complete" && (
                <section aria-label="Common-time calculated state differences">
                  <h4>Common-time calculated states · {state.frame}</h4>
                  <p>
                    Evaluation: {formatUtc(state.evaluation_at ?? undefined)} ·
                    B minus A
                  </p>
                  <dl className="metadata">
                    <dt>Position difference (km)</dt>
                    <dd>{state.difference_position_km?.join(", ")}</dd>
                    <dt>Velocity difference (km/s)</dt>
                    <dd>{state.difference_velocity_km_s?.join(", ")}</dd>
                    <dt>Position-vector separation (km)</dt>
                    <dd>{state.separation_km}</dd>
                    <dt>Velocity-difference magnitude (km/s)</dt>
                    <dd>{state.relative_speed_km_s}</dd>
                  </dl>
                  {[state.first, state.second].map(
                    (s, i) =>
                      s && (
                        <dl className="metadata" key={i}>
                          <dt>{i === 0 ? "A" : "B"} position (km)</dt>
                          <dd>{s.position_km.join(", ")}</dd>
                          <dt>{i === 0 ? "A" : "B"} velocity (km/s)</dt>
                          <dd>{s.velocity_km_s.join(", ")}</dd>
                          <dt>{i === 0 ? "A" : "B"} calculation execution</dt>
                          <dd>
                            {formatUtc(
                              s.teme?.calculated_at ?? s.calculated_at,
                            )}
                          </dd>
                        </dl>
                      ),
                  )}
                  {markers.length === 2 && active ? (
                    <Globe comparison={markers} />
                  ) : (
                    <p>
                      {state.frame === "ITRS"
                        ? "These ITRS states exceed the globe display extent or lack validated rendering vectors. Numerical results remain available."
                        : "TEME numerical states are not rendered as Earth-fixed positions. Request a supported ITRS comparison to view both disconnected markers in the existing globe."}
                    </p>
                  )}
                </section>
              )}
              <ul>
                {comparison.assumptions.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
            </section>
          )}
        </>
      )}
    </section>
  );
}
