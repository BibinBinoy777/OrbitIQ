# Phase 11.3.1 — historical attachment receipt assessment

Assessment on **21 October 2026**. The user supplied an actual attachment,
`sat000039452.json`, with a CelesTrak fulfillment summary for Swarm-A, NORAD
39452 / 2013-067B, 2013-12-30 through 2014-01-02, three element sets.
**The attachment is now received, but strict JSON validation fails.**
Phase 11.3.1 remains PARTIAL; no scientific residual calculation is authorized.

This is a new receipt checkpoint, not a rewrite of the earlier reports that
correctly recorded no attachment at their execution time. The supplied message
attributes the file to CelesTrak. Original email headers/mail authentication were
not supplied or independently checked. Actual provider-email receipt/acquisition
and historical publication/availability timestamps remain unknown. The request
timestamp is not substituted for any of those times. Personal correspondence,
contact details, IP address and browser fingerprint are not reproduced here.

## Original preservation and intake result

| Item | Actual result |
| --- | --- |
| Original file size | **1,227 bytes** |
| Whole-original SHA-256 | `c55dc4cbb2331a162014833a1a354e6f62ff4572d5238954b8108f69cae3053c` |
| Original modified or overwritten | **No** |
| Strict JSON | **Rejected**: `JSONDecodeError`, expecting value, line 1, column 129, zero-based ASCII byte offset 128 |
| Leading-decimal numeric tokens outside strings | **9** |
| Original-file accepted candidates | **0**; document parsing stopped before record enumeration |
| Database ingestion / prediction evaluations / real ESA residuals | **0 / 0 / none** |

The unchanged published `scripts/inspect_historical_gp.py` captured original
bytes and receipt metadata before parsing. The original, receipt, inspection and
last-written manifest are stored in a fresh mode-0700 capture beneath the existing
Git-ignored private `data/historical-gp-intake/` location, with mode-0600 files.
Every manifest hash/size and the equality of uploaded/captured original bytes
were checked. Source-derived diagnostics and regression evidence are separately
retained beneath ignored `data/historical-gp-intake-assessments/`.

The intake audit exited **0**, meaning capture and diagnostic execution completed;
its document-validation/scientific result was **BLOCKED**. This is not a successful
JSON acceptance. Zero network, database, process, propagation or residual attempts
were recorded by the offline audit and callable sentinels. No source URL or
historical retrieval time was invented. The original attachment is not a public
test fixture and was not added to Git.

## Format diagnosis, not accepted normalization

JSON number syntax requires an integer part before a decimal point. A numeric
token shaped like `.123` must instead have the form `0.123`; this also applies
to leading-decimal scientific notation. The supplied file has nine such tokens.
The strict reader correctly refuses the document rather than silently repairing it.

A separately labelled diagnostic masked string literals, located exactly those
nine numeric tokens, and inserted only the missing zeros **in memory**. Decimal
comparisons confirmed equal numeric values for each before/after token; all
other bytes were retained. That probe then passed strict JSON decoding and the
existing intake/element-model checks for all three records, with no duplicates
or additional model exclusions. The probe is explicitly source-derived diagnostic
material, not a genuine rewritten provider attachment or an approved input.

No normalized GP payload was saved or ingested, no ordinary parser was loosened,
and no missing orbital field or value was fabricated. Diagnostic original/probe
hashes and exact byte offsets are retained privately. The whole-original hash
above continues to identify the actual received file. Model compatibility of
an in-memory probe does not retroactively make that original valid JSON or
authenticate its provider, fitting lineage or availability.

The following source-index/epoch metadata was inspected in that diagnostic;
UTC interpretation uses the existing CelesTrak GP convention for suffix-free
epochs. These are **not selected evaluation inputs**:

| Original zero-based source index | Epoch text, interpreted as UTC | Identifier checks | Model-only probe |
| --- | --- | --- | --- |
| 0 | `2013-12-30T20:24:39.765600` | 39452 / 2013-067B | Compatible |
| 1 | `2014-01-01T05:30:45.095904` | 39452 / 2013-067B | Compatible |
| 2 | `2014-01-02T06:43:57.421344` | 39452 / 2013-067B | Compatible |

All three probe epochs are within the intended request calendar scope and the
existing ±7-day bound for both endpoints of the ordinary convertible ESA interval.
This is a bounded epoch-offset diagnostic, **not approved temporal pairing**.
No closest-epoch record was selected. Dynamic satellite initialization/propagation
was not executed, and no claim of full dynamic parser validation is made.
Historical availability remains null and forecast eligibility remains false.

## Acceptance status and next action

| Criterion | Updated checkpoint |
| --- | --- |
| AC5 genuine GP/TLE acquired/validated | **PARTIAL**: an original attributed historical attachment was supplied and hash-preserved, but its strict JSON input validation fails and source authentication is limited to the supplied provenance |
| AC6 spacecraft identity matching | **PARTIAL**: attachment labels/probe identifiers agree with the known reference mapping; no fully accepted GP input yet |
| AC7 temporal overlap/pair suitability | **BLOCKED**: preliminary epoch bounds fit, but original-format acceptance, actual pair/provenance/availability assessment and approved reference-quality selection remain open |
| AC12 TEME→reference realization qualification | **BLOCKED**: no approved IGb08 treatment or uncertainty budget |
| AC16 qualified operational adapter | **BLOCKED**: no qualified input/reference pair or operational adapter |

This checkpoint records progress in acquisition, not a new full 22-criterion
acceptance assessment. Full-reference time anomalies/precision, format/interval
documentation discrepancies, per-epoch quality acceptance, actual-pair lineage
and independence also remain unresolved. Earlier 5,118 converted / 2,529 excluded
time diagnostics remain prior evidence; they were not rerun here. Independent
prediction accuracy is unestablished and uncertainty remains unquantified.

The next input-format step is either a corrected strict-JSON export from the
provider or a separately reviewed, explicitly versioned normalization path that
preserves the original hash, transformation ledger and record indices. Neither
is silently authorized for scientific use by this diagnostic. Do not hand-edit
the original or call a reserialized derivative original provider bytes. Retain
any corrected provider response as a new private capture, with its own hash and
actual receipt metadata; do not replace this original.

Prepared provider follow-up, **not sent by this task**:

> Thank you for the three historical Swarm-A / NORAD 39452 element sets. The
> supplied JSON attachment contains nine numeric literals without a leading zero
> before the decimal point, which strict JSON readers reject. Could you resend
> the same source records as valid JSON, preserving the original epochs, element
> set identifiers and numerical precision? Please retain any available source
> creation/publication/archive timestamps and applicable reuse information. If
> those timestamps are unavailable, please leave their availability unknown.

Even after format acceptance, do not calculate real residuals until reference
time/quality/frame treatment and actual pairing are qualified. Unknown historical
availability can support only an otherwise justified retrospective comparison,
not a claim that OrbitIQ issued a historical forecast.

## Actual verification and preserved state

- Fresh targeted regression command: `uv run --locked pytest -q
  backend/tests/test_historical_gp_intake.py
  backend/tests/test_phase1131_qualification.py
  backend/tests/test_phase113_swarm_inspection.py`: **159 passed**, zero
  failures/errors/skips. Existing deliberate duplicate-ZIP fixture warning only.
- Actual original-file intake audit and separately instrumented format probe
  completed with zero network/database/process/propagation/residual attempts.
- All **294** starting nonignored source/report files and **16** existing private
  data files remain byte-identical. No application code, test, dependency,
  scientific guard or prior report was modified.
- Original database bytes, schema, tables, integrity and foreign-key fingerprints
  remain unchanged. Database SHA-256 remains
  `ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
- The full backend/frontend/browser/PDF suites and builds were **not rerun** for
  this data receipt and documentation checkpoint. Earlier results remain scoped
  to their recorded source/runtime states and are not claimed as new executions.

Branch remains `phase-11.3.1-readiness-hardening`, HEAD
`371ce35b577209401ba7961e5bd29c3bd65a9c4d`; index remains empty. No commit, push,
remote CI dispatch/rerun, merge, release, deployment or production-infrastructure
change occurred in this receipt assessment. Its new report and all private
attachments/diagnostics remain local. Existing CI success applies to the published
readiness commit, not to this new uncommitted receipt report or scientific input
qualification. Phase 8 production gates remain separate and open.
