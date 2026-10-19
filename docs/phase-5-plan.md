# Phase 5 implementation plan

Baseline: main at 8bf431c with the completed, uncommitted pre-Phase 5 changes
preserved. Reran 337 backend and 125 frontend tests successfully before changes.
Schema 2 stores one validated satellite OMM per snapshot, not catalog batches.
Existing per-catalog history supports before_id but caps pages at 100, has no
lookahead/count envelope, and the frontend only loads the first 20. Specific
older IDs already have independent strict detail/propagation routes. Insertion
IDs do not establish retrieval/epoch chronology; insertion time is not recorded.

The existing database contains one real ISS snapshot, integrity ok and SHA-256
c389d0f1d663957be70a32f846f8e968e70a4f46c37343a5b80ceca5954e5f59.
Preserve it, all existing user changes and prior phase artifacts. Do not migrate,
ingest new data, commit, push, deploy, publish, or modify remotes.

1. Extend storage with bounded read-only keyset browsing/search: insertion-ID
   high-water anchor, name/NORAD/OBJECT_ID exact/partial matches in bounded scan
   windows, explicit continuation even for empty match windows. Report exact
   bounded counts only when established; never infer oldest/latest retrieval
   from ID order. Keep malformed metadata inspectable, scientific use strict.
2. Expose global snapshot and satellite-discovery pages using existing API/error
   conventions. Add lookahead pagination metadata to existing per-catalog history.
   Direct snapshot ID access and selected-context membership remain explicit.
3. Compare at most two fixed stored snapshots. Explain the single-record model:
   shared NORAD ID or first-only/second-only, with invalid provenance/identifiers
   incompatible. Retrieval chronology can be known, equal/ambiguous or unknown.
   Compare canonical supported units, wrapping cyclic angles into [-180,180).
4. Optional common-time TEME/ITRS state comparison reuses the existing validated
   SGP4/coordinate services, checks time/frame/units/identity and subtracts only
   valid compatible results. Preserve partial valid inspection and strict errors.
5. Add lazy discovery/history/comparison navigation, retained investigation state,
   direct source detail, exact-source explorer links and return context. Reuse
   GroundTrack/timeline. Extend the existing Globe renderer with two labelled
   disconnected common-time ITRS markers; never connect them into a trajectory.
6. Isolated fixtures test large pagination, missing metadata, matching/differences,
   units/wrapping, state guards, safe errors, no ingestion/writes, cancellation,
   UI flows and graphics fallback. No fixture enters the application DB.
7. Run full regressions, 40/6 reference audits, quality/type/build and actual
   responsive browser/API checks. Real archive has only one snapshot: distinct
   historical changes cannot be evidenced from it; label fixture-backed integration
   separately. Record all 27 requested criteria and actual evidence/limitations in
   phase-5-report.md and phase-5-integration-results.json.
