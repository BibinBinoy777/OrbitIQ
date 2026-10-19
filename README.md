# OrbitIQ

Satellite exploration and orbital investigation. Phase 1 adds validated CelesTrak
GP ingestion, persistent retrieval snapshots and reference-tested backend SGP4
propagation. Phase 2 adds a read-only scientific snapshot/position viewer,
explicit freshness and provenance checks. Phase 3 adds Astropy ITRS/WGS84
ground tracks with explicit offline IERS policy. Phase 4 adds an interactive Three.js
Earth, source-information panel and exact-sample timeline. See [Phase 4 verification](docs/phase-4-report.md), [Phase 3 verification](docs/phase-3-report.md), [scientific conventions](docs/scientific-conventions.md),
[Phase 2 verification](docs/phase-2-report.md) and the
[Phase 1 ingestion contract](docs/phase-1.md). Live ingestion requires CelesTrak
network access; viewing stored snapshots and running offline tests does not. Reference agreement is not a guarantee of predicted satellite accuracy.

The pre-Phase 5 foundation adds a read-only **Scientific-data readiness** view and
`GET /api/readiness`, separate from liveness. It reports bounded database metadata,
stored epoch/retrieval freshness, local EOP coverage/prediction policy and actual
leap-expiry metadata. See [readiness semantics](docs/scientific-data-readiness.md),
[controlled EOP maintenance and rollback](docs/eop-maintenance.md), and the
[implementation and verification report](docs/pre-phase-5-readiness-report.md).
Maintenance uses isolated validated package environments and explicit operator
selection; ordinary API requests never refresh resources.

Phase 5 adds **Discovery & history**: bounded stored-name/NORAD/international-ID
search, keyset history browsing and direct snapshot access, fixed-source element
and common-time TEME/ITRS comparisons, and exact-source explorer navigation.
Snapshot IDs order insertions, not retrieval chronology. Each schema-2 snapshot
contains one satellite record; no catalog-wide batch is invented. Counts and
missing metadata remain explicit, and comparisons do not establish maneuvers or
anomalies. See the [Phase 5 report](docs/phase-5-report.md) and
[structured verification evidence](docs/phase-5-integration-results.json).

## Requirements and installation

Use Python 3.12, uv (validated with 0.12.23), Node.js 24 and npm 11.
From the repository root:

```sh
uv sync --locked
cd frontend
npm ci
```

Both lockfiles must be retained. Use `uv lock` or `npm install` only for intentional
dependency updates. On a machine with a read-only home directory, set
`UV_CACHE_DIR=/tmp/orbitiq-uv-cache` and `npm_config_cache=/tmp/orbitiq-npm-cache`.
The local tests need no external services or credentials. Live ingestion needs
HTTPS access to CelesTrak through the inherited proxy and trusted CA configuration.

## Development

In terminal one, from the repository root:

```sh
uv run --locked uvicorn orbitiq.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

In terminal two:

```sh
cd frontend
npm run dev
```

Vite serves on port 5173 and proxies `/api` to port 8000. The status view requests
`/api/health` and displays success or failure. For a different backend, export
`ORBITIQ_BACKEND_URL` before starting Vite. The health endpoint returns
`{"status":"ok","service":"OrbitIQ"}`; it is a liveness check, not a database
or scientific-data readiness check. Production hosting and routing are outside
Phase 0; a production server must provide the same-origin `/api` route.

`.env.example` documents configuration. Files named `.env` are **not automatically
loaded**; export variables in your shell. Do not store credentials in frontend
variables (anything prefixed `VITE_` is public). No API keys are required.

## Database operations

The API never creates or opens a database at startup. Set an **absolute** path
explicitly. Parent directories must already exist. No default database path,
automatic migrations, or destructive reset command is provided.

```sh
mkdir -p data backups
export ORBITIQ_DATABASE_PATH="$PWD/data/orbitiq.sqlite3"
PYTHONPATH=backend uv run --locked python -m orbitiq.database --help
```

For the database commands, set `PYTHONPATH=backend` (from the repository root):

```sh
export PYTHONPATH=backend
uv run --locked python -m orbitiq.database init
uv run --locked python -m orbitiq.database check
uv run --locked python -m orbitiq.database backup "$PWD/backups/orbitiq-001.sqlite3"
```

Run `init` only when deliberately creating a new database. It exclusively creates
a new file and refuses any existing path. The initial schema contains only a
schema version (2) and an empty snapshot archive, with no satellite or observation
records. Existing schema-1 databases require the explicit migration documented
in `docs/phase-1.md`.

Backups use SQLite's online backup API, rather than copying a live database file.
The source must exist and pass integrity/schema checks. The destination must not
exist. Keep backups outside the checkout in durable protected storage for real
usage; ignored local backups are not a disaster recovery system.

Restore to a **new path**, validate it, then explicitly select it:

```sh
export ORBITIQ_DATABASE_PATH="$PWD/data/restored-001.sqlite3"
uv run --locked python -m orbitiq.database restore "$PWD/backups/orbitiq-001.sqlite3"
uv run --locked python -m orbitiq.database check
```

Restore refuses an existing destination and preserves the original database and
backup. Stop any database writers before switching the configured path. Retain
the original until the restored data has been verified. These commands support
OrbitIQ schema versions 1 and 2. No restore procedure overwrites a live database.

## Checks

From the repository root:

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

Formatting: `uv run --locked ruff format .` and `cd frontend && npm run format`.
Tests use temporary databases and mocked frontend health responses. Live proxy
validation additionally requires both development processes: request
`/api/health` on port 5173 and verify the JSON above. The backend suite includes published SGP4 reference cases. Current transformation and browser checks are documented in `docs/phase-3-report.md`.
See `docs/phase-1-report.md`
for ingestion evidence; `docs/phase-0-report.md` records the earlier foundation checks.

## Architecture and production direction

See [product foundation and launch gates](docs/product-foundation.md) for the
Phase 0 acceptance criteria, module boundaries, scientific provenance contract,
managed PostgreSQL evaluation criteria, and security/operations gates. The initial
schema is versioned in `backend/orbitiq/migrations/001_initial.sql`. Phase 1 adds
migration 002 and an explicit, pre-backed-up upgrade command;
unknown versions are refused. See `docs/phase-1.md`.

The frontend health request times out after five seconds and is cancelled when
the component unmounts. Modern browsers supporting `AbortSignal.any` and
`AbortSignal.timeout` are required; broader browser support needs explicit review.

`.github/workflows/ci.yml` defines locked backend and frontend checks for pull
requests, pushes and manual runs. Its commands are validated locally; GitHub CI
has not run because these files have not been committed or pushed. There is no
production deployment workflow in Phase 0.


## Phase 1 live ingestion

Connectivity and one real ISS snapshot are now verified; see the
[Phase 1 implementation report](docs/phase-1-report.md). Use the existing database,
not a fresh initialization:

```sh
export PYTHONPATH=backend
export ORBITIQ_DATABASE_PATH=/workspace/OrbitIQ/data/orbitiq.sqlite3
uv run --locked python -m orbitiq.ingestion.celestrak 25544 --verify-replay
uv run --locked python -m orbitiq.database verify-archive
```

Run a new live retrieval only when needed, respecting the source's limits.
`--verify-replay` makes one download and processes it twice; exact duplicate
content reuses the existing snapshot without overwriting history. The optional
`ORBITIQ_CELESTRAK_URL` is documented in `.env.example` and the Phase 1 guide.
Proxy rejection, upstream HTTP status, timeout and identifiable TLS failures are
reported distinctly without printing credentials or response bodies. The current
live database, backups and evidence are Git-ignored; they are local application
data, not production durable storage.

## Phase 2 scientific review

Start the same backend/Vite processes with the existing database configured.
Load a catalog's stored snapshots, explicitly select the latest stored or a
historical dataset, then request a backend calculation near that dataset's epoch.
The viewer shows epoch, first retrieval, freshness, source hash, frame, units and
limitations; it does not fetch new orbital data or present a globe. TEME is the
only supported frame on the original position endpoint. Separate Phase 3
terrestrial endpoints extend this without replacing it. Calculated vectors are not direct observations.

Freshness defaults to fresh through 24h, aging through 72h, then stale, based on
the element epoch rather than retrieval time. Optional exported
`ORBITIQ_FRESH_HOURS`/`ORBITIQ_STALE_HOURS` change this presentation policy, not
model accuracy. See the scientific guide for unknown/future timestamps and
backward compatibility of the legacy flat freshness fields. No database migration
or new dependency is required for Phase 2.

Reproduce the per-case published-vector audit (no network or database writes):

```sh
PYTHONPATH=backend uv run --locked python scripts/verify_scientific_references.py --output docs/phase-2-reference-results.json
```

The full backend/frontend check commands above include the additional scientific,
API and frontend tests. Browser checks and their tested scope are recorded in the
Phase 2 report. No commit, push, deployment or publication is part of this work.


## Phase 3 Earth-fixed coordinates and ground tracks

With the same backend and Vite processes, load a stored snapshot, choose a track
start near its orbital epoch and select duration/step. Generate the track to show
a longitude/latitude graticule map and select a calculated sample. This supports
historical intervals from an explicitly selected source; it does not fetch data.
The map breaks at the antimeridian and shows steps over five minutes as dots.
Loading/error/empty states clear previous tracks. Failed samples reject the
entire request; partial responses are not supported or drawn.

New read-only endpoints (old TEME position route unchanged):

```text
/api/snapshots/{id}/earth-fixed?at=<aware ISO timestamp>&frame=ITRS
/api/satellites/{catalog}/ground-track?snapshot_id=<id>&start=<aware ISO>&end=<aware ISO>&step_seconds=60&frame=ITRS
```

Each point preserves the source TEME state/provenance and adds ITRS km/km/s,
geodetic latitude/longitude in degrees and WGS84 ellipsoidal height in km.
This height is not sea-level height or terrain clearance. No visibility,
collision, direct-observation or quantified accuracy claim is made.

The locked Astropy package includes local IERS and leap data; no startup or
request downloads occur. Default `ORBITIQ_EOP_POLICY=measured_or_predicted` labels
predicted EOP explicitly; `measured_only` rejects predictions. Out-of-range,
missing, expired predictions (>30-day table age) or expired leap data fail
explicitly. Resource updates require an intentional lockfile update, scientific
checks and worker restart. See [scientific conventions](docs/scientific-conventions.md)
for the policy, actual source hashes/coverage, leap-crossing restriction and API
error contract. No credentials or new network domain are required for tracks.

Defaults: at most 361 points / 24 hours; integer step 10..3600 s. The point count
is floor(duration/step)+1, so a 24-hour request at 60 seconds exceeds the default
point limit. Aligned samples only; the requested end need not be sampled.
Optional `ORBITIQ_TRACK_MAX_SAMPLES` and `ORBITIQ_TRACK_MAX_DURATION_SECONDS` may
lower limits or raise them to hard ceilings of 1000 / 86400 respectively.
Settings are exported shell variables, not automatically loaded from `.env`.
No database initialization, migration, reset or derived storage is needed.

Reproduce the numerical transform audit without downloads or database writes:

```sh
PYTHONPATH=backend uv run --locked python scripts/verify_earth_fixed_references.py --output docs/phase-3-reference-results.json
```

The existing full test/lint/format/build commands include all Phase 3 tests.
No new dependency or lockfile change was needed. Browser smoke checks use tools
available in this cloud environment; Playwright/Chromium are not application
dependencies. No public deployment or remote GitHub CI run is claimed.


## Phase 4 interactive explorer

Use the same backend/Vite startup commands and explicit database path. The Earth
loads without inventing satellite positions. Submit a NORAD catalog ID to search
**stored snapshots only**, choose a source and generate a track near its epoch.
There is no global name search, automatic ingestion or full-catalog coverage.
The existing source provenance and TEME inspector remain available in the
“Source provenance and TEME inspection” disclosure.

The globe, 2D map, information panel and timeline share one dataset/sample index.
Use the slider, previous/next controls or Play/Pause. Playback moves **one returned
sample per second**, stops at the end and makes **zero API requests**. No positions
are interpolated. Reset timeline selects the first sample; Reset track window
restores the source time, 90-minute duration and 60-second step, clearing the old
result. Editing the interval or changing source cancels requests and stops playback.
Reduced-motion preference disables playback while keeping manual controls usable.

Drag or use the labelled camera buttons to rotate/tilt; scroll/pinch or use zoom
buttons; Reset camera restores the default Earth view, and Focus satellite centres
the selected calculated marker. Clicking the marker or Inspect satellite focuses
its accessible information panel. Arrow keys on the canvas rotate/tilt; + / -
zoom and 0 resets the camera. Panning is disabled to preserve an Earth-centred
view. WebGL2 is required for 3D, but not for search, source data, the 2D map,
coordinate tables or timeline. Graphics errors/context loss show fallback status
and a retry option; context restoration can recover automatically.

Only backend ITRS vectors are rendered as satellite positions. The backend adds
`ground_position_km`, an Astropy WGS84 normal footpoint at zero ellipsoidal height,
to existing Earth-fixed responses. No new endpoint, database migration or orbital
algorithm is needed. Browser code only chooses a display basis/scale. Marker size,
a small surface-overlay lift and static image/lighting are illustrative; the Earth
texture is not current imagery or validated cartography. Scientific timestamps
remain UTC; requested sample, element epoch, retrieval and execution times remain
separate. Source/EOP freshness and unquantified uncertainty remain visible.

Dependencies: exactly pinned `three=0.186.1`, `@types/three=0.186.0`, recorded in
the updated npm lockfile; Python dependencies and lockfile are unchanged. The
Earth image and upstream license are served from `frontend/public/assets` with
attribution. No external texture/tile request, API key, state-management library
or new environment configuration is needed. Run `npm ci` after updating source.
The lazy renderer chunk is about 556 kB minified / 139 kB gzip; Vite's 500-kB
warning remains visible. A local build does not prove target-device GPU performance
or public-deployment readiness. See the Phase 4 report for actual test evidence.
