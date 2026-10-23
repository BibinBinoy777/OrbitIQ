import { useCallback, useEffect, useId, useRef, useState } from "react";
import {
  explorerSource,
  getDetail,
  getSnapshotPage,
} from "./investigation-api";
import type { SnapshotPage, StoredSnapshot } from "./investigation-api";
import { getReadiness } from "./readiness-api";
import type { ReadinessResult } from "./readiness-api";
import type { SnapshotSummary } from "./scientific-api";
import { formatUtc } from "./time-presentation";

const errorText = (e: unknown) =>
  e instanceof Error ? e.message : "Request unavailable. Retry.";
function eligible(s: StoredSnapshot) {
  return (
    s.validation_status === "structural_and_epoch_propagation_passed" &&
    s.metadata_issues.length === 0 &&
    !!explorerSource(s)
  );
}
export default function StoredCatalog({
  onExplore,
  onBrowse,
  onReadiness,
}: {
  onExplore: (source: SnapshotSummary) => void;
  onBrowse: () => void;
  onReadiness: () => void;
}) {
  const id = useId();
  const [page, setPage] = useState<SnapshotPage | null>(null);
  const [readiness, setReadiness] = useState<ReadinessResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [auditError, setAuditError] = useState("");
  const [selectionError, setSelectionError] = useState("");
  const [opening, setOpening] = useState<number | null>(null);
  const active = useRef<AbortController | null>(null);
  const selection = useRef<AbortController | null>(null);
  const read = useCallback(async (controller: AbortController) => {
    // Fail independently: absent provider audit must not hide stored snapshots.
    await Promise.all([
      getSnapshotPage(new URLSearchParams({ limit: "5" }), controller.signal)
        .then((value) => {
          if (!controller.signal.aborted) setPage(value);
        })
        .catch((e) => {
          if (!controller.signal.aborted) setError(errorText(e));
        }),
      getReadiness("", controller.signal)
        .then((value) => {
          if (!controller.signal.aborted) setReadiness(value);
        })
        .catch((e) => {
          if (!controller.signal.aborted) setAuditError(errorText(e));
        }),
    ]).finally(() => {
      if (!controller.signal.aborted) setLoading(false);
    });
  }, []);
  function refresh() {
    active.current?.abort();
    selection.current?.abort();
    const controller = new AbortController();
    active.current = controller;
    setLoading(true);
    setError("");
    setAuditError("");
    setReadiness(null);
    setOpening(null);
    setSelectionError("");
    void read(controller);
  }
  useEffect(() => {
    const controller = new AbortController();
    active.current = controller;
    void read(controller);
    return () => {
      active.current?.abort();
      selection.current?.abort();
    };
  }, [read]);
  async function open(source: StoredSnapshot) {
    selection.current?.abort();
    const controller = new AbortController();
    selection.current = controller;
    setOpening(source.id);
    setSelectionError("");
    try {
      const summary = explorerSource(source);
      if (!eligible(source) || !summary)
        throw new Error(
          "Source metadata is incomplete. Inspect it in Discovery & history.",
        );
      await getDetail(source, controller.signal); // Existing full backend provenance validation.
      if (!controller.signal.aborted) onExplore(summary);
    } catch (e) {
      if (!controller.signal.aborted) setSelectionError(errorText(e));
    } finally {
      if (!controller.signal.aborted) setOpening(null);
    }
  }
  const ingestion = readiness?.components.ingestion;
  const empty =
    page?.total_count === 0 &&
    page.total_count_status === "exact_within_anchor" &&
    !page.has_more &&
    !page.snapshots.length;
  return (
    <section className="stored-catalog" aria-labelledby={id}>
      <h2 id={id}>Start with stored satellite data</h2>
      <p>
        Choose an archived snapshot below or browse stored history. Loading this
        catalog never contacts an orbital-data provider.
      </p>
      <div className="toolbar">
        <button type="button" onClick={() => void refresh()} disabled={loading}>
          Reload stored catalog
        </button>
        <button type="button" onClick={onBrowse}>
          Browse stored catalog
        </button>
        <button type="button" onClick={onReadiness}>
          Inspect data readiness
        </button>
      </div>
      {loading && <p role="status">Loading stored catalog information…</p>}
      {error && (
        <p role="alert">
          Stored catalog unavailable: {error}
          {page
            ? " Previously loaded metadata is retained; opening a snapshot rechecks its source."
            : " This is not an empty-catalog result."}
        </p>
      )}
      {page && (
        <>
          <dl className="metadata">
            <dt>Stored satellite snapshot records</dt>
            <dd>
              {page.total_count_status === "exact_within_anchor" &&
              page.total_count !== null
                ? page.total_count
                : "Unavailable — count exceeds the bounded assessment"}
            </dd>
            <dt>Count scope</dt>
            <dd>
              One satellite record per snapshot; repeated satellites can occur.
              Not a count of unique satellites or validated usable sources.
              Records after this history anchor are excluded.
            </dd>
            <dt>Usable snapshot count</dt>
            <dd>
              Not assessed globally. Each selected source is validated before
              opening.
            </dd>
            <dt>Catalog assessed (UTC)</dt>
            <dd>{formatUtc(page.evaluated_at)}</dd>
          </dl>
          {empty && (
            <p role="status">
              No stored snapshots are available. Ask the local operator to
              configure storage and collect an approved satellite before
              exploring.
            </p>
          )}
          {!empty && !page.snapshots.length && (
            <p role="status">
              No records returned in this bounded window. Browse stored history
              or retry; absence here does not establish an empty archive.
            </p>
          )}
          {!!page.snapshots.length && (
            <ul className="catalog-records">
              {page.snapshots.map((source) => (
                <li key={source.id}>
                  <h3>
                    {source.object_name ?? "Unnamed stored record"} · NORAD{" "}
                    {source.catalog_id ?? "unknown"} · snapshot #{source.id}
                  </h3>
                  <p>
                    Source: {source.provider ?? "unknown"}. Element freshness:{" "}
                    <strong>{source.freshness_info.state}</strong>. Epoch:{" "}
                    {formatUtc(source.orbital_epoch ?? undefined)}. First
                    retrieval: {formatUtc(source.retrieved_at ?? undefined)}.
                  </p>
                  {source.freshness_info.state !== "fresh" && (
                    <p className="notice">
                      {source.freshness_info.state === "stale"
                        ? "Stale elements: use as historical input; ask the operator about collection if current data are needed."
                        : "Element age requires review. Inspect readiness and source details before current-time use."}{" "}
                      Retrieval success does not guarantee a current or accurate
                      orbit.
                    </p>
                  )}
                  {!eligible(source) && (
                    <p>
                      Source metadata is incomplete or unsupported. Use
                      Discovery & history to inspect it; this record is not
                      offered as a validated calculation source.
                    </p>
                  )}
                  <button
                    type="button"
                    disabled={!eligible(source) || opening !== null}
                    onClick={() => void open(source)}
                  >
                    Open stored snapshot #{source.id}
                  </button>
                </li>
              ))}
            </ul>
          )}
          {page.has_more && (
            <p>
              Only the five newest insertions are listed here. Browse stored
              history for more; insertion order is not retrieval chronology.
            </p>
          )}
        </>
      )}
      {opening !== null && (
        <p role="status">Validating exact stored source #{opening}…</p>
      )}
      {selectionError && (
        <p role="alert">
          Source could not be opened: {selectionError} Inspect it in Discovery &
          history or reload the catalog.
        </p>
      )}
      {ingestion && (
        <div className="collection-status">
          <p>Collection status: {ingestion.message}</p>
          {ingestion.latest_attempt_failed === true && (
            <p className="notice">
              The latest provider collection attempt failed. Previously stored
              records remain accessible; this is not evidence that the archive
              is empty.
            </p>
          )}
          <p>
            Last audited successful acquisition:{" "}
            {formatUtc(
              typeof ingestion.last_successful_acquisition_at === "string"
                ? ingestion.last_successful_acquisition_at
                : undefined,
            )}
            . A successful acquisition may reuse an existing snapshot.
          </p>
        </div>
      )}
      {auditError && (
        <p>
          Collection status unavailable: {auditError} Stored catalog access is
          assessed separately.
        </p>
      )}
      <details>
        <summary>How to begin and recover missing data</summary>
        <p>
          Open a snapshot, inspect source/epoch information, and generate a
          backend-calculated track or position near its epoch. Calculated
          positions are not observations; prediction uncertainty remains
          unquantified.
        </p>
        <p>
          If storage is empty or unavailable, ask the local operator to follow
          the installation and ingestion guide. Collection is an explicit
          operator action with a shared two-hour cooldown; this page cannot
          trigger a provider refresh. Keep the existing archive when repairing
          configuration or restoring a backup.
        </p>
      </details>
    </section>
  );
}
