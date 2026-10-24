# E8 engineering verification

Baseline: `309aa02826bc0ca36ce82ed31d14fb76dbeecbfb`.
Branch: `engineering-e8-nasa-igs-feasibility` in the separate E8 worktree.
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
  `50c685da75711d645361e1ee6ae21c3fee251403`; subsequent changes were documentation
  and the fixed-column whitespace attribute only. CI rechecks its exact tree.
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
results remained identical and scientifically BLOCKED. The next exact-commit CI
result must be observed rather than inferred from the earlier local success.

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

## Preservation, publication and pending remote gate

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
No redundant workflow was added. Commit/push and exact-final-SHA CI/artifact review
remain pending at this local checkpoint; prior E7 success is not E8 verification.

E4 remains **OPEN**. Swarm-A Phase 11.3.1 remains **PARTIAL**, scientific evaluation
**BLOCKED**. This feasibility work does not establish production or scientific
readiness. Real comparison work requires prerequisite evidence and explicit user
approval after this report.
