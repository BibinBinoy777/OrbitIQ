# Phase 3 plan (recorded before implementation)

Baseline inspected: Phase 1/2 reports, Phase 2 per-case results, scientific
conventions, SGP4 engine, snapshot validation/storage/migrations, services, API
schemas/routes, frontend viewer/styles/tests and locked dependencies. Branch
`work` has no commits; existing project files are untracked and must be preserved.
No AGENTS instructions were found in earlier inspection. Current rerun: **177
backend / 31 frontend tests pass**. All 40 reference comparisons remain in the
baseline. Astropy 7.2.3, pyerfa 2.0.1.5 and astropy-iers-data
0.2026.10.12.1.3.27 are already installed. No new dependency is needed.

The existing engine returns WGS72 SGP4 TEME, geocentric km and km/s, aware UTC
microsecond timestamps and ±7-day epoch bounds. No conversion, ground track,
map or globe exists. Original position endpoint remains TEME-only.

Implementation:

1. Add a separate Astropy TEME -> ITRS transform at the same UTC obstime,
   retaining original TEME state and using WGS84 ellipsoidal geodetic output.
   Verify against Vallado 2006 Appendix C (also Astropy's reference test), SOFA
   geodesy/time reference constants and analytic WGS84 axes/poles.
2. Use the locked package's explicit local IERS-A file and leap-second file;
   **no automatic downloads** at startup, request time or in tests. Validate
   UT1 and polar-motion status/range, finite values, leap-second validity and
   velocity finite-difference support times. Reject missing/out-of-range EOP;
   label IERS predictions and reject predictions from tables older than 30 days.
   Offer measured-only policy. Serialize Astropy global table/config contexts.
   Updates are deliberate dependency-lock updates, not hidden runtime refreshes.
3. Add read-only geodetic and catalog + explicit snapshot track routes. Fixed
   source snapshot for the whole interval, same provenance validation, no schema
   changes or derived persistence. Validate ordering/epoch bounds before work;
   default 60-second step, maximum 24-hour interval / 361 points, configurable
   within hard ceilings, minimum step 10 seconds. Include start and only aligned
   samples <= end (no irregular appended endpoint). Reject entire request on any
   failed sample: **no partial results**, no fabricated points. Backend declares
   segment breaks at antimeridian crossings.
4. Extend the existing viewer with an accessible responsive longitude/latitude
   SVG graticule map, selected sample and coordinate table, explicit UTC/EOP/
   WGS84/provenance/uncertainty labels, loading/empty/error states and safe
   cancellation. No browser orbital math, no 3D/globe infrastructure.
5. Run baseline regressions, all 40 SGP4 comparisons, independent transform/time/
   geodesy tests, policy/error/limits/API/frontend checks, lint/format/types/build,
   real configured-data HTTP/browser tracks and DB integrity/fingerprint check.
   Distinguish fixture tests, numerical reference cases and actual stored ISS
   requests. Record exact outputs and limitations in the Phase 3 report.

Acceptance: all 16 criteria in the uploaded request must be individually marked
PASS, FAIL or BLOCKED in the final report. Scientific reference agreement,
explicit EOP/time/frame/height contracts, bounded chronological sampling, failed
sample rejection, safe validated APIs, backend-driven antimeridian-safe UI,
traceable provenance, unchanged DB, full regression/quality checks and factual
documentation are required. No claim of universal accuracy or observer visibility.
No commit, push, deployment, publication or Phase 4 work.

Database baseline SHA-256:
`c389d0f1d663957be70a32f846f8e968e70a4f46c37343a5b80ceca5954e5f59`.
One snapshot, integrity `ok`; schema is recorded in `schema_version` (not SQLite
`user_version`). Ground tracks do not require persistence or a migration.
