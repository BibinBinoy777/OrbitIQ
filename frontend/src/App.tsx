import { lazy, Suspense, useEffect, useState } from "react";
import { getHealth } from "./api";
import ScientificExplorer from "./ScientificExplorer";
import ReadinessDashboard from "./ReadinessDashboard";
import type { SnapshotSummary } from "./scientific-api";
const Investigations = lazy(() => import("./Investigations"));
export default function App() {
  const [view, setView] = useState<"explorer" | "readiness" | "investigations">(
    "explorer",
  );
  const [visited, setVisited] = useState(false);
  const [explorerSource, setExplorerSource] = useState<
    SnapshotSummary | undefined
  >();
  const openInvestigations = () => {
    setVisited(true);
    setView("investigations");
  };
  const [status, setStatus] = useState("Connecting to backend…");
  useEffect(() => {
    const controller = new AbortController();
    getHealth(controller.signal)
      .then((message) => {
        if (!controller.signal.aborted) setStatus(message);
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setStatus("Backend unavailable. Check that the API is running.");
      });
    return () => controller.abort();
  }, []);
  return (
    <main>
      <p>ORBITIQ / EXPLORER</p>
      <h1>Explore Earth’s orbital neighborhood.</h1>
      <p>Satellite exploration grounded in traceable orbital data.</p>
      <p role="status">{status}</p>
      <nav className="toolbar" aria-label="OrbitIQ sections">
        <button
          type="button"
          aria-current={view === "explorer" ? "page" : undefined}
          onClick={() => setView("explorer")}
        >
          Satellite explorer
        </button>
        <button
          type="button"
          aria-current={view === "readiness" ? "page" : undefined}
          onClick={() => setView("readiness")}
        >
          Scientific-data readiness
        </button>
        <button
          type="button"
          aria-current={view === "investigations" ? "page" : undefined}
          onClick={openInvestigations}
        >
          Discovery & history
        </button>
      </nav>
      {view === "readiness" ? (
        <ReadinessDashboard onExplore={() => setView("explorer")} />
      ) : view === "explorer" ? (
        <>
          {explorerSource && (
            <button type="button" onClick={openInvestigations}>
              Return to discovery / comparison
            </button>
          )}
          <ScientificExplorer
            key={explorerSource?.id ?? "manual"}
            initialSource={explorerSource}
          />
        </>
      ) : null}
      {visited && (
        <div hidden={view !== "investigations"}>
          <Suspense fallback={<p role="status">Loading stored-data tools…</p>}>
            <Investigations
              active={view === "investigations"}
              onExplore={(source) => {
                setExplorerSource(source);
                setView("explorer");
              }}
            />
          </Suspense>
        </div>
      )}
    </main>
  );
}
