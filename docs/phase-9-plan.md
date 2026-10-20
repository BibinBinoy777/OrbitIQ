# Phase 9 — Investigation reports and evidence export

## Audited baseline and contract

Start: clean `main` at `341812ae66409691e9cf07b15e50dba3ab894e26`.
The archive is schema-3 SQLite with immutable source snapshots, raw GP response
bytes, normalized OMM fields/units and ingestion provenance. Browser saves and
parameter links use the existing validated version-1 investigation definition:
snapshot, TEME position, ITRS ground track/selected sample, or A/B comparison.
There is no server-owned investigation table, authentication or private archive
ownership service. Saved UUID/title/notes/creation time exist only in the browser.

Authoritative scientific exports must resolve exact source references through
existing source validation and calculation/comparison services. Browser definitions
are inputs, never evidence of a successful calculation. No source acquisition,
database migration, persistent export store, queue, AI or new dependency is needed.

Source hashes identify exact stored uncompressed CelesTrak GP JSON response-body
bytes. They are not normalized-record hashes, provider-published signatures or
proof of observational accuracy. Source observation/publication timestamps and
independent source authentication are not recorded. Insertion times exist only
where actually recorded. Calculation timestamps/versions and ITRS EOP/leap hashes,
policy and geodetic units are already available from scientific services.

## Design before implementation

- Add a bounded read-only backend report endpoint with a versioned canonical model.
  Accept the existing definition and revalidate its exact catalog/ID/epoch/retrieval/
  checksum references. Missing or mismatched sources refuse export; no substitution.
- Identify an investigation configuration using a documented normalized-definition
  SHA-256, distinct from source hashes and browser UUIDs. Each generated report has
  a separate report UUID/server timestamp. Deterministic titles describe the
  configuration; saved title, notes, UUID and creation time are explicitly excluded
  browser-only metadata. No fictitious server investigation identity is introduced.
- Reuse backend calculations. Capture results once per generation. Source-only or
  element-only requests do not claim a position calculation. Scientific calculation
  failures retain verified source context and explicit unavailable/partial status;
  they contain no fabricated zero vectors or partial ground tracks.
- Both JSON download and printable HTML/print preview use that same captured report
  object, with no frontend orbital math or second calculation request. Include the
  required cover, summary, overview, results, provenance, validation, limitations,
  reproducibility and footer. Printing isolates the report from the application.
- Expose report actions in existing investigation contexts and saved/read-only
  views. Abort stale work, bound responses, suppress duplicate generation, allow
  explicit retry and escape all report text. Exclude local/private notes and secrets.
- Keep anonymous access limited to the existing public read-only archive. Reject
  attempts to pass private ownership/local metadata as report inputs. No account
  or authorization capability is invented. Future protected archives must apply
  their access policy before report construction.
- Apply existing production request/admission/rate limits to the new route. Keep
  offline EOP, science tolerances, deduplication and immutable archive guarantees.

## Acceptance and planned verification

| Criterion | Evidence required |
| --- | --- |
| AC-01 JSON | Actual API and browser download; documented versioned schema and attachment headers |
| AC-02 print | Accessible preview, standalone escaped HTML, report-only browser printing/PDF; page/table/hash layout checks |
| AC-03 traceability | Exact identities/hashes, original byte scope, source links and explicit authenticity/publication gaps |
| AC-04 scientific metadata | Backend-value comparisons for TEME/ITRS, epochs/timestamps/units, versions and EOP policy/resources |
| AC-05 honesty | Source refusal and unavailable-calculation tests, explicit source-only/missing/legacy/uncertainty labels |
| AC-06 consistency | One captured model; cross-format identity/provenance/value/validation/EOP checks, including changes during requests |
| AC-07 access | Existing public archive boundary, rejected invalid/private fields, no local notes/store exposed and no admin operation |
| AC-08 regression | Complete backend/frontend and trusted scientific reference regressions; normal archive/report preservation |
| AC-09 docs | API/schema/hash/time/status/printing/security/limits and reproducibility documentation |
| AC-10 verification | Actual lint/format/type/build, API/integration and available browser/PDF results, with failures disclosed |
| AC-11 completion | Factual phase report and evidence; unverified compatibility/infrastructure kept separate |

Phase 8 remains open for hosting/domain/public HTTPS, independent host-loss
recovery, production monitoring/alerts and required repository protection. The
published Phase 8 commit passed its exact CI; new Phase 9 work requires separate
publication authorization and its own exact-commit verification. No commit, push,
deployment, remote settings change or new acquisition is authorized by this phase.
