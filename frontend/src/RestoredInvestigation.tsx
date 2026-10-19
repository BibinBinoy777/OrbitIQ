import { lazy, Suspense, useEffect, useRef, useState } from "react";
import ScientificExplorer from "./ScientificExplorer";
import type { Investigation } from "./saved-investigation";
import { restoreInvestigation } from "./restore-investigation";
const Investigations = lazy(() => import("./Investigations"));

function Reconstruction({
  investigation,
  shared,
  active,
  onExplore,
}: {
  investigation: Investigation;
  shared: boolean;
  active: boolean;
  onExplore: (source: import("./scientific-api").SnapshotSummary) => void;
}) {
  const [result, setResult] = useState<Awaited<
    ReturnType<typeof restoreInvestigation>
  > | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    const c = new AbortController();
    restoreInvestigation(investigation, c.signal)
      .then((value) => {
        if (!c.signal.aborted) setResult(value);
      })
      .catch((e) => {
        if (!c.signal.aborted)
          setError(
            e instanceof Error
              ? e.message
              : "Investigation references could not be restored.",
          );
      });
    return () => c.abort();
  }, [investigation]);
  if (error) return <p role="alert">Restoration unavailable: {error}</p>;
  if (!result)
    return <p role="status">Checking exact historical source references…</p>;
  return (
    <>
      <p role="status">
        Investigation inputs restored: NORAD {investigation.source.catalog_id},
        snapshot #{investigation.source.snapshot_id}. Source epoch, first
        retrieval and hash match.
      </p>
      {investigation.mode === "comparison" ? (
        <Suspense fallback={<p role="status">Loading comparison…</p>}>
          <Investigations
            active={active}
            initialInvestigation={investigation}
            readOnly={shared}
            onExplore={onExplore}
          />
        </Suspense>
      ) : (
        <ScientificExplorer
          initialSource={result.sources[0]}
          initialInvestigation={investigation}
          readOnly={shared}
          active={active}
        />
      )}
    </>
  );
}
export default function RestoredInvestigation({
  investigation,
  error,
  shared,
  active,
  onCopy,
  onExplore,
}: {
  investigation: Investigation | null;
  error: string;
  shared: boolean;
  active: boolean;
  onCopy: () => void;
  onExplore: (source: import("./scientific-api").SnapshotSummary) => void;
}) {
  const [attempt, setAttempt] = useState(0);
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    heading.current?.focus();
  }, []);
  return (
    <section
      className="restored-investigation"
      aria-labelledby="restored-title"
    >
      <h2 id="restored-title" tabIndex={-1} ref={heading}>
        {shared
          ? "Shared investigation · read-only inputs"
          : "Reopened investigation"}
      </h2>
      {error && <p role="alert">Invalid investigation link: {error}</p>}
      {investigation && (
        <>
          <p>
            {shared
              ? "This link contains view parameters, not a cloud save. Its inputs are read-only; camera and timeline navigation do not update the link."
              : "Reopened from browser-local parameters. Changes in this view are not automatically saved; save a copy or edit the saved record."}
          </p>
          <p>
            Calculations requested here are recomputed using the current backend
            implementation and available EOP/leap resources. Original numerical
            outputs are not stored or guaranteed to be identical. Positions are
            calculated, not observations; prediction uncertainty remains
            unquantified.
          </p>
          <div className="toolbar">
            {shared && (
              <button type="button" onClick={onCopy}>
                Explore an editable copy
              </button>
            )}
            <button type="button" onClick={() => setAttempt((n) => n + 1)}>
              Retry reconstruction / recompute
            </button>
          </div>
          <Reconstruction
            key={attempt}
            investigation={investigation}
            shared={shared}
            active={active}
            onExplore={onExplore}
          />
        </>
      )}
    </section>
  );
}
