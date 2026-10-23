# Stored catalog and portable investigation recovery (E6)

## Begin with archived data

The Explorer opens with **Start with stored satellite data**. It reads the
existing `/api/snapshots?limit=5` and `/api/readiness` endpoints independently.
These requests do not collect provider data, initialize storage, or modify the
archive. **Browse stored catalog** opens Discovery & history; **Inspect data
readiness** opens the existing operational assessment.

- Loading is bounded by the existing client timeouts (catalog 10 seconds,
  readiness 5 seconds). Reload retries the assessment and cancels obsolete work.
- Populated lists show the newest five immutable snapshot records. An exact
  count applies only within the API's history anchor and bounded assessment.
  Repeated NORAD IDs are possible. Unique satellites and globally usable source
  counts are not inferred. Unavailable counts are explicitly identified.
- Empty means an exact zero with no rows or continuation, not a transport error.
  Ask the operator to follow the [installation guide](../README.md) and
  [collection guide](ingestion-operations.md). The browser cannot initiate a provider
  refresh. Repair configuration without deleting an existing archive.
- Provider collection failure does not mean archived records disappeared. Last
  audited successful acquisition is shown separately from first retrieval and
  orbital epoch. An acquisition can deduplicate to an existing snapshot.
- Staleness comes from the backend's established freshness assessment. Recent
  retrieval does not establish a recent epoch or prediction accuracy. Current
  data require an explicit operator collection, subject to the existing cooldown.
- Incomplete or unsupported source metadata prevents opening that row as a
  calculation source; other records remain accessible. Discovery provides details.
- A failed reload retains previously loaded metadata with an explicit warning.
  Opening always validates the exact stored source through the existing detail
  endpoint before passing it to Explorer. There is no fixture/latest substitution.

Source and epoch details are shown inline. The expandable first-run guidance
explains selecting a record and requesting a backend position/ground track near
its epoch. Calculated positions are not observations; uncertainty is unquantified.

## Export one local save

In **Saved investigations**, each card has **Export portable bundle**. This uses
local browser APIs and a native download, without an upload or new server endpoint.
Check the browser's download result and keep the file somewhere you control.
The application can report that a download was requested, not that your operating
system successfully retained it. Preparation failures are visible and retryable.

The single-record version-1 bundle wraps the existing version-1 saved record:

```json
{
  "kind": "orbitiq_saved_investigation_bundle",
  "schema_version": 1,
  "exported_at": "2026-10-23T00:00:00.000000Z",
  "record": {
    "schema_version": 1,
    "id": "c7fcaa37-5da9-4bd5-8000-582c07b66830",
    "title": "E6 SYNTHETIC FORMAT EXAMPLE - NOT OBSERVED HISTORY",
    "description": "",
    "created_at": "2026-10-19T00:00:00.000000Z",
    "updated_at": "2026-10-19T00:00:00.000000Z",
    "investigation": {
      "schema_version": 1,
      "mode": "snapshot",
      "frame": "TEME",
      "source": {
        "snapshot_id": 7,
        "catalog_id": 25544,
        "orbital_epoch": "2024-01-01T00:00:00.000000Z",
        "retrieved_at": "2024-01-01T01:00:00.000000Z",
        "response_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
      }
    }
  }
}
```

This example describes synthetic input references, not available archive data or
scientific evidence. The title and requested parameters are included; **private
local notes are excluded by default**. The per-card checkbox explicitly includes
them. The file is plaintext: titles/notes can identify you. Inspect it before
sharing. The filename uses only the mode and UUID, never user-supplied title text.

Supported modes retain their existing schemas: `snapshot` (TEME), `position`
(TEME with `at`), `ground-track` (ITRS with `at` and bounded track sampling), and
`comparison` (TEME/ITRS, optional calculation time, second exact source, category).
A track includes its start, duration, step and selected sample index. Source
references retain snapshot and catalog IDs, epoch, first retrieval and payload
SHA-256. Timestamps normalize to UTC with six fractional digits. Original local
creation/modification times remain unchanged. Export time is separate.

Existing saves contain **inputs**, not results, findings, uncertainty estimates,
or scientific acceptance metadata. This feature preserves that representation.
It does not silently redesign the existing report/evidence export format.

## Restore in another browser

1. Open **Saved investigations**, then choose a **Portable investigation file**.
2. Review its title, identifier, mode/frame, exact source provenance, calculation
   time/sampling or comparison source, original local times and included notes.
   Previewing does not write anything. Cancel returns focus to file selection.
3. Use **Confirm local import** to persist. Success announces whether a save was
   inserted or already present. The saved list updates immediately.
4. Open the restored investigation. Exact source checks and backend calculation
   reconstruction follow the existing saved-investigation workflow.

JSON is bounded to **16 KiB** (16,384 UTF-8 bytes) before reading and again after
reading. Empty files, unreadable/invalid UTF-8, malformed JSON, duplicate keys
(including escaped equivalents), unknown versions/fields, unsupported modes,
invalid IDs/timestamps/provenance and invalid sampling are rejected. Existing
validators enforce saved-record and input bounds. File extension/MIME alone does
not establish validity. Errors do not echo raw imported content.

Imported text remains text: no HTML, scripts, formulas or URLs are executed.
There is no authenticity signature, confidentiality or scientific promotion.
Do not interpret structurally valid JSON as trusted results.

No source snapshot payloads, full orbital database, EOP/leap resources, private
attachments, server findings or evidence reports are in the bundle. The target
must have the exact referenced archive records. Missing IDs or differing hashes,
epochs or retrieval times produce an explicit reconstruction failure; the system
does not substitute the latest source or claim those records were restored.
Once Saved investigations has loaded, a file can restore local inputs offline.
Opening/calculating needs the local
API and matching archive. This is not database backup or disaster recovery.

## Collisions, failures and concurrency

- Identical normalized record content (ignoring only its UUID) is already saved;
  confirming does not write or duplicate it. Export time is not part of that test.
- An existing UUID with different content is never overwritten. Cancel, or
  explicitly choose **Import as a separate copy with a new identifier**. Copying
  preserves original input/local timestamps and generates a secure UUID. Repeating
  that import finds the previously copied content and does not duplicate it.
- Confirmation revalidates the file record and destination. A changed destination
  since preview requires a fresh preview. Import shares the existing same-origin
  Web Lock with save/edit/delete writers. Concurrent cooperating application tabs
  are serialized; uncooperative old app versions or direct developer-tool writes
  are outside that guarantee.
- Import requires Web Locks and secure UUID support when copying. Use a current
  supported browser on localhost or HTTPS. Unsupported contexts fail explicitly;
  export remains available. There is no unsafe fallback for import.
- The existing store remains limited to 50 saves / 256 KiB. Corrupt or unsupported
  destination storage refuses mutation; the application does not clear it.
  Quota/permission errors preserve prior records. No saves are evicted to make room.
- Persistence uses the existing atomic `localStorage.setItem`, followed by a read
  check. If confirmation cannot be read back after a successful write, success
  cannot be confirmed; inspect/refresh local saves before retrying. There is no
  multi-step destructive rollback. Retrying validated unchanged content is safe.

Playwright WebKit 1.62 offline emulation rejects even in-memory `File` reads
(`NotReadableError` with both arrayBuffer and FileReader). The WebKit regression
therefore denies all HTTP through browser routing and proves a health request
fails before running the same native-file recovery checks. Chromium/Firefox use
context offline mode. This is not an offline-install or physical-device Safari
certification; loading an unvisited application screen still needs its assets.

Keyboard focus moves to the preview and returns to file selection on cancel or
the restore heading on success. Errors are associated with file input and
announced. Automated accessibility scans supplement E2 checks and manual review;
a clean scan alone is not complete accessibility certification.

## Boundaries

Phase 11.3.1 remains **PARTIAL**; scientific evaluation remains **BLOCKED**.
ESA time clarification, KIN-quality qualification and frame alignment remain
unresolved; historical availability/creation timestamps are unknown, complete GP
fitting lineage and statistical independence are not established. No qualified
Swarm-A residuals are produced by this feature.

E4 remains **OPEN**. Hosting/public HTTPS, independent off-machine recovery,
monitoring/actual alert delivery, and default-branch protection/required checks
remain blocked. Previously verified bounded artifact retention is separate.
No production deployment, DNS change, paid resource or private-data upload is
part of E6. See the [E6 report](engineering-e6-report.md) for executed checks.
