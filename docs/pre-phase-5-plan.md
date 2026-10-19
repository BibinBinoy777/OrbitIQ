# Pre-Phase 5 readiness and EOP maintenance plan

Inspected the Phase 3/4 reports, health/API composition, read-only SQLite schema,
scientific-resource loader/policy, coordinate/track services, frontend clients,
locks and tests. Git is clean on main at 8bf431c. Baseline rerun: 268 backend and
96 frontend tests pass. Current data are immutable package-managed resources from
astropy-iers-data 0.2026.10.12.1.3.27, loaded through explicit local paths supplied
by that package, cached per process; no automatic download. Prediction age,
coverage, leap expiry and ±0.5-second support requirements already fail strictly.
The database has schema 2, one real ISS snapshot, integrity ok and SHA-256
c389d0f1d663957be70a32f846f8e968e70a4f46c37343a5b80ceca5954e5f59.

Implementation:

1. Separate GET /api/readiness?at=<aware ISO> from unchanged /api/health. Return
   safe bounded component assessments and explicit evaluation/target UTC times.
   Reuse the exact EOP calculation policy. Distinguish package release age (not
   recorded), data coverage, prediction-region age and requested-time usability.
2. Read at most 101 snapshot metadata rows via indexed descending insertion ID,
   without raw orbital bodies/integrity scans or schema writes. If history is
   <=100 rows, derive actual latest retrieval from that complete bounded set.
   Otherwise label the inspected tail and global latest/freshness unknown; do
   not confuse insertion order with retrieval order. Apply SQLite time/VM budgets.
   Existing insertion timestamp and ingestion error history were never recorded:
   expose unknown, not invented. Epoch-age freshness retains existing thresholds.
3. Add a read-only dashboard view using the existing local React state and fetch
   conventions, explicit refresh/target/retry, accessible statuses and direct
   navigation back to the preserved explorer. No background polling/maintenance.
4. Operator CLI stages an exact supported astropy-iers-data pin in a fresh isolated
   backend source/environment using uv and authoritative PyPI, preserving active
   files/lock/environment. Record acquisition/version/checksums and source digest.
   Validate complete tables/units/coverage/statuses/leaps, strict boundaries,
   candidate loading, full backend regression and both reference audit scripts.
5. Activate only a validated immutable candidate by atomically selecting its
   environment in an operator manifest. Preserve previous selector/history,
   verify selection and roll back automatically on verification failure. Explicit
   rollback and a non-deploying launcher description make the selected environment
   usable after an operator restart. No installed-package overwrite, public admin
   endpoint, automatic worker switch or change to scientific equations/policy.
   A matching optional receipt can expose real verification/acquisition times.
6. Rehearse the full acquire/validate/select/rollback lifecycle with the currently
   locked version, not an unsolicited upgrade; keep the application's live Python
   environment and DB unchanged. Fault injection uses isolated tests only.
7. Add API, bounded-query, policy/boundary, maintenance failure/rollback/provenance,
   dashboard/loading/error/cancellation tests. Run full 268/96 regressions plus new
   tests, 40/6 references, quality/build/locked setup and actual HTTP/browser checks.
   Document all 22 acceptance criteria and actual evidence/remaining limitations.

No commit, push, remote changes, deployment, publication, historical investigation,
satellite discovery or unrelated refactor. Operator manifests are small maintenance
receipts/selectors, not a new scientific database or runtime resource store.
