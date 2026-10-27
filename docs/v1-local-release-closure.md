# OrbitIQ V1 — inquiry tracking and local release closure

**Authorized publication checkpoint — 27 October 2026:** the owner authorized
committing and pushing the reviewed nine-file Windows compatibility patch to
`publication/windows-compatibility-2026-10-27`, then checking its exact-commit CI.
The reported native Windows17 pass and four matching source backups are recorded
in the publication addendum below. Earlier local/pending statements remain dated
checkpoints. New remote CI is **PENDING**, not a reported pass. No merge or
production deployment is authorized.

**Windows final review — 26 October 2026:** the owner reports **17 native Windows
tests passed, 0 failed, 0 skipped in 7.09 seconds**; see the
[final-review addendum](#windows-final-review-and-owner-test-result--26-october-2026).
Earlier Linux results and startup reports remain separate. Windows browser
workflows remain unverified, and the new CI job has not run. Earlier dated
checkpoints below remain historical; this patch is local and unpublished.

**Publication review — 26 October 2026:** the owner authorized publishing this
verified documentation on `publication/v1-verified-docs-2026-10-26`. Earlier
"local/unpublished" statements describe their dated verification checkpoints.
The publication commit and its remote CI must be verified separately; no new CI
success is asserted by this pre-publication snapshot. Scientific validation and
production readiness remain **NO-GO**; no deployment is authorized.

**Latest decision:** local engineering **GO_FOR_INTENDED_LOCAL_USE** for the
implementation verified at `8160bcb972c5c1486b2b138008b0cd4d5bd633c4`. See the
[final helper-integration decision](#final-helper-integration-decision--25-october-2026).
Earlier outcomes below are retained historical assessments. Owner acceptance is
unchanged; scientific validation and production readiness remain **NO-GO**.

Assessment: **25 October 2026, Asia/Calcutta**. Target decision date:
**31 October 2026**. This is a local V1 candidate assessment, not public-production
approval or scientific qualification.

**Outcome:** current backend/frontend integration, locked installation, restart
and separate synthetic backup/restore passed. A demonstrated PDF-verification
defect was fixed. Six generated PDFs pass all existing content checks; the complete
browser/seven-PDF release gate remains **PARTIAL** because of documented runtime
limitations. Scientific comparison remains **BLOCKED — NO-GO**, and E4 remains OPEN.

Branch `engineering-e8.2-igs-reference-qualification`, starting HEAD
`b0a03205e3930b55651232d8b7ffbc9e879ae8c6`, preserved. Existing unpublished changes
were retained. The [machine-readable evidence](v1-local-release-evidence.json)
records source fingerprints, commands, scoped results and remaining dependencies.

**Current owner acceptance:** **ACCEPTED_FOR_INTENDED_LOCAL_USE**, dated
**2026-10-25**. The [acceptance addendum](#owner-acceptance-addendum--25-october-2026)
supersedes earlier pending-owner statements only; earlier sections remain
historical evidence. Local engineering retains **CONDITIONAL GO**; scientific
validation and production readiness retain **NO-GO**.

## IGS inquiry accurately recorded

The new [inquiry status record](igs-inquiry-status.json) says
**SENT_USER_REPORTED**, based on the operator's statement and pasted sent text.
It identifies the exact ERP product/hash and the four topics actually asked.
Recipient role is reported as IGS Analysis Center Coordinator. Actual recipient
mailbox, sent timestamp and message identifier are **unknown/null**: no reliable
sent-message metadata was provided. Delivery is **not verified**, reply **pending**.
The record date is not asserted to be the send date.

Original E8.7.10 draft/report/ledger remain unchanged, including their historical
UNSENT status at creation; their hashes are bound in the new status record. The
operator's sent wording is not claimed identical to the original draft. No raw
correspondence, personal contact information, invented receipt or provider answer
was added. No message was sent by this task. Sending resolves no scientific gate.

## Requirement selected and concrete fix

Reviewed E1–E7 readiness evidence and E4 final closure. E6 addressed E5's local
onboarding/portable-recovery priority; E7 addressed historical-window contract
drift. The useful remaining local requirement was to verify the **current working
tree as an integrated, reproducible candidate**, including its unpublished tools
and tests, rather than repeat the ERP audit.

The browser/PDF work demonstrated a release-verifier defect. A complete limitation
sentence in `chromium-comparison.pdf` crossed pages 15–16. Poppler's raw extraction
inserted the known page header/footer between its words. The existing checker
removed whitespace but retained that page furniture, falsely reporting missing
scientific limitation text.

Changed [the PDF verifier](../scripts/verify_report_pdf.py) to validate raw page
count and known numbered running furniture at page boundaries, then remove only
that furniture before matching body text. All **six preexisting assertion ASTs**
are unchanged: required warnings/limitations, source identity, timestamps, track
rows, sections, privacy and layout/page-counter checks remain. Interior lookalike
body text is preserved; missing/wrong furniture or genuinely omitted content fails.

Added [15 synthetic regressions](../backend/tests/test_report_pdf_verifier.py),
including the cross-page case, missing warning words, malformed counters,
boundary placement and interior lookalikes. No application behavior, dependency,
scientific algorithm or acceptance threshold changed.

## Actual verification

| Check                              | Result and scope                                                                                                                                                                                                                              |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Final integrated backend           | **1,582 passed**, zero failures/errors/skips, 69.73 s; rerun after the verifier fix. Source hashes unchanged during execution.                                                                                                                |
| Current frontend                   | **427 passed**, zero failures/errors/skips. All 87 captured frontend source hashes still match.                                                                                                                                               |
| Python lint/format                 | `ruff check .` and `ruff format --check .` passed; 253 Python files formatted.                                                                                                                                                                |
| Frontend lint/format/types/build   | ESLint, Prettier and `tsc --noEmit && vite build` passed; dependency-tree check passed.                                                                                                                                                       |
| Fresh installation                 | New Python environment with `uv sync --locked`, fresh `npm ci`, production frontend build, actual frontend/API proxy passed.                                                                                                                  |
| Startup/storage safety             | Missing DB gives liveness but 503 readiness without creating a DB; explicit initialization works, duplicate init refuses, schema-3 migration is a no-op.                                                                                      |
| Failure/restart                    | Injected provider failure retains fixture history; restart and recovery/deduplication passed without live provider requests.                                                                                                                  |
| Backup/restore                     | SQLite engine backup restored to a separate new fixture target; complete schema/table fingerprints equal, integrity/FK checks OK, recovered APIs HTTP 200. This is local synthetic recovery only.                                             |
| Production-gateway Chromium subset | **7 critical cases**, **5 loading/error/retry/fallback cases**, **2 empty-observation cases** passed; two deliberate diagnostics failed as expected and produced evidence. Real WebGL2 was observed, not a physical-GPU/device certification. |
| Generated PDF components           | **6 passed**: snapshot, position, short ground track, comparison, maximum track and saved report; every expected source/warning/section/page counter checked, including all **361** maximum-track rows.                                       |
| Complete browser/seven-PDF gate    | **NOT PASSED / PARTIAL**. Offline seventh PDF, full E2/E6/E7 harness and pinned Firefox/WebKit coverage remain unverified in this task.                                                                                                       |

Commands and receipts are recorded in the ledger. Main executed commands included:

```text
/workspace/OrbitIQ/.venv/bin/python -m pytest -q --junitxml=/tmp/orbitiq-v1-closure/backend-final/backend-tests.xml
npm test -- --maxWorkers=2 --reporter=default --reporter=junit --outputFile.junit=/tmp/orbitiq-v1-closure/frontend/tests.xml
npm run lint
npm run format:check
npm run build
/workspace/OrbitIQ/.venv/bin/ruff check .
/workspace/OrbitIQ/.venv/bin/ruff format --check .
python3 scripts/verify_fresh_checkout.py --output /tmp/orbitiq-v1-closure/fresh-checkout
python scripts/verify_report_pdf.py --directory /tmp/orbitiq-v1-closure/native-browser/host-results/chromium-report/reports --output /tmp/orbitiq-v1-closure/native-browser/host-results/pdf-six-results-after.json
```

The installation command ran from a hash-verified **425-file disposable starting
working-tree snapshot**, tree `9582a30c70042bc0736bb9321e4e604eeda0601a`, with its
own temporary index and no commit. This was necessary because the existing
installation verifier intentionally exports the index, which would omit the real
worktree's unpublished files. The original index was untouched. Later inquiry/
closure documents and the PDF-verifier-only fix are outside that installation
snapshot; runtime application and dependency hashes still match current source.
The final integrated backend separately includes the verifier fix and new tests.

Existing warnings remain visible: the **558.60 kB** globe chunk, Starlette/httpx
deprecation, an intentional duplicate ZIP-member test warning, and fresh-install
`whatwg-encoding` deprecation. No dependency updates or warning suppression were used.

## Browser limitations and evidence boundaries

The native runtime was **Chromium 154.0.8037.57 / Playwright 1.62.0**, not the pinned
three-engine browser image. Current API image build succeeded. Gateway tests used
the exact pinned web final stage assembled with the tested current frontend
artifact and unchanged gateway configurations; this was not a complete multistage
web-image build or a remotely sealed release.

The first browser attempt could reach the internal gateway but not its published
loopback port. A task-only raw TCP bridge then preserved the actual gateway's
responses, CSP and assertions for the passing subset. The full run was stopped
when Docker VFS filled root storage. A native history helper also encountered a
container-only axe library path; that environment failure is not recorded as a
passing history run or an application defect. No unrelated images/data were pruned.

A smaller host-loopback API/Vite-preview run generated the six PDFs. Its standalone
offline HTML navigation failed with **ERR_BLOCKED_BY_ADMINISTRATOR** under system
Chromium policy, so the seventh PDF was not generated. No policy bypass, skipped
offline assertion or seven-file success claim was introduced. The six PDFs were
checked after fixing the verifier; they are component results, not complete browser
release acceptance. Preview checks do not establish production gateway behavior.

All task-owned services, containers, networks and synthetic volumes were cleaned;
test ports were verified free. The two task-created image tags were removed after
their IDs were recorded. Existing Docker cache/images were preserved. Storage
remains constrained; use an adequately resourced permitted runtime for the full
browser gate. All 14 host fixture files retained their hashes. No original research
or operator archive was mounted into these tests.

## Remaining requirements and October 31 decision

| Requirement                             | What remains                                                                                                                                                                                                                                                                                                       |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Local browser/offline export acceptance | Complete the unchanged full browser and seventh offline-PDF checks in a permitted runtime with sufficient storage and the required engines. No new domain is needed for this.                                                                                                                                      |
| Human product acceptance                | Agree the local V1 feature scope and review critical journeys, keyboard/screen-reader behavior and physical devices. Automated viewports/WebGL/axe do not prove those human checks.                                                                                                                                |
| E4 hosting/HTTPS/persistence            | An authorized target, URL/identity, durable storage and certificate ownership; actual remote TLS and replacement/restart preservation tests. No approved target was available to this task.                                                                                                                        |
| E4 independent backup                   | Approved off-machine destination/recovery host, least-privilege access, key recovery/retention policy, actual retrieval and separate restoration proof. No private upload was authorized or performed.                                                                                                             |
| E4 monitoring                           | Approved host/schedule/receiver/recipient and demonstrated failure/recovery delivery with human receipt. Local monitor/error tests do not establish actual alert delivery.                                                                                                                                         |
| Current CI / required checks            | Exact-candidate CI and enforcement evidence remain unverified; no publication occurred. E7's last recorded public repository, unprotected main, empty rulesets and protection-read 403 are historical findings, not freshly checked settings. Existing bounded artifact retention evidence is likewise historical. |

The shortest defensible path is to finish the remaining browser/offline-file
acceptance in an allowed runtime, fix only demonstrated defects, complete owner
acceptance of an agreed **local V1** scope, then freeze the reviewed candidate for
an evidence-based decision by **31 October 2026, Asia/Calcutta**. Public production
and a scientifically qualified historical comparison are separate decisions.
The date and passing automation cannot replace infrastructure evidence or an IGS
technical answer. An IGS delay need not halt the existing explorer/history/report
engineering, but no unqualified accuracy or comparison claim may be added.

Existing UI/report contracts say calculated data are not observations, uncertainty
is unquantified and scientific certification is not implied. The tests retain those
limitations. ERP epoch scale, zero/extension meanings, subdaily treatment, TIO,
complete frame/physical-point compatibility, quality/provenance claims and final
comparison authorization remain unresolved as applicable. Unused fields and unknown
independence are not automatically universal blockers for a bounded unweighted
claim, but no such claim or waiver was authorized here.

## Preservation and milestones

Five files belong to this task: inquiry status JSON; PDF verifier; its new tests;
this report; release evidence JSON. Only the PDF verifier modifies an existing file.
All earlier user changes and historical reports remain preserved. Documentation,
JSON/source consistency, links, privacy, whitespace and complete diff checks passed.

Before/after checks preserve all four worktree branches/HEADs, **230 entries** in
prior private manifests, **72 original private files**, the older **178-file**
research inventory, actual XML/SP3/ERP original and expanded hashes, protocols,
retrospective policy and activation record. The real database remains schema **3**,
**two snapshots**, SHA-256
`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
The separate restored fixture contains one synthetic snapshot, not the real archive.
Compact test evidence and six synthetic PDF/JSON captures are preserved privately
under `data/v1-release-closure-local/`; local preservation is not independent backup.

| Milestone                                     | Current result                                              |
| --------------------------------------------- | ----------------------------------------------------------- |
| Local integration/build/installation/recovery | PASS within recorded scopes; browser/PDF acceptance PARTIAL |
| Published current changes                     | NO                                                          |
| Remote CI for current candidate               | NOT VERIFIED                                                |
| Production deployed                           | NO                                                          |
| Production infrastructure verified            | NO — E4 OPEN                                                |
| NASA/IGS scientific comparison                | BLOCKED — NO-GO                                             |

The acceptance journeys used only explicitly synthetic/public-reference fixtures.
**No genuine G05/G30/ERP research propagation, state transformation, interpolation,
residual or uncertainty calculation occurred.** No EOP/protocol/admission policy,
research data, original database content or scientific status was changed.

## Final closure continuation — 25 October 2026

This assessment continues the preceding closure; it does not restart its audits.
The ledger's `final_acceptance_assessment` preserves the preceding evidence identity
and records the current decisions. **No application, verifier, test, dependency,
protocol or scientific-policy source changed in this continuation.** Exact backend/
scripts and 87 frontend hashes still match the tested state, and the six PDF bytes
still match their successful receipts. The 1,582/427 passes, build and installation/
restart/recovery results are reused, not described as fresh reruns.

### Exact outstanding browser checks

The seventh artifact is **`chromium-position-offline.pdf`**. In
`scripts/verify_report_browser.py`, stage `standalone HTML`, the browser opens the
downloaded `chromium-position.html` with `file://`. It must display the report,
contain seven sections, preserve a white print background and repeating table
headers, make only file requests, capture the offline JSON/PDF and produce no
page/CSP errors. Prior navigation failed with **ERR_BLOCKED_BY_ADMINISTRATOR**
before that capture. No new permitted runtime or evidence that policy changed was
supplied. The blocked navigation was not retried, replaced by HTTP navigation,
bypassed or marked passed. **No additional browser/PDF check completed here.**

Current root storage is approximately **474 MB free**, compared with the recorded
**2.54 GB** pinned browser image alone, before API/web/runtime copies and outputs.
`/tmp` has about 16 GB free but is not the existing Docker storage location; moving
the shared daemon/cache was not attempted. Playwright 1.62.0 is installed, but its
default managed-browser cache is absent. Existing native Chromium does not close
the pinned three-engine requirement. No research, database, old images or shared
cache was removed to create space.

Still missing: the complete historical/window browser run, configured nonempty
synthetic observation journeys, full E2 accessibility/layout/performance and
E6 portable-recovery/E7 coverage, plus complete pinned Chromium/Firefox/WebKit
release execution. The earlier helper axe-path failure and interrupted harness
remain incomplete runs. Earlier historical CI passes are not fresh passes here.

**Smallest required action:** an authorized runtime that permits the unchanged
synthetic offline-file workflow, with sufficient Docker storage for the browser,
API/web and output layers. Run the existing outstanding suite there with its
assertions intact. No public domain is required for this local verification.

### Recovery and operational review

Retained evidence establishes reproducible locked installation, safe explicit
initialization, missing-storage refusal, frontend/API communication, synthetic
provider failure/restart recovery, and a consistent local fixture backup restored
to a separate target. It establishes neither protection of the real archive off
machine nor recovery from an independently stored copy.

The current supported environment reports no configured hosting capabilities,
outbound identities or secret bindings; database-variable readiness is unknown.
This is not proof that resources do not exist in outside accounts. No approved
external backup destination or recovery host was available to use, so no external
transfer was attempted. Required completion evidence remains:

- **Hosting/HTTPS/persistence:** owner-approved target/URL/access, durable volume,
  certificate ownership and actual TLS/replacement/restart preservation checks.
- **Independent recovery:** approved destination and recovery host, privately
  configured least-privilege identity/key recovery, retention/RPO/RTO, then actual
  retrieval and restoration to a new target with schema/payload/audit/API proof.
- **Monitoring:** approved runtime/schedule/receiver/recipient and demonstrated
  failure/recovery delivery plus human receipt. Configured commands and local
  monitor tests do not establish operational delivery.
- **Release controls:** remaining browser checks, current exact-source remote
  checks and authorized branch-rule readback/enforcement evidence. E7's settings
  observations remain historical. Current remote artifact retention/upload has not
  been verified. No settings, credentials, DNS or accounts were changed.

E4 remains **OPEN**. Neither local test success nor existing configuration closes
an external production requirement. No deployment or service purchase occurred.

### Owner acceptance and three separate decisions

The new [owner checklist](v1-user-acceptance-checklist.md) covers startup, main
journeys, investigation/history, exports, errors/recovery, scientific limitations,
accessibility, deployment scope and data handling. Status is
**PENDING_USER_ACCEPTANCE**. No explicit owner confirmation has been received;
agent review and automation are not human acceptance.

| Decision                     | Current assessment | Evidence and remaining condition                                                                                                                                                                                                                                     |
| ---------------------------- | ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Local engineering completion | **CONDITIONAL GO** | Integrated 1,582/427 passes, build, locked installation/restart/separate fixture recovery and six PDFs support a local candidate. Finish the browser/offline-PDF gate and obtain explicit owner acceptance of its scope. This is not unconditional release approval. |
| Scientific validation        | **NO-GO**          | IGS inquiry remains SENT_USER_REPORTED, reply pending; essential time/EOP/frame, applicable physical-point/quality/provenance and protocol authorization requirements remain unresolved. No genuine comparison is authorized.                                        |
| Production readiness         | **NO-GO**          | E4 OPEN: authorized hosting/HTTPS/durability, independent recovery, real alert delivery and release-control enforcement are unverified. No production deployment occurred.                                                                                           |

The shortest defensible October 31 path is to provide the permitted browser
runtime, finish only outstanding checks, complete explicit owner acceptance, and
freeze the reviewed evidence for the local V1 decision. If those conditions stay
open, retain CONDITIONAL GO rather than claim completion. Public production and
scientific validation stay separate; no deadline waiver or requirement relaxation.

Only this report, its JSON evidence and the new checklist changed in this
continuation. Targeted documentation, link, source/evidence consistency, whitespace
and preservation checks passed. No broad tests were rerun without a relevant code
change. Original scientific inputs and expanded hashes, database/schema/snapshots,
protocols, policies, activation record and all other user files were preserved;
no genuine scientific calculation, publication or deployment occurred.

## Browser verification and owner preparation continuation

Assessment **25 October 2026, Asia/Calcutta**. Earlier sections and their outcomes
are retained as historical receipts; this section records the latest preparation.
No new browser pass or completed owner review is claimed.

The current environment was inspected again: root/Docker storage still has only
about **474 MB free**, with about 16 GB separately available in `/tmp`. Playwright
**1.62.0** and system Chromium are installed, the default managed-browser cache
is absent, and no native Firefox/Firefox-ESR executable was found. No approved
external runtime was supplied through the supported context. The existing pinned
Docker browser runtime still cannot fit its writable runtime copy here. No large
download, rebuild, managed-policy change or shared-cache pruning was attempted.

Per-engine outcome in this continuation:

| Engine   | New outcome                                      | Retained / outstanding scope                                                                                                                                                                                                                                                            |
| -------- | ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Chromium | **BLOCKED for the outstanding gate; no new run** | Prior critical/error cases and six PDF passes retained. `chromium-position-offline.pdf` still requires authorized `file://` HTML navigation. The previous administrator restriction was not bypassed or retried under unchanged prerequisites. Full release harness remains incomplete. |
| Firefox  | **NOT EXECUTED**                                 | No usable native/cache runtime discovered; full pinned runtime blocked by Docker capacity. All required browser journeys remain unverified in this task.                                                                                                                                |
| WebKit   | **NOT EXECUTED**                                 | No managed runtime cache; full pinned runtime blocked by Docker capacity. All required browser journeys remain unverified in this task.                                                                                                                                                 |

No new reproducible browser product defect was found, so neither browser
assertions nor production code were changed. The smallest external prerequisite
remains an authorized offline-file-capable runtime with the required engines and
enough storage for the pinned browser plus API/web/runtime/output layers. The
remaining exact scenarios are listed in the preceding continuation and ledger.

### Prepared owner archive and launch workflow

The existing fixture seeder assumed container UID 10001 and fixed container
paths. Added an explicit **`--local-owner`** mode and **`--directory`** option so
the same synthetic setup can run under the current local user without privileged
ownership changes. The local CLI selects only the bundled reference-derived
synthetic fixture. It retains the existing absolute/empty/non-symlink target
guards and read-only database. Default no-argument container paths, receipt and
UID behavior are unchanged. This is acceptance tooling, not a new application
or scientific feature.

Prepared archive: `/tmp/orbitiq-v1-owner/acceptance/archive.sqlite3`, receipt
`/tmp/orbitiq-v1-owner/acceptance-receipt.json`. It contains exactly two explicitly
synthetic catalog-6251 snapshots, IDs 1 and 2. A fresh loopback API process passed
health/readiness and listing checks, confirmed those synthetic names, and stopped;
the database SHA-256 stayed unchanged. An initial smoke-driver lookup used the
wrong `name` key; the driver was corrected to the documented `object_name` key
and rerun successfully. No application defect or code change was involved.

**Four targeted synthetic setup tests passed in 0.90 s**, covering real local
fixture creation/no chown, integrity/read-only state, non-overwrite, default
container owner/receipt/CLI compatibility and path refusal. Targeted Ruff lint and
formatting passed. Current application and frontend modules/dependencies remain
unchanged: prior 1,582 backend/427 frontend passes are retained at their recorded
scope. They are not described as a new full run covering the new CLI/test file.
No broad suites, browser flows or six-PDF checks were repeated.

The [owner checklist](v1-user-acceptance-checklist.md#safe-local-launch) now supplies
the complete fresh-directory seed, explicit synthetic DB selection, loopback API/
frontend launch, workspace dependency paths, source confirmation, main journeys,
report exports and safe stop/restart/retry instructions. It does not silently
initialize or replace the real archive. No service is left running. Temporary
workspace fixture paths are not backups or a portable installation.

All six owner items remain unchecked and status remains
**PENDING_USER_ACCEPTANCE**. The owner must record browser/OS/device/date/outcomes;
agent preparation, API smoke checks and automated tests do not constitute that
review. Public production and genuine scientific validation remain separate.

Local engineering remains **CONDITIONAL GO**, scientific validation **NO-GO**,
production readiness **NO-GO**. IGS reply and operational E4 requirements remain
pending. Complete the outstanding browser checks in a permitted runtime and the
owner's hands-on review before the October 31 local V1 decision. No deadline waiver,
real research calculation, prototype activation, data transfer, publication or
deployment occurred. The original research inputs, hashes, database, protocols,
policies and historical scientific reports are preserved.

## Owner acceptance addendum — 25 October 2026

The owner explicitly confirmed in this conversation:

> Yes, I am satisfied with this version of OrbitIQ for its intended local use.

Recorded status: **ACCEPTED_FOR_INTENDED_LOCAL_USE**. Acceptance date:
**2026-10-25, Asia/Calcutta**. No precise acceptance time was supplied or inferred.
The exact scope is **the current OrbitIQ version for its intended local use**.
This statement establishes scope acceptance, not individual technical outcomes,
browser/OS/device observations, or a formal acceptance of remaining engineering
limitations. All six [technical checklist items](v1-user-acceptance-checklist.md#six-item-owner-review)
remain unchecked. No new technical test or human journey result is claimed.

This addendum supersedes previous **PENDING_USER_ACCEPTANCE** statements for the
current status only. The earlier pending entries and test receipts are preserved
as historical evidence. The ledger updates its current owner assessment and
records the preceding values and evidence-file identity in
`owner_acceptance_addendum`. Earlier `browser_owner_preparation` receipts retain
their original pending status at the time of preparation.

| Decision                     | Status after owner confirmation                                                                                           |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Owner acceptance             | **ACCEPTED_FOR_INTENDED_LOCAL_USE** — current version for intended local use only.                                        |
| Local engineering completion | **CONDITIONAL GO**, unchanged. Outstanding technical gates have neither passed nor been formally accepted as limitations. |
| Scientific validation        | **NO-GO**; scientific study **BLOCKED — NO-GO**, with IGS frame/EOP clarification pending.                                |
| Production readiness         | **NO-GO**; E4 remains **OPEN**.                                                                                           |

The seventh offline PDF, `chromium-position-offline.pdf`, remains blocked by the
recorded **ERR_BLOCKED_BY_ADMINISTRATOR** restriction. Full
Chromium/Firefox/WebKit coverage remains incomplete. Public hosting, HTTPS,
off-machine backup/recovery, actual alert delivery and release-control enforcement
remain unverified. Scope acceptance resolves none of those technical requirements.
Essential ERP epoch-scale, zero-field, subdaily/TIO and frame compatibility, plus
applicable physical-point, quality/uncertainty, provenance/independence and protocol
authorization requirements, remain unresolved. No scientific comparison is enabled.

Only the checklist, this report and its JSON ledger changed for this addendum.
Targeted formatting, JSON structure/evidence consistency, local links, whitespace,
source-hash and preservation checks passed. No broad application suites, browser
checks or PDF flows were rerun for this documentation-only change. Original
research inputs and hashes, database contents, protocols, retrospective-admission
policy, activation and prior evidence remain unchanged. No propagation, real-state
transformation, interpolation or residual calculation occurred. No publication or
deployment occurred.

## Final browser gate attempt — 25 October 2026

**Result: PARTIAL; the browser gate is not closed.** Owner acceptance remains
**ACCEPTED_FOR_INTENDED_LOCAL_USE**, dated **2026-10-25**, without an invented time.
Local engineering remains **CONDITIONAL GO**. Scientific validation and production
readiness remain **NO-GO**; IGS frame/EOP clarification remains pending. Prior
sections and receipts remain historical; the new ledger block
`final_browser_gate_attempt` records this attempt separately.

### Runtime and exact offline restriction

Fresh measurements found **496,369,664 bytes** available on the root/Docker
filesystem and **17,130,287,104 bytes** on `/tmp`; Docker still uses VFS. No approved
external runtime was supplied through the supported environment context. The
existing pinned browser image is approximately **2.54 GB**; no large image was
pulled or started. A cached API/web attempt with read-only current-source mounts
exhausted root capacity before service readiness. Advertised image sizes did not
adequately account for VFS copies. That attempt executed no browser scenarios;
only task-owned containers/network were removed and free space recovered to
**496,340,992 bytes**. No shared-cache pruning or daemon change occurred. An earlier
task-driver import failure was corrected to use the existing application venv and
explicit backend path; no application defect was established.

The managed file `/etc/chromium/policies/managed/urls.json` explicitly has
`URLBlocklist: ["*"]` and an allowlist for HTTP, HTTPS, WSS and selected `chrome:`
pages, with **no `file:` allowance**. Its hash is in the ledger. This corroborates
the prior **ERR_BLOCKED_BY_ADMINISTRATOR** failure. The seventh
**`chromium-position-offline.pdf` remains BLOCKED**. No repeated offline navigation,
new offline PDF, policy modification or alternate-browser policy evasion occurred;
the original content/source/timestamp/limitation/page-break assertions are intact.

Playwright **1.62.0** successfully downloaded its Debian-13 Firefox **153.0/build
1538**, WebKit **26.5/build 2336** and FFmpeg packages into task-owned `/tmp`, using
the existing proxy and CA verification. This does not install system dependencies
or establish runnable browsers. Firefox startup did not complete: it reported
`Sandbox: writing /proc/self/uid_map: EROFS`, a software-framebuffer error and
unwritable Fontconfig caches. The task-owned stalled launch was terminated after
about 43 seconds; these logs do not establish a single root cause. Sandboxing was
not disabled. WebKit launch validation reported six missing libraries:
`libgtk-4.so.1`, `libgraphene-1.0.so.0`, `libharfbuzz-icu.so.0`,
`libmanette-0.2.so.0`, `libhyphen.so.0`, `libGLESv2.so.2`. Validation was not skipped.
Neither engine reached application tests or provided an observed running version.

### Newly executed Chromium checks

The available **system Chromium 154.0.8037.57** ran existing HTTP-based scripts
against the current backend and hash-matched tested production assets through
**loopback Vite preview**. These are UI/component integration results; preview does
not establish production nginx CSP, rate limiting, sealed release images, offline
report behavior or complete three-engine coverage. All four commands exited **0**:

| Existing script                                | Newly verified scope                                                                                                                                                                                                                         |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `verify_history_browser.py`                    | **8** history cases and **7** E7 window/retry/captured-export cases passed.                                                                                                                                                                  |
| `verify_engineering_e2.py`                     | **23** blocking checks passed; **6** automated accessibility views and **4** viewport layouts; zero recorded issues. Real WebGL2 used SwiftShader, not a physical-device certification.                                                      |
| `verify_engineering_e6.py`                     | **13** cases passed, including **4** native export/restore round trips, collision handling, offline JSON import and explicit persistence/transport fault injections. Offline JSON import is separate from blocked `file:` report navigation. |
| `verify_observation_browser.py --mode fixture` | **4** configured synthetic-observation cases passed; **0** scientific observations used and no independence claim established.                                                                                                               |

The retained task adapter only selects system Chromium and rebinds container-only
result/axe-library paths, including the imported history helper. Existing script,
assertion and application sources remain unchanged. Test outputs and exact
commands/versions are recorded under `/tmp/orbitiq-v1-browser-gate` and fingerprinted
in the ledger. The new checks use only the explicitly synthetic catalog-6251
fixtures; genuine G05/G30/Swarm or IGS research inputs were not used. No product
assertion failed and no product defect or regression fix was introduced.

| Engine   | Passed in this attempt                            | Blocked / unexecuted                                                                                                                                                                                                                       |
| -------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Chromium | Four HTTP UI scripts above, within preview scope. | Seventh offline PDF blocked by managed policy; full pinned release harness and these journeys through the production gateway remain unexecuted. Previously passed critical/failure/empty-observation/six-PDF evidence retained, not rerun. |
| Firefox  | No application scenarios.                         | Startup did not complete; all application journeys unexecuted.                                                                                                                                                                             |
| WebKit   | No application scenarios.                         | Six missing runtime libraries; all application journeys unexecuted.                                                                                                                                                                        |

All **14** fixture-file hashes remained unchanged. API/preview processes were
terminated. Initial simple bind checks saw TIME_WAIT; follow-up reuse-address
binds succeeded, TCP connections were refused and no listener remained on 8080 or 18001. Owned Docker containers/network were removed. Downloaded test packages and
synthetic receipts remain task-local; no research data was uploaded.

### Remaining gate and preservation

The smallest complete solution remains an **authorized offline-file-capable
runtime**, with all Playwright dependencies, functioning browser sandboxing,
writable caches and enough storage for runtime copies if using Docker VFS. Run
the unchanged release harness with E2 coverage against the exact reviewed source,
all three engines, both synthetic archive modes and all seven PDF checks. No
assertion waiver or local-engineering status upgrade is justified by this attempt.

Only this report and its JSON ledger changed. Targeted formatting, JSON/evidence,
link, whitespace, scoped-diff and preservation checks passed; broad backend and
frontend suites and earlier six-PDF checks were not repeated. The existing owner
checklist, all six unchecked technical items, previous evidence blocks, original
research inputs/hashes, database contents, protocols, retrospective-admission
policy and activation remain unchanged. No real-input propagation, spacecraft
transformation, orbital interpolation, residual or uncertainty calculation occurred.
Scientific comparison stays **BLOCKED — NO-GO**. Public hosting/HTTPS, off-machine
backup/recovery, actual alert delivery and release-control enforcement remain
unverified; E4 remains **OPEN**. No publication or deployment occurred.

## Browser runtime resolution and retained CI verification — 25 October 2026

**New finding:** the existing authorized GitHub Actions workflow has retained,
verifiable **three-engine and seven-PDF evidence** for baseline commit
`b0a03205e3930b55651232d8b7ffbc9e879ae8c6`. This supplies previously uninspected
baseline evidence for the unchanged application. It is **not a new browser run
or verification of the complete unpublished working tree**. Current local runtime
blockers remain. Local engineering retains **CONDITIONAL GO** pending current
helper integration; owner acceptance retains **ACCEPTED_FOR_INTENDED_LOCAL_USE**,
dated **2026-10-25**, with all six technical checkboxes unchanged.

### Existing authorized runner and artifact verification

Read-only GitHub queries found the existing `.github/workflows/ci.yml` active.
[Run 40067874081](https://github.com/BibinBinoy777/OrbitIQ/actions/runs/40067874081)
completed successfully for the exact baseline SHA: **backend**, **frontend** and
**release-images** jobs all succeeded on GitHub-hosted Ubuntu runners. This proves
that the existing route operated for that baseline; it does not prove present
capacity or current-source verification. Self-hosted runner inventory returned
**403: Resource not accessible by integration**, so no claim of absent runners is
made. The local branch lookup returned **404: Branch not found**. No new workflow
was dispatched: the existing workflow checks out a Git ref and has no input for a
local source archive. Repeating its baseline would not exercise local helper edits.

Downloaded only existing synthetic/public **release-evidence**, **frontend-dist**
and **browser-pdf-regressions** artifacts into task-local `/tmp`. Each ZIP's SHA-256
matched its GitHub API digest. The existing `verify_release_evidence.py verify-files`
command passed the compact sealed record; all **69** sealed evidence entries were
checked and **68** browser counterparts matched the raw browser archive. Integrity
verification is not deployment approval. No private research input was uploaded.

The sealed source capture covers **380** tracked files. Current **57 backend
application files**, **87 frontend files**, **10 deployment files**, dependency
locks, Dockerfile, browser scripts and assertions match the captured baseline.
No extra untracked application/fixture path exists. The current tested frontend
artifact's **13** files also match the retained CI frontend byte-for-byte.
Exactly two tracked helper files differ: `scripts/seed_browser_fixtures.py` and
`scripts/verify_report_pdf.py`. Additional local research tooling/tests/docs were
not present in that CI checkout and are not claimed remotely verified.

A focused AST check established that the seeder's default function is identical
after reducing the added `local_owner=False` guard; the original **six** PDF main
assertions are unchanged. The prior four seed tests and 15 PDF-verifier regressions
remain historical results, not reruns. This analysis supports evidence reuse but
does not claim a fresh end-to-end run of the modified helpers.

### Seventh PDF and per-engine results

The current `verify_report_pdf.py` was executed against the retained CI PDFs:
**all seven passed**, including **`chromium-position-offline.pdf`** and **361**
maximum-track rows. Source identifiers/hashes, timestamps, warnings, limitations,
page counters and existing content assertions passed. The offline PDF is **8
pages**, **44,895 bytes**, SHA-256
`ea78049255612089a105bd100315a55d299118169976b82fed378f2850197929`.
It was generated by authorized CI using **Chromium 151.0.7922.34**, not newly
generated here. Its local `file:` generation remains blocked by unchanged managed
policy. The fresh check revalidated artifact bytes; it did not bypass that policy.

| Engine                     | Verified retained CI results at the exact baseline                                                  | Current execution scope                                                                                            |
| -------------------------- | --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Chromium **151.0.7922.34** | **27** release flows; E2 enabled, **13** E6 and **7** E7 cases; offline HTML and seven PDFs passed. | System **154.0.8037.57** prior HTTP-preview passes retained. No new browser run; local offline generation blocked. |
| Firefox **153.0**          | **25** release flows; E2 enabled, **13** E6 and **7** E7 cases; offline HTML passed.                | Prior local sandbox/framebuffer startup failure retained; current application scenarios not executed.              |
| WebKit **26.5**            | **25** release flows; E2 enabled, **13** E6 and **7** E7 cases; offline HTML passed.                | Six required host libraries still unavailable; current application scenarios not executed.                         |

Thus **77 baseline release flows** and the separate E2/E6/E7 checks have direct
retained evidence; no baseline application suite failed. Native PDF generation
is Chromium-only by existing design. The original CI harness command was
`python3 scripts/run_browser_regressions.py --release ci --engineering-e2 --output
"${RUNNER_TEMP}/orbitiq-release/browser"`; its receipt records **233.172 seconds**.
Exact fresh artifact-check commands, versions, hashes and per-engine receipts are
in `browser_runtime_resolution` in the existing JSON ledger. These results
supersede any implication that baseline three-engine/offline evidence was absent;
they do not supersede the blocked local-runtime or unverified-current-candidate scope.

### Runtime requirements and capacity

Fresh inspection found **496,308,224 bytes** free on root/Docker and
**16,497,442,816 bytes** free on `/tmp`. Managed Chromium's policy SHA-256 is
unchanged and still excludes `file:`. Existing downloaded Firefox, WebKit and
FFmpeg occupy **603,907,593 apparent bytes**. The six missing WebKit libraries
were independently checked and remain unavailable. No browser launch or completed
UI/backend/frontend suite was repeated, no software installed, no Docker attempt
made, and no sandbox/security/policy change attempted in this continuation.

Use the existing CI route or an administrator-provided compatible test host;
no duplicate workflow is needed. The exact current helpers must be supplied to
and tested in an approved execution context before its complete-harness status
can advance. A local host also needs explicitly permitted synthetic offline-file
navigation, functional browser sandboxing, writable caches and the six previously
listed shared libraries. Recommendations and settings are not operational proof.

Measured virtual image payloads total approximately **2.9 GB**; prior API/web
copies alone exhausted approximately **496 MB** despite advertising approximately
359 MB. Retained browser diagnostics are **132.8 MB** compressed / **140.1 MB**
expanded; host UI outputs occupy **25.5 MB**. Budget **8 GiB free** for a prebuilt
VFS test run, conservatively allowing two payload/copy equivalents, at least
1 GB temporary/artifact space and margin; use **16 GiB free** as a clean-build
planning target for additional base/build/npm layers. These are estimates, not
measured peak requirements or guaranteed minima. Missing-library installation
footprint remains unmeasured. Confirm the actual runner/driver/dependencies and
free space before execution; no storage was provisioned here.

### Current decision and preservation

Local engineering remains **CONDITIONAL GO**: unchanged-application baseline
browser evidence is now verified, while full updated-helper/current-worktree
end-to-end execution remains unverified. No product defect was demonstrated and
no product code or tests were changed. Scientific validation and production
readiness remain **NO-GO**; IGS frame/EOP clarification is pending and E4 remains
**OPEN**. Hosting/HTTPS, off-machine recovery, actual alerts and release-control
enforcement remain unverified.

Only this report and its JSON ledger changed. Formatting, JSON/evidence structure,
source/receipt consistency, local links, whitespace, scoped diff and preservation
checks passed. All prior evidence blocks, owner checklist, research inputs/hashes,
database contents, protocols, retrospective-admission policy and activation remain
unchanged. No real-input propagation, spacecraft transformation, orbital
interpolation, residual or uncertainty calculation, external private-data transfer,
publication or deployment occurred.

## Final helper integration decision — 25 October 2026

**Local engineering: GO_FOR_INTENDED_LOCAL_USE**, for the verified implementation
at `8160bcb972c5c1486b2b138008b0cd4d5bd633c4`. The former current-helper/browser
condition is resolved by actual exact-source CI, not by waiving a blocked test.
The owner accepted this intended-local-use scope on **2026-10-25**; no precise
acceptance time or individual checklist observations were supplied. Scientific
validation and production readiness remain **NO-GO**. This is a bounded local
engineering decision, not a public-launch or scientific-accuracy claim.

### Source and evidence chronology

The prompt refers to the earlier `b0a0320` baseline and its two changed helpers.
Subsequent authorized publication already placed those exact changes at **8160bcb**.
[CI run 40218611266](https://github.com/BibinBinoy777/OrbitIQ/actions/runs/40218611266)
passed **backend**, **frontend** and **release-images** for that full SHA.
Both current helpers and their two regression-test files were compared byte for
byte with that published source and match. Source-bound retained receipts cover
**431** committed files, **69** sealed evidence entries and verified artifact
archive digests. Earlier baseline-only/unexecuted entries remain historical;
`final_helper_verification` is the current ledger assessment.

That exact-source CI passed **1,586 backend tests**, **427 frontend tests**,
**77 release flows** (Chromium **27**, Firefox **25**, WebKit **25**), E2/E6/E7,
and **all seven PDFs**, including the offline PDF and **361** maximum-track rows.
Versions were Chromium **151.0.7922.34**, Firefox **153.0**, WebKit **26.5**.
These are actual results from the prior authorized publication run, not new broad
runs in this task and not an assertion that baseline CI tested later changes.
No new runner or unpublished-source transfer is now needed for this closed gate.

### Fixture seeder review and current tests

Relative to `b0a0320`, the seeder adds **`--directory`** and **`--local-owner`**.
The local-owner CLI always uses the bundled public-reference-derived synthetic
fixture, writes only the explicitly supplied fresh directory, retains current-user
ownership and adds a synthetic marker, exact DB path and SHA-256 receipt. No
research-file override is offered. Default `/fixtures`, `/reference.json`, receipt
and container UID 10001 behavior are preserved.

The local target must be absolute, nonsymlink and empty. A repeated invocation on
its seeded target deliberately **refuses without altering any existing bytes**;
it is safe refusal, not permission to overwrite or silently reinitialize. The
created archive is read-only, contains two explicitly synthetic catalog-6251
snapshots and passes SQLite integrity checks. The real DB path is not taken from
environment/default storage. Tests use disposable directories only.

**Four current-source seeder tests passed**, covering creation, read-only/integrity,
non-overwrite, absolute/symlink refusal and default container CLI/owner contract.

### PDF verifier review and current tests

The only behavior change adds validated raw-page reading order before the original
content assertions. It removes the exact recognized header/footer only at validated
page boundaries, allowing complete sentences split across pages to match. It
rejects wrong/missing raw page boundaries and missing, misplaced or misnumbered
running furniture; interior lookalike text stays body content.

All **six original main assertion expressions** remain unchanged. They still check
pagination/counters, captured identifiers, generation/source timestamps, source
hashes, validation, warnings/limitations, track coordinates and clocks, seven
sections, application exclusion and private-note exclusion. The release harness
still requires exactly seven passing PDFs and 361 maximum-track rows. Nothing is
silently skipped. **Fifteen current-source PDF regressions passed**, including
prefix/suffix/split furniture, genuine omitted warning text, malformed pages and
interior lookalikes. This demonstrates rejection of the tested incomplete-content
cases, not universal optical or physical-printer assurance. No new PDF was generated
or claimed in this task; the seven-PDF generation occurred in the authorized CI run.

Fresh targeted command:

```bash
/workspace/OrbitIQ/.venv/bin/python -m pytest -q \
  backend/tests/test_owner_acceptance_seed.py \
  backend/tests/test_report_pdf_verifier.py \
  --junitxml=/tmp/orbitiq-v1-helper-final/helper-tests.xml
```

**19 passed in 0.93 s**, zero failures/errors/skips. Targeted Ruff lint/format and
three-document Prettier checks passed. Existing broad suites/browser checks were
not repeated. No helper, application, dependency or test implementation changed.

### Separate decisions and remaining requirements

| Decision              | Current status                                                                                                                                                     |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Owner acceptance      | **ACCEPTED_FOR_INTENDED_LOCAL_USE**, dated 2026-10-25; exact scope unchanged.                                                                                      |
| Local engineering     | **GO_FOR_INTENDED_LOCAL_USE**, tied to the unchanged verified implementation and recorded automated/local-recovery scope. No helper integration condition remains. |
| Scientific validation | **NO-GO**; study **BLOCKED — NO-GO**, Phase 11.3.1 **PARTIAL** and IGS frame/EOP clarification pending.                                                            |
| Production readiness  | **NO-GO**; E4 remains **OPEN**.                                                                                                                                    |

The six individual owner-review items remain unchecked. No human-device,
screen-reader, printer or general accessibility certification is inferred. Local
managed `file:` restrictions and local Firefox/WebKit startup/dependency problems
remain unchanged; the required automated integration ran in authorized CI without
bypassing those local restrictions. Real hosting/HTTPS, off-machine recovery,
actual alert delivery and required-check enforcement remain open production work.
The main branch was observed unprotected with no rulesets; protection-detail access
returned 403. No controls were changed. Scientific time/EOP/frame, physical-point,
quality/provenance and protocol requirements remain separate unresolved gates.

Only this report, its JSON ledger and the checklist's current status paragraph
were updated; the latter avoids contradicting the verified decision. Owner scope,
date, confirmation and all six checkbox bodies remain unchanged. Prior evidence
and scientific reports are retained. This documentation-only addendum is **local
and unpublished**; its bytes were not part of the earlier CI run. The implementation
is byte-identical to verified **8160bcb**, and no fresh-CI claim is made for the
subsequent documentation. Formatting, JSON/evidence/source consistency, links,
whitespace, scoped diff and preservation checks passed.

Original G05/G30 XML, IGS SP3/ERP, their hashes, database contents, protocols,
retrospective-admission policy/activation and active EOP policy remain unchanged.
No real-research propagation, spacecraft transformation, interpolation, residual
or uncertainty calculation, policy change, publication, deployment, DNS or
infrastructure action occurred in this task. The targeted seeder tests exercised
only their existing explicitly synthetic fixture path, not the scientific study.

## Local V1 owner handoff preparation — 25 October 2026

**Handoff instructions are ready for owner execution; all six manual-review items
remain PENDING_OWNER_OBSERVATIONS.** This is preparation, not a completed owner
usability review. Existing owner acceptance remains **ACCEPTED_FOR_INTENDED_LOCAL_USE**
and local engineering **GO_FOR_INTENDED_LOCAL_USE**. Scientific validation and
production readiness retain **NO-GO**; no new feature phase has started.

The three current documents were reconciled. Their latest four decisions were
already consistent; no status correction or helper change was needed. The
[owner execution guide](v1-user-acceptance-checklist.md#owner-execution-guide) now
provides six matching procedures, each identifying state/prerequisites, numbered
actions, observable expected results, pass evidence and failure/block details.
The original six checkbox items and acceptance criteria, owner statement/date/scope
and unreported observation status remain unchanged.

The practical path uses only the existing explicitly synthetic catalog-6251
fixture and snapshot metadata/element views: launch/readiness, inspect an exact
source, save, close/restart at the same profile/origin/archive, reopen, inspect
history/provenance, export/import, then check keyboard access and readability.
No blocked real-data comparison is authorized. The guide makes explicit that:

- Browser saves belong to their exact profile/origin; changing host/port/profile,
  clearing site data or deleting temporary fixture storage is not a recovery path.
- A portable bundle restores saved inputs/title and optional notes; it does not
  contain the orbital archive or frozen results. Captured report JSON/HTML/PDF is
  a different format, excludes local title/notes and is not portable-import input.
- Formats should be compared from one captured report; actual download completion,
  page breaks, errors and limitations need human inspection on the intended computer.
- Offline policy blocks are recorded as **BLOCKED**. Recovery operations and
  screen-reader/device observations not performed are **NOT_RUN**. Instructions,
  earlier automation and scope acceptance are not evidence that they occurred.

A [blank defect record](v1-user-acceptance-checklist.md#reproducible-defect-record)
captures identity/context, numbered reproduction, expected/actual behavior, severity,
sanitized error/evidence, repeatability, a supported proposed fix and focused
regression. No actual defect report or owner observation was supplied, and source
inspection demonstrated no product defect requiring a fix. No speculative UI,
application, dependency, helper or test changes were made.

Action names and behavior were checked against current components, existing browser
scripts and the backup/recovery runbook. Documentation formatting, JSON/evidence
structure, links/anchors, source consistency, scoped diff, whitespace and preservation
checks passed. No broad backend/frontend/browser suite, helper regression, browser
startup or resource-intensive Docker attempt was repeated. The earlier 4/15 helper
passes and exact-implementation CI at **8160bcb** (1,586 backend, 427 frontend, 77
browser flows, seven PDFs) remain retained evidence, not newly executed tests.
No new screenshot, PDF or recovery receipt was generated in this handoff task.

The remaining manual items are startup/primary workflows, investigations/history,
report/export, errors/recovery, limits/accessibility and deployment/data expectations.
They require direct owner observations using the guide. The existing local runtime
restrictions, profile-local saves, source-dependent reconstruction and unquantified
scientific accuracy remain documented limitations. IGS frame/EOP clarification and
other essential scientific prerequisites remain pending; the study stays **BLOCKED**.
E4 remains **OPEN**, with HTTPS/hosting, durable storage, independent backup/recovery,
actual alerts and branch/required-check enforcement still outstanding.

Only these three V1 documentation files changed. Original research inputs/hashes,
database contents, comparison protocols, retrospective-admission policy/activation,
active EOP policy, earlier evidence and the clean published worktree are preserved.
This handoff update is **local and unpublished**. No real-data scientific operation,
private-data upload, publication, deployment, hosting, DNS or infrastructure change
occurred. The four decision gates remain separate and unchanged.

## Owner checklist acceptance — 26 October 2026

The owner confirmed: "i accept `user-acceptance-checklist.md`." This refers to the
existing [V1 owner checklist](v1-user-acceptance-checklist.md) and is recorded as
**ACCEPTED_FOR_INTENDED_LOCAL_USE**, dated **2026-10-26 (Asia/Calcutta)**, with no
precise acceptance time supplied. The original 2026-10-25 local-use acceptance and
all preceding preparation/verification evidence remain preserved.

The owner has accepted the checklist for the current version's intended local
scope. No item-specific observations or formal waiver were provided: all six
manual criteria remain unchecked and **PENDING_OWNER_OBSERVATIONS**. This addendum
supersedes the handoff's pending overall checklist acceptance only; its historical
preparation status and unreported technical observations remain accurate.

Local engineering stays **GO_FOR_INTENDED_LOCAL_USE** on the retained exact-source
CI/helper evidence. Scientific evaluation remains **BLOCKED — NO-GO**, Phase 11.3.1
**PARTIAL**, and IGS frame/EOP clarification **PENDING**. Production readiness stays
**NO-GO**, E4 **OPEN**. Hosting/HTTPS, independent backup/recovery, actual alerts and
release-control enforcement remain unverified. No new browser/device, accessibility,
PDF, recovery or application test result is inferred from the acceptance.

Only this closure report, its existing JSON ledger and the checklist were updated.
Focused documentation, JSON/evidence, link, whitespace and preservation checks
passed; broad application/browser/PDF suites were not repeated. Original research
inputs and hashes, database contents, scientific protocols, retrospective-admission
policy/activation, active EOP policy and prior reports remain unchanged. No real
scientific calculation, commit, push, deployment or infrastructure action occurred.
This acceptance addendum remains **local and unpublished**.

## Agent-executed local checklist verification — 26 October 2026

The owner requested that the assistant perform the checks. The available local
workflows were executed against the unchanged implementation corresponding to
**8160bcb972c5c1486b2b138008b0cd4d5bd633c4**. Only five existing documentation paths
differed from that published source before this task; application, dependency and
verification-script bytes were unchanged. Served production-dist files matched
the retained verified CI artifact byte-for-byte. This was native **Chromium
154.0.8037.57**, Playwright **1.62.0**, on the Linux cloud workspace, via loopback
Vite preview and the actual FastAPI service. It was not the release nginx gateway,
a new CI run, Firefox/WebKit rerun or the owner's physical device.

Only the existing explicitly synthetic catalog **6251**, snapshot IDs **1/2**,
read-only archive `/tmp/orbitiq-v1-owner/acceptance/archive.sqlite3` was configured.
The observation archive was not configured. Synthetic calculations made by the
existing browser workflows are software exercises, not acquired observations or
qualification of any genuine historical research input. No G05/G30/Swarm research
record, real ERP interpolation or scientific residual calculation was used.

Fresh execution results:

- Startup health/readiness returned HTTP 200, with exactly two labelled synthetic
  snapshots. Seven critical browser journeys passed against the actual API,
  including discovery, keyboard save/share/reopen, restored definitions, readiness,
  timeline/graphics and missing-source disclosure.
- Eight history journeys and seven E7 regression cases passed. Explicit transport/
  wrong-window fault cases remain labelled as injected; normal source/history
  requests used the actual API.
- The E2 suite passed **23 checks**, with **zero axe violations across six views**,
  keyboard skip/focus/dialog controls, visible globe rendering, resource lifecycle,
  retry behavior and no horizontal page overflow at **320/390/768/1440** pixels.
  Axe left color-contrast checks incomplete in three views; these are not passes.
  No screen reader, physical device or actual browser-zoom observation is claimed.
- Portable investigations passed **13 cases** and **four native download/import/
  re-export round trips**, including idempotency, collision/cancel, notes policy,
  exact-source refusal and explicitly injected storage/download failures.
- A fresh persistent browser profile saved a synthetic title, note and source
  definition. Browser and both services were closed/restarted at the same origin;
  stored records matched exactly and reopened. Actually stopping this owned API
  displayed the backend error; submitting a search exposed its explicit retry,
  which recovered after API restart without changing the saved records.
- Six newly generated PDFs passed the existing text/pagination verifier: snapshot,
  position, ground track, comparison, maximum track and saved card. All sections,
  source identity, warnings, page counters and **361 maximum-track rows** checked.
  JSON/HTML same-capture downloads and print-preview assertions preceding the
  offline stage completed. The full report-browser command **exited 1** at
  `file:` navigation with **ERR_BLOCKED_BY_ADMINISTRATOR**; the seventh offline PDF
  was not generated. No overall report-browser pass is claimed. The managed policy
  hash stayed `47e595d31fd4f9e4273dba00536d7d4b7c0e8c50aa4017bc6e5c33dd4193855a`.
- The documented recovery command passed against only the synthetic archive:
  SQLite backup, distinct restore, full schema/table digests and provenance checks,
  and four restored API responses (all 200). Source content remained unchanged;
  the command removed only its new restored target and retained its local backup.
  Reusing that recovery directory was correctly refused with exit 1, preserving
  both existing artifacts and source. This is local fixture recovery, not durable
  off-machine backup, a real-archive rehearsal or production recovery.

The first custom outage probe omitted submitting the search before expecting its
retry button; the actual view correctly remained idle. This test-driver error
also left the intentionally stopped API unavailable for the first report attempt;
its PDF verifier correctly found no PDFs. The temporary driver was corrected,
only affected restart/report checks were rerun, and original attempt receipts
were retained. No product assertion, application code or security policy was
changed. No demonstrated application defect required a fix.

Commands and logs, screenshots, downloads, PDF results, restart evidence and
synthetic recovery manifest are retained under
`/tmp/orbitiq-agent-local-review-20261026/`; their identities and command results
are in the existing JSON ledger's `agent_assisted_review_20261026` section. The
assistant visually inspected the report preview and first snapshot PDF page for
obvious clipping; that limited inspection is not full print/visual certification.
Temporary local receipts are not independent backups. All owned servers were
stopped and loopback ports released after checking.

The [checklist](v1-user-acceptance-checklist.md#agent-executed-local-checks--26-october-2026)
now maps the six areas to scoped agent results. The six original owner checkbox
criteria stay unchanged: no owner-device, screen-reader or understanding result is
invented. Owner acceptance remains **ACCEPTED_FOR_INTENDED_LOCAL_USE**; engineering
remains **GO_FOR_INTENDED_LOCAL_USE** based on scoped current and retained evidence.
Scientific study remains **BLOCKED — NO-GO**, Phase 11.3.1 **PARTIAL**, IGS reply
**PENDING**. Production remains **NO-GO**, E4 **OPEN**: hosting/HTTPS, durable storage,
independent recovery, actual alert delivery and release-control enforcement are
still unverified. Earlier exact-commit three-engine/seven-PDF CI remains historical
valid evidence for unchanged code; it does not convert this local offline block
or unperformed human checks into passes.

Only the three existing V1 documents were updated. Focused formatting, JSON/evidence,
links, source identities, whitespace and preservation checks passed. No broad
backend/frontend suite was rerun. Original research files/hashes, real database,
protocols, retrospective-admission policy/activation, active EOP policy, previous
reports and unrelated changes are preserved. No commit, push, deployment, external
provider access, upload or infrastructure change occurred; updates remain local.

## Windows compatibility and CI preparation — 26 October 2026

**Owner-reported Windows local-use progress is recorded; native automated tests
and CI execution remain pending.** The owner's instructions identify
`D:\OrbitIQ-local-review`, branch `publication/v1-verified-docs-2026-10-26`, HEAD
`c904082f55df8ad133eefffceb5cca73da7287ff`, and successful Python 3.12/locked backend
and frontend dependency installation. The earlier console transcript captures
HEAD, a clean pre-fix checkout, Python 3.12.14, successful locked dependency installs
and the initial Windows `fsync` failure. It does not capture later successful startup.

The owner now reports successful synthetic seeding with `--local-owner --catalog-only`:
`synthetic_only: true`, `validation_fixture_created: false`, catalog **6251**, IDs
**1/2**, demo DB `D:\OrbitIQ-demo\owner-review-windows-2\archive.sqlite3`. The owner
also reports `Application startup complete` and
`Uvicorn running on http://127.0.0.1:8000`. These strings are recorded as supplied
startup evidence, not an agent-captured Windows log. No DB hash, direct health/
readiness result or specific frontend/browser observation was supplied with this
follow-up. The original `OSError: [Errno 9] Bad file descriptor` is preserved as
an actual failed initialization that motivated the fix, never reclassified as PASS.

The assistant's available execution environment is Linux at
`/workspace/OrbitIQ-e82`; the owner's `D:` filesystem is not attached. Its branch
and HEAD remain preserved. Current cloud content was compared with published
**c904082**, identifying exactly these five pre-existing, unpublished fix files:

1. `backend/orbitiq/database.py`
2. `backend/tests/test_database_publication.py`
3. `backend/tests/test_local_catalog_seed.py`
4. `scripts/seed_browser_fixtures.py`
5. `docs/windows-local-demo-compatibility.md`

The two production/helper files were reviewed and are unchanged in this follow-up.
The database uses **`r+b`** for its own completed staging file, retains mandatory
flush, no-overwrite hard-link publication and cleanup. The catalog-only mode is
explicit, local-owner-only, synthetic, read-only and excludes evidence-bundle
creation and ownership changes. Existing release-fixture/security/scientific paths
are preserved. No operator database is used by the tests; the new subprocess CLI
probe even sets an explicit temporary synthetic sentinel as the configured DB and
verifies that it remains unchanged.

The existing `.github/workflows/ci.yml` now has a **`windows-compatibility`** job:
`windows-latest`, PowerShell, Python 3.12, uv **0.12.23**, `uv sync --locked --python
3.12`, and only these existing focused selections:

```text
backend/tests/test_database_publication.py
backend/tests/test_local_catalog_seed.py
backend/tests/test_foundation.py
backend/tests/test_e3_recovery.py::test_destination_not_visible_until_validation_completes
backend/tests/test_e3_recovery.py::test_publication_race_preserves_other_creators_file
```

Coverage is **17 cases**: writable flush with initialization/backup/restore,
validation and cleanup, flush-failure refusal, existing-target/source preservation,
validation-before-publication and publication races, explicit catalog-only guards,
and an actual subprocess CLI seeding/receipt/no-overwrite check. The CLI test checks
all required receipt fields, labels and IDs against the resulting read-only SQLite
archive, avoids the POSIX bundle path and verifies no configured sentinel or
validation archive was touched. Only JUnit XML is uploaded, never a DB/demo archive.
`release-images` now depends on the Windows job as well as backend/frontend; all
existing job steps, triggers and read-only repository permissions are preserved.

**Fresh local verification: 17 passed in 5.06 seconds in Linux**, zero failures,
errors or skips. One existing Starlette/httpx deprecation warning remains. The
previous **94 passed in 9.93 seconds in Linux** is retained as prior evidence and
was not rerun or re-labelled Windows. Targeted lint/format, strict YAML duplicate-
key parsing, job/dependency checks, documentation/JSON links and preservation checks
passed. `actionlint` is not installed; the YAML checks are not GitHub execution or
an independently executed full Actions schema validator.

**Native Windows automated execution: NOT RUN in this task. New Windows CI job:
NOT RUN — awaiting authorized publication.** No workflow dispatch, commit or push
occurred. No broad backend, frontend, browser, PDF or unrelated scientific suite
was repeated. Earlier full CI belongs to its exact published commits; it does not
verify the subsequently changed local source, tests or workflow.

The [owner checklist](v1-user-acceptance-checklist.md#windows-compatibility-follow-up--26-october-2026)
and JSON ledger separate the captured failure/install transcript, owner-reported
startup, prior Linux94, current Linux17, intended Windows coverage and pending CI.
The existing four decisions remain: owner **ACCEPTED_FOR_INTENDED_LOCAL_USE**, local
engineering **GO_FOR_INTENDED_LOCAL_USE**, scientific study **BLOCKED — NO-GO**, and
production readiness **NO-GO**. No six-item/manual browser pass is inferred. Essential
scientific frame/EOP, reference-point, quality/provenance and protocol gates remain
open; IGS clarification is pending, Phase 11.3.1 PARTIAL. Production hosting/domain,
independent backups, actual alerts and release controls stay deferred/unverified.

Original research files/hashes, real DB, previous evidence, protocols/admission/EOP
policies, branches and unrelated changes are preserved. All follow-up changes stay
**local and unpublished**; nothing is deployed and no external data is uploaded.
Detailed task receipts are under `/tmp/orbitiq-windows-ci-closure-20261026/` and are
local engineering records, not durable backups or acquired scientific evidence.

## Windows final review and owner test result — 26 October 2026

**OWNER_REPORTED_NATIVE_WINDOWS_PASS:** the owner reports the documented focused
command passed **17 tests, 0 failed, 0 skipped in 7.09 seconds**. A raw native log,
JUnit, exact run time and current Windows file hashes were not supplied; no
assistant-executed native run is claimed. Prior **94 Linux passes in 9.93 seconds**
and **17 Linux passes in 5.06 seconds** remain unchanged historical evidence.
Owner-reported synthetic seeding/backend startup is distinct from the unverified
Windows frontend/browser/manual workflows. The new remote Windows CI job has
**NOT RUN**. No broad or focused application suite was rerun during this review,
because source/test/workflow bytes were unchanged; documentation-only consistency,
formatting, lint, YAML/dependency, whitespace and preservation checks were used.

All nine unpublished paths, including both new focused test files and the new
compatibility report, were reviewed against published **c904082**. No blocking
implementation defect was found. Atomic no-overwrite publication, mandatory
writable staging flush and success/failure cleanup are retained. Catalog-only
mode is explicit, synthetic, local-owner-only, does not call `chown`, and excludes
the POSIX evidence-bundle path. Tests exercise production functions and the real
CLI with exact required receipt/DB assertions and no-overwrite checks. The
workflow uses Windows/PowerShell, Python 3.12, locked dependencies and only a
JUnit artifact; a failed Windows job blocks `release-images`. Static YAML checks
passed, but neither `actionlint` nor GitHub execution occurred.

The discrepancy found was stale current summaries saying native tests were still
pending. Four existing tracking documents now record the owner result through
this addendum; their earlier evidence is preserved. All nine cloud files have LF
and localized diffs. The owner's reported LF-to-CRLF warnings do not establish
whitespace errors or prove the Windows diff has no whole-file rewrites. No Git
configuration, scientific code, tests or workflow changed in this final review.

Cloud database/research hashes, protocols, policies, branches and known demo
archives remain unchanged. The cloud environment cannot inspect the owner's
Windows working tree, demo DB or C: source-backup directory. Their final status,
hashes, backup size and completeness remain unverified; no backup was deleted.
The guarded updater backs up overwritten existing text files only, so nine
backup files are not a valid completeness requirement. Final Windows publication
sign-off remains conditional on those local checks. No commit, push, publication,
deployment or remote CI was performed.

Owner acceptance remains **ACCEPTED_FOR_INTENDED_LOCAL_USE**, local engineering
**GO_FOR_INTENDED_LOCAL_USE** within its existing scope. Six owner checkboxes stay
unchecked. Scientific study remains **BLOCKED — NO-GO**, production readiness
**NO-GO**, Phase 11.3.1 **PARTIAL**, IGS clarification **PENDING**, E4 **OPEN**.
See the [compatibility review](windows-local-demo-compatibility.md#final-compatibility-review--26-october-2026)
and JSON ledger section `windows_compatibility_final_review_20261026`.

## Authorized Windows publication checkpoint — 27 October 2026

The owner supplied Windows `git status --short --untracked-files=all`, showing
exactly the six modified and three new reviewed paths, all unstaged, and
`git diff --check` exit **0**. LF-to-CRLF warnings were recorded without a
whitespace failure. These are owner-supplied console results, not direct access
to the Windows filesystem. Native focused tests remain separately recorded as
**17 passed, 0 failed, 0 skipped in 7.09 seconds**, owner-reported; the prior
Linux94 and Linux17 receipts are preserved, not rerun or relabelled.

The updater backup inventory reports **four files / 237,292 bytes**: the previous
workflow and three V1 tracking files. Both raw SHA-256/size and LF-normalized hashes
match the published pre-update contents (the raw files are CRLF). This is consistent
with two already-fixed source files being skipped and three new files having no
preimages. The backup was retained. It is a source/documentation backup, not a
research database backup, off-machine recovery demonstration or a direct C: audit.
Current Windows research/demo hashes and ACLs were not supplied.

Owner screenshots show backend-connected status, both synthetic catalog-6251
snapshots, source-detail display, save confirmation, report-ready status, a
portable JSON download opened in an editor and the matching import preview.
Final import, refresh/reopen persistence and Windows PDF/download-content checks
are not established by these screenshots. No original owner checkbox was marked
passed on this basis.

The owner explicitly authorized committing and pushing exactly the reviewed
nine-file patch on `publication/windows-compatibility-2026-10-27`, followed by
CI verification for the exact commit. Source/tests/workflow remain unchanged by
this documentation checkpoint. New CI must verify **backend**, **frontend**,
**windows-compatibility** and **release-images**. The committed snapshot cannot
contain its own future SHA or CI result; those must be read back and reported
separately. Earlier pending/blocked statements remain historical evidence.

Scientific study stays **BLOCKED — NO-GO**, Phase 11.3.1 **PARTIAL**, IGS
clarification **PENDING**, production readiness **NO-GO**, E4 **OPEN**. Owner
acceptance and scoped local engineering decisions remain unchanged. No real
historical scientific comparison, merge, deployment or private-data upload is
authorized by publication.
