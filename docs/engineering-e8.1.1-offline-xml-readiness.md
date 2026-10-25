# E8.1.1 — Offline historical OMM XML intake readiness

Engineering scope: prepare safe **local inspection**, not acquire or qualify a
real historical record. No NORAD 39533 historical XML attachment was available or
inspected. The user reports a CelesTrak request for 25–31 December 2023; submission
does not establish delivery. **NASA/IGS study: BLOCKED. Residuals: NOT PERFORMED.**

Baseline: E8 commit `b0a03205e3930b55651232d8b7ffbc9e879ae8c6`.
Separate worktree `/workspace/OrbitIQ-e811`, branch
`engineering-e8.1.1-offline-xml-readiness`. Existing E7/E8 worktrees and branches,
previous reports and the [E8 proposed protocol](engineering-e8-comparison-protocol.md)
are preserved. This task has no publication steps.

## Reused functionality and narrow additions

The existing historical JSON/CSV diagnostics are Swarm-specific; the E8 inspector
accepts a unique GP JSON record, not a multi-record OMM XML attachment. The locked
`sgp4.omm.parse_xml` reader extracts fields but does not enforce this study's
structure, duplicate-field, identity or selection policy.

The new [XML inspector](../scripts/inspect_historical_xml.py) reuses:

- Historical intake's bounded regular-file reads, no-symlink path checks,
  expected-hash verification, explicit operator provenance, private exclusive
  captures, receipt, manifest and safe stdout/error handling.
- CSV intake's numeric conversion and exact-epoch checks; the unchanged
  `Elements` model for field/range/Earth/UTC/TEME/SGP4 compatibility.
- The locked library's OMM XML field extraction, after a strict offline preflight.

No existing parser, scientific engine, application route, database, dependency,
lockfile or workflow is modified. No satellite is initialized by the inspector.
The only additions are this document, the inspector and synthetic tests.

## Run against a future original attachment

Install the existing locked dependencies using the repository's normal setup.
From the checkout root, choose a **new** private archive directory:

```sh
mkdir -m 700 "$PWD/data/e8-xml-intake"
PYTHONPATH=backend uv run --locked python scripts/inspect_historical_xml.py \
  --attachment /absolute/private/path/provider-attachment.xml \
  --archive-root "$PWD/data/e8-xml-intake"
```

The input and archive must use absolute paths without symlink components. The
archive must already exist, be owned by the operator and have mode `0700`.
Use `data/` or another approved private location excluded from Git, Docker build
contexts and ordinary CI uploads. Do not place raw provider bytes in test fixtures.
No actual provider request or authentication is performed by this command.

Optional flags:

- `--expected-sha256` checks a separately recorded original-file hash before capture.
- `--metadata /absolute/private/path/receipt-claims.json` supplies operator
  assertions. Supported keys are `provider`, `acquired_at`, `received_at`,
  `original_filename`, `format`, `notes`. Put request/source information in these
  private fields; omit contact details and credentials. Supply receipt/acquisition
  times only when actually known, as explicit ISO timestamps with a timezone.
  Missing times stay JSON `null`; file modification time, orbital epoch and
  storage time never fill them. Original assertions are not authenticated facts.
- `--synthetic` labels test input and its reports `SYNTHETIC_TEST_ONLY`. It only
  changes the evidence label and cannot enable acceptance. Use it for invented
  fixture data, never to represent acquired scientific evidence.

Each attempt with readable, hash-matching input creates a new private capture
directory containing `attachment.original`, `receipt.json`, `inspection.json`
and a completion `manifest.json`. Source bytes are copied unchanged **before**
parsing. The original is only read; existing captures are not overwritten.
The manifest covers file sizes/hashes. `stored_at_utc` is the capture time, not
email receipt. `tool_sha256` identifies the reused capture implementation;
`xml_inspector_sha256` separately identifies the XML inspector.

Stdout contains a bounded summary without filenames, record values or source
content. Read detailed identifiers, source indices, original epoch/creation text,
coverage, field errors, duplicates and eligibility in the **private** inspection
file. Do not upload that file to ordinary CI for a genuine attachment. Exit 1
means intake/whole-document refusal; malformed but readable originals remain in
their new private capture for review. A failed write may leave an incomplete
capture with no completion manifest; preserve it for investigation. Exit 0 means
inspection completed, including any record exclusions, **not** scientific success.
Always inspect parsing status, per-record errors and selection blockers.

## Supported profile and explicit limits

This is a bounded OMM **2.0**, namespace-free, SGP4/TLE-parameter inspection
profile: an `omm` root or `ndm` containing `omm` messages, with
`id="CCSDS_OMM_VERS"`. It supports multiple segments and retains source order.
It is not a general CCSDS XSD validator. Namespaced documents, other versions,
covariance/spacecraft/user-defined sections and unknown structures are refused
for review, never silently discarded or converted. Schema-location hints are
never fetched. Do not alter a real attachment to make it fit this profile.

Limits reuse the historical intake's 2-MiB source and 512-record budgets, with
additional limits of 30,000 XML nodes, depth 12 and 4,096 characters per field.
DTD/entity declarations, HTML/login pages, malformed or empty responses,
duplicate fields/groups and unsupported explicit units are refused. XML requires
explicit Earth/TEME/UTC/SGP4 metadata instead of silently inheriting the GP JSON
defaults. Missing header originator/creation metadata is reported as invalid.
OMM header creation is retained as an unverified message-creation claim; it is
not automatically Space-Track publication metadata or proof of availability.

XML decoding/unescaping and numeric parsing form a separate model-validation
view; neither rewrites original bytes. Timestamp text is retained. The existing
exact-epoch rule rejects nonzero submicrosecond digits, non-UTC offsets and
invalid/leap-second calendars; extra zero fractional digits do not change time.
Timezone-free GP epochs use the existing documented UTC convention, not local time.
The parsed-field digest is **not** the original XML/header/attribute hash.

## Parsing, eligibility and scientific qualification are separate

Identity must match NORAD **39533** / COSPAR **2014-008A**. A PRN name alone
does not establish spacecraft identity. Wrong/mixed objects remain visible in
the report and do not become candidates. A future genuine record still requires
cross-checking against retained official SVN G064 / G30 identity evidence.

The request calendar is `[2023-12-25T00:00:00Z, 2024-01-01T00:00:00Z)`.
The unchanged protocol GP-epoch window is
**[2023-12-25T23:44:42Z, 2023-12-31T23:59:42Z], inclusive**. Temporal eligibility
is reported separately from parsing and identity, retaining all exclusions.
No nearest-record selection, rounding, repair, interpolation, guard relaxation
or satellite substitution is permitted.

The existing protocol ranks eligible records by decreasing epoch. The inspector
only reports a `latest_unique_static_candidate_index` for later provenance review;
`selected_source_index` remains `null`. Competing records at the latest eligible
epoch, including repeated identical records, block that assessment without
falling back to an earlier input. Element-set/revolution numbers and source
order are not tie-breakers. Duplicate groups use parsed field text, with their
scope explicitly distinguished from original-byte hashes.

Every report remains **scientifically BLOCKED**, including synthetically valid
ones. A successful local parse cannot establish genuine historical acquisition,
publication/availability, complete fitting lineage, independent prediction
accuracy, statistical independence or an approved comparison. IGS20 alignment,
satellite physical reference point, reference quality/uncertainty, dependencies
and protocol/approval gates remain unresolved. IGS includes ESA contributions;
it is not an ESA-free reference. The Swarm-A workstream remains **PARTIAL** with
evaluation **BLOCKED**, and E4 remains **OPEN**.

## Verification

The test module is explicitly **SYNTHETIC readiness evidence only**. It derives
invented XML fixtures from the established numeric-format fixture and never
opens genuine historical GP or reference files. New tests block networking,
satellite initialization and engine propagation calls in the inspector process.
CLI cases run isolated subprocesses with an explicit backend import path.

```sh
uv run --locked pytest backend/tests/test_historical_xml_intake.py
uv run --locked pytest backend/tests/test_historical_gp_intake.py \
  backend/tests/test_historical_csv_intake.py \
  backend/tests/test_historical_gp_reconciliation.py \
  backend/tests/test_igs_feasibility.py
uv run --locked ruff check .
uv run --locked ruff format --check .
```

Actual local results on 24 October 2026, using the existing locked Python 3.12.14
environment with the parent `PYTHONPATH` removed:

| Check                                                      | Actual result                                      |
| ---------------------------------------------------------- | -------------------------------------------------- |
| New synthetic XML readiness tests                          | **58 passed**, 8.91 seconds                        |
| Complete backend suite, including those 58                 | **1,410 passed**, 89.75 seconds; no failures/skips |
| Repository-wide Ruff lint                                  | Passed                                             |
| Repository-wide Ruff format                                | Passed; 227 Python files                           |
| Documentation Prettier, local links, fences and whitespace | Passed                                             |
| Offline lock consistency                                   | Passed; 31 packages resolved from unchanged lock   |
| New-file privacy/syntax/scientific-boundary review         | Passed                                             |

The full suite retained two known warnings: Starlette's test-client deprecation
and the deliberate duplicate-member ZIP safety fixture. The first new-test
collection attempt used pytest's reserved parameter name `request`; renaming that
test argument fixed collection without changing assertions. Initial formatting
findings were fixed. Review found that ElementTree raises separate exceptions for
unknown/unsupported encodings; safe refusal and two synthetic regression cases
were added before the final runs. No existing test or scientific guard was weakened.

The initial offline lock check encountered the runtime's read-only default uv
cache. It passed using an explicit `/tmp` cache and the existing Python interpreter;
no network access or dependency installation was needed. The repository has no
configured Python static type checker; no unrelated frontend type/build checks,
browser/PDF flows, remote CI or fresh installation were rerun. Their earlier
results are not fresh E8.1.1 verification.

Before/after integrity checks verified all **72** original private files against
the established trusted baseline. Read-only database checks retained schema **3**,
**two** snapshots and SHA-256
`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
All **53** E8 private evidence files and their preservation manifest remained
unchanged. The original compressed IGS reference SHA-256 stayed
`26f16fa5f97cce851948fa88711aed47f60ee2e4ddfe36f0e98b1076e79fbe38`;
local decompression retained expanded SHA-256
`8a638375273ab74011aebd9ffcc480df02b5718440c8fb7c51c408ff220d231c`.
These byte-integrity checks are not a new scientific inspection or independent
backup. No real historical GP XML was parsed or qualified.

All **369** original E7 tracked files and **380** original E8 tracked files stayed
unchanged; those worktrees remain clean at their original commits. All pre-existing
tracked files in the new worktree also match the E8 baseline. Exactly three new,
unstaged/uncommitted files comprise the reviewed change:

1. `scripts/inspect_historical_xml.py`
2. `backend/tests/test_historical_xml_intake.py`
3. `docs/engineering-e8.1.1-offline-xml-readiness.md`

**Offline engineering readiness: locally verified. Genuine historical input:
not received/qualified. NASA/IGS scientific study: BLOCKED.** No external data
service, authentication attempt, real-input propagation, scientific residual,
database change, commit, push, deployment or existing-branch rewrite occurred.
