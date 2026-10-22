# Engineering E2: accessibility, usability and globe performance

E2 is an engineering milestone alongside Phase 11.3.1. That scientific phase
remains **PARTIAL**, with scientific evaluation **BLOCKED**. ESA time,
KIN-quality and frame-alignment questions remain unresolved. These browser
fixtures are not scientific evidence; no genuine Swarm-A propagation or residuals
are produced.

## Scope and acceptance

Start: `ca2e93f4da1088c8f41a4e21f62d9af520cd4568`, clean branch
`engineering-e1-browser-pdf-ci`. Work branch:
`engineering-e2-accessibility-performance`.

Acceptance: address demonstrated keyboard/semantics/loading defects; audit actual
responsive pages; record reproducible globe and bundle measurements; retain all
77 E1 flows, five failure cases, two expected-failure diagnostic probes and seven
PDF inspections; run E2 checks in the existing release-image CI job. Timing is
informational, not an unstable shared-runner performance gate.

## Application changes

- Add a keyboard-first skip link to the workspace. Its activation focuses the
  workspace without changing the URL fragment owned by investigation routing.
- Preserve the gold focus indicator on the current navigation button. Previously
  the later current-page rule replaced the focus rule with the same blue outline
  used when the button was not focused.
- Use a dark focus outline in the white printable dialog. The previous gold on
  white outline had insufficient contrast (1.37:1 on white; the new dark
  outline is 18.40:1). Native dialog handling, initial focus,
  Escape cancellation, opener restoration and printing remain intact.
- Give labelled camera/pagination groups and calculated-result containers roles
  that support their accessible names. Generic labelled divs did not establish
  those semantics.
- Bound the loading state for a stalled renderer-module request to 15 seconds
  and expose Retry 3D.
  Ignore a timed-out import that arrives later; a retry can use the subsequently
  loaded module. Dynamic import itself is not abortable; the watchdog bounds the
  visible wait rather than the underlying network request. Preserve renderer exceptions in the browser console rather than
  swallowing the diagnostic. This watchdog cannot interrupt synchronous GPU work
  that blocks the JavaScript event loop.

No orbital calculations, track samples, numerical transforms, database code or
scientific gates change. Existing loading, empty archive, unavailable API,
report retry, cancellation, clipboard fallback, save errors and download errors
remain in use. No responsive redesign was justified by the audited layouts.

## Browser and accessibility method

`scripts/verify_engineering_e2.py` extends the Python Playwright framework used
by E1. It runs on each of Chromium, Firefox and WebKit against disposable release
services, using the labelled E1 synthetic public Vallado 6251 input. It never
mounts the normal database or private evidence. The browser image includes
**axe-core 4.11.1**, pinned in the frontend development lockfile. Only that test
library is copied from the npm tooling stage; it is not imported into the app.

The audit checks keyboard-first skip navigation and current-page focus; six axe
WCAG A/AA scans (initial explorer, readiness, empty saves, shared track, mobile
print dialog and mobile discovery/save); labelled controls; native dialog Enter,
Tab, Escape and opener restoration; layouts at 1440x1000, 768x1024, 390x844 and
320x740 with DPR 1; keyboard local save/retry/reopen; download-denial/retry; and
scene disposal. Chromium additionally holds a real renderer chunk request and
advances the browser clock past the watchdog, then releases the request and
retries the actual renderer. No fake success API responses or canvas replacements
are used. Synthetic browser-storage and download exceptions are explicitly
fault-injection cases.

Axe incomplete checks are retained with their target selectors for human review.
A clean automated scan does not prove screen-reader usability. Focus colours,
control semantics and page landmarks are inspected separately. Native desktop
assistive-technology sessions, physical touch devices and broad user studies are
not available in this environment.

## Globe measurement method and gates

Use the same pinned browser image, synthetic three-sample ground track, viewport,
DPR, headless software graphics configuration and script for baseline and E2.
Baseline uses the preserved E1 web image, not a source reset. Three fresh document
navigations (`?e2=0/1/2`) preserve normal browser caching between repetitions.
The preceding explorer audit warms the browser asset cache; these are not cold
public-network startup measurements.
Wait for the real track, renderer and Earth texture resource. Record context
creation, first draw and test-observed readiness relative to document navigation.
Observed readiness includes network-idle waiting and test overhead; it is not an
isolated renderer initialization benchmark. Context creation-to-first-draw is
recorded separately.

Each repetition samples requestAnimationFrame for two seconds while settled and
two seconds with 12 camera-key actions, reporting median/p95 callback intervals,
actual WebGL draw calls and buffer uploads. Callback cadence is **not rendered
FPS**: the renderer already draws on demand. Three same-document removal/reopen
cycles verify that disconnected native canvases have lost/released contexts.
Connected scenes retained for navigation state are reported separately.

Chromium CDP TaskDuration deltas describe main-thread task time during each pair
of sampling windows, not whole-process CPU usage. Browser heap estimates are
informational; the instrumentation retains context references, so they are not
proof of bounded memory or absence of a heap leak. Other engines can omit these
unsupported counters. GPU process memory and physical-device measurements remain
open. Software graphics results cannot predict hardware performance.

Blocking invariants: settled scenes issue no draw calls; camera actions issue
real draws when native rendering is available; removed scenes release contexts;
functional/keyboard/layout/axe checks pass. Hardware-sensitive time and memory
values have no CI thresholds. Firefox fallback must pass its functional checks
but is never called a native 3D pass.

## Bundle investigation

Vite already emits `globe-renderer` as a dynamic import. The E1 renderer chunk is
558,595 bytes (558.60 kB in Vite's rounded display), approximately 140.28 kB gzip; initial entry
is approximately 287.89 kB / 89.25 kB gzip. Research-only source maps outside the
repository attribute about 2.16 MB of unminified renderer sources to a single
Three.js installation. React and application code occupy the entry chunk.
`npm ls three axe-core` confirms a single Three.js version (0.186.1).

The default explorer needs the globe, so it requests the asynchronous renderer
at startup. The directly opened saved-list route leaves the
explorer unmounted. Splitting the same renderer into smaller files would not itself reduce
that view's required bytes. There is no measured reason to replace the renderer,
reduce detail or introduce speculative manual chunks. The 500 kB warning remains
enabled. No arbitrary budget is adopted. Production builds retain no source maps
or test-only axe library; research maps stay under `/tmp`.

## Reproduction

From a checkout, install locked frontend dependencies and run:

```sh
cd frontend
npm ci
npm test
npm run lint
npm run format:check
npm run build
cd ..
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
docker build --target api -t orbitiq-api:e2 .
docker build --target web -t orbitiq-web:e2 .
docker build -f deploy/Dockerfile.browser -t orbitiq-browser:e2 .
python scripts/run_browser_regressions.py --release e2 --browser-image e2 \
  --engineering-e2 --output /tmp/orbitiq-e2-regressions
```

The output directory must not exist. Host `pdftotext` is required. Managed cloud
builds use the optional `proxy_ca` BuildKit secret and a writable Buildx cache,
while keeping TLS verification enabled. The runner creates and removes only its
own read-only synthetic fixture volume, services and private Docker network.
Run without `--engineering-e2` for the unchanged E1-only suite.

CI reuses the existing release-image job and diagnostic artifact. E2 evidence
files contain browser versions, graphics capabilities, timing distributions,
axe violations/incomplete checks, layouts and resource checks. Existing E1 PDF
limitations remain: native PDF generation is Chromium-only; Firefox fallback is
not native WebGL verification. As in E1, successful WebKit screenshots are
omitted because its screenshot implementation injects inline CSS incompatible
with the application CSP; layout, keyboard and trace checks still run. See the [E1 procedure](engineering-e1-browser-pdf-ci.md)
and [E2 report](engineering-e2-report.md) for actual results.

Publication uses the engineering branch only. No merge, deployment, public HTTPS,
production recovery, alert-delivery or branch-protection configuration is part of
E2. Phase 8 production closure remains a separate milestone.
