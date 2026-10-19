import { useRef, useState } from "react";
import type { Investigation } from "./saved-investigation";
import {
  LIMITS,
  parseInvestigation,
  shareLink,
  titleFor,
} from "./saved-investigation";
import { saveInvestigation } from "./investigation-storage";

export function ShareAction({
  investigation,
}: {
  investigation: Investigation;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [result, setResult] = useState<{
    key: string;
    url: string;
    message: string;
  } | null>(null);
  const [busy, setBusy] = useState(false);
  const key = JSON.stringify(investigation);
  async function copy() {
    setBusy(true);
    try {
      const url = shareLink(investigation, window.location.href);
      setResult({
        key,
        url,
        message:
          "Link created. It contains view parameters; your title and notes are not included.",
      });
      try {
        if (!navigator.clipboard?.writeText) throw new Error();
        await navigator.clipboard.writeText(url);
        setResult({
          key,
          url,
          message:
            "Share link copied. Title and private notes were not included.",
        });
      } catch {
        setResult({
          key,
          url,
          message:
            "Clipboard access was unavailable. Select and copy the link below; copying has not been confirmed.",
        });
      }
    } catch {
      setResult({
        key,
        url: "",
        message:
          "A link could not be created. Check the view parameters and application URL.",
      });
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="share-action">
      <button type="button" disabled={busy} onClick={() => void copy()}>
        {busy ? "Creating share link…" : "Copy share link"}
      </button>
      {result?.key === key && (
        <>
          <p role="status">{result.message}</p>
          {result.url && (
            <>
              <label>
                Shareable investigation link
                <input ref={input} readOnly value={result.url} />
              </label>
              <button
                type="button"
                onClick={() => {
                  input.current?.focus();
                  input.current?.select();
                }}
              >
                Select link for manual copying
              </button>
              <p>
                Anyone with this link can reconstruct its parameters if the same
                archived snapshots remain accessible. It does not share your
                browser’s saved list.
              </p>
            </>
          )}
        </>
      )}
    </div>
  );
}

export default function InvestigationActions({
  build,
  readOnly = false,
}: {
  build: () => Investigation;
  readOnly?: boolean;
}) {
  const [title, setTitle] = useState<string | undefined>();
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<{
    key: string;
    message: string;
    error: boolean;
  } | null>(null);
  let context: Investigation;
  try {
    context = parseInvestigation(build());
  } catch {
    return readOnly ? null : (
      <p className="notice">
        Saving this view requires complete source identity, epoch, retrieval and
        hash metadata.
      </p>
    );
  }
  if (readOnly) return null;
  const key = JSON.stringify(context);
  async function save() {
    setBusy(true);
    try {
      const saved = await saveInvestigation(
        context,
        title ?? titleFor(context),
        description,
      );
      setFeedback({
        key,
        message: `Saved “${saved.title}” in this browser. Open Saved investigations to reopen it.`,
        error: false,
      });
    } catch (e) {
      setFeedback({
        key,
        message:
          e instanceof Error ? e.message : "Local save could not be confirmed.",
        error: true,
      });
    } finally {
      setBusy(false);
    }
  }
  return (
    <section
      className="investigation-actions"
      aria-label={`Save or share ${context.mode} investigation`}
    >
      <h4>Keep this investigation</h4>
      <p>
        {context.mode} · exact source #{context.source.snapshot_id}. Local saves
        belong to this browser and do not sync across devices. Share links
        contain parameters, not notes or calculated results.
      </p>
      <form
        className="controls"
        onSubmit={(e) => {
          e.preventDefault();
          void save();
        }}
      >
        <label>
          Investigation title
          <input
            required
            maxLength={LIMITS.title}
            value={title ?? titleFor(context)}
            onChange={(e) => setTitle(e.target.value)}
          />
        </label>
        <label>
          Private local notes (optional)
          <textarea
            maxLength={LIMITS.description}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </label>
        <button type="submit" disabled={busy}>
          {busy ? "Saving locally…" : "Save in this browser"}
        </button>
      </form>
      {feedback?.key === key && (
        <p role={feedback.error ? "alert" : "status"}>{feedback.message}</p>
      )}
      <ShareAction investigation={context} />
    </section>
  );
}
