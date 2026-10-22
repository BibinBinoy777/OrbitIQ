# E1 — browser and PDF regression automation

E1 is a parallel engineering milestone. Phase 11.3.1 remains **PARTIAL** and
scientific evaluation **BLOCKED**. ESA time, KIN-quality and actual-pair IGb08
alignment are unresolved. These tests do not qualify Swarm-A or independent
orbital accuracy. They never use private ESA/GP inputs or the operator database.

## Coverage and CI strategy

The existing `OrbitIQ checks` workflow runs on pushes, pull requests and manual
dispatch. Its `release-images` job now builds the existing pinned Playwright
runtime and executes browser/PDF checks after the existing image smoke check.
All three engines run sequentially against one pair of prebuilt release images;
this avoids rebuilding and transferring API/web images in three matrix jobs.
The job remains blocking, with a 20-minute timeout and no blanket retries.

| Existing runner | Chromium | Firefox | WebKit |
| --- | --- | --- | --- |
| Critical application/saved investigation/ground track/sharing | 7 | 7 | 7 |
| Historical analysis, pagination, exports and navigation | 8 | 8 | 8 |
| Empty observation archive | 2 | 2 | 2 |
| Explicit synthetic observation package | 4 | 4 | 4 |
| Reports, JSON/HTML export, print layout and saved card | 6 | 4 | 4 |
| Total flow checks | 27 | 25 | 25 |

These are 77 flow groups with multiple assertions, not 77 independent scientific
tests. Chromium additionally generates seven PDFs: snapshot, position, short
track, comparison, maximum track, saved card, and standalone offline position.
The existing Poppler checker verifies parseable text, page counters, all seven
report sections, source hashes/epochs/retrieval clocks, warnings/limitations and
every returned track row, including the 361-row maximum. No OCR or pixel baseline
is used. Firefox/WebKit verify HTML/print CSS and downloads, not native PDF output.

Five additional Chromium fault-injection checks cover a held health request's
loading indicator, an aborted health request's actionable error, a real empty
history response, failed report generation followed by a successful explicit
retry, and actual disabled-WebGL fallback. Transport faults are labelled as such;
no fake API responses or mock canvas are used. These are counted separately
from the preserved 77 existing flow groups.

Chromium requests SwiftShader software WebGL2. The existing globe check records
whether a real WebGL2 canvas initialized or the application's explicit 2D fallback
was shown. A fallback pass is not a 3D rendering pass. No API/canvas mocks are
introduced. WebKit skips screenshots during successful flows because its screenshot
implementation injects inline CSS incompatible with the unchanged application CSP;
layout/focus checks and tracing still run. Failure screenshots are best-effort.

## Fresh-checkout local commands

Requirements: Linux/WSL2, Docker with the local Unix socket, Python 3.12, Node 24, uv 0.12.23,
and host Poppler `pdftotext`. On Ubuntu install `poppler-utils` with the system
package manager. The browser image pins Playwright 1.62.0 and the matching browser
image digest; Python and Node application dependencies retain their existing locks.
Poppler comes from the runner OS, not a new application dependency.

```sh
uv sync --locked
docker build --target api -t orbitiq-api:e1 .
docker build --target web -t orbitiq-web:e1 .
docker build -f deploy/Dockerfile.browser -t orbitiq-browser:e1 .
python3 scripts/run_browser_regressions.py --release e1 --output /tmp/orbitiq-e1-results
```

The output directory must not exist. The runner owns only its unique containers,
network and fixture volume, and removes them in `finally`. No host ports are
published. It waits for the actual gateway `/api/ready` response before browser
work. It selects the explicit local Docker socket rather than a remote context.
Use an available task-owned `BUILDX_CONFIG` if the default build cache is read-only.
Managed proxy environments may additionally require the existing optional
`--secret id=proxy_ca,src=/path/to/combined-ca-bundle` on each image build; keep
inherited proxy configuration and TLS verification. No CA is embedded in an image.

To recheck generated PDFs without starting browsers again:

```sh
python3 scripts/verify_report_pdf.py \
  --directory /tmp/orbitiq-e1-results/chromium-report/reports \
  --output /tmp/orbitiq-e1-results/pdf-recheck.json
```

The individual existing `verify_*browser.py` command-line interfaces remain
available. `verify_history_browser.py --fixture` explicitly labels synthetic CI
history; omit it only for a separately authorized genuine-archive rehearsal.
Setting `ORBITIQ_BROWSER_DIAGNOSTICS` opts those runners into fixture-only trace,
console, failure screenshot and external-request-guard collection. Do not enable
CI diagnostics against private archives or authenticated personal sessions.

## Fixture provenance and isolation

`seed_browser_fixtures.py` creates only a new empty named volume. It uses the
existing public Vallado-derived `vallado-leo.json` catalog-6251 fixture, labels its
name `E1 SYNTHETIC UI FIXTURE - NOT OBSERVED HISTORY`, and deliberately changes
three fields and the second epoch for UI change-analysis coverage. These two
records are not genuine historical retrievals. The existing storage contract
requires a CelesTrak-shaped source URL; that string in a fixture is not evidence
of an actual provider request or receipt. Fixed retrieval dates are test inputs.

The separate observation package reuses the existing synthetic 3/-4/0-km
arithmetic pattern, labelled `SYNTHETIC-ONLY-*`, with zero independently verified
observations. Its calculations concern catalog 6251 only, never Swarm-A 39452.
One service configuration has no observation archive; a second opts into this
explicit synthetic package. The fixture volume is mounted read-only at runtime
and hash-checked before/after. The normal database is never mounted or opened.

Services run on a Docker internal network; fixture initialization has no network.
Browser contexts additionally abort external HTTP(S) requests. Test images may be
downloaded at build time, but routine tests have no live CelesTrak/ESA dependency.
Bundled EOP/leap policies and all scientific guards remain unchanged. Updates to
expired resources require separate review, not a fallback download or tolerance.

## Failure diagnostics and artifacts

Any unexpected nonzero suite exit, timeout, missing flow/PDF output, changed
fixture or assertion fails the job. The runner records stage names, exit codes,
durations and logs. Independent browser suites continue after a suite failure
to collect useful cross-browser evidence; a failure never becomes a pass.

Two deliberate probes verify failure plumbing: an absent UI element must fail
with a screenshot, trace and error JSON; an external navigation must be blocked
and fail with the denied URL recorded. Their expected nonzero exits are explicitly
labelled in `commands.json` and excluded from the 77 product-flow count.

Open the exact commit's Actions run, select `release-images`, and download
`browser-pdf-regressions`. Upload runs with `always()` and retains artifacts for
seven days. `failure.json`, stage logs, `diagnostics/console.json`, screenshots
and `trace-*.zip` identify the failing engine/stage. Open traces locally using
the matching Playwright `show-trace` tool. Generated PDFs/JSON/HTML are retained
for content inspection. Traces contain DOM/network data from these fixtures.
The artifact root is a dedicated new output directory; database volumes, private
research, credentials and unrelated workspace files are never copied into it.

## Scope and remaining checks

This suite covers existing flows, not a complete WCAG/screen-reader assessment,
physical GPUs/devices, native Safari, physical printers or production hosting.
The existing 2D fallback is reported honestly. Real provider connectivity,
scientific qualification, genuine-history investigation and off-machine recovery
remain separate tasks. See the E1 verification report for executed counts,
durations, local/fresh-checkout evidence and exact-commit CI results when available.
