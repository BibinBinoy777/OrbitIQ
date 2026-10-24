# E8 engineering verification

Baseline: `309aa02826bc0ca36ce82ed31d14fb76dbeecbfb`.
Branch: `engineering-e8-nasa-igs-feasibility` in the separate E8 worktree.
Status: **E8 feasibility engineering verified on the corrected implementation
baseline below**. This receipt and metadata-only documentation additions receive
their own exact-SHA CI before final handoff.

The [feasibility report](engineering-e8-feasibility-report.md) ends in
**BLOCKED — ADDITIONAL EVIDENCE REQUIRED**. That scientific decision is separate
from software/feasibility-task completion and production readiness.

## Scope and actual local results

Only an offline metadata/eligibility inspector, 46 deterministic tests, tiny
synthetic fixtures, metadata-only evidence and documentation were added. No
runtime backend/frontend implementation, orbital algorithm, source-storage
schema, database, dependency, lockfile, workflow or existing scientific threshold
changed. The inspector has no network client, comparison/propagation call, output
state vectors, database writes or scientific-approval switch.

- **46 focused E8 tests passed**. They cover actual fixed-column layout through
  synthetic controls, compression/hash/size/EOF protection, supported time/frame
  metadata, filename/header conflicts, unknown units, malformed/missing/duplicate
  records and epochs, predicted/maneuver/missing/unknown-quality exclusions,
  exact GP precision/static model compatibility, nominal time-dependent SINEX
  identity/PRN ambiguity, missing resources, exact deterministic converted epochs,
  seven-day boundaries, fixed first-epoch anchoring and no-overwrite CLI output.
- **1,352 full backend tests passed**, zero failures/skips. Two existing warnings:
  Starlette test-client deprecation and intentional duplicate-ZIP-member fixture.
- **427 frontend tests passed** across 30 files. Frontend source/lockfiles are
  byte-identical to E7; the separate worktree temporarily used the existing locked
  node_modules through a local symlink, removed after verification. Python likewise
  used the matching existing locked environment with this worktree's backend on
  PYTHONPATH. This reuse is not a fresh-install claim.
- ESLint, frontend Prettier, TypeScript, production build, Ruff lint/format,
  locked-uv consistency, actionlint and whitespace checks passed. The existing
  approximately 558.60-kB globe chunk warning remains visible. The one raw SP3
  test fixture intentionally preserves blank flag columns through column 80;
  `.gitattributes` exempts only its required trailing blanks from Git's end-of-line
  whitespace warning. Other whitespace checks and fixed-column assertions remain.
- Unchanged numerical audits passed: **40 SGP4**, **six terrestrial**, **32 expanded**,
  **28 independent geodetic** cases and **28 separate algebraic round trips**.
  These tests do not establish real-world prediction accuracy.
- Explicit migration/backup/restore selection: **five passed** against temporary
  fixtures. The real database was never used as the study's input or destination.
- A separate fresh Git-index checkout passed locked uv/npm installs, build,
  live frontend/API proxy, missing-database safety, explicit initialization,
  duplicate-init refusal, no-op migration, injected collection failure/recovery,
  restart and separate restore rehearsal. Tested tree:
  `50c685da75711d645361e1ee6ae21c3fee251403`. Initial subsequent changes were
  documentation and the fixed-column whitespace attribute; later CLI-test and
  compressed-input corrections were separately verified by the exact corrected
  CI tree below, including another full fresh-checkout rehearsal.
- The final inspector independently parsed the genuine 102,609-byte gzip product,
  verified its SHA-256, expanded 253,250-byte SHA-256, all 96 epochs / 3,072 P
  records, and checked official nominal identity plus time/resource eligibility
  for G30 and G10. Both returned zero eligible GP/reference epochs and zero
  scientific acceptance; no source coordinates were exported or propagated.
- All 96 exact source tags converted with existing local leap resources. Each
  epoch's UT1/polar-motion preflight (including ±0.5-second support) succeeded with
  IERS_B_final central flags. This verifies time/resource diagnostics, not frame
  realization alignment or an uncertainty budget.
- The complete local Docker/browser/PDF release rehearsal was not rerun: inherited
  root-filesystem capacity was about 2.2 GiB and previous local Firefox/WebKit host
  limits remain. No browser assertions, gateway limits, timeouts or tests were
  weakened. Full existing E1–E7 coverage must pass exact-commit remote CI.

The first focused run found two test expectation issues: a removed position record
was correctly refused as an unsupported state record, and datetime's default
string formatting omitted zero fractional digits. Assertions were corrected to
check the actual refusal and explicit six-digit formatting; parser/precision
requirements were not relaxed. The final results above followed those corrections
and the added strict metadata-header/identity checks.

## First remote CI run and corrective verification

Commit `111995ebca025e11f661c9c932337e3e263822dd`,
[run 40066531919](https://github.com/BibinBinoy777/OrbitIQ/actions/runs/40066531919),
passed frontend but had **1 failed / 1,351 passed** backend tests. Release/browser
checks were skipped because backend did not pass. The new CLI subprocess test
could not import `orbitiq`: local testing supplied PYTHONPATH, whereas pytest's
own pythonpath configuration does not propagate to child processes in CI.

The test now explicitly removes any inherited caller PYTHONPATH and supplies the
child with the absolute backend path, matching the documented standalone CLI
invocation. All refusal/no-overwrite assertions remain. Review also added safe
refusal of malformed DEFLATE streams rather than an
unhandled compression traceback, covered by the existing integrity test. No
orbital, scientific qualification, dependency or workflow behavior changed.
Corrective tests were run with PYTHONPATH removed from the parent environment:
**46 focused and 1,352 full backend tests passed**. Genuine G30/G10 inspection
results remained identical and scientifically BLOCKED. The corrected remote CI
result was then observed and independently verified below.

## Corrected published baseline and remote verification

Implementation commit: `ef1c8f3308941a82d28d70208b6c26c0c4ced480`.
[Exact-commit run](https://github.com/BibinBinoy777/OrbitIQ/actions/runs/40067071165): **backend, frontend and release-images succeeded**.
No failed/cancelled required execution step was accepted; only the two optional
manual image-retention steps were skipped on an ordinary push.

- Remote JUnit: **1,352 backend / 427 frontend tests passed**,
  zero failures/errors/skips. All 46 E8 tests run offline with synthetic controls;
  no genuine GP/reference product or NASA connectivity is needed by CI.
- Locked installation/advisory checks, Ruff, ESLint, formatting, TypeScript,
  production builds, all existing numerical audits and migrations/recovery passed.
  Actual advisory lookup checked 29 Python packages with zero matches/skips; npm
  reported zero vulnerabilities. This is execution-time lookup evidence.
- Existing E1 **77 flows** (27 Chromium / 25 Firefox / 25 WebKit), E2 **62 checks**,
  E6 **39 scenarios / 12 cross-context round trips / 39 native downloads**, and E7
  **21 cases / three native captured-history downloads** passed. All suites and
  assertions remain; E8 added no redundant browser workflow or mock data feed.
- E2/E6/E7 axe scans totalled **36**, with zero reported violations. Manual/device
  and screen-reader certification remain outside this evidence.
- **Seven PDFs passed**, including all 361 maximum-track rows.
- Gateway/configuration, loopback TLS/API smoke, exact frontend/image matching and
  source/image sealing passed. All **380 source files** were independently
  hashed against the published Git blobs. Full and compact release records both
  verified all **69 sealed evidence files** and frontend artifacts offline.
  Production approval remains false; no image registry publication or deployment.
- Fresh checkout matched exact tree `519552802dda5060775989b29f1124427d253dfa` and passed locked installs,
  frontend/API startup/proxy, safe initialization/refusal, injected failure/recovery,
  restart and separate restore. Restored/source fingerprints matched and the
  disposable source was unchanged. This is not independent production recovery.
- All nine expected artifacts belonged to this SHA and were unexpired when
  inspected. GitHub metadata confirmed configured seven-/90-day retention bounds;
  future expiry/global settings were not tested. Text/trace and extracted PDF
  text passed the established credential/contact scan. Database/key files were
  absent; ZIP integrity and PNG/PDF signatures passed. Images were not OCR-scanned.
  Existing narrowly identified synthetic URL canaries/Playwright image references
  were retained as known test strings. No private product was uploaded.
- Source evidence still states **BLOCKED — ADDITIONAL EVIDENCE REQUIRED**, zero
  scientific epochs and no propagation/residual calculation. Test and artifact
  success cannot promote the genuine candidate to scientific acceptance.

| Milestone                       | Evidence/status                                                       |
| ------------------------------- | --------------------------------------------------------------------- |
| Local engineering verification  | Passed, scoped above                                                  |
| Published implementation        | Corrected E8 engineering commit above                                 |
| Remote CI / retained artifacts  | Exact corrected commit verified                                       |
| Reference acquisition           | VERIFIED via BKG; CDDIS authentication BLOCKED                        |
| Candidate scientific evaluation | BLOCKED; no eligible historical GP and unresolved qualification gates |
| Production deployment           | Not performed                                                         |
| Production infrastructure       | Not verified; E4 OPEN                                                 |

The final documentation receipt is published separately and its own exact-commit
CI/artifacts must be checked before final handoff; this report records the
already-verified implementation baseline without claiming an unobserved later run.

## Reproduction

With locked dependencies installed from the repository root:

```sh
uv sync --locked
uv run --locked pytest backend/tests/test_igs_feasibility.py
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
npm --prefix frontend ci
npm --prefix frontend test
npm --prefix frontend run lint
npm --prefix frontend run format:check
npm --prefix frontend run build
```

Actual-product inspection requires separately retained private inputs. It never
fetches a product or substitutes a test fixture if inputs/resources fail. Example
using the preserved E8 files in this worktree:

```sh
PYTHONPATH=backend uv run --locked python scripts/inspect_igs_reference.py \
  --product data/e8-nasa-igs/original/IGS0OPSFIN_20240010000_01D_15M_ORB.SP3.gz \
  --product-name IGS0OPSFIN_20240010000_01D_15M_ORB.SP3.gz \
  --product-sha256 26f16fa5f97cce851948fa88711aed47f60ee2e4ddfe36f0e98b1076e79fbe38 \
  --gp data/e8-nasa-igs/original/gps-current.bin \
  --gp-sha256 8e1b961369ba5d083ec99b792453e26e82217f0ac609dc6f4eece432a0f5ef87 \
  --metadata data/e8-nasa-igs/original/igs-satellite-metadata.bin \
  --metadata-sha256 ac93d053eac7d8b08ce129b6af98667e1867296e1685417d38c081cd046558ae \
  --prn G30 --catalog-id 39533 \
  --output data/e8-nasa-igs/new-inspection.json
```

Choose a new output filename: existing output is refused. Original/canonical hashes
have different documented meanings. CLI inputs must be regular bounded files;
missing/malformed/ambiguous inputs, mismatched hashes and unavailable resources
fail with a safe error, without echoing source contents or partial comparison.
A successful inspection still returns a scientifically BLOCKED report. It cannot
be used to authorize a comparison.

The profile is deliberately narrow: combined FIN GPS-only SP3-c P, IGS20/HLM/IGS,
900-second cadence, at most 96 epochs, complete fixed-column records, supported
GPS tag precision and exact first-header reconciliation. SP3-d, other constellations,
velocity/correlation records and newer realizations are refused; this is not a
general SP3 conformance validator. Header-fraction rounding in other products is
not automatically accepted. Partial declared grids can be inspected but remain
an explicit daily-coverage blocker. Metadata mapping is a nominal civil-calendar
lookup, not proof of an interval's sub-second physical time scale.

## Preservation and publication boundaries

The original E7 worktree stays on its verified commit. Its tracked files, previous
reports, real schema-3 two-snapshot database and 72 private files are checked
against the existing trusted manifest. All 72 existing private files and the
schema-3 two-snapshot archive were unchanged; database SHA-256 remained
`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
The 12-file source/privacy/link/syntax/evidence review passed. All 369 original
E7 tracked files stayed byte-identical in that worktree. Only README changes among
previously tracked E8-baseline files. The 53 new E8 private evidence files (plus
their manifest) also passed size/hash and Git-exclusion checks.
New E8 captures have a separate private
preservation manifest, including original compressed bytes, GP JSON and official
metadata. They are under ignored `data/e8-nasa-igs/`, absent from Git/Docker/CI.
The filesystem copy is not independent durable backup.

Only the new inspector/tests/synthetic fixtures/docs and a narrow README link are
intended for publication. No default-branch merge, history rewrite, deployment,
paid resource, account creation, private data upload or provider correspondence
is authorized/performed. The earlier NASA-investigation publication authorization
applies to the corrected E8 engineering branch; the updated E8 request supplies
its baseline and prohibits scientific comparisons, which remain absent.

The existing CI workflow already covers locked installs, complete tests, frontend
build, numerical references, migrations, fresh-checkout recovery, pinned release
containers/TLS, E1–E7 browser/accessibility/PDF checks and sealed artifact verification.
No redundant workflow was added. The corrected implementation's actual E8
publication/CI/artifact evidence is recorded above; prior E7 success was not used
as a substitute. Final documentation publication receives its own exact-SHA CI.

E4 remains **OPEN**. Swarm-A Phase 11.3.1 remains **PARTIAL**, scientific evaluation
**BLOCKED**. This feasibility work does not establish production or scientific
readiness. Real comparison work requires prerequisite evidence and explicit user
approval after this report.
