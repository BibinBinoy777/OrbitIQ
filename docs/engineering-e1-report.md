# E1 implementation and local verification report

Checkpoint: **22 October 2026**, before publication of this engineering update.
Starting commit: `a29a5ac7cac5cd10c17f2d64305b1f961d6c4580`; starting tree clean.
Working branch: `engineering-e1-browser-pdf-ci`.

## Scope and acceptance criteria

Connect the existing browser and PDF runners to blocking push/PR/manual CI,
retain all three engines and seven PDFs, use only isolated public/synthetic
fixtures, verify useful failure artifacts/nonzero exits, preserve private inputs,
and document reproducible commands. Phase 11.3.1 stays **PARTIAL**, scientific
evaluation **BLOCKED**. No real Swarm-A propagation, transform or residual occurs.

## Implementation

- Extend the existing `release-images` job: reuse its API/web images, build the
  existing digest-pinned Playwright image once, run all engines sequentially,
  inspect PDFs with Poppler, and upload fixture-only diagnostics with `always()`.
- Add a standard-library Docker orchestrator and exclusive fresh-volume seeder.
  API/web roots and the fixture mount are read-only; network is internal and no
  host port is published. Readiness is condition-based, not a fixed startup sleep.
- Add opt-in shared Playwright tracing, console/request-failure records, failure
  screenshots and an external HTTP(S) guard. Existing CLI interfaces remain usable.
- Declare synthetic history with `--fixture`, removing an accidental ISS-only
  navigation assumption by re-entering the requested catalog after form remount.
- Add five explicit Chromium loading/empty/error/recovery/WebGL-failure checks.
  Two separate expected-failure probes verify nonzero exits and diagnostics.
- Add the [operator guide](engineering-e1-browser-pdf-ci.md) and README pointer.
  No application dependencies, lockfiles, physics, product UI or scientific gates
  change. Poppler is an OS-provided verification tool; Playwright remains 1.62.0.

## Actual local results

| Executed command / check | Result |
| --- | --- |
| Locked API/web image builds and existing browser Dockerfile build | PASS; no host virtualenv/node_modules/private archive required by images |
| `python scripts/run_browser_regressions.py --release e1 --output /tmp/orbitiq-e1/browser-run-final` | PASS; 653.978 seconds before final cleanup; 77 existing flow groups, five additional fault-injection cases, seven PDFs; fixture unchanged |
| Chromium 151.0.7922.34 | 27 existing groups passed; actual software WebGL2 canvas recorded |
| Firefox 153.0 | 25 existing groups passed; explicit 2D fallback recorded, not a WebGL rendering pass |
| WebKit 26.5 | 25 existing groups passed; actual software WebGL2 canvas recorded |
| Final targeted `verify_browser_failure_states.py` rerun | All five cases passed with the final held-request completion handling; no cancellation traceback |
| Existing `verify_report_pdf.py`, invoked by orchestrator | Seven PDFs passed; all sections, provenance, warnings, page counters and track rows retained; maximum report 72 pages / 361 rows |
| Expected missing-element and external-navigation probes | Both exited 1 as intended; valid PNGs, readable trace ZIPs and error JSON checked; denied URL recorded |
| `uv run --locked pytest -q --junitxml=/tmp/orbitiq-e1/backend.xml` | 1,208 passed, two existing warnings; 88.13 seconds |
| `npm test` | 344 passed, 25 files; 18.211 seconds command time |
| `npm run lint`, `npm run format:check`, `tsc --noEmit`, `npm run build` | PASS; existing Vite chunk-size warning retained |
| `uv run --locked ruff check .`, `uv run --locked ruff format --check .` | PASS |
| Actionlint 1.7.7 on `.github/workflows/ci.yml` | PASS; downloaded tool checksum verified |
| `git diff --check` | PASS |

Full backend tests ran after the orchestration/diagnostic implementation; later
changes were confined to the browser harness and documentation. The final
held-request fix was rerun through all five affected browser cases. No earlier
partial browser run is represented as final verification. Local logs and original
failed/partial attempts are retained under `/tmp/orbitiq-e1/`.

## Investigated failures and reliability limits

Initial image builds could not write the default Buildx cache; a task-owned
`BUILDX_CONFIG` fixed the managed-environment restriction without changing Docker
credentials or TLS. Initial new-script formatting/lint findings were corrected.
The controlled failure probe caught unreadable new script files; public scripts
are readable and browser containers use the host artifact owner's UID/GID.

A partial run then exposed the history runner's implicit return to catalog 25544;
the explicit catalog is now restored, preserving every two-record assertion. That
outdated partial run was interrupted, its late-created container removed, and a
fresh complete run passed. The new loading test initially closed a held request;
it was changed to complete the real request after checking loading, and all five
affected cases reran successfully without the cancellation traceback.

There are no blanket test retries, forced passes or relaxed scientific tolerances.
Runtime depends on Docker/browser infrastructure; build/install network failures
are separate from provider-data availability. The local complete browser run used
the managed Docker environment and took about 11 minutes; CI has a 20-minute job
budget and its actual duration must be read from the exact commit's Actions run.
Native PDF generation is Chromium-only. WebKit success screenshots remain omitted
for CSP compatibility. Physical devices/GPUs, native Safari, screen readers,
printers, real providers and production infrastructure remain outside this suite.

## Preservation and publication boundary

The existing 72 private files and ordinary database match the established hash
baseline. All prior phase reports, protocol, frame investigation, application code,
lockfiles and scientific guards remain unchanged. Test fixture fingerprints also
match before/after. No E1 containers, networks or volumes remain after validation.
Generated artifacts contain public/synthetic fixtures only and are not Git inputs.

This document records pre-publication local evidence. It does not claim remote CI
has run yet. After authorized publication, verify the exact pushed SHA against
all backend, frontend and extended release-image jobs; that fresh checkout is the
remote reproducibility check. Consult the exact-commit Actions run and final
publication receipt for actual results. No main-branch merge, release, deployment,
DNS or repository-protection change belongs to E1. Production launch gates remain
separate. ESA time, KIN-quality and actual-pair frame qualification remain open;
historical availability/creation clocks are unknown, lineage incomplete and
independence unestablished. No qualified Swarm-A residuals exist.
