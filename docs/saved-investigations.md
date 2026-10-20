# Saved investigations and sharing (schema 1)

Use the existing backend/Vite startup commands and explicit database path in the
README. No new dependency, environment variable, endpoint or migration is needed.
The application has no authentication or user ownership service. Investigation
records therefore live in browser storage; no anonymous server write API exists.

## Use

Inspect a discovery detail or historical source, calculate a TEME position, generate
a track and select a returned sample, or complete an A/B comparison. **Save in this
browser** captures that actual context, with a title and optional private local
notes. A successful message follows a validated write and exact storage read-back.
An incomplete source cannot be saved. Editing calculation inputs clears old results.

Open **Saved investigations** to list, reopen, edit or delete a local record, or
copy its share link. The editor supports title/notes, position evaluation time,
comparison time/frame and track interval/step/selected sample. Source references
stay fixed; save a new investigation to use another source. Deletion requires a
second confirmation and affects only the local record. It neither deletes archived
snapshots nor revokes parameter links. Open views do not silently update saved records.

`#/saved` opens the local list. `#/investigation?...` reconstructs a parameter
link. Opening a local record also places its parameter link in the address bar;
reloading that URL opens a read-only shared view, while retaining the local save.
Use the list to edit that record. **Explore an editable copy** explicitly creates
an editable in-memory view; it does not automatically save or import anything.
Camera/timeline navigation is temporary and does not rewrite a shared definition.
The copy button confirms clipboard completion; if restricted, select the displayed
link and copy manually. Titles, notes and local IDs are excluded from links.

## Persistence and recovery boundaries

Storage key: `orbitiq.saved-investigations.v1`. Data belong to this browser profile
and origin (scheme, hostname and port), including localhost development ports.
Reload and normal browser restart retain saves when browser storage is retained.
Private browsing, profile deletion, clearing site data, storage eviction or quota
failure can remove or prevent saves. These are plaintext local data accessible to
scripts on this origin; do not put credentials or sensitive information in notes.
There is no cloud backup, cross-device synchronization or browser-save import/backup
feature. Phase 9 adds explicit [investigation reports and evidence export](investigation-reports.md)
for current configurations and backend results. These exports exclude local titles,
notes, UUIDs and creation times and do not restore the browser's saved list.

Keep a browser/profile backup if these local records matter. Advanced users may
copy the exact value of the key through browser developer tools into a private
backup file. Retain the original before any manual restoration; inspect a backup
in a separate browser profile first. There is no automatic merge/import/repair.
Corrupt, oversized or unsupported-version data are preserved verbatim and writes
are refused; the UI does not silently reset the store. A read-back failure means
no save was confirmed, even if a browser accepted the write before the failure.
Do not clear the key as a first recovery step. The SQLite archive has its separate
[backup and restore runbook](backup-restore-runbook.md); it contains no local saves.

All writes reread and validate the full envelope. Web Locks serialize cooperating
same-origin tabs where available. Updates/deletes reject stale record contents,
including edits sharing a millisecond timestamp. Without Web Locks, the synchronous
fallback has no cross-tab atomicity guarantee; avoid concurrent editing. An exact
read-back confirms the current stored value, not disk durability or future retention.

## Versioned local schema

Envelope: `{ "schema_version": 1, "records": [SavedInvestigation, ...] }`.
Each record has exactly these fields:

| Field | Meaning |
| --- | --- |
| `schema_version` | Integer `1`; unknown versions rejected without migration/reset |
| `id` | Cryptographically generated UUID v4, local identity only |
| `title`, `description` | Trimmed title and optional notes; rendered as text |
| `created_at`, `updated_at` | Browser clock timestamps, explicit UTC; modification cannot precede creation |
| `investigation` | Validated reconstruction inputs below |

Each investigation has `schema_version: 1`, `mode`, `frame`, `source` and only
the fields required by its mode. Every source contains exactly `snapshot_id`,
`catalog_id`, `orbital_epoch`, `retrieved_at`, `response_sha256`. A comparison has
a second complete reference in `comparison_source`; both are verified separately.

| Mode | Frame | Additional fields |
| --- | --- | --- |
| `snapshot` | `TEME` | None; original source inspection, not an evaluation time |
| `position` | `TEME` | `at`: requested propagation time |
| `ground-track` | `ITRS` | `at`: selected sample time; `track`: `start`, `duration_minutes`, `step_seconds`, `selected_index` |
| `comparison` | `TEME` or `ITRS` | `at`: common evaluation time or `null` for element-only comparison; `comparison_source`; `category`: `all`, `shared`, `added`, `removed` or `incompatible` |

The source frame is TEME. Backend conventions remain SGP4/WGS72, Cartesian km and
km/s; tracks transform to ITRS and WGS84 geodetic degrees/ellipsoidal km. Those
fixed conventions are defined by this schema and existing services, not mutable
URL choices. Store references, not orbital payloads, calculated vectors or images.
Camera orientation/zoom, disclosure state and playback state are not serialized;
camera defaults and paused playback apply, while the selected track sample is restored.

Bounds: 50 records, 256 KiB total UTF-8 envelope, 8192 bytes per record and 4096
bytes per investigation. Titles are nonempty, single-line, at most 120 JavaScript
string code units; descriptions at most 1000. Unsafe control characters are refused.
Snapshot IDs are positive safe integers; catalog IDs are 1–339999. Timestamps must
have an explicit timezone, valid calendar date and at most six fractional digits;
they normalize to UTC with six digits. Leap-second literals are not accepted.
Track duration is an integer 1–1440 minutes, step 10–3600 seconds, at most 361
samples, with an in-range zero-based index and matching `at = start + index*step`.
Unknown keys, invalid enums, duplicate local IDs and unsupported versions fail closed.
Backend time-window and resource limits still apply and may be stricter.

## URL contract and access

Format: `<application-origin>/<application-path>#/investigation?<parameters>`.
The fragment is parsed by the app; it is not an API path or server storage ID.
The generator removes any original query string. Full URL length is at most 2048
characters; only the 19 known parameter names are allowed, once each, and every
parameter must be relevant to the selected mode. Only HTTP/S URLs without user
credentials are accepted. No executable deserialization or external data URL is used.

| Parameters | Meaning |
| --- | --- |
| `v=1`, `mode`, `frame` | Schema and mode/frame above |
| `catalog`, `snapshot`, `epoch`, `retrieved`, `sha` | Complete first source identity; `sha` is lowercase 64-digit SHA-256 |
| `at` | Position/selected track/common comparison time; absent for snapshot or element-only comparison |
| `b_catalog`, `b_snapshot`, `b_epoch`, `b_retrieved`, `b_sha`, `category` | Comparison only |
| `start`, `duration_minutes`, `step_seconds`, `selected_index` | Ground track only |

All state is validated before source requests. Resolution requests the exact
snapshot ID through the existing bounded listing API, compares catalog, epoch,
retrieval and hash, then requests detail through the existing source-validation
service. Missing records, unsupported provenance or mismatches are explicit errors.
Metadata alone do not prove payload availability; detail retrieval must succeed.
It never substitutes a newer snapshot or starts ingestion. A recipient with an
empty or different archive cannot reconstruct the investigation merely from a link.

Links contain no title, notes, user identity, tokens, stored numerical output,
resource-policy override or administrative permission. Anyone with a link and
access to the matching archive can reconstruct its public scientific parameters.
These are not secret capability tokens and have no expiry or revocation service.
Shared input controls are disabled and local mutation actions are absent; explicit
editable copies do not alter the sender's browser. The recipient may edit their
own URL parameters, subject to the same validation and backend rules.

## Scientific meaning

Satellite identity, source epoch, first retrieval, requested evaluation time,
calculation execution time and browser save timestamps remain distinct. There is
no observation timestamp because these are calculated orbital states, not direct
observations. Existing views display provenance, frame, units and freshness.

Restoring inputs means exact archived references and supported parameters match.
Subsequent calculations use the current backend implementation, library versions
and available EOP/leap resources. Original numerical results and original EOP
resources are not captured by local saves; byte-identical historical output is
not guaranteed. Strict resource/time policies remain authoritative. Missing or
disallowed resources produce errors rather than fabricated coordinates.
Independent observation-based prediction validation remains **BLOCKED** and
uncertainty remains unquantified. Numerical reference agreement is not universal
prediction accuracy or evidence of physical maneuvers/collisions.
