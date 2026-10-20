# Investigation reports and evidence export (schema 1 / template 1)

Phase 9 adds on-demand JSON evidence, a printable preview and standalone HTML.
Use **Generate investigation report** from a source/position view, a calculated
track, comparison, saved card or reconstructed shared view. Then download JSON,
download HTML or open the preview and choose **Print report / Save as PDF**.
Opening HTML offline also supports browser printing. Printing does not fetch data.
Generation has loading, cancellation, retry and duplicate-request suppression;
changing context discards pending/captured work. Regenerate explicitly requests new
backend calculations and creates a new report ID/time. Downloads reuse one capture.

## Authoritative data and access

An investigation is currently a validated configuration, saved in browser storage
or encoded in a share link. There is no server investigation table, owner account
or private investigation API. Scientific facts come from exact immutable archive
references and existing backend services. No frontend orbital calculations occur.

Local saved UUID, title, notes and creation time are **excluded** from requests and
exports. Their fields are explicitly null with `browser_only_excluded`, rather
than incorrectly presented as server evidence. The report title describes verified
source IDs and mode. A `configuration-sha256:` identifier describes the configuration,
not a user, saved-record UUID, ownership token or permanent report location.

Anonymous users can read the existing public archive and generate its reports.
Shared read-only views permit export; they still have no save/share mutation
controls. Unknown fields (including private record/owner/title/note fields) are
rejected. There are no protected server records to exercise cross-account access
against. Before introducing accounts/private archives, authorize **both sources**
and any server investigation before building a report; this public boundary is not
a substitute for future per-user authorization. Do not put credentials in inputs.

## Endpoint and bounds

`GET /api/investigation-reports?definition=<URL-encoded JSON>` accepts the existing
[schema-1 definition](saved-investigations.md#versioned-local-schema), with exactly
its relevant fields. Source references contain snapshot ID, catalog ID, orbital
epoch, first retrieval time and lowercase response SHA-256. A comparison requires
both complete references. Invalid/extra fields, duplicate JSON keys, nonfinite
numbers, unsupported versions and invalid sampling fail closed.

```sh
curl --get --fail --data-urlencode 'definition@definition.json' \
  http://127.0.0.1:8000/api/investigation-reports --output evidence.json
```

This requires an existing configured archive; it never creates one. A successful
response has `application/json`, `Cache-Control: no-store`, `nosniff` and an
attachment filename `orbitiq-report-<report UUID>.json`. JSON/HTML browser download
names use the same UUID. Downloads are requested; browser retention is not a
confirmed backup. Reports are not stored, retrievable by UUID or cryptographically
signed on the server.

| Boundary | Limit / behavior |
| --- | --- |
| Decoded definition | 2048 UTF-8 bytes; existing modes only |
| IDs | Positive safe integers; catalog 1–339999 |
| Track | 1–1440 minutes, 10–3600 second step, at most 361 points; selected index/time must agree |
| Scientific bounds | Existing configured sampling, epoch-distance and EOP policies also apply |
| Encoded API report | At most 8 MiB; nonfinite output refused |
| Browser response | Streamed with 8 MiB cap and 25 second timeout; depth/node bounds |
| Production request | Existing 4096-byte URI, read-only method/body/header and calculation-admission limits |
| Release gateway | Existing calculation rate bucket (1 request/second, burst 6); API remains private |

Production limits apply only in the configured production boundary/gateway.
Local development is not an Internet-facing abuse-control configuration. Cancel
aborts browser receipt; synchronous backend work can finish within its existing
bounded calculation rather than being interrupted mid-transform. No background
queue, cache, persistence, ingestion or new external fetch is introduced.

| Failure | Outcome |
| --- | --- |
| Invalid definition/query | 422, safe error envelope, no report |
| Missing snapshot | 404; no newer source substituted |
| Mismatched reference or calculation lineage | 409; no report |
| Corrupt/unverifiable source/archive | Existing safe 422/503 source/storage error; no report |
| Verified sources, unavailable calculation/EOP | 200 `partial`, explicit reason; unavailable vectors are null/absent |
| Output too large | 413 `report_too_large` |
| Invalid/nonfinite output | Safe 500; no evidence download |
| Gateway throttling / admission busy | Existing 429 / 503; retry later |

## Schema and versioning

The generated [JSON Schema](investigation-report-schema.json) describes the actual
backend serialization model. [This complete example](phase-9-export-example.json)
was downloaded through the local release gateway using the genuine archived ISS
source; it is neither an observation nor a database backup.

| Root field | Meaning |
| --- | --- |
| `schema_version`, `template_version`, `kind` | Contract 1, presentation 1, `orbitiq_investigation_report` |
| `report_id`, `generated_at` | New server UUID v4 and generation-start UTC time |
| `status` | `complete` or `partial` requested-content coverage, not scientific certification |
| `investigation` | Configuration identity, generated title, exact definition and explicit excluded local fields |
| `sources` | Primary and optional comparison source, each independently checked |
| `calculation` | `complete`, `unavailable` or `not_requested`, existing service data and safe errors |
| `validation` | Scope, warning status, blocked independent validation, unquantified uncertainty and missing fields |
| `methodology` | Current representation, software versions, frames/units, EOP policy, hash/print scope |
| `limitations`, `warnings` | Explicit scientific/reproducibility limits and captured source/result warnings |

Snapshot mode has no requested state. Element-only comparison retains comparison
data with `not_requested` common-time state. Position includes TEME state. Tracks
include all returned ITRS points with full TEME/EOP derivations in JSON. Comparisons
retain A/B membership, element differences and optional common-time states in the
requested TEME/ITRS frame. A failed whole track has no partial coordinate series.
An unavailable comparison can retain verified metadata/elements; its failed
state/difference fields remain explicitly unavailable.

Unknown schema/template versions are rejected by the renderer. Incompatible field
or scientific-meaning changes require a new schema version and readers/tests.
Presentation changes that affect interpretation require a template version change.
Version 1 calculation data reuse existing documented service structures (represented
as JSON objects in the root schema); this is not a new orbital data standard.

## Evidence, timestamps, units and hashes

Each source records provider/type/URL, validated object name/designator, exact
reference, OMM elements/units, original recorded validator/SGP4 version and status,
current integrity checks, source freshness evaluated at report generation, and
recorded archive insertion time or `unknown_legacy`. Report checking verifies
payload bytes, parsed record, normalized fields/units and provenance through the
existing loader; it does not claim to rerun every original ingestion check.

`payload_hash.value` / `reference.response_sha256` is SHA-256 of the **exact stored
uncompressed CelesTrak GP JSON HTTP response-body bytes**. It excludes headers and
does not canonicalize or hash normalized fields. A multi-record response hash
identifies that entire stored body, while snapshot evidence selects its one record.
It is a locally verified checksum, not a provider-published hash/signature or
independent source authentication. `provider_published_hash` is null/not recorded;
`source_authenticity` is `not_independently_verified`.

The configuration ID is SHA-256 over the version-1 validated definition serialized
by Python `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=True)`
and encoded UTF-8; datetimes first serialize through Pydantic to normalized UTC
(`Z`, microseconds when nonzero). Array order is retained. Equivalent timezone
spellings normalize before hashing. This identifies the input configuration only;
it excludes report time/UUID, results and browser metadata. It is not a package
integrity hash or a claim of identical historical calculations.

Orbital epoch, first retrieval, insertion, requested evaluation, calculation
execution and report generation times are distinct. Inputs require explicit ISO
timezone with at most six fractional digits; numeric, naive and leap-second
literal inputs are refused. Outputs retain explicit UTC (`Z`/`+00:00`). Observation
time is null/not applicable: these are mean elements and calculated states.
Provider publication time is null/not recorded. No missing date is inferred.

Source/state frame is TEME; terrestrial results are ITRS with WGS84 geodetic
latitude/longitude in degrees and ellipsoidal height in km. Cartesian positions
are km and velocities km/s. SGP4 uses WGS72. Per-field OMM units and existing
comparison angular-difference conventions are retained. A difference is not an
independent maneuver/anomaly/collision finding.

Validation is `validated_with_warnings`, with narrowly stated source integrity and
available-calculation scope. `complete` means requested coverage, not accuracy,
authenticity or certification. Independent observation-based validation remains
`blocked`; uncertainty is `unquantified`. Freshness is not accuracy. Missing values
are explicitly null/unavailable, never synthesized zeros.

## EOP and reproducibility

ITRS calculations retain the actual per-result resource hashes, local package
version, prediction flags, policy, leap expiry and versions already emitted by the
science services. Methodology records configured `measured_only` or
`measured_or_predicted`, or invalid configuration, when applicable. TEME/source-only
requests identify EOP as not applicable. Automatic downloads and degraded fallback
remain disabled; unsupported/expired/disallowed EOP produces unavailable results.

This is a **current recomputation** from exact archived sources. Browser saves
never preserved original numeric output. Report UUID/time and calculation times
can differ on regeneration; resources/software/policy can also change. Exact
replay needs matching archived sources, software and EOP/leap resources. The export
records available identifiers but embeds neither original HTTP bodies nor resource
binaries, dependencies or a complete replay environment. Preserve the archive and
verified backups separately. No source acquisition occurs during reporting.

## Printing, security and compatibility

The preview and HTML use one deterministic presentation function over the captured
backend report. They include cover/identity, summary, overview/inputs, results,
provenance, validation, limitations, methodology and footer. All returned track
ITRS/geodetic rows are printed; selected sample/full state and comparisons include
their derivation metadata. Full per-point TEME/EOP derivations remain in JSON, as
the report explicitly states. Summary text describes content; it is not AI or an
unsupported narrative finding.

Use A4 portrait/default scale. Tables repeat headings and avoid splitting rows;
hashes/URLs wrap without truncation. CSS margin boxes provide page counters where
supported. If a print engine lacks them, enable browser headers/footers. Native
PDF fidelity/page numbering varies; Chromium headless PDFs are verified, while
Firefox/WebKit native print dialogs/PDF engines and physical printers are not.
Large tracks intentionally produce longer evidence tables. Browser print settings
and driver behavior can change pagination. PDF is a browser facility; there is no
server PDF engine or bundled PDF dependency.

Preview uses a labelled native modal with keyboard focus, Escape and focus return.
Report-only print styling excludes application navigation and local notes. React
renders text; standalone HTML escapes every interpolation and includes a CSP
disallowing scripts, frames, network resources and forms. No HTML from source names
is trusted. Downloads use bounded payloads and blob URLs with cleanup. No secrets,
raw response bodies, database paths, browser store or log details are exported.
The existing logger records route/status/size/timing, not report query contents.

No dependency, environment variable, schema migration, public deployment or
production infrastructure change is required. Rebuild release images to pick up
the route and gateway rate-limit classification. Phase 8 launch gates remain
separate. Automated browser checks use only loopback services with a restored
read-only archive, never a production archive or fake live observations.

## Verification commands

```sh
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
cd frontend
npm test
npm run lint
npm run format:check
npm run build
```

For actual browser verification, use the pinned `deploy/Dockerfile.browser` runtime
and an isolated local release plus separate restored archive. Run
`scripts/verify_report_browser.py --base-url http://127.0.0.1:8080 --engine chromium
--first <exact ID> --second <exact ID> --output-directory <private artifacts>`;
repeat with Firefox/WebKit. The runner requires existing genuine sources and
writes downloads/screenshots/results; Chromium also writes PDFs. Never substitute
fabricated production observations. Validate PDF text/page counters using
`python scripts/verify_report_pdf.py --directory <artifacts> --output <results.json>`
(requires `pdftotext`). Add `--maximum-track` to the Chromium runner to check 361
samples and their printed rows. See [actual Phase 9 evidence](phase-9-report.md).
