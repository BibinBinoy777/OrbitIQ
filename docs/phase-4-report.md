# Phase 4: interactive 3D satellite explorer and orbital timeline

## Outcome and inspected baseline

**All 19 requested acceptance criteria PASS within the documented scope.**
OrbitIQ now has a genuine interactive Three.js WebGL Earth, stored-data selection,
source/position information and exact-sample orbital timeline, integrated with the
Phase 3 map and scientific backend. No Phase 5 work, database migration, new
orbital model, commit, push, deployment or publication was performed in Phase 4.

Engineering review date: **2026-10-19 IST**; scientific/test artifact timestamps
remain explicit UTC. Git began clean on `main` at `bf3f113`, the previously
authorized initial publication. Historical phase reports describe their own
pre-publication state and remain unchanged. Remote GitHub CI was not queried or
triggered for this phase; its current outcome is not asserted.

Before code changes, inspected repository/Git status, Phase 1/2/3 reports, all
requested reference/integration artifacts, React clients/state/map/styles/tests,
backend routes/schemas/SGP4/coordinates/provenance/storage and dependency locks.
The baseline rerun passed **256 backend / 61 frontend tests**. No globe library,
timeline playback, routing framework or global state store existed. Discovery was
stored snapshots by catalog ID. Astropy supplied ITRS vectors/geodetic results
but no Cartesian zero-height surface footpoint.

The plan and acceptance gates were recorded before coding in
[phase-4-plan.md](phase-4-plan.md). The database was opened read-only: schema 2,
one real ISS snapshot, integrity ok; its SHA-256 was recorded. No absent historical
source, database or test evidence was assumed available.

## Implementation and dependencies

| Responsibility | Implementation |
| --- | --- |
| Search and source selection | Existing `ScientificExplorer`, explicit NORAD-ID submit, stored snapshots and cancellation |
| Track request and shared state | Existing `GroundTrack`, one validated dataset/index for globe, map, timeline and information |
| Source details | `snapshot-api.ts` / `SatelliteInfo.tsx`, existing validated detail endpoint |
| Timeline | `Timeline.tsx`, local state/timer and reduced-motion hook |
| Globe lifecycle/accessible UI | `Globe.tsx`, lazy load, safe failure/retry and keyboard buttons |
| Rendering and presentation basis | `globe-renderer.ts`, `globe-geometry.ts`, Three.js / OrbitControls |
| Scientific surface geometry | Small additive Astropy helper and response field in the existing coordinate service/schema |

New exact pins: **three 0.186.1**, **@types/three 0.186.0**, compatible with the
existing React/TypeScript/Vite setup. npm lockfile adds eight package entries:
Three.js, its type package and six development-only transitive dependencies
required by those types. Physics/tween/WebXR helpers among those development
packages are not imported as product features. No existing locked npm package
version changed. The application has no new React scene framework or state store.
Python dependencies/`uv.lock` are byte-identical to baseline: SGP4 2.27, Astropy
7.2.3, pyerfa 2.0.1.5 and IERS-data 0.2026.10.12.1.3.27 remain unchanged.

A 2048-pixel static Earth JPEG is served locally from `public/assets`, copied
byte-for-byte from Three.js r186 examples with its upstream MIT license and source
attribution retained. Image SHA-256:
`2faa400d1eade3bc44caf6750d1b772bd9bbb6d87362c02bc7c3304e78fa0a9d`.
This is an illustration, not current imagery, observational data or scientifically
validated cartography. No external tile/texture/CDN request or credential is used
by the running browser. Package and illustration downloads occurred during setup;
there were **zero new orbital/EOP downloads** during integration.

## APIs and scientific coordinate handling

Consumed the existing read-only routes:

- `/api/health`
- `/api/satellites/{catalog}/snapshots?limit=20`
- `/api/snapshots/{id}` for normalized orbital elements and provenance
- `/api/satellites/{catalog}/ground-track?...&frame=ITRS`
- Existing `/api/snapshots/{id}/position?...&frame=TEME` remains in the source/TEME disclosure.

No new endpoint or external provider was introduced. A small missing capability
was justified: render a true WGS84 surface track without browser geodetic math.
Earth-fixed responses therefore add **`ground_position_km`**, a finite ITRS vector
of the WGS84 normal footpoint at **zero ellipsoidal height**, computed by Astropy
`EarthLocation.from_geodetic`. It is not a radial projection or another orbital
prediction. Original SGP4, TEME/ITRS vectors, limits, EOP rules and scientific
reference tolerances remain unchanged. Existing clients can ignore the additive
field; the frontend accepts old valid 2D responses but disables 3D markers if
required rendering vectors are absent.

Client validation checks scientific frame/units, snapshot/hash/epoch/retrieval,
chronology, complete/atomic response status and requested interval correspondence.
New optional Cartesian vectors and calculation times are validated when present.
Globe rendering requires valid ITRS position and footpoint vectors, timestamp and
bounded display extent. No fabricated marker or failed-sample placeholder.

Display basis is **ITRS (x,y,z) -> Three (x,z,-y)**, divided uniformly by
**6378.137 km**. This preserves handedness/distances and performs no celestial
frame transformation. Earth is a WGS84 ellipsoid with polar/equatorial ratio
1-1/298.257223563. Satellite centres use exact returned vectors at the selected
sample; no TEME vector is overlaid directly on Earth. Source mean elements remain
separate from propagated position, with inclination in degrees, eccentricity
unitless and mean motion in rev/day from the existing normalized record.
Unsupported fields/derived periods are not invented.

Surface paths preserve backend segment breaks. Three.js draws same-segment line
segments only for spacing <=60 s; coarse points remain dots. 2D retains its <=5
minute rule. Both views consume exactly the same dataset/index and never add fake
antimeridian/intermediate points. Satellite glyph size is exaggerated; the surface
overlay uses a **1.002 display lift** to remain visible. These are explicitly
labelled illustrative, while satellite-centre distances keep one scale. Fixed
lighting and static texture do not represent illumination at the selected time.
Tessellated imagery is not a precision shoreline/geographic reference. Display
extent is limited to vectors within 400 equatorial Earth radii; outside that
extent, metadata remains usable and markers are withheld.

The backend extension is tested against WGS84 analytic axes/poles and the
published SOFA gd2gc constant case with analytic removal of its known geodetic
normal height. It checks finite values, ellipsoid membership, API output and
unchanged temporary DB. All **40** SGP4 and **6** terrestrial/time/geodesy audit
cases still pass at their original limits. The approximately **1.32 cm** fixed-EOP
Vallado residual remains a limited-case residual, not a universal accuracy claim.
Unquantified orbit uncertainty, no direct-observation validation, unsupported
leap crossing and finite/maintained EOP coverage remain visible.

## Timeline, interaction and request bounds

Default track window remains **90 minutes at 60-second steps**, near the selected
snapshot epoch. Backend limits remain 361 points / 24 hours by default, 1000-point
hard ceiling, 10..3600-second steps and source ±7-day window. Ordering/bounds and
impossible calendar input fail explicitly. One failed sample rejects the entire
track; old results/playback clear before a failed new request.

Previous/next, integer slider, play/pause and reset operate only on **actual
returned samples**. Playback advances one sample each real second, stops at end
and makes **no network request**. It neither interpolates positions nor infers an
orbit in JavaScript. A 60-second sampling grid therefore plays at 60 seconds of
simulation time per tick; it is not a live observation stream. Reset timeline
selects the first sample; Reset track window restores source time/90 min/60 s and
clears old results. Editing interval/source, fatal track failure and unmount remove
the timeline/timer. Document hiding and a newly enabled reduced-motion preference
pause playback; reduced motion disables Play while retaining manual controls.

UTC labels distinguish orbital epoch, first retrieval, selected/requested sample
and actual calculation time. Source microseconds are preserved. There is no
invented insertion timestamp, live-age claim or uncertainty percentage.

Search remains an explicit, cancellable request by NORAD catalog ID; no request
per keystroke, no global/name-catalog coverage claim, no implicit live ingestion.
Source detail is loaded once per selected source. Track fetch uses the existing
20-second timeout; source detail uses five seconds. Late results are ignored after
cancellation. Only the active dataset/source details are kept in component memory;
no persistent timeline cache or derived table was added.

OrbitControls supplies drag/zoom/pinch, with Earth-centred camera bounds and pan
disabled. Buttons provide rotate/tilt/zoom/reset/focus. Canvas arrow keys and +/-/0
provide alternatives. Clicking the real selected marker or Inspect satellite
focuses its accessible information region. Reset camera restores the initial
Earth view; new tracks focus their first valid satellite position. No automatic
Earth spin, decorative satellite or hidden interpolation is used.

## Accessibility, layout and performance

Preserved the dark-blue palette and scientific inspector while adding a coherent
Earth/timeline workspace and adjacent information panel. The information and
source/TEME disclosure remain available independently of WebGL. Responsive grid
stacks on narrower screens; controls wrap, focus remains visible and scientific
values wrap without overflow. Labels, semantic sections, native slider/buttons,
polite time/status announcements, safe errors and coordinate-table/map alternatives
support keyboard and non-WebGL use. Reduced-motion preference is observed and
updated while the page is open.

The renderer is lazy-loaded and renders on demand: no idle animation loop, easing,
interpolated trajectory or continuous texture fetch. Geometry/detail are bounded:
one satellite, at most 1000 surface samples, roughly 4300 mesh triangles, one
surface-point buffer and one line-segment buffer. Device pixel ratio is capped at
2. Dataset replacement disposes old GPU geometry; unmount disconnects controls/
resize/listeners, cancels pending frame, disposes geometry/material/texture and
renderer/context. Texture completion after disposal is handled. Context loss
stops rendering and announces a fallback; the map/timeline remain usable. Actual
context restoration recovers; a manual Retry 3D option recreates the renderer.

Final build sizes: application **256.51 kB minified / 80.05 kB gzip**, lazy globe
renderer **555.74 kB / 139.14 kB gzip**, CSS **4.27 kB / 1.52 kB gzip**. Vite's
500-kB chunk warning remains visible; its threshold was not raised. Lazy loading
keeps Three.js out of the initial application chunk, but first usable 3D still
needs the renderer and approximately 513-kB static image. No bandwidth budget,
low-end physical GPU benchmark, full accessibility audit, screen-reader
certification or broad cross-browser claim is made.

## Actual verification evidence

| Check | Executed result |
| --- | --- |
| Pre-change regression baseline | **256 backend / 61 frontend passed** |
| Final backend full suite | **268 passed**, original 256 + 12 surface/API checks |
| Published SGP4 audit | **40 passed / 0 failed**, original tolerances preserved |
| Terrestrial/time/geodesy audit | **6 passed / 0 failed** |
| Final frontend full suite | **96 passed**, original 61 + 35 new cases |
| Ruff lint / format | PASS; 45 Python files formatted |
| Frontend ESLint / Prettier | PASS |
| TypeScript / production Vite build | PASS, with documented lazy-chunk size warning |
| Clean source `uv sync --locked` + backend tests/lint/format | PASS, **268 tests** |
| Clean source `npm ci` + frontend tests/lint/format/build | PASS, **96 tests**, final source included |
| Python lock check / unchanged existing npm package versions | PASS |
| SQLite `check` / `verify-archive` | PASS, integrity ok / one snapshot |
| Real desktop/tablet/mobile WebGL/browser integration | PASS; details below |
| Remote CI / public deployment / production recovery | NOT VERIFIED or performed in this phase |

New frontend cases cover display-basis/extent validity and segment breaks,
renderer-wrapper initialization/failure/context recovery/disposal, supported
source details and safe failures, timeline exact stepping/play/pause/end/reset,
hidden-page/reduced-motion behavior, shared dataset/index, request cancellation,
late track/search protection, source-detail abort, window reset, invalid calendar
input, optional vector validation and continued old-response 2D use. Renderer
lifecycle unit tests use a mock; they are **not** called real WebGL verification.

Actual Chromium **154.0.8037.57**, Playwright **1.62.0**, WebGL **2.0**, ANGLE
**SwiftShader software renderer** executed the browser checks. This is real WebGL
shader rendering, not a mocked canvas, but it does not establish physical GPU
throughput or support on untested devices. Viewports **1440x1000**, **820x1180**
and **390x844** all passed:

- Initial Earth, changed rendered camera view, rotate/zoom/reset and useful focus.
- Genuine stored ISS snapshot/detail and a real backend **91-point** ITRS track.
- Two antimeridian-separated 2D segments; shared globe/map/timeline/selected data.
- Pointer marker inspection and keyboard slider interaction.
- Play/pause/whole-sample progression with **zero extra playback API requests**.
- Source/epoch/retrieval/execution labels, explicit predicted EOP and limitations.
- Bound-error clearing, empty catalog, original TEME inspector and no overflow.

Actual `WEBGL_lose_context` loss/restoration passed: fallback announcement,
continued map/timeline use and recovered renderer. A separately labelled forced
missing-WebGL capability plus real reduced-motion browser preference passed:
source/map/slider usable, Play disabled, manual Next working. There were **zero
JavaScript page errors** and **zero external browser requests**. Screenshots were
captured and desktop/mobile composition visually inspected. The initial camera
assertion attempted to read an intentionally non-preserved WebGL drawing buffer;
it was corrected to compare actual compositor screenshots, which passed. No app
rendering behavior or scientific assertion was weakened to make that check pass.

[Machine-readable integration evidence](phase-4-integration-results.json) records
actual UTC run time, versions, graphics backend, checks and representative values.
Source: existing catalog **25544**, snapshot **1**, orbital epoch
`2026-10-18T11:12:47.040768+00:00`, first retrieval
`2026-10-18T17:14:39.983172+00:00`, source SHA-256
`556827b7dc6cbccd0cbc3e40a9e0a0ed2205ad2d2006a8649e16ee8c0c143d4b`.
This is actual local HTTP/calculation integration from a genuine stored source,
not a new satellite download or direct observation. Mocked fixture tests remain
separate. Generated scientific audit files for this run are
`/tmp/orbitiq-phase4-sgp4-results.json` and
`/tmp/orbitiq-phase4-transform-results.json`; prior phase artifacts were preserved.

Clean install used a source-only temporary copy, excluding real DB/backups,
secret files, Git metadata, virtual environments, node_modules/build/caches.
Both frozen installs and checks passed. Existing Starlette TestClient HTTPX and
npm transitive `whatwg-encoding` deprecation warnings remain visible. They were not
suppressed and no existing dependency was upgraded merely to remove them.

## Database preservation and files changed

No initialization, ingestion, overwrite, reset, restoration, migration or database
schema change. All new interactions are read-only computed responses. Original
migrations, immutable snapshot/triggers and existing backups remain. Schema **2**,
**1** snapshot, integrity **ok**, archive verification successful. Before/after
SHA-256 is exactly:

`c389d0f1d663967be70a32f846f8e968e70a4f46c37343a5b80ceca5964e5f59`

The additive API and unit tests use temporary databases. No persistent timeline,
ground-point or derived-history storage was introduced. Local/cloud-task storage
still does not establish production durability or disaster recovery.

New files:

- `backend/tests/test_phase4_rendering.py`
- `frontend/src/Globe.tsx`, `globe-renderer.ts`, `globe-geometry.ts`
- `frontend/src/Timeline.tsx`, `use-reduced-motion.ts`, `SatelliteInfo.tsx`, `snapshot-api.ts`
- `frontend/src/Globe.test.tsx`, `Timeline.test.tsx`, `globe-geometry.test.ts`, `snapshot-api.test.ts`, `Explorer.integration.test.tsx`, `test-fixtures/explorer.ts`
- `frontend/public/assets/earth-atmosphere.jpg`, `THREE-LICENSE.txt`, `README.md`
- `docs/phase-4-plan.md`, `phase-4-integration-results.json`, this report

Updated:

- `backend/orbitiq/orbits/coordinates.py`, `api/scientific_schemas.py`: authoritative additive footpoints.
- `frontend/package.json`, `package-lock.json`: exact compatible Three.js/type pins.
- `frontend/src/App.tsx`, `ScientificExplorer.tsx`, `GroundTrack.tsx`, `style.css`: integrated workspace and preserved original inspection.
- `frontend/src/ground-track-api.ts`, `ground-track-api.test.ts`: additive rendering contract validation.
- `README.md`, `docs/scientific-conventions.md`: interaction, display, scientific and setup conventions.

No original test/assertion was deleted or loosened. Python locks/declarations,
SGP4 implementation, ingestion, storage, migrations, prior phase reports/reference
artifacts and database bytes are preserved. No additional environment credential,
network rule or reusable startup/configuration change is required: existing
`uv sync --locked`, `npm ci` and backend/Vite startup instructions cover this phase.

## Every requested acceptance criterion

| Criterion | Status | Evidence / scope |
| --- | --- | --- |
| Existing Phases 1/2/3 remain intact | **PASS** | Original suites retained, 268/96 full passes, original TEME route/browser inspector |
| Genuine interactive 3D Earth | **PASS** | Three.js WebGL2; real camera-image changes and interactions |
| Selection uses real backend-supported records | **PASS** | Explicit stored NORAD-ID lookup, real ISS selection/detail |
| Scientifically compatible satellite markers | **PASS** | Validated same-time backend ITRS vectors, uniform display basis, no TEME overlay |
| Information has units/timestamps | **PASS** | Elements/ITRS/UTC source, target and execution fields; tests/browser |
| Timeline uses actual calculated samples | **PASS** | Shared integer sample index and real returned positions |
| Playback never fabricates intermediate positions | **PASS** | Exact-sample timer, no interpolation or playback request |
| Ground tracks preserve provenance/breaks | **PASS** | Same fixed snapshot/hash/epoch/segment IDs in map/globe/client |
| Failed samples not rendered valid | **PASS** | Atomic API errors, validation, cleared results, missing-vector marker suppression |
| Stale data/scientific limits visible | **PASS** | Existing freshness tests retained; source/EOP/uncertainty/leap/residual labels |
| Requests/playback bounded and cancellable | **PASS** | Limits/timeouts/abort/late-result tests, no playback API requests, pause/cleanup |
| Usable WebGL failure fallback | **PASS** | Unsupported-browser scenario and actual context-loss recovery with usable map/timeline |
| Usable desktop/mobile layouts | **PASS** | Desktop/tablet/mobile browser/layout checks and inspected screenshots |
| Keyboard/status accessibility | **PASS** | Native labelled controls, slider keys, marker-to-info focus and status announcements; scoped smoke checks |
| Frontend tests pass | **PASS** | 96 current and clean-copy tests |
| Backend/scientific regressions pass | **PASS** | 268 tests plus unchanged 40/6 audits |
| Lint/format/TypeScript/build pass | **PASS** | Current and clean source; size warning explicitly retained |
| Existing database preserved | **PASS** | Exact original SHA-256, schema/count/integrity/archive verification |
| Documentation matches implementation | **PASS** | Pre-code plan, conventions, README, integration evidence and this report |

No in-scope criterion remains FAIL or BLOCKED. Passing these checks does not
establish complete scientific validation, full accessibility certification or
public-launch readiness.

## Limits, deferred work and next phase

No full catalog/name index, multi-satellite scene, arbitrary off-grid interpolation,
observation validation, uncertainty estimation, visibility/collision analysis,
persistent derived results or automatic EOP maintenance. The declared 400-Earth-
radius display extent and coarse-sample path limits are visualization bounds;
numeric data remain authoritative. Graphics were verified in one software-rendered
Chromium environment, not mobile physical GPUs or multiple browser engines. The
renderer chunk warning and first-load asset cost remain performance work.

Production still requires target-device performance/accessibility/security review,
authentication/rate/abuse decisions where needed, monitored scientific-resource
coverage/expiry, persistent managed storage and verified independent recovery,
proper root asset/API routing and an authorized repeatable deployment process.
Local builds/WebGL do not prove those outcomes. No infrastructure was added to
imply otherwise.

Recommended next phase, **only when authorized**: provenance-preserving historical
snapshot comparison and investigation workflows, using this timeline/explorer as
the presentation foundation, with clear differences between changed source
models, calculated positions and direct observations. Do not begin Phase 5
automatically. No commit, push, deployment or publication is part of Phase 4.
