import { useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";
import type { Investigation } from "./saved-investigation";
import type { InvestigationReport as CapturedReport } from "./report-api";
import { getInvestigationReport } from "./report-api";
import { reportHtml, reportJson, reportSections } from "./report-presentation";
import "./report-print.css";

function ReportPreview({
  report,
  onClose,
}: {
  report: CapturedReport;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null),
    title = useId();
  useEffect(() => {
    const focus = document.activeElement;
    document.body.classList.add("report-printing");
    dialog.current?.showModal();
    return () => {
      document.body.classList.remove("report-printing");
      if (focus instanceof HTMLElement && focus.isConnected) focus.focus();
    };
  }, []);
  return createPortal(
    <dialog
      className="report-dialog"
      ref={dialog}
      aria-labelledby={title}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
    >
      <div className="report-controls">
        <button type="button" autoFocus onClick={() => window.print()}>
          Print report / Save as PDF
        </button>
        <button type="button" onClick={onClose}>
          Close printable report
        </button>
      </div>
      <article
        className="report-sheet"
        aria-label="OrbitIQ investigation report"
      >
        <header>
          <p className="report-brand">ORBITIQ / INVESTIGATION REPORT</p>
          <h1 id={title}>{report.investigation.title}</h1>
          <p>
            Report {report.report_id} · schema {report.schema_version} /
            template {report.template_version}
          </p>
          <p>Generated (UTC): {report.generated_at}</p>
          <p className="report-callout">
            Coverage: {report.status}. Validation:{" "}
            {String(report.validation.status)}. Calculated data are not
            observations.
          </p>
        </header>
        {reportSections(report).map((section) => (
          <section key={section.id}>
            <h2>{section.title}</h2>
            {section.paragraphs.map((p, i) => (
              <p key={i}>{p}</p>
            ))}
            {section.tables.map((t, i) => (
              <table key={i}>
                <caption>{t.caption}</caption>
                <thead>
                  <tr>
                    {t.columns.map((c) => (
                      <th scope="col" key={c}>
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {t.rows.map((row, index) => (
                    <tr key={index}>
                      {row.map((v, n) => (
                        <td key={n}>{v}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            ))}
          </section>
        ))}
        <footer>
          OrbitIQ · Report {report.report_id} · Generated {report.generated_at}{" "}
          · schema {report.schema_version} / template {report.template_version}.
          Scientific certification is not implied.
        </footer>
      </article>
    </dialog>,
    document.body,
  );
}

export default function InvestigationReport({
  investigation,
}: {
  investigation: Investigation;
}) {
  const [report, setReport] = useState<CapturedReport | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [message, setMessage] = useState(""),
    [preview, setPreview] = useState(false);
  const request = useRef<AbortController | null>(null);
  const heading = useRef<HTMLHeadingElement>(null),
    title = useId();
  const urls = useRef(new Map<string, number>());
  useEffect(() => {
    const allocated = urls.current;
    return () => {
      request.current?.abort();
      for (const [u, timer] of allocated) {
        window.clearTimeout(timer);
        URL.revokeObjectURL(u);
      }
      allocated.clear();
    };
  }, []);
  async function generate() {
    if (request.current) return;
    const c = new AbortController();
    request.current = c;
    setBusy(true);
    setError("");
    setMessage("");
    setReport(null);
    setPreview(false);
    try {
      const captured = await getInvestigationReport(investigation, c.signal);
      if (!c.signal.aborted) {
        setReport(captured);
        heading.current?.focus();
      }
    } catch (e) {
      if (!c.signal.aborted)
        setError(
          e instanceof Error ? e.message : "Report generation failed. Retry.",
        );
    } finally {
      if (!c.signal.aborted) setBusy(false);
      if (request.current === c) request.current = null;
    }
  }
  function cancel() {
    request.current?.abort();
    request.current = null;
    setBusy(false);
    setMessage("Report generation cancelled. No export was generated.");
  }
  function download(format: "json" | "html") {
    if (!report) return;
    setError("");
    try {
      const content =
        format === "json" ? reportJson(report) : reportHtml(report);
      const url = URL.createObjectURL(
        new Blob([content], {
          type:
            format === "json"
              ? "application/json;charset=utf-8"
              : "text/html;charset=utf-8",
        }),
      );
      const a = document.createElement("a");
      a.href = url;
      a.download = `orbitiq-report-${report.report_id}.${format}`;
      a.hidden = true;
      document.body.append(a);
      try {
        a.click();
      } finally {
        a.remove();
      }
      const timer = window.setTimeout(() => {
        URL.revokeObjectURL(url);
        urls.current.delete(url);
      }, 1000);
      urls.current.set(url, timer);
      setMessage(
        "Download requested. Check your browser downloads; both formats use this captured report without recalculating.",
      );
    } catch {
      setError(
        "The browser could not prepare the download. Your investigation was not changed. Retry the download.",
      );
    }
  }
  return (
    <section className="investigation-report-actions" aria-labelledby={title}>
      <h4 id={title} ref={heading} tabIndex={-1}>
        Investigation report & evidence
      </h4>
      <p>
        Generate from exact archived sources and current backend calculations.
        Local titles, private notes and saved-record metadata are excluded. No
        export is stored on the server.
      </p>
      <button type="button" disabled={busy} onClick={() => void generate()}>
        {busy
          ? "Generating investigation report…"
          : error
            ? "Retry report generation"
            : report
              ? "Regenerate report"
              : "Generate investigation report"}
      </button>
      {busy && (
        <>
          <p role="status">
            Checking source identities and generating the report…
          </p>
          <button type="button" onClick={cancel}>
            Cancel report generation
          </button>
        </>
      )}
      {error && <p role="alert">{error}</p>}
      {message && <p role="status">{message}</p>}
      {report && (
        <>
          <p role="status">
            Report ready ·{" "}
            {report.status === "partial"
              ? "some calculations unavailable; inspect the reasons"
              : "requested content captured"}
            . Report ID: {report.report_id}. Generated (UTC):{" "}
            {report.generated_at}.
          </p>
          <div className="toolbar">
            <button type="button" onClick={() => download("json")}>
              Download JSON evidence
            </button>
            <button type="button" onClick={() => setPreview(true)}>
              Open printable report
            </button>
            <button type="button" onClick={() => download("html")}>
              Download printable HTML
            </button>
          </div>
          <p>
            JSON, preview and printable HTML use the same captured facts.
            Regenerating requests new calculations; it does not reproduce the
            original saved output.
          </p>
        </>
      )}
      {preview && report && (
        <ReportPreview report={report} onClose={() => setPreview(false)} />
      )}
    </section>
  );
}
