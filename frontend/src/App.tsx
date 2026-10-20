import { lazy, Suspense, useEffect, useState } from "react";
import { getHealth } from "./api";
import ScientificExplorer from "./ScientificExplorer";
import ReadinessDashboard from "./ReadinessDashboard";
import {
  parseInvestigation,
  parseShareLink,
  shareLink,
} from "./saved-investigation";
import type { Investigation } from "./saved-investigation";
import type { SnapshotSummary } from "./scientific-api";
const Investigations = lazy(() => import("./Investigations"));
const SavedInvestigations = lazy(() => import("./SavedInvestigations"));
const RestoredInvestigation = lazy(() => import("./RestoredInvestigation"));
type View = "explorer" | "readiness" | "investigations" | "saved" | "restored";
function route() {
  if (window.location.hash === "#/saved")
    return { investigation: null, error: "", shared: true };
  try {
    return {
      investigation: parseShareLink(window.location.href),
      error: "",
      shared: true,
    };
  } catch (e) {
    return {
      investigation: null,
      error: e instanceof Error ? e.message : "Unsupported link.",
      shared: true,
    };
  }
}
export default function App() {
  const [opened, setOpened] = useState(route);
  const [revision, setRevision] = useState(0);
  const [view, setView] = useState<View>(
    window.location.hash === "#/saved"
      ? "saved"
      : opened.investigation || opened.error
        ? "restored"
        : "explorer",
  );
  const [visited, setVisited] = useState(false);
  const [explorerVisited, setExplorerVisited] = useState(view === "explorer");
  const [explorerSource, setExplorerSource] = useState<
    SnapshotSummary | undefined
  >();
  function navigate(next: View) {
    if (next !== "restored" && window.location.hash)
      window.history.replaceState(
        null,
        "",
        window.location.pathname + window.location.search,
      );
    if (next === "explorer") setExplorerVisited(true);
    if (next === "investigations") setVisited(true);
    if (next === "saved")
      window.history.replaceState(
        null,
        "",
        window.location.pathname + window.location.search + "#/saved",
      );
    if (next === "restored" && opened.investigation)
      window.history.replaceState(
        null,
        "",
        shareLink(opened.investigation, window.location.href),
      );
    setView(next);
  }
  function open(investigation: Investigation, shared = false) {
    window.history.replaceState(
      null,
      "",
      shareLink(investigation, window.location.href),
    );
    setOpened({
      investigation: parseInvestigation(investigation),
      error: "",
      shared,
    });
    setRevision((n) => n + 1);
    setView("restored");
  }
  function explore(source: SnapshotSummary) {
    setExplorerSource(source);
    navigate("explorer");
  }
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
    const changed = () => {
      const next = route();
      setOpened(next);
      setRevision((n) => n + 1);
      const target =
        window.location.hash === "#/saved"
          ? "saved"
          : next.investigation || next.error
            ? "restored"
            : "explorer";
      setView(target);
      if (target === "explorer") setExplorerVisited(true);
    };
    window.addEventListener("hashchange", changed);
    return () => {
      controller.abort();
      window.removeEventListener("hashchange", changed);
    };
  }, []);
  return (
    <main>
      <p>ORBITIQ / EXPLORER</p>
      <h1>Explore Earth’s orbital neighborhood.</h1>
      <p>Satellite exploration grounded in traceable orbital data.</p>
      <p className="notice">
        For exploration and historical analysis. Calculated positions are not
        observations; prediction uncertainty is unquantified. Independent
        observation-based prediction validation is not yet available.
      </p>
      <p role="status">{status}</p>
      <nav className="toolbar" aria-label="OrbitIQ sections">
        <button
          type="button"
          aria-current={view === "explorer" ? "page" : undefined}
          onClick={() => navigate("explorer")}
        >
          Satellite explorer
        </button>
        <button
          type="button"
          aria-current={view === "readiness" ? "page" : undefined}
          onClick={() => navigate("readiness")}
        >
          Scientific-data readiness
        </button>
        <button
          type="button"
          aria-current={view === "investigations" ? "page" : undefined}
          onClick={() => navigate("investigations")}
        >
          Discovery & history
        </button>
        <button
          type="button"
          aria-current={view === "saved" ? "page" : undefined}
          onClick={() => navigate("saved")}
        >
          Saved investigations
        </button>
        {(opened.investigation || opened.error) && (
          <button
            type="button"
            aria-current={view === "restored" ? "page" : undefined}
            onClick={() => navigate("restored")}
          >
            Return to opened investigation
          </button>
        )}
      </nav>
      {view === "readiness" && (
        <ReadinessDashboard onExplore={() => navigate("explorer")} />
      )}
      {explorerVisited && (
        <div hidden={view !== "explorer"}>
          {explorerSource && (
            <button type="button" onClick={() => navigate("investigations")}>
              Return to discovery / comparison
            </button>
          )}
          <ScientificExplorer
            key={explorerSource?.id ?? "manual"}
            initialSource={explorerSource}
            active={view === "explorer"}
          />
        </div>
      )}
      {visited && (
        <div hidden={view !== "investigations"}>
          <Suspense fallback={<p role="status">Loading stored-data tools…</p>}>
            <Investigations
              active={view === "investigations"}
              onExplore={explore}
            />
          </Suspense>
        </div>
      )}
      {view === "saved" && (
        <Suspense
          fallback={<p role="status">Loading browser-local investigations…</p>}
        >
          <SavedInvestigations onOpen={(v) => open(v)} />
        </Suspense>
      )}
      {(opened.investigation || opened.error) && (
        <div hidden={view !== "restored"}>
          <Suspense fallback={<p role="status">Loading investigation…</p>}>
            <RestoredInvestigation
              key={revision}
              investigation={opened.investigation}
              error={opened.error}
              shared={opened.shared}
              active={view === "restored"}
              onCopy={() => {
                if (opened.investigation) open(opened.investigation);
              }}
              onExplore={explore}
            />
          </Suspense>
        </div>
      )}
    </main>
  );
}
