# Phase 4 implementation plan and acceptance gates

Recorded before code changes. Inspected the Phase 1/2/3 reports, numerical and
integration artifacts, repository/Git status, React clients/state/visualization,
backend schemas/propagation/storage and installed toolchain. Current `main` is
clean at bf3f113; the preceding authorized publication is historical. This task
explicitly prohibits committing, pushing, deploying or publishing new work.
Baseline rerun: 256 backend tests and 61 frontend tests pass. Existing database:
schema 2, one real ISS snapshot, integrity ok, SHA-256
`c389d0f1d663957be70a32f846f8e968e70a4f46c37343a5b80ceca5954e5f59`.

Architecture: React local state, native fetch cancellation, validated TypeScript
clients, no routing/store/globe framework. Phase 3 supplies ITRS satellite vectors
and geodetic surface coordinates, a 2D SVG map and atomic bounded track responses.
It has no playback and no rendering dependency. Discovery is explicitly stored
snapshots by NORAD ID, not a full public catalog or name-search index.

Plan:

1. Pin Three.js 0.186.1 and compatible @types/three 0.186.0; use OrbitControls
   without a React scene framework. Lazy-load the renderer; serve an attributed
   static Earth asset locally if available. No tiles, live map service, fake
   satellites, auto-spin, solar illumination claims or new external data source.
2. Add backend WGS84 zero-height footpoint Cartesian vectors to Earth-fixed
   results. This missing data enables authoritative surface geometry without
   browser geodetic calculations. Reuse Astropy EarthLocation and existing
   geodetic output. Original SGP4/TEME/ITRS values, limits, EOP rules and database
   remain unchanged. Add analytic/reference/API tests without relaxing any test.
3. Extend existing track client to validate optional ITRS vectors, footpoints,
   and execution times; missing data disable 3D markers while leaving the 2D
   fallback/metadata available. Use one shared track and selected sample for
   globe, map, timeline and information. No interpolation or playback requests.
4. Separate globe renderer/lifecycle, accessible wrapper/controls, timeline
   state/controls, and source-information client/panel. Preserve catalog-ID search
   with explicit submit, snapshot selection and cancellation. Add normalized
   element details through the existing snapshot-detail endpoint, not invented
   parameters or new storage. Keep original TEME inspection available.
5. Render Earth as a WGS84 ellipsoid; map ITRS axes to Three.js display axes by
   an explicit right-handed basis and uniform km scale. Render satellite at the
   exact returned ITRS position; enlarged marker size is explicitly illustrative.
   Surface paths use backend footpoints, preserve segments and avoid coarse-gap
   connections. Camera rotation/zoom/reset/focus, keyboard controls, WebGL error/
   context-loss fallback and manual recovery. Dispose resources and render on
   demand with bounded geometry/device pixel ratio.
6. Timeline: default 90 minutes/60-second samples near source epoch, previous/
   next/range selector, explicit play/pause at one sample/second, stop at end,
   reset to first sample, no wrap/interpolation. Pause on input/source changes,
   failures, hidden document, reduced-motion preference and unmount. Announce
   selected UTC time; preserve source epoch/retrieval/execution distinctions.
7. Verify baseline regressions, 40 SGP4 + 6 terrestrial reference audits, new
   API/display/lifecycle/timeline/cancellation tests, lint/format/types/build,
   clean locked installation, real Chromium WebGL + desktop/mobile/keyboard/
   reduced-motion/fallback/context-loss requests, and byte-identical database.
   Capture evidence; document browser/software-renderer limits honestly.

Acceptance: individually mark all 19 uploaded Phase 4 criteria PASS/FAIL/BLOCKED
in docs/phase-4-report.md. Genuine interactive WebGL Earth, validated coordinate
markers, real stored-data discovery, explicit timestamps/units, exact-sample
playback, shared provenance/segments, no failed/fake samples, warnings, bounded
cancellation, usable WebGL fallback, responsive keyboard-accessible controls,
passing regression/quality checks, preserved DB and factual docs are mandatory.
No assumption that local WebGL/build success establishes public-launch readiness.
