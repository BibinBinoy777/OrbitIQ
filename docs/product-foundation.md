# Product foundation and launch gates

OrbitIQ is intended for a maintained public service. Phase 0 establishes reliable
local development; it does not establish public-launch readiness. Each later phase
must state acceptance criteria, execute appropriate checks, investigate failures,
and record evidence and limitations before expanding scope.

## Phase 0 acceptance criteria

- Locked installations reproduce in a separate source copy.
- FastAPI starts and returns the documented health response, without opening or
  initializing a database.
- The React application builds, requests health through the Vite proxy, handles
  failure, cancels abandoned requests, and bounds request duration.
- Backend API/storage tests and frontend component/network tests execute and pass.
- Linting, formatting and type checks pass.
- Explicit database initialization, backup and restoration preserve existing
  files and reject unknown schema versions.
- Development commands, configuration, and recovery steps are documented.
- CI jobs are defined; remote execution status is reported separately from local
  command success. No commit, push, deployment or publication is authorized.

## Module boundaries

`backend/orbitiq/main.py` composes the FastAPI app; `api/` owns HTTP routes.
`database.py` owns explicit storage maintenance; `migrations/` contains versioned
schema SQL. Frontend `api.ts` owns the network boundary; React components own
presentation. Add separate ingestion, application-service, orbital-calculation,
and validation modules when their first use case is implemented. Do not add empty
service layers, queues, distributed services, or an ORM without a concrete need.
Orbital propagation and coordinate transformations must remain on the backend.

## Scientific contract for future phases

Use SGP4 and Astropy with trusted reference cases, explicit tolerances and
recorded library/model versions. Preserve original upstream records and provenance.
Store upstream source, retrieval time, orbital epoch, calculation time, frame,
units, validation status and applicable uncertainty/limitations alongside derived
results. Use UTC timestamps with explicit timezone; document each astronomical
time scale. Label propagated/calculated positions separately from direct
observations. A library import, health check or plausible-looking globe does not
validate orbital science. No anomaly or collision claim may exceed its evidence.

## Storage and migrations

SQLite is a development starting point. Migration `001_initial.sql` records
schema version 1 and is applied only by explicit `init` to an exclusively created
file. Never edit a released migration. Before changing schema, introduce a new
versioned migration and a tested, explicit upgrade command with transactions,
pre-upgrade backup, compatibility checks, and recovery instructions. There is no
existing-database upgrade command in Phase 0; unsupported versions are refused.

Evaluate managed PostgreSQL before public launch: durable volumes, concurrent
writers, connection limits, transactional migrations, encrypted backups,
point-in-time recovery, region and cost requirements. Document the decision using
expected load and retention requirements. An ephemeral cloud-task filesystem
cannot hold authoritative historical records or the sole backup copy.

Retain immutable raw orbital inputs and calculated-result provenance. Agree on
retention, recovery point and recovery time objectives before collecting durable
history. Test recovery into a separate target, verify integrity and meaningful
record content, and record recovery time. File existence alone is insufficient.

## Development, test and production configuration

Development: loopback-only API and Vite proxy; explicitly exported configuration.
Tests: disposable temporary databases and mocked network responses; no production
credentials or storage. Production: separate configuration and credentials,
external durable storage, controlled API ingress, and no Vite development server.
There is no production configuration or deployment implemented in Phase 0.

## Security and operations gates before public exposure

- Review public and protected endpoints, authentication/authorization boundaries,
  input schemas, CORS, CSRF where relevant, rate limits and abuse controls.
- Put limits and timeouts on upstream ingestion, payloads, pagination and expensive
  calculations; handle failures with safe messages and bounded retries.
- Use TLS, least-privilege secrets and database access, dependency checks and
  redacted structured logs. Never log credentials or unnecessary user information.
- Add distinct liveness/readiness checks when runtime dependencies exist. Current
  `/api/health` asserts only process liveness.
- Define metrics, alerts, failure recovery, backup verification and operational
  ownership. Distinguish stale data from current data visibly in the UI.
- Prepare repeatable deployment, migration and rollback procedures; validate them
  in staging with durable storage. A local build is not deployment evidence.
- Audit keyboard navigation, focus, contrast, screen-reader behavior, mobile
  layouts and globe alternatives using real-browser tests before public launch.
- Before scientific launch, pass trusted propagation/frame/time reference cases
  and review the displayed units, epochs, provenance and uncertainty labels.

These are launch gates, not capabilities claimed by the Phase 0 implementation.
