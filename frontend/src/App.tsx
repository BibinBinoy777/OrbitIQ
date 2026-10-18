import { useEffect, useState } from "react";
import { getHealth } from "./api";
import ScientificExplorer from "./ScientificExplorer";
export default function App() {
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
      <p>PHASE 3 · EARTH-RELATIVE ANALYSIS</p>
      <h1>OrbitIQ</h1>
      <p>Satellite exploration and orbital investigation.</p>
      <p role="status">{status}</p>
      <ScientificExplorer />
    </main>
  );
}
