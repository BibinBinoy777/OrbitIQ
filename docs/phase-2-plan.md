# Phase 2 plan and acceptance checks

Inspection: Phase 1 report, README, Phase 1 guide, product foundation, fixture
provenance, 24 reference comparisons, SGP4/OMM engine, migrations 001/002, snapshot
storage/provenance, API routes, React health view and locked dependency manifests.
Read-only database baseline: schema 2, one real snapshot; saved file fingerprint.

Risks ranked before implementation:

1. High: persisted provenance is not rechecked before returning scientific results;
   malformed metadata or unusable numbers can fail outside a safe API contract.
2. High: TEME vectors could be mistaken for Earth-fixed/observed positions; no
   response schema currently declares vector dimensions/units and limitations.
3. Medium: reference suite lacks dedicated low-perigee/circular LEO coverage;
   time normalization and freshness boundary cases need explicit tests.
4. Medium: age mixes an implicit server clock with a coarse recent/stale label;
   retrieval recency must not stand in for element epoch recency.
5. Medium: frontend has no snapshot, provenance, freshness or propagation view.

Implementation sequence:

- Preserve all existing fixed references; add independent published LEO vectors.
- Harden numeric/time boundaries without changing valid SGP4 calculation behavior.
- Add deterministic epoch/retrieval age policy, typed additive scientific metadata,
  application-service provenance checks, and safe structured error handling.
- Add an accessible, responsive read-only snapshot/propagation panel, preserving
  health checks and using backend calculations only.
- Run full regressions and actual stored-data HTTP checks, compare the original
  database fingerprint, and write docs/phase-2-report.md with every acceptance item.

Acceptance evidence required:

- Existing 103 backend tests, 24 reference comparisons and 6 frontend tests retained.
- New published vectors use unchanged 1e-5 km / 1e-8 km/s absolute tolerances.
- UTC normalization, Julian day input, fractional/negative offsets and failure
  boundaries tested; no fabricated vectors or loosened assertions.
- Exact deterministic freshness rules and separate timestamps, units/frame,
  immutable source hash, and non-quantified uncertainty visible in API and UI.
- Invalid numbers/times, missing provenance, unsupported frames and calculation
  failures produce safe appropriate HTTP errors.
- Complete backend/frontend suites, lint/format/type checks and production build pass.
- Original schema-2 database and record stay byte-for-byte unchanged; no migration
  unless justified by actual data requirements (none currently identified).

Scope decisions: TEME is the only output frame. No coordinate transform is
currently implemented or necessary for API correctness. No Earth-orientation data
is needed. Reject requests for unsupported frames; defer transformations, globe,
ground tracks and EOP handling until separately justified/reference-tested.
No new database, dependency, deployment or later-phase infrastructure is planned.
All results must distinguish published numerical verification from observational
accuracy, self-consistency tests, mocks and actual stored-data/API validation.
