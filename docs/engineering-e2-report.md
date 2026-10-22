# E2 implementation and verification report

This is a local pre-publication checkpoint. Remote CI is pending at the time of
writing; the final publication receipt must identify the exact pushed commit and
its GitHub Actions run. Local checks are not remote CI or production evidence.

## Repository and scope

Starting branch: `engineering-e1-browser-pdf-ci`. Starting commit:
`ca2e93f4da1088c8f41a4e21f62d9af520cd4568`. The working tree was clean. E2 branch:
`engineering-e2-accessibility-performance`. No reset, rebase, force push, merge,
release, deployment or infrastructure change is included.

The [method and reproduction commands](engineering-e2-accessibility-performance.md)
describe the application architecture, acceptance criteria and limitations.

## Demonstrated issues and fixes

The completed E1-image baseline found four explicit failures: no keyboard-first
skip link; current-location styling masking focus; low-contrast focus in the
white printable dialog; and a renderer chunk request that could leave the globe
loading indefinitely. E2 adds a router-safe workspace skip link, distinct gold
navigation focus, a dark dialog focus outline and a 15-second module-load
watchdog with working retry and rejection of late initialization. The module
fetch may still complete; the visible loading state is bounded. Dialog outline contrast
on white increases from 1.37:1 to 18.40:1.

Labelled generic containers now expose camera/pagination groups and calculated
result regions. Six automated axe WCAG A/AA scans complement real keyboard,
focus, layout, save/download-recovery and renderer-lifecycle interaction. They
are not a screen-reader conformance certification.

Baseline actual layouts had no page overflow at 1440, 768, 390 or 320 CSS pixels.
No responsive redesign was needed. Baseline native Chromium released all three
removed scenes' contexts; retained connected scenes belonged to the active and
preserved navigation views. Rendering was already on demand. No measured defect
justified geometry, pixel-ratio, animation-loop or React-render optimizations.

## Local verification

- Frontend: **345 tests passed in 25 files** (one new skip/fragment test; the
  existing constructor-failure test now also verifies diagnostics and retry).
- ESLint, Prettier, TypeScript and Vite production build: **passed**.
- Ruff lint/format and actionlint: **passed**.
- Full E1/E2 browser/PDF run: **passed**, 1164.299 seconds on this managed
  Docker/VFS environment. All **77 E1 flows** (27 Chromium, 25 Firefox, 25
  WebKit), **five failure-state cases**, both deliberately failing diagnostic
  probes (expected exit 1), and **seven PDF checks** passed their expectations.
  The maximum-track PDF contains all 361 checked sample rows.
- E2: **62 checks passed** (23 Chromium, 18 Firefox, 21 WebKit), including
  **18 axe scans** with no reported WCAG A/AA violations. Incomplete contrast
  checks remain visible in evidence; this is not complete conformance proof.
- Actual WebGL2 rendered in Chromium 151.0.7922.34 and WebKit 26.5. Firefox
  153.0 used the explicit fallback and did not exercise native graphics disposal.
  WebKit's reported renderer string is "Apple GPU" on this Linux test runtime;
  that reported string is not evidence of physical Apple hardware.
- Layouts fit all four viewports in all engines. Keyboard save failure/retry,
  native JSON-download failure/retry, dialog focus/Enter/Tab/Escape and opener
  restoration passed. Chromium's held real module request produced the 15-second
  fallback and recovered with the real renderer after release and explicit retry.
- Backend tests were not rerun locally: no backend source, API, Python dependency
  or schema changed. The unchanged CI backend job will run its full suite and
  scientific/migration checks on the published E2 commit.

The build retains the existing renderer chunk warning. No warning threshold,
scientific guard, test assertion or E1 workflow is disabled to obtain a pass.

## Bundle measurements

Exact bytes below use the same builds and Python gzip level 9 for both columns;
Vite's own gzip display uses a different compression default. Hash-only import
changes can alter compressed size by a byte without changing the raw length.

| Asset                  | E1 bytes / gzip | E2 bytes / gzip |
| ---------------------- | --------------: | --------------: |
| Entry JavaScript       |  287888 / 88922 |  288375 / 89063 |
| Main CSS               |     7468 / 2214 |     7681 / 2287 |
| Dynamic globe renderer | 558595 / 138971 | 558595 / 138972 |
| Discovery JavaScript   |   44765 / 12536 |   44778 / 12544 |
| Report CSS             |      2448 / 939 |      2523 / 970 |

The entry grows 487 bytes raw for access/recovery behavior. The renderer remains
the same raw size and remains dynamically imported; the default explorer needs
it at startup. The single Three.js installation accounts for the renderer's
large dependency payload. No unsupported bundle reduction is claimed. The locked
axe-core development dependency does not enter production JavaScript; production
builds contain no source maps. Research-only source maps remain outside Git.

## Globe measurement results

[Recorded raw engineering results](engineering-e2-measurements.json) retain the
initial baseline, complete browser-run observations and the quieter paired
repeat. All use Linux, Chromium 151.0.7922.34, the same pinned E2 browser image,
1440x1000 viewport, DPR 1, SwiftShader WebGL2, identical three-sample synthetic
tracks and the same measurement script. No other regression suite ran during
the paired repeat. The fixture API stayed the same across the paired images;
browser-cache warming and order still limit causal comparisons.

| Paired measurement, three repetitions      |              E1 baseline |                       E2 |
| ------------------------------------------ | -----------------------: | -----------------------: |
| Test-observed readiness, ms                | 1040.8 / 1166.3 / 1218.5 | 1203.7 / 1705.4 / 1337.7 |
| Context creation to first draw, ms         |       55.4 / 38.7 / 49.8 |       60.5 / 26.2 / 64.8 |
| Stable rAF p95, ms                         |       16.7 / 16.8 / 16.8 |       16.8 / 16.8 / 16.8 |
| Camera-interaction rAF p95, ms             |       16.7 / 16.8 / 16.8 |       16.8 / 16.8 / 16.8 |
| Main-thread task seconds over both windows |       .102 / .073 / .080 |       .196 / .357 / .098 |
| Idle draw calls, each repetition           |                        0 |                        0 |
| Draw calls for 12 camera actions, each     |                       60 |                       60 |
| Interaction buffer uploads, each           |                        0 |                        0 |

The paired baseline reports coarse browser heap estimates of 11,900,000 bytes
and E2 reports 26,000,000 bytes; the earlier isolated E1 baseline also reported
26,000,000 bytes. These estimates vary between runs and do not isolate retained
application memory or establish a causal increase.
All three removed native scenes release their contexts, while two connected
scenes remain for active/preserved navigation views. This verifies the tested
resource lifecycle, not absence of every possible heap or GPU-memory leak.

The earlier full regression run recorded Chromium readiness of 1807.5, 7944.1
and 19287.0 ms and interaction p95 values of 483.2, 150.0 and 83.2 ms. Those
spikes did not recur in the paired repeat. Renderer JavaScript is byte-identical
after normalizing the hashed entry-import filename. No reliable causal speed
improvement or regression is established by these few noisy samples. The initial
spikes remain recorded; a physical-device, cold-network, larger-scene and
whole-process CPU/GPU study is outside this milestone. No timing threshold is
used to conceal variation or make CI flaky.

The measurable improvements are keyboard/focus access and bounded visible
loading/recovery. The 500 kB warning remains explained rather than suppressed.

## Preservation and scientific boundary

A pre-edit SHA-256 manifest covers 401 existing files, including 72 private data
files. Integrity checks found all private files, the normal SQLite database and every
existing report unchanged. The final publication review repeats this manifest
comparison. New browser services use separate
read-only disposable synthetic fixtures, never the normal archive.

Phase 11.3.1 remains **PARTIAL**; scientific evaluation remains **BLOCKED**. ESA
inquiry RITM0144536 time, KIN-quality and frame-alignment questions remain open.
Historical GP availability and creation timestamps remain unknown; fitting
lineage and statistical independence remain unestablished. No genuine Swarm-A
propagation, ESA residuals, forecasting or independent-accuracy claim is made.

Phase 8 production gates remain separate: hosting/HTTPS, independent off-machine
recovery, monitoring with actual alert delivery, and branch protection/required
checks. Repository evidence still reports `main` unprotected; E2 changes no
settings. Neither a local build nor passing engineering CI closes these gates.

## Changed files

- Application: `frontend/src/App.tsx`, `Globe.tsx`, `GroundTrack.tsx`,
  `Investigations.tsx`, `ScientificExplorer.tsx`, `style.css`, `report-print.css`.
- Frontend regression tests: `frontend/src/App.test.tsx`, `Globe.test.tsx`.
- Dependency lock: `frontend/package.json`, `frontend/package-lock.json`.
- Browser automation: `scripts/verify_engineering_e2.py`,
  `scripts/run_browser_regressions.py`, `deploy/Dockerfile.browser`.
- CI: `.github/workflows/ci.yml`; no redundant workflow is added.
- Documentation: `README.md`, this report,
  `docs/engineering-e2-accessibility-performance.md`,
  `docs/engineering-e2-measurements.json`.

All 19 files are limited to E2. Databases, private attachments/correspondence,
credentials, environment files, browser artifacts, research source maps and
unrelated changes are excluded. Existing E1 runners and previous phase reports
are preserved. GitHub publication and exact-commit CI verification are separate
from this local checkpoint; no production milestone is claimed here.
