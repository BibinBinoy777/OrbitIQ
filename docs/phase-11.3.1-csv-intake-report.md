# Phase 11.3.1 — CSV intake completion checkpoint

Local verification on **21 October 2026**. The CSV intake task is implemented and
locally verified. Overall Phase 11.3.1 is **PARTIAL**, and scientific evaluation
is **BLOCKED**. No publication, remote CI, deployment or production-readiness
claim is made. Machine-readable supporting evidence is in
[CSV verification](phase-11.3.1-csv-verification.json); the
[intake guide](phase-11.3.1-historical-csv-intake.md) gives the complete verified
17-column mapping, budgets, numeric rules and operator commands.

## Review and scope

Branch: `phase-11.3.1-readiness-hardening`.
HEAD: `67abe1588bcada4fd30ee46134a71c4d27dcbd05`, unchanged.
The initial index was empty and remains empty. Existing tracked modifications
and untracked Phase 11 work were identified before implementation and retained.
The original five-file implementation was reviewed, formatted and completed;
those files are not the complete earlier Phase 11 working tree.

Files changed by this task:

| File | Change |
| --- | --- |
| `scripts/inspect_historical_csv.py` | New explicit, bounded, static CSV adapter and private capture CLI |
| `scripts/inspect_historical_gp.py` | Optional trusted inspector callable for shared durable capture; default JSON behavior unchanged |
| `scripts/reconcile_historical_gp.py` | Explicit CSV comparison, source tokens/indices/order, exact Decimal values, precision and provenance diagnostics |
| `scripts/qualify_swarm_inputs.py` | Extend existing unpublished qualifier with mutually exclusive CSV input, ten gates and genuine-reference epoch-bound diagnostics; exclusive private output |
| `backend/tests/test_historical_csv_intake.py` | 82 synthetic test cases covering intake, reconciliation, preservation and the scientific boundary |
| `docs/phase-11.3.1-historical-csv-intake.md` | Verified schema, mappings, semantics and private workflow |
| `docs/phase-11.3.1-csv-intake-report.md` | This additive checkpoint |
| `docs/phase-11.3.1-csv-verification.json` | Sanitized local evidence and source/check hashes |

No dependency, lockfile, database schema/migration, application runtime or frontend
source was changed by this task. Existing phase reports were not rewritten. Of
302 source/report files fingerprinted at task start, only the three existing
scripts listed above changed; the other 299 remain byte-identical. The two new
code files and three new documents are additive. Earlier Phase 11 modifications
remain separately visible in Git and were included in the full-workspace tests.
Nothing was reset, discarded, staged, committed, pushed or deployed.

## Genuine-source results

| Evidence | Result |
| --- | --- |
| Original malformed JSON | 1,227 bytes; SHA-256 `c55dc4cbb2331a162014833a1a354e6f62ff4572d5238954b8108f69cae3053c` |
| Separate CSV original | 644 bytes; SHA-256 `2b5712d5c2fe3fd6f8106633cb84780d6562eb455f49922fbbbbe9d09a26f1c4` |
| Existing nine-token assessment | SHA-256 `620e9545fd4820709a3ecfff101e3705f4a70fbde2ae91de6f48dd5e7c0c8575` |
| Source structure | 17 unique verified columns; three rows; comma/CRLF; no quoted or missing cells in actual file |
| Static record validation | Three candidates; zero exclusions; all match NORAD 39452 / 2013-067B and pass existing element-model constraints |
| Exact comparison | All 51 values equal: 39 numerical and 12 text; source indices/order preserved; no added/removed/duplicate records |
| Source lexical changes | Six `e`/`E` case differences; no source precision change or unexplained difference |
| Comparison-type differences | Three JSON `int` → CSV `Decimal` entries for `MEAN_MOTION_DDOT`, labelled separately from source precision |
| Actual ESA time audit | 7,647 accounted for: 5,118 converted, 1,806 submicrosecond exclusions, 723 second-60 exclusions |
| Epoch bounds | All three candidates fit ±7 days across the ordinary converted ESA interval; no record or temporal pair selected |
| Genuine Swarm-A scientific evaluation | Zero predictions, null residuals, no normalized observations, operational adapter false |

Record validation is traceable without publishing the orbital payload:

| Source index | Source epoch text (UTC convention) | Structure / element model | Scientific acceptance |
| --- | --- | --- | --- |
| 0 | `2013-12-30T20:24:39.765600` | PASS / PASS | BLOCKED |
| 1 | `2014-01-01T05:30:45.095904` | PASS / PASS | BLOCKED |
| 2 | `2014-01-02T06:43:57.421344` | PASS / PASS | BLOCKED |

Raw source fields, exact original/CSV comparison text and full reports are retained
only in new private captures and qualification diagnostics. Original JSON, CSV,
nine-token assessment and ESA products were not edited. All 27 preexisting private
files fingerprinted at task start remain identical. Source capture manifests and
new result manifests were verified. A preliminary diagnostic stopped on an
incorrect expectation of zero internal numeric-type differences; its completed
private intake capture was preserved, and a fresh successful audit was appended.
No original or prior diagnostic was replaced.

That investigation corrected classification in reconciliation: interpreting the
CSV floating-field text `0` as Decimal is an adapter type choice, not a change in
source text or precision. A synthetic regression now covers that distinction.
Exact values and source spelling continue to be checked separately. Preliminary
lint failures were corrected. Final results below supersede earlier runs; no test
or functionality was removed, skipped or weakened to produce a pass.

The successful genuine-source audit ran with network, database and subprocess
operations denied and propagation/residual callables replaced by failure guards.
All four attempt counters were **zero**. The CSV qualifier bypassed the older
dynamic single-record JSON diagnostic. Reconciliation used only the reviewed,
hash-pinned nine-edit in-memory comparison view; no repaired JSON GP payload was
saved or accepted. The original still fails strict JSON validation.

The ordinary SQLite file remains SHA-256
`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
Read-only schema, complete table contents, integrity and foreign-key checks match
the baseline: schema version 3, two existing genuine ISS snapshots, no Swarm-A
snapshot and unchanged ingestion ledger/gate. Test databases are isolated fixtures.

## Executed verification

| Check | Actual local outcome |
| --- | --- |
| Locked Python installation: `uv sync --locked` | PASS; lockfiles unchanged |
| Focused final CSV/GP/reconciliation/qualification tests | **240 passed**, including 82 CSV cases |
| Full final backend: `uv run --locked --no-sync pytest -q` | **1,155 passed**, two expected warnings from adversarial duplicate-member ZIP fixtures |
| Frontend: `npm test` | **344 passed** in 25 test files |
| Ruff lint / format check; frontend ESLint / Prettier | PASS |
| TypeScript `tsc --noEmit`; `npm run build` | PASS |
| Published SGP4 / earth-fixed / expanded scientific audits | **40 / 6 / 32 passed**, zero failed |
| Geodetic audit | **28 independent cases + 28 round-trips passed** |
| Golden reference lifecycle | **6 published vector components + 3 exact offline replays passed** |
| Chromium / Firefox / WebKit regression checks | **77 flows passed** across all three engines; API unmocked |
| PDF checks | **7 passed**, including all 361 maximum-track rows |
| `git diff --check`, source/private preservation and database fingerprint | PASS |

Backend and focused tests were rerun after the final reconciliation change; lint
and formatting were checked again on final files. Frontend/build/scientific/golden
checks used unchanged application/runtime sources and were not invalidated by that
operator-only comparison change. Browser checks used byte-matching backend and
built frontend copies on an internal Docker network with no published ports;
normal legacy ISS and clearly synthetic reference/UI calculations ran there.
**No genuine Swarm-A propagation or real ESA residual calculation occurred.**
Seven PDFs were generated/inspected through Chromium; Firefox/WebKit exercised
report/download/offline-HTML regressions without claiming native PDF rendering.
No browser/PDF check was omitted. These are local regressions, not deployed tests,
independent observational accuracy validation, or remote CI. Frontend packages
were already installed; `npm ci` was not rerun in this task. The unchanged package
lockfile is preserved. Raw logs and artifacts are under the task-owned
`/tmp/orbitiq-csv-adapter/` directory and are not durable off-machine evidence.

## Independent gates and acceptance

| Gate | Current status |
| --- | --- |
| 1. Source identity | PARTIAL — labels match, provider authentication unestablished |
| 2. Record structure | PASS — supported actual CSV schema |
| 3. Numbers / element model | PASS — static checks, not dynamic validity |
| 4. Historical selection | BLOCKED — no approved source record selection |
| 5. Temporal pairing | BLOCKED — epoch bounds do not approve pairing |
| 6. Time system | PARTIAL — ordinary subset only; 2,529 exclusions retained |
| 7. Coordinate frame | BLOCKED — IGb08 alignment unqualified |
| 8. Reference quality | BLOCKED — no approved per-epoch quality selection |
| 9. Provenance / independence | BLOCKED — availability, authentication and actual-pair fitting lineage unknown |
| 10. Operational evaluation | BLOCKED — no qualified adapter or residual authorization |

The task's AC-01–AC-12 are PASS **for their stated intake, preservation, regression
and explicit-blocker scope**, not for completing scientific qualification:
unchanged originals (01), actual schema (02), three static model passes (03),
source field/index traceability (04), exact numeric/lexical reconciliation (05),
discrepancies and missing provenance reported (06), JSON strictness (07), historical
and Phase 9 regressions (08), independent gates (09), residual block enforced (10),
executed checks (11), and explicit outstanding limitations (12).

Next: resolve reference-product documentation/time anomalies and predeclare a
justified quality/temporal selection, qualify IGb08 treatment with authoritative
parameters or a defensible precision-scoped error budget and independent tests,
and document actual-pair provenance/availability/lineage. A future comparison must
remain retrospective unless historical availability is independently established.
Do not enable real evaluation merely because CSV parsing now works.

Phase 8 public hosting/HTTPS, independent recovery, real alert delivery, publication
CI and branch-protection evidence remain separate, open production milestones.
This task makes no change to those statuses and initiates no remote workflow.
