# E5 product and architecture audit

Assessment: **23 October 2026 (IST)**. Baseline: `engineering-e4-final-closure`,
`6bab52b268e0e5950d70f9dd9e7f54760bd002ea`. E5 uses
`engineering-e5-product-acceptance`. See the [execution report](engineering-e5-report.md)
and [prioritized roadmap](engineering-e5-roadmap.md). E5 assesses the existing
product; it does not mean the full product vision has been implemented.

## Acceptance and evidence rules

Accept E5 when material capabilities have implementation/test traceability,
important supported journeys run against actual services, demonstrated bounded
defects have regression protection, and remaining gaps have actionable priorities.
Preserve earlier reports, private inputs, archive contents and scientific gates.
Run backend/frontend, reference audits, E1 browser/PDF, E2 accessibility, E3
installation/recovery and E4 integrity checks on the candidate. Distinguish local
results, exact-commit remote CI, publication and production operations.

Classification describes the stated bounded capability, not every future
interpretation of its name. “Implemented and verified” means evidence for the
specified fixture/reference cases, not universal correctness, production capacity
or genuine independent satellite accuracy. Historical local-data evidence is not
fresh provider acquisition. No CelesTrak or ESA orbital requests are necessary.

## Architecture reconciled against implementation

`backend/orbitiq/main.py` composes HTTP routes; `api/` bounds inputs and translates
safe errors. `services/` orchestrates reads, fixed-source calculations and reports.
`orbits/` owns SGP4, sampling, freshness and Astropy/EOP transformations.
`ingestion/` contains the single-object provider adapter and durable collection
ledger. `storage.py`, `database.py` and three SQL migrations own persistence.
`maintenance/` contains explicit replay, backup, monitoring and resource commands.
React components present these contracts; frontend TypeScript API modules validate
responses. Three.js renders calculated ITRS samples, never propagates an orbit.

These are implemented separations, not empty planned modules. There is no ORM,
server-owned investigation table, job queue, automatic request-time resource
update or continuous ephemeris cache. Schema remains **3**, with no E5 migration.
The Phase 0 [foundation](product-foundation.md) is historical acceptance/planning;
its future-tense modules now exist, and the later phase/E1–E4 reports document
those increments. It is not a current inventory of missing code.

Backend module paths below are relative to `backend/orbitiq/`; test filenames refer
to `backend/tests/`, and component/TypeScript filenames to `frontend/src/`.
Verification scripts are in `scripts/`. Python CLI commands need
`PYTHONPATH=backend` and an explicit absolute database path where applicable.

| Bounded capability                                                      | Classification                                         | Actual implementation / interface                                                                                                                                            | User journey and verification                                                                                                                                                                                                                      |
| ----------------------------------------------------------------------- | ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Validated single-object CelesTrak JSON acquisition                      | Implemented and verified                               | `ingestion/celestrak.py`, `collection.py`; operator `python -m orbitiq.ingestion.collection collect NORAD`                                                                   | Explicit collection, whole-response rejection, cooldown/retry/audit; `test_phase1.py`, `test_phase6_collection.py`, `test_e3_ingestion.py`; fresh-checkout failure/recovery uses MockTransport, not a live provider                                |
| Immutable satellite snapshots and schema maintenance                    | Implemented and verified                               | `storage.py`, `database.py`, migrations 001–003; exclusive init, backed-up migrate, engine backup/new-path restore                                                           | `test_foundation.py`, `test_e3_recovery.py`, `test_phase6_collection.py`; E3 installation/restart/restore; real archive preserved rather than reinitialized                                                                                        |
| Stored discovery, bounded search/history and snapshot details           | Implemented and verified                               | `services/investigations.py`, `analysis.py`; `GET /api/discovery/satellites`, `/snapshots`, `/satellites/{catalog_id}/snapshots`, `/snapshots/{snapshot_id}`                 | `Investigations.tsx`, `ScientificExplorer.tsx`; literal name/NORAD/designator search and exact source selection; `test_phase5.py`, `Investigations.test.tsx`, critical/history browsers                                                            |
| Provider retrieval audit and data readiness                             | Implemented and verified                               | Schema-3 ingestion ledger; `services/ingestion_status.py`, `readiness.py`; `GET /api/readiness`; operator history                                                            | `ReadinessDashboard.tsx`; `test_readiness.py`, `test_phase6_collection.py`, `test_e3_ingestion.py`, readiness component/browser checks; HTTP 200 is a diagnostic response, not proof of healthy science                                            |
| Backend TEME propagation                                                | Implemented and verified                               | `orbits/elements.py`, `engine.py`, `services/analysis.py`; `GET /api/snapshots/{snapshot_id}/position`                                                                       | Explicit aware time, SGP4/WGS72, ±7-day bound; `test_phase2_science.py`, `test_phase2_api.py`, `scientific-api.test.ts`; published-reference audits, E5 real browser UTC/invalid-input recovery                                                    |
| Earth-fixed state, geodesy and sampled tracks                           | Implemented and verified                               | `orbits/coordinates.py`, `earth_orientation.py`, `sampling.py`, `services/ground_tracks.py`; `/snapshots/{snapshot_id}/earth-fixed`, `/satellites/{catalog_id}/ground-track` | `GroundTrack.tsx`, `SatelliteInfo.tsx`; strict local EOP/leap policy, all-or-nothing samples; `test_phase3_api.py`, `test_phase3_science.py`, `test_phase611_geodesy.py`, ground-track tests and real browsers                                     |
| Interactive globe and exact-sample UTC timeline                         | Implemented and verified                               | `Globe.tsx`, `globe-renderer.ts`, `globe-geometry.ts`, `Timeline.tsx`                                                                                                        | Camera/markers, selected sample, playback/end/reset, hidden-view pause and fallback; globe/timeline tests, critical browsers and E2. Single selected source or A/B comparison, not a global multi-satellite scene                                  |
| Exact-source common-time comparisons                                    | Implemented and verified                               | `services/investigations.py`; `GET /api/comparisons`                                                                                                                         | A/B source selection, element differences, optional TEME/ITRS states; `test_phase5.py`, restoration tests, critical/history browsers. Differences are not anomaly or maneuver detection                                                            |
| Bounded historical change analysis and explainable findings             | Implemented and verified                               | `services/history.py`; `GET /api/historical-analysis`                                                                                                                        | `HistoricalAnalysis.tsx`, `history-api.ts`; inspect ≤20 records/page, rules/source hashes/limitations and captured JSON; `test_phase11_history.py`, component tests, `verify_history_browser.py`                                                   |
| Browser-local saved definitions and parameter links                     | Implemented and verified                               | `saved-investigation.ts`, `investigation-storage.ts`, `restore-investigation.ts`; existing read APIs                                                                         | `SavedInvestigations.tsx`, `RestoredInvestigation.tsx`; exact-reference reopen, safe missing source, local save/share, conflict detection; storage/restoration tests and critical browsers. No account, cloud save or cross-device synchronization |
| JSON investigation reports and printable HTML                           | Implemented and verified                               | `reporting.py`, `services/reports.py`; `GET /api/investigation-reports`; `report-api.ts`, `report-presentation.ts`                                                           | `InvestigationReport.tsx`; snapshot/position/track/comparison capture; `test_phase9_reports.py`, report tests/browser, paired JSON/PDF checks. Generated files are downloads, not a server report archive                                          |
| Native PDF production                                                   | Partially implemented                                  | Browser print dialog plus printable HTML; no server PDF API                                                                                                                  | Native headless generation/content inspection is Chromium-only; seven PDF checks. Firefox/WebKit printable view/layout is checked; their OS print dialogs/native PDF output are unverified                                                         |
| Evidence capture and offline numerical replay                           | Implemented and verified                               | `replay*.py`, `services/replay.py`, `maintenance/replay.py`; operator `python -m orbitiq.maintenance.replay`                                                                 | Exact bytes/resources/version hashes, bounded import/preflight and tolerance outcomes; `test_phase10_replay.py`, `test_phase101_integrity.py`, golden/offline verification scripts. Not a browser replay/import feature                            |
| Finding-level offline replay                                            | Documented but not implemented                         | Explicit limitation in `services/history.py` and [history methodology](historical-analysis-methodology.md)                                                                   | Findings export rules/inputs; comparison recipes reproduce underlying calculations, not an independent replay of findings. No finding-replay endpoint or bundle kind                                                                               |
| Generic operator-supplied observation validation                        | Implemented and verified                               | `observation_validation.py`, `services/observation_validation.py`, `maintenance/observation_validation.py`; `/api/observation-validations[/{run_id}]`                        | `ObservationValidation.tsx`; absent/empty and labelled fixture-package inspection; `test_observation_validation.py`, `verify_observation_browser.py`. Bounded compatible-input discrepancy arithmetic does not qualify an actual reference dataset |
| Historical GP/reference static intake and diagnostics                   | Implemented and verified                               | Static intake/reconciliation scripts listed below; no operational ingestion or public upload API                                                                             | Bounded parsing, identity, time/quality and blocked-pairing guards. E5 runs fixture regressions, not private-source requalification. Software diagnostics do not qualify the scientific pair                                                       |
| Genuine Swarm-A independent reference comparison                        | Blocked by an unresolved dependency or scientific gate | Phase 11.3.1 diagnostic/qualification scripts and reports; no qualified operational adapter                                                                                  | Existing exclusion/time/protocol tests preserve blockers. ESA time, KIN acceptance and frame alignment unresolved; no genuine propagation/residuals performed in E5                                                                                |
| Error recovery and local lifecycle                                      | Implemented and verified                               | `api/errors.py`, `boundary.py`, `runtime.py`, operator recovery; bounded frontend requests/cancellation                                                                      | E3 fresh checkout plus provider failure/retry/restart/full separate restore; E1 failure injection; E5 three modes retain source/result across append/restart/restore                                                                               |
| Cross-workflow provenance after subsequent input                        | Implemented and verified                               | Existing exact references, read-only reports and append-only archive; no new storage                                                                                         | `test_e5_product_acceptance.py`: position/track/comparison survive a later synthetic input, app recreation and separate engine restore; vectors/time/frames/units and fixed resource identities preserved                                          |
| Automated keyboard/accessibility and viewport support                   | Implemented and verified                               | E2 focus/skip link, controls, reduced motion, dialogs and fallback                                                                                                           | `verify_engineering_e2.py`: four widths, keyboard/error recovery and axe scans; incomplete checks retained. Not full accessibility certification                                                                                                   |
| Physical-device usability, native GPU capacity and assistive technology | Implemented but insufficiently verified                | Existing UI and informational E2 measurements                                                                                                                                | No physical-device/screen-reader/long-soak/native-GPU or public-load result. Software graphics and desktop viewport emulation do not close this gap                                                                                                |
| Exact-source candidate integrity / bounded CI artifact retention        | Implemented and verified                               | `verify_release_evidence.py`, `verify_retained_candidate.py`, existing three CI jobs                                                                                         | E4 unit tests, source/image/frontend seals and actual retained candidate evidence. Selected image bytes require manual opt-in; routine CI retains evidence only. Not production backup or deployment                                               |
| Production operation and disaster recovery                              | Blocked by an unresolved dependency or scientific gate | Existing runbooks/containers, E4 five-gate tracking                                                                                                                          | Hosting/HTTPS, independent recovery, actual alerts and branch protection remain blocked. Bounded artifact retention alone passed E4; no provisioned production service is claimed                                                                  |

Static diagnostics use `scripts/inspect_historical_gp.py`,
`inspect_historical_csv.py`, `reconcile_historical_gp.py`,
`inspect_swarm_reference.py`, `qualify_swarm_inputs.py` and
`assess_swarm_pairing.py` (all under `scripts/`). Their parser/reconciliation/gate
coverage is in `test_historical_gp_intake.py`, `test_historical_csv_intake.py`,
`test_historical_gp_reconciliation.py`, `test_phase1131_qualification.py`,
`test_swarm_pairing_assessment.py` and `test_swarm_comparison_protocol.py`.
Private diagnostic output is not a source for operational ingestion or a genuine
residual calculation; it remains outside Git. The scientific-pairing gate is still
blocked despite implemented and fixture-tested software diagnostics.

## Contracts and persistent meaning

| Concept                                     | Backend/storage authority                                                                                | Frontend/export agreement and limits                                                                                                                                                                                                      |
| ------------------------------------------- | -------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Satellite identity                          | Validated NORAD integer, 1–339999; one satellite per snapshot                                            | Names are display/search fields, not matching authority; safe integers required by browser contracts                                                                                                                                      |
| Snapshot identity                           | Archive-local insertion ID plus exact response SHA-256, catalog, epoch and first retrieval               | Saved definitions/reports require all five fields; missing/mismatched source is refused without selecting a newer one. IDs are not portable across unrelated archives                                                                     |
| Element epoch / first retrieval / insertion | Separate immutable fields; legacy insertion time may be absent                                           | Freshness measures epoch age, not acquisition success. Public listing is metadata-only; detail/calculation/report revalidates raw payload provenance                                                                                      |
| Requested versus execution time             | `at` is the aware evaluation instant normalized to UTC; `calculated_at` records execution                | Timeline selects returned samples only. E5 rejects a supplied TEME response time that differs from the request, including microseconds; equivalent offsets accepted. Absent legacy metadata remains unknown, never invented               |
| Frames and units                            | TEME/WGS72 SGP4; Astropy ITRS; WGS84 ellipsoidal geodesy; km, km/s, degrees                              | No frontend orbit propagation. Calculated positions are labelled; surface-map height is not sea-level or terrain clearance. No arbitrary observation-frame substitution                                                                   |
| EOP/leap resources                          | Offline selected resources, actual hashes/versions/coverage/flags and strict failure policy              | Resource failures remove results or give explicit partial/unavailable report state. Measured/predicted distinctions retained; no request-time download                                                                                    |
| Freshness and quality                       | Configurable epoch-based 24h/72h default labels, separate retrieval ledger; structural/epoch validation  | Fresh/aging/stale/unknown/future do not express prediction accuracy. Input validation and published-reference agreement do not establish observational validation                                                                         |
| Reopened investigations                     | Version-1 parameters/exact source references in browser localStorage                                     | Recompute using current backend/resources. E5 verifies invariance for unchanged software/resources; different execution clocks and freshness are expected. Original numerical results require a captured report/replay bundle             |
| Reports and hashes                          | One authoritative backend capture; configuration hash differs from unique report ID and raw payload hash | JSON/HTML/preview/PDF use the same capture. Browser title/notes/UUID excluded. Hashes demonstrate byte linkage, not provider authenticity or independent science                                                                          |
| Failure                                     | Safe additive `error`/legacy `detail`, bounded parameters and calculation admission                      | Missing 404, malformed request 422, mismatched exact report source 409, storage/resources unavailable as documented. Partial report retains errors/limitations rather than fabricated zero states; cancellation removes abandoned results |

The API is read-only and anonymous. Configuring a validation archive makes its
bounded evidence API readable; private research must never be mounted there for
public use. No authenticated ownership or private cloud-save guarantee exists.
The development OpenAPI document reflects registered routes, but discovery,
comparison, history and observation envelopes use manual TypeScript validators
rather than shared generated models. Existing contract tests cover selected
fields and refusal paths; whole-contract generation is not implemented.

## Product workflow interpretation

The real UI starts with a health request and an empty globe; it does not
silently fetch providers or preload a global catalog. The user explicitly loads a
NORAD's snapshots, or opens stored discovery, selects an exact source and generates
a sampled track. The actual archive currently contains two genuine ISS snapshots;
E5 browser journeys use a separate explicitly synthetic/public-reference archive.
No extra live history or Swarm accuracy evidence is inferred from those tests.

The E1 runner already exercises discovery → detail → save → reopen/reload → shared
recipient, fixed-source track selection, A/B ITRS comparison, readiness, historical
analysis/export, observation-package absence/fixture, and four report modes with
partial/maximum cases. E5 extends its real critical journey with offset-to-UTC
TEME calculation, invalid-time failure/retry, and actual playback/end/reset with
no new API request. The [execution report](engineering-e5-report.md) records
which runs completed and their limitations.

E3 verifies backend shutdown/restart and provider recovery with a disposable
archive. E5 API integration additionally verifies report identity and numerical
results after a newer source and restart/restore. Browser reload verifies local
saves in the same browser context; browser-profile migration, cleared storage,
multi-device saves and OS/browser restart persistence are not established.

## Performance and verification limits

The [existing E2 measurements](engineering-e2-report.md#globe-measurement-results)
show no settled idle draws and bounded camera work in the tested three-point
scene, plus large noisy readiness/interaction spikes during concurrent work.
Those spikes remain evidence, not a measured product speed improvement. The lazy
renderer remains above Vite's 500 kB warning threshold and Firefox uses the 2D
fallback. Useful numerical, map, timeline and export workflows work without
native 3D; Firefox native globe interaction itself is unverified.

E5 changes no renderer algorithm, orbital calculation, dependency, lockfile,
sampling/resource policy or performance threshold. There is no before/after
performance improvement claim. Larger scenes, slow/cold networks, physical
mobile GPUs and whole-process memory/soak tests are prioritized separately.

Scientific status remains **Phase 11.3.1: PARTIAL; evaluation: BLOCKED**. Historical
availability/creation timestamps remain unknown; complete fitting lineage and
statistical independence remain unestablished. E4 remains **OPEN**, production
readiness **NOT VERIFIED**, public launch **NO-GO**.
