import { useEffect, useRef, useState } from "react";
import {
  deleteInvestigation,
  loadSaved,
  SAVED_CHANGED,
  STORAGE_KEY,
  updateInvestigation,
} from "./investigation-storage";
import type { SavedInvestigation } from "./investigation-storage";
import type { Investigation } from "./saved-investigation";
import { LIMITS, parseInvestigation, shiftTime } from "./saved-investigation";
import { ReportAction, ShareAction } from "./InvestigationActions";
import { formatUtc } from "./time-presentation";

function state() {
  try {
    return { records: loadSaved(), error: "" };
  } catch (e) {
    return {
      records: [] as SavedInvestigation[],
      error: e instanceof Error ? e.message : "Browser saves unavailable.",
    };
  }
}
function Editor({
  record,
  onDone,
}: {
  record: SavedInvestigation;
  onDone: (message: string) => void;
}) {
  const v = record.investigation;
  const [title, setTitle] = useState(record.title),
    [description, setDescription] = useState(record.description);
  const [at, setAt] = useState("at" in v ? (v.at ?? "") : ""),
    [frame, setFrame] = useState(v.frame);
  const [start, setStart] = useState(
    v.mode === "ground-track" ? v.track.start : "",
  );
  const [duration, setDuration] = useState(
    v.mode === "ground-track" ? String(v.track.duration_minutes) : "90",
  );
  const [step, setStep] = useState(
    v.mode === "ground-track" ? String(v.track.step_seconds) : "60",
  );
  const [index, setIndex] = useState(
    v.mode === "ground-track" ? String(v.track.selected_index) : "0",
  );
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit() {
    setBusy(true);
    setError("");
    try {
      let investigation: Investigation = v;
      if (v.mode === "position")
        investigation = parseInvestigation({ ...v, at });
      if (v.mode === "comparison")
        investigation = parseInvestigation({ ...v, at: at || null, frame });
      if (v.mode === "ground-track")
        investigation = parseInvestigation({
          ...v,
          at: shiftTime(start, Number(index) * Number(step)),
          track: {
            start,
            duration_minutes: Number(duration),
            step_seconds: Number(step),
            selected_index: Number(index),
          },
        });
      await updateInvestigation(record, {
        title,
        description,
        investigation,
      });
      onDone(
        "Local investigation updated. Reopening recomputes any requested calculation; no past result was stored.",
      );
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Update could not be confirmed.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <form
      className="saved-editor controls"
      aria-label="Edit local investigation"
      onSubmit={(e) => {
        e.preventDefault();
        void submit();
      }}
    >
      <p>
        Source identifiers and provenance remain fixed. Use the explorer to save
        a different source as a new investigation.
      </p>
      <label>
        Saved title
        <input
          autoFocus
          required
          maxLength={LIMITS.title}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
      </label>
      <label>
        Saved local notes
        <textarea
          maxLength={LIMITS.description}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </label>
      {(v.mode === "position" || v.mode === "comparison") && (
        <label>
          Saved evaluation time
          {v.mode === "comparison" ? " (blank for elements only)" : ""}
          <input
            required={v.mode === "position"}
            value={at}
            onChange={(e) => setAt(e.target.value)}
          />
        </label>
      )}
      {v.mode === "comparison" && (
        <label>
          Saved coordinate frame
          <select
            value={frame}
            onChange={(e) => setFrame(e.target.value as "ITRS" | "TEME")}
          >
            <option>TEME</option>
            <option>ITRS</option>
          </select>
        </label>
      )}
      {v.mode === "ground-track" && (
        <>
          <label>
            Saved track start
            <input
              required
              value={start}
              onChange={(e) => setStart(e.target.value)}
            />
          </label>
          <label>
            Saved duration (minutes)
            <input
              type="number"
              min="1"
              max="1440"
              required
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
            />
          </label>
          <label>
            Saved step (seconds)
            <input
              type="number"
              min="10"
              max="3600"
              required
              value={step}
              onChange={(e) => setStep(e.target.value)}
            />
          </label>
          <label>
            Saved sample index (zero based)
            <input
              type="number"
              min="0"
              max="360"
              required
              value={index}
              onChange={(e) => setIndex(e.target.value)}
            />
          </label>
        </>
      )}
      <button disabled={busy} type="submit">
        {busy ? "Updating…" : "Save changes"}
      </button>
      <button type="button" onClick={() => onDone("")}>
        Cancel editing
      </button>
      {error && <p role="alert">{error}</p>}
    </form>
  );
}
export default function SavedInvestigations({
  onOpen,
}: {
  onOpen: (v: Investigation) => void;
}) {
  const [data, setData] = useState(state),
    [message, setMessage] = useState("");
  const [editing, setEditing] = useState<SavedInvestigation | null>(null),
    [deleting, setDeleting] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    const refresh = (event: Event) => {
      if (
        !(event instanceof StorageEvent) ||
        event.key === STORAGE_KEY ||
        event.key === null
      )
        setData(state());
    };
    window.addEventListener("storage", refresh);
    window.addEventListener(SAVED_CHANGED, refresh);
    window.addEventListener("focus", refresh);
    return () => {
      window.removeEventListener("storage", refresh);
      window.removeEventListener(SAVED_CHANGED, refresh);
      window.removeEventListener("focus", refresh);
    };
  }, []);
  useEffect(() => {
    if (message) heading.current?.focus();
  }, [message]);
  async function remove(record: SavedInvestigation) {
    setBusy(true);
    try {
      await deleteInvestigation(record);
      setDeleting(null);
      setMessage(
        "Deleted from this browser. Source snapshots and existing shared links were not deleted or revoked.",
      );
      setData(state());
    } catch (e) {
      setMessage(
        e instanceof Error ? e.message : "Deletion could not be confirmed.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="saved-investigations" aria-labelledby="saved-title">
      <h2 id="saved-title" ref={heading} tabIndex={-1}>
        Saved investigations
      </h2>
      <p>
        Local to this browser and application origin. No accounts, cloud storage
        or cross-device synchronization. Clearing site data removes these saves.
        Up to 50 investigations / 256 KiB.
      </p>
      <p>
        Links contain reconstruction parameters, not your local identifier,
        title or notes. Anyone with a link can inspect its parameters; links
        cannot be revoked by deleting a local save.
      </p>
      <button type="button" onClick={() => setData(state())}>
        Refresh local saves
      </button>
      {data.error && <p role="alert">{data.error}</p>}
      {message && <p role="status">{message}</p>}
      {!data.error && !data.records.length && (
        <p>
          No saved investigations yet. Open a stored snapshot, position, track
          or comparison and choose “Save in this browser”.
        </p>
      )}
      {data.records.map((record) => (
        <article
          className="saved-card"
          key={record.id}
          aria-label={record.title}
        >
          <h3>{record.title}</h3>
          <p className="local-notes">{record.description}</p>
          <dl className="metadata">
            <dt>Persistence / schema</dt>
            <dd>This browser only / version 1</dd>
            <dt>Mode / coordinate frame</dt>
            <dd>
              {record.investigation.mode} / {record.investigation.frame}
            </dd>
            <dt>Satellite / exact source</dt>
            <dd>
              NORAD {record.investigation.source.catalog_id} / snapshot #
              {record.investigation.source.snapshot_id}
            </dd>
            {record.investigation.mode === "comparison" && (
              <>
                <dt>Comparison source</dt>
                <dd>
                  NORAD {record.investigation.comparison_source.catalog_id} /
                  snapshot #{record.investigation.comparison_source.snapshot_id}
                </dd>
              </>
            )}
            <dt>Element epoch</dt>
            <dd>{formatUtc(record.investigation.source.orbital_epoch)}</dd>
            <dt>First retrieval</dt>
            <dd>{formatUtc(record.investigation.source.retrieved_at)}</dd>
            {"at" in record.investigation && (
              <>
                <dt>Evaluation time</dt>
                <dd>
                  {record.investigation.at
                    ? formatUtc(record.investigation.at)
                    : "Elements only; no state requested"}
                </dd>
              </>
            )}
            <dt>Local created / modified</dt>
            <dd>
              {formatUtc(record.created_at)} / {formatUtc(record.updated_at)}
            </dd>
          </dl>
          <div className="toolbar">
            <button type="button" onClick={() => onOpen(record.investigation)}>
              Open {record.title}
            </button>
            <button
              type="button"
              onClick={() => {
                setEditing(record);
                setMessage("");
              }}
            >
              Edit {record.title}
            </button>
            <button
              type="button"
              onClick={() => {
                setDeleting(record.id);
                setMessage("");
              }}
            >
              Delete {record.title}
            </button>
          </div>
          {deleting === record.id && (
            <div role="group" aria-label="Confirm local deletion">
              <p>
                Delete this investigation from this browser? Orbital history
                remains unchanged.
              </p>
              <button
                type="button"
                disabled={busy}
                onClick={() => void remove(record)}
              >
                Confirm local deletion
              </button>
              <button type="button" onClick={() => setDeleting(null)}>
                Keep investigation
              </button>
            </div>
          )}
          {editing?.id === record.id && (
            <Editor
              key={record.updated_at}
              record={editing}
              onDone={(msg) => {
                setEditing(null);
                setMessage(msg);
                setData(state());
              }}
            />
          )}
          <ShareAction investigation={record.investigation} />
          <ReportAction investigation={record.investigation} />
        </article>
      ))}
    </section>
  );
}
