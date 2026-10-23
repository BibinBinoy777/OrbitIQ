import { useEffect, useId, useRef, useState } from "react";
import { confirmImport, previewImport } from "./investigation-storage";
import type {
  ImportPreview,
  SavedInvestigation,
} from "./investigation-storage";
import { exportBundle, readBundleFile } from "./portable-investigation";
import { formatUtc } from "./time-presentation";

export function PortableExport({ record }: { record: SavedInvestigation }) {
  const [notes, setNotes] = useState(false);
  const [feedback, setFeedback] = useState<{
    error: boolean;
    message: string;
  } | null>(null);
  const urls = useRef(new Map<string, number>());
  useEffect(() => {
    const allocated = urls.current;
    return () => {
      for (const [url, timer] of allocated) {
        clearTimeout(timer);
        URL.revokeObjectURL(url);
      }
    };
  }, []);
  function download() {
    setFeedback(null);
    let url: string | undefined;
    try {
      const file = exportBundle(record, notes);
      url = URL.createObjectURL(
        new Blob([file.json], { type: "application/json;charset=utf-8" }),
      );
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = file.filename;
      document.body.append(anchor);
      try {
        anchor.click();
      } finally {
        anchor.remove();
      }
      const allocated = url;
      urls.current.set(
        allocated,
        window.setTimeout(() => {
          URL.revokeObjectURL(allocated);
          urls.current.delete(allocated);
        }, 60000),
      );
      setFeedback({
        error: false,
        message: `Portable download requested. Save the file to keep it; download completion is controlled by your browser. Private local notes ${notes ? "are included" : "are excluded"}.`,
      });
    } catch {
      if (url) URL.revokeObjectURL(url);
      setFeedback({
        error: true,
        message:
          "Portable export could not be prepared. Retry; your original save is unchanged.",
      });
    }
  }
  return (
    <section
      aria-label={`Portable export for ${record.title}`}
      className="portable-tools"
    >
      <h4>Portable recovery file</h4>
      <p>
        Includes this saved title and input parameters. Plaintext JSON, without
        confidentiality or proof of authorship. Orbital source records and
        calculated results are not included.
      </p>
      <label>
        <input
          type="checkbox"
          checked={notes}
          onChange={(e) => setNotes(e.target.checked)}
        />
        Include private local notes for {record.title}
      </label>
      <button type="button" onClick={download}>
        Export portable bundle for {record.title}
      </button>
      {feedback && (
        <p role={feedback.error ? "alert" : "status"}>{feedback.message}</p>
      )}
    </section>
  );
}

export default function PortableImport() {
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [copy, setCopy] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const file = useRef<HTMLInputElement>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const previewHeading = useRef<HTMLHeadingElement>(null);
  const revision = useRef(0);
  const id = useId();
  useEffect(
    () => () => {
      revision.current++;
    },
    [],
  );
  useEffect(() => {
    if (preview) previewHeading.current?.focus();
  }, [preview]);
  async function choose(candidate: File | undefined) {
    const request = ++revision.current;
    setPreview(null);
    setError("");
    setMessage("");
    setCopy(false);
    if (!candidate) {
      setBusy(false);
      return;
    }
    setBusy(true);
    try {
      const bundle = await readBundleFile(candidate);
      if (request === revision.current)
        setPreview(previewImport(bundle.record));
    } catch (e) {
      if (request === revision.current)
        setError(
          e instanceof Error
            ? e.message
            : "Portable file unavailable. Choose another file.",
        );
    } finally {
      if (request === revision.current) setBusy(false);
    }
  }
  function cancel() {
    revision.current++;
    setPreview(null);
    setError("");
    setBusy(false);
    setMessage("Import cancelled. No local saves were changed.");
    file.current?.focus();
  }
  async function restore() {
    if (!preview || busy) return;
    setBusy(true);
    setError("");
    try {
      const result = await confirmImport(preview, copy);
      setPreview(null);
      setMessage(
        result.inserted
          ? "Investigation restored in this browser. Exact orbital source records were not restored; opening checks their availability and recomputes requested calculations."
          : "This investigation is already saved. No duplicate was created and no local save was changed.",
      );
      heading.current?.focus();
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Import could not be confirmed. Preview the file again.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="portable-tools" aria-labelledby={id + "-title"}>
      <h3 id={id + "-title"} ref={heading} tabIndex={-1}>
        Restore a portable investigation
      </h3>
      <p>
        Choose a local version-1 JSON bundle (up to 16 KiB). Files stay in your
        browser; nothing is uploaded. JSON evidence reports are a different
        format and cannot restore local saves.
      </p>
      <label htmlFor={id + "-file"}>Portable investigation file</label>
      <input
        id={id + "-file"}
        ref={file}
        type="file"
        accept=".json,application/json"
        aria-describedby={id + "-error"}
        aria-invalid={!!error}
        disabled={busy && !!preview}
        onChange={(e) => {
          const candidate = e.target.files?.[0];
          e.target.value = "";
          void choose(candidate);
        }}
      />
      <p id={id + "-error"} role={error ? "alert" : undefined}>
        {error}
      </p>
      {busy && (
        <p role="status">
          {preview
            ? "Confirming local restoration…"
            : "Reading and validating local file…"}
        </p>
      )}
      {message && <p role="status">{message}</p>}
      {preview && (
        <section aria-labelledby={id + "-preview"}>
          <h4 id={id + "-preview"} ref={previewHeading} tabIndex={-1}>
            Preview portable investigation
          </h4>
          <dl className="metadata">
            <dt>Title</dt>
            <dd>{preview.record.title}</dd>
            <dt>Local identifier</dt>
            <dd>{preview.record.id}</dd>
            <dt>Mode / frame</dt>
            <dd>
              {preview.record.investigation.mode} /{" "}
              {preview.record.investigation.frame}
            </dd>
            <dt>Satellite / exact source</dt>
            <dd>
              NORAD {preview.record.investigation.source.catalog_id} / snapshot
              #{preview.record.investigation.source.snapshot_id}
            </dd>
            <dt>Source epoch / first retrieval</dt>
            <dd>
              {formatUtc(preview.record.investigation.source.orbital_epoch)} /{" "}
              {formatUtc(preview.record.investigation.source.retrieved_at)}
            </dd>
            <dt>Source checksum</dt>
            <dd className="hash">
              {preview.record.investigation.source.response_sha256}
            </dd>
            {preview.record.investigation.mode !== "snapshot" && (
              <>
                <dt>Requested calculation time</dt>
                <dd>
                  {formatUtc(preview.record.investigation.at ?? undefined)}
                </dd>
              </>
            )}
            {preview.record.investigation.mode === "ground-track" && (
              <>
                <dt>Track sampling</dt>
                <dd>
                  Start {formatUtc(preview.record.investigation.track.start)};
                  duration {preview.record.investigation.track.duration_minutes}{" "}
                  minutes; step{" "}
                  {preview.record.investigation.track.step_seconds} seconds;
                  selected index{" "}
                  {preview.record.investigation.track.selected_index}
                </dd>
              </>
            )}
            {preview.record.investigation.mode === "comparison" && (
              <>
                <dt>Comparison source / category</dt>
                <dd>
                  NORAD{" "}
                  {preview.record.investigation.comparison_source.catalog_id} /
                  snapshot #
                  {preview.record.investigation.comparison_source.snapshot_id};{" "}
                  {preview.record.investigation.category}
                </dd>
                <dt>Comparison epoch / first retrieval</dt>
                <dd>
                  {formatUtc(
                    preview.record.investigation.comparison_source
                      .orbital_epoch,
                  )}{" "}
                  /{" "}
                  {formatUtc(
                    preview.record.investigation.comparison_source.retrieved_at,
                  )}
                </dd>
                <dt>Comparison checksum</dt>
                <dd className="hash">
                  {
                    preview.record.investigation.comparison_source
                      .response_sha256
                  }
                </dd>
              </>
            )}
            <dt>Original local creation / modification</dt>
            <dd>
              {formatUtc(preview.record.created_at)} /{" "}
              {formatUtc(preview.record.updated_at)}
            </dd>
            <dt>Included local notes</dt>
            <dd className="local-notes">
              {preview.record.description || "None included"}
            </dd>
          </dl>
          <p>
            Structural validation is not scientific qualification or trusted
            authorship. Source snapshots, results, findings, EOP/leap resources
            and database backups are not in this bundle. Exact source
            availability is checked when you open it; prediction uncertainty
            remains unquantified and independent validation remains blocked.
          </p>
          {preview.status === "already_saved" && (
            <p>
              This content is already saved, possibly under a different
              identifier. Confirmation will not add a duplicate.
            </p>
          )}
          {preview.status === "collision" && (
            <>
              <p>
                An existing investigation uses this identifier with different
                contents. It will not be overwritten.
              </p>
              <label>
                <input
                  type="checkbox"
                  checked={copy}
                  disabled={busy}
                  onChange={(e) => setCopy(e.target.checked)}
                />
                Import as a separate copy with a new identifier
              </label>
            </>
          )}
          <div className="toolbar">
            <button
              type="button"
              disabled={busy || (preview.status === "collision" && !copy)}
              onClick={() => void restore()}
            >
              Confirm local import
            </button>
            <button type="button" disabled={busy} onClick={cancel}>
              Cancel import
            </button>
          </div>
        </section>
      )}
    </section>
  );
}
