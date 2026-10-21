# Phase 11.3.1 — pre-acquisition readiness hardening

Local work on **21 October 2026**. **Software readiness improved; Phase 11.3.1
remains PARTIAL and overall scientific qualification BLOCKED.** No genuine
historical GP attachment was received or acquired, no temporal pair was approved,
and no actual ESA prediction/reference residual or accuracy result was generated.

The user-provided confirmation states that a CelesTrak request for Swarm-A,
39452, 2013-12-30 through 2014-01-02, JSON, was submitted at
2026-10-21T06:10:16Z. This supersedes the prepared-request status for next actions;
earlier reports remain unchanged as historical execution records. A request
confirmation is not orbital data. Personal correspondence/contact/IP information
was not copied into the repository. No request, login, email or source download
was performed by this task.

## Outstanding acceptance criteria

These are the exact four BLOCKED criteria from the prior 22-criterion assessment.
None has been promoted by readiness work:

| AC | Meaning | Current evidence / blocker |
| --- | --- | --- |
| 5 | Genuine GP/TLE acquired/validated | Request confirmation supplied; actual original attachment absent. Synthetic format tests do not satisfy acquisition or authentication. |
| 7 | Temporal overlap/pair suitability | No authentic GP epoch/provenance/availability and no accepted reference-quality interval; bound diagnostics are not actual pairing. |
| 12 | TEME→reference realization qualification | ESA source is IGb08; the pipeline supplies TEME/ITRS. No approved precision-specific realization treatment or justified error budget. |
| 16 | Qualified operational adapter | No qualified pair or operational importer. Intake diagnostics deliberately do not propagate, normalize reference positions or calculate residuals. |

AC6 identity matching remains PARTIAL without an actual GP. AC9 actual GPS
conventions and AC10 required conversions remain PARTIAL because the full-source
precision/second-60 exclusions are unresolved. The prior assessment remains
**15 PASS / 3 PARTIAL / 4 BLOCKED**, with evidence scoped to its original execution;
the new readiness deliverables do not redefine or silently close those criteria.

## Inspection and implementation

Started on `phase-10-evidence-replay`, HEAD
`be3710dae9f21bae817637d7bfdb87509b3f6a34`, with **51** unstaged
modified/untracked Phase 11 paths and an empty index. Captured hashes for **288**
existing nonignored source/report files, **14** private ESA/qualification files,
and database bytes plus full schema/table/integrity/foreign-key fingerprints.
Inspected the three prior Phase 11.3.1 documents, retained qualification and ESA
inspection scripts/tests, GP ingestion/model, strict JSON/time/file helpers,
scientific models and the existing acceptance/gate design before edits.

Only five new files were added:

- `scripts/inspect_historical_gp.py`: bounded private capture and diagnostic CLI.
- `backend/tests/test_historical_gp_intake.py`: explicitly synthetic format,
  selection, provenance, storage and calculation-boundary tests.
- `docs/phase-11.3.1-historical-intake.md`: intake contract and receipt instructions.
- `docs/phase-11.3.1-readiness-report.md`: this assessment.
- `docs/phase-11.3.1-readiness-results.json`: structured execution/preservation proof.

No existing code, dependency, lock, environment configuration, scientific policy,
frontend, deployment file or previous report was changed. No database initialization,
migration, ingestion, reset, restoration or write occurred. Existing Phase 11
workflows and their operational/synthetic residual functionality remain intact.

The [intake guide](phase-11.3.1-historical-intake.md) documents exact bounds,
commands and limitations. Original bytes/hash/size and supplied provider/filename/
format/acquisition/receipt notes are preserved **before** parsing in exclusive,
private captures. Missing metadata remains null; storage time is separate. A
last-written manifest anchors members but does not authenticate a provider or
create immutable/off-machine storage. Interrupted captures are retained incomplete.

Single-object and multi-record arrays retain source indices and original whole-file
hashes. Model checks, target/designator, exact timestamp precision, intended request
scope and ±7-day intersections produce explicit candidate/exclusion reasons.
Duplicates are excluded without dropping their indices. Parsed-record hashes have
an exact documented serialization scope and are never called original record-byte
hashes. Mixed model failures are individually reported; invalid JSON/nonfinite
constants/duplicate keys refuse the entire document. There is no nearest-epoch or
automatic input choice, no source URL forgery and no inferred historical availability.

The existing single-record parser performs propagation during validation; the new
tool therefore reuses the underlying `Elements` model instead, and explicitly
reports that dynamic parser validation has **not** executed. Nine PARTIAL/BLOCKED
gates cover source identity, numerical structure, historical selection, time,
frame, lineage, quality, configuration and residual authorization. There is no
gate-promotion flag or route from intake to scientific evaluation.

## Actual checks

See [structured evidence](phase-11.3.1-readiness-results.json) for exact final
commands, exit codes, source identities, retained output hashes and preservation.
Commands used locked uv dependencies, `PYTHONPATH=backend` where applicable and
`UV_CACHE_DIR=/tmp/orbitiq-readiness/uv-cache`. Frontend commands ran in `frontend`.

| Newly executed check | Actual result |
| --- | --- |
| Final backend `uv run --locked pytest -q --junitxml=…/backend.xml` | **1,033 passed**, zero failures/errors/skips; **70 new** intake tests plus all 963 existing tests |
| Frontend `npm test` | **344 passed**, 25 files |
| Locked sync, Ruff lint/format, ESLint, Prettier, TypeScript, production build, Git whitespace | All final commands exit 0 |
| Existing SGP4 / terrestrial / expanded scientific audits | **40 / 6 / 32** checks pass; numerical references, not independent observed accuracy |
| Existing geodesy audit | **28** independent mathematical cases and **28** separate round-trips pass |
| Existing golden evidence lifecycle | **6** published components, **3** exact offline replays pass |
| Final new intake, three fresh audited processes | All exit 0; synthetic-only seven-record fixture yields 1 candidate / 6 excluded each, no selection; reports byte-identical; zero network/database/process/propagation/residual attempts |
| Unchanged real ESA qualifier, fresh offline execution without GP | Exit 0 audit, scientific decision BLOCKED; **5,118 converted / 2,529 excluded**, 7,647 total; zero network/database/process attempts |
| Preservation | All 288 starting files and 14 private files unchanged; database hash/full fingerprint, HEAD and empty index unchanged |

The real-source audit explicitly retains **1,806 submicrosecond** and **723
second-60** exclusions. GPS scale, original frame IGb08, explicit leap/EOP resource
identities, UTC bounds and endpoint checks remain present. This is subset time
diagnostics, not full-reference approval, all-epoch frame validation or GP pairing.

The initial new test run had **3 failures / 66 passes**: a Pydantic model-level
failure has no field location, and the new formatter incorrectly indexed it.
Corrected that formatter and added explicit missing-required-field diagnostics;
all 69 then passed. Initial Ruff import ordering was corrected. A subsequent
full run passed 1,032 tests. Added a clearer exact-precision exclusion diagnostic
and one test, then reran the full final suite and quality checks (1,033), plus
three fresh intake audits and a fresh real-source qualification audit. No existing
test, tolerance, leap policy or EOP guard was weakened or removed.

Existing warnings remain: Starlette/httpx deprecation, the deliberate duplicate-ZIP
test warning, Vitest environment/performance notices and the globe bundle-size
advisory. They did not fail checks. Browser/PDF flows, controlled observation-package
replays and public-source research were **not rerun in this task**: runtime/backend,
frontend, scientific helpers and all earlier immutable evidence are byte-preserved.
The earlier **77 browser flows / seven PDFs / six controlled package replays**
are prior reported evidence, not new results. No new browser or remote check is
claimed. Nothing was unavailable among the checks selected here.

## Remaining evidence and operational boundaries

Await the original provider JSON. Then follow the private receipt workflow and
review actual provenance, all indices/exclusions and candidate completeness.
Define the evaluation selection rule before computing errors, and establish actual
pairing only after the time, quality and realization gates pass. Unknown source
availability permits only a later justified **retrospective** comparison; current
receipt and element epoch cannot establish a historical forecast.

ESA format/interval/GPS second-60 discrepancies, unsupported time precision,
per-epoch quality approval, IGb08 treatment, actual GP lineage and independence
remain unresolved. Prediction uncertainty is **not quantified**. No ESA coordinate
fixtures or private products were copied into Git; synthetic capture outputs live
only under an explicitly synthetic private `/tmp` test directory. No real residual,
new observation package, operational Swarm adapter or accuracy claim was produced.

Original database SHA-256 remains
`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
Final local working tree has **56** unstaged modified/untracked paths, including
the earlier Phase 11 work. Nothing was committed, pushed, published, deployed,
dispatched to remote CI or changed in repository remotes/production infrastructure.
Local verification is complete for this readiness scope; genuine acquisition and
scientific qualification are open. Phase 8 public hosting/HTTPS, off-machine
recovery, real alert delivery, authorized publication/exact-commit CI and branch
protection remain separate unverified milestones.
