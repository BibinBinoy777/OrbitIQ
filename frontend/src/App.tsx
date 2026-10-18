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
      <p>ORBITIQ / EXPLORER</p>
      <h1>Explore Earth’s orbital neighborhood.</h1>
      <p>Satellite exploration grounded in traceable orbital data.</p>
      <p role="status">{status}</p>
      <ScientificExplorer />
    </main>
  );
}
