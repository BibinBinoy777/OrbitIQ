# Phase 11.3.1 — corrected export readiness and revalidation checkpoint

Local assessment on **21 October 2026**. **No corrected provider export is present.**
The bounded private-location inventory found only the original rejected attachment.
The correction request is prepared for manual submission, **not submitted** by
this task. Phase 11.3.1 remains **PARTIAL** and scientific evaluation **BLOCKED**.
No real-data replacement validation, actual temporal pairing, operational propagation
or real Swarm-A residual calculation was performed.

## Audit and preservation

Branch `phase-11.3.1-readiness-hardening`, HEAD
`371ce35b577209401ba7961e5bd29c3bd65a9c4d`. Started with **52** modified/untracked
paths, empty index; recorded hashes of **295** existing nonignored files and
**23** existing private files plus the database's full read-only fingerprint.
All these files remain unchanged, including the earlier implementation, receipt
assessment, ESA products, database, historical records and scientific reports.

Reviewed the receipt assessment, original Phase 11.3.1 and frame/time reports,
historical-intake guide, intake and Swarm qualification scripts, strict bounded
JSON parser, GP `Elements` model, scientific gates and corresponding tests.

| File category | Existing implementation/evidence |
| --- | --- |
| Operator implementation | `scripts/inspect_historical_gp.py`, `scripts/qualify_swarm_inputs.py`, `scripts/inspect_swarm_reference.py`; existing strict JSON, GP model and scientific runtime |
| Synthetic tests | `backend/tests/test_historical_gp_intake.py`, `test_phase1131_qualification.py`, `test_phase113_swarm_inspection.py`; published numerical reference fixtures |
| Public documentation | Prior Phase 11 reports/assessments and intake guide; metadata and limitations, not raw private attachments |
| Private evidence | Ignored `data/historical-gp-intake/`, `data/historical-gp-intake-assessments/`, retained ESA products and ordinary database under `data/` |

The search was limited to the configured private intake/assessment directories;
no repeated unrelated search, source download, email access or provider retry
occurred. There is exactly one captured GP attachment, not a replacement:

- Filename `sat000039452.json`; **1,227 bytes**.
- Original SHA-256
  `c55dc4cbb2331a162014833a1a354e6f62ff4572d5238954b8108f69cae3053c`.
- Capture manifest/member hashes and sizes match; original bytes are unchanged.
- Provider identity remains the recorded **user-supplied CelesTrak fulfillment
  claim**, not newly authenticated email headers or an independent download.
- Actual email receipt and acquisition times remain **null**. The existing capture
  storage clock is separate and unchanged; it is not promoted into receipt time.
- Three records were provider-reported and found by the earlier diagnostic probe;
  original strict-document enumeration remains zero because parsing was rejected.

Reviewed all nine recorded token offsets and surrounding lexical contexts against
the original. They are outside strings, have numeric-value delimiters, and involve
three occurrences each of ECCENTRICITY, BSTAR and MEAN_MOTION_DOT. The proposed
insertions preserve each token's Decimal value. This supports the narrow syntax
diagnosis, not automatic acceptance. **No real-source comparison view, corrected
GP payload or repair fallback was reconstructed or saved in this task.**

## Bounded additions

Five new files only; no existing source, test, report or lockfile was edited:

- `scripts/reconcile_historical_gp.py`
- `backend/tests/test_historical_gp_reconciliation.py`
- `docs/phase-11.3.1-corrected-export-request.md`
- `docs/phase-11.3.1-corrected-export-readiness.md`
- `docs/phase-11.3.1-corrected-export-results.json`

The [correction request](phase-11.3.1-corrected-export-request.md) includes the
original request/target/range/count, exact JSON issue, preservation of numerical
values/precision/epochs/metadata, and unknown availability/reuse information.
No request was submitted, no identity impersonated and no email sent.

The new comparison module is an **offline helper**, not a new importer, adapter,
writable API or repair mode. The original intake/parser remains strict. Its
`reconcile()` function returns BLOCKED immediately when replacement bytes are
absent, before reading original inputs, validating real data or replaying any
assessment. It is tested with synthetic inputs only in this checkpoint.

For a future supplied replacement it requires bounded bytes and explicit SHA-256
anchors for the original, prior assessment and new attachment. It uses the existing
intake/strict parser/model to enumerate all replacement records and their failures;
invalid documents, mixed invalid records and duplicates stop reconciliation.
No record is silently dropped. All source hashes, counts and indices are retained.

Only for comparison, after a strict/model-compatible replacement is supplied, the
helper can verify and replay the **existing nine-token assessment** in memory.
This is not a new detector or general repair algorithm: it requires the original
hash/size, assessment hash/type, exactly nine ordered nonoverlapping token edits,
original byte matches, outside-string numeric context, zero insertion only,
Decimal equality, and the prior comparison-view hash. No altered GP input is
returned or written. It still reports independent assessment review as unestablished.
The ledger and proposed numeric interpretation require independent operator
review before any real execution; hashes alone do not provide that review.

Matching uses catalog ID, designator and exact normalized UTC epoch, retaining
both original and replacement indices. Ambiguous same-epoch identities are
reported without automatic matching. No closest-epoch selection is made. A changed
epoch appears as removed/added identity; element-set identifiers and all other
fields are compared explicitly. Added/removed fields or records, type changes,
numeric value changes and unsupported nested metadata stop acceptance.

Exact Decimal comparison detects changes that binary float parsing could hide.
Scalar numeric representation/precision changes are reported separately, including
added trailing zeros or integer/decimal representation changes. Pure whitespace,
key order and record order do not themselves imply different contents. Decimal
representation is not a claim to retain every original lexical spelling: exact
bytes/hashes remain the original evidence. No numerical tolerance or rounding is
introduced. Any unknown field/value or precision difference needs review.

Even a semantic match has status **PARTIAL**, `source_accepted=false`,
`comparison_ready=false`, null availability and residuals, zero prediction
evaluations and no operational adapter. Scientific gates remain independently
blocked/partial. No flag can promote the comparison into scientific acceptance.
This helper does not authenticate a provider, establish actual historical
availability, quantify uncertainty or approve an input repair fallback.

## Procedure when the genuine corrected export arrives

1. Preserve it as a **new** private capture using the existing intake command in
   [the guide](phase-11.3.1-historical-intake.md). Record actual supplied provider,
   original filename/format, byte count/hash and receipt metadata. Keep unknowns
   null, and retain the original capture unchanged.
2. Review strict document/model diagnostics, all source indices, missing fields,
   wrong identifiers, duplicate groups and every exclusion. Parser success is not
   source authentication or scientific qualification.
3. Independently review the original's recorded nine-token assessment and pin
   its hash alongside the original and replacement hashes. Then call the helper's
   `reconcile(original_raw, assessment_raw, replacement_raw,
   original_sha256=…, assessment_sha256=…, replacement_sha256=…)` with bounded
   bytes read from those private captures using the existing intake `read_input`.
   Load the helper from the trusted repository with `runpy.run_path`, not from an
   attachment. Retain the returned report privately using a new exclusive file;
   the helper itself performs no output or database writes.
4. Inspect original/replacement counts, identities, epoch changes, all matched
   source indices, numeric/precision/field differences and missing provenance.
   Stop acceptance for unexplained discrepancies. Obtain provider clarification
   when required; do not hand-edit the replacement or select a convenient record.
5. Document target/source authenticity, availability meaning, record/reference
   selection policy and actual pairing separately. Unknown availability limits a
   future otherwise justified comparison to **retrospective** interpretation.
6. Resolve source time/quality/format discrepancies and a defensible IGb08
   treatment with authoritative evidence and independent tests before any
   operational adapter, propagation or residual calculation.

A scientific repair fallback is **not executed or approved here**. If a corrected
export cannot be obtained, separately justify that fallback and document immutable
source/complete token ledger, reproducible rules, independent numeric review,
strict parse/model checks, full original/derived comparison, explicit derived
labelling and all unchanged scientific gates before considering it.

## Current milestone status

| Milestone | Status | Evidence / remaining condition |
| --- | --- | --- |
| Original received and preserved | PASS | Existing immutable capture/member hashes and size reverified |
| Original accepted by strict JSON | BLOCKED | Earlier strict rejection remains; parser unchanged |
| Correction request prepared | PASS | Exact manual request documented |
| Correction request submitted | NOT STARTED | No evidence of submission; user action pending |
| Corrected export received | BLOCKED | Only original capture present in scoped inventory |
| Replacement records strictly parsed | NOT STARTED | No replacement; only synthetic software tests executed |
| Replacement reconciled against original | NOT STARTED | Helper tested; real comparison awaits replacement and independent assessment review |
| Target identity fully validated | PARTIAL | Original metadata consistent with 39452/2013-067B; no newly accepted GP |
| Temporal pairing qualified | BLOCKED | Preliminary bounds are not a qualified pair or source selection |
| Time qualification completed | PARTIAL | Prior 5,118 ordinary conversions and 2,529 exclusions preserved; full source unresolved |
| IGb08 alignment completed | BLOCKED | No approved realization treatment/parameters/error budget |
| Reference quality assessed | PARTIAL | Prior header/plot review preserved; no accepted epoch-quality interval |
| Provenance assessed | PARTIAL | Claimed provider and source integrity recorded; authentication/availability limited |
| Independence assessed | PARTIAL | Unknown actual GP fitting lineage and possible shared reference inputs disclosed; independence not established |
| Operational adapter qualified | BLOCKED | No accepted input/reference pair or scientific adapter |
| Real residuals generated | NOT STARTED | Required gates blocked; intentionally no real calculation |
| Scientific accuracy independently validated | BLOCKED | No qualified independent comparison; uncertainty unquantified |

No IGb08 transformation, identity approximation, parameter set or tolerance was
invented. Existing GPS precision/second-60 exclusions remain; no timestamp was
rounded to increase coverage. Existing Phase 11 functionality remains intact.

## Actual verification

[Structured evidence](phase-11.3.1-corrected-export-results.json) records commands,
exits, hashes and preservation. `UV_CACHE_DIR` was the task directory under `/tmp`;
script commands used `PYTHONPATH=backend`.

| Newly executed check | Actual result |
| --- | --- |
| Full final backend pytest | **1,073 passed**, zero failures/errors/skips: all 1,033 existing cases plus **40 new** synthetic cases |
| Frontend tests | **344 passed**, 25 files; frontend bytes unchanged |
| Locked sync, Ruff lint/format, ESLint, Prettier, TypeScript, Vite production build, Git whitespace | Passed |
| Existing SGP4 / terrestrial / expanded-science audits | **40 / 6 / 32** passed; numerical verification, not observational accuracy |
| Existing geodesy audit | **28** independent mathematical cases plus **28** round-trips passed |
| Existing golden lifecycle | **6** published components and **3** offline replays passed |
| Three fresh offline helper audits | Missing-replacement gate returns before ledger replay; synthetic semantic match stays PARTIAL; identical report projections; zero network/database/process/propagation/residual/actual-ledger-replay attempts |
| Preservation | All 295 prior nonignored files and 23 private files unchanged; DB bytes/full fingerprint, HEAD and index unchanged |

The initial 35 synthetic tests passed. Initial new-file lint line-length issues
were corrected. Added four malformed-assessment tests; the full 1,072-case suite
passed. Review then made unknown nested metadata an explicit reconciliation stop,
with one new test. The full final 1,073-case suite reran after that code change.
No existing test or scientific check was weakened, removed or skipped. Existing
Starlette/httpx, deliberate duplicate-ZIP and bundle-size advisories remain.

The frontend and scientific CLI results above were executed during this task;
their runtime/source files were unchanged by the subsequent helper-only nested
metadata change. Final backend/helper audits and lint/format cover the final
helper bytes. **Browser/PDF flows were not rerun**, and no earlier remote CI is
claimed to verify these uncommitted changes. No real replacement was parsed,
reconciled, propagated or evaluated; no genuine-source comparison view was replayed.

## Next human action and publication boundary

Manually submit the [prepared correction request](phase-11.3.1-corrected-export-request.md)
through the existing CelesTrak correspondence/provider workflow. Then supply the
original corrected JSON attachment and available non-sensitive receipt/provenance
metadata. No credentials or private email body are needed in Git.

No commit, push, publication, remote CI dispatch/rerun, merge, release, deployment,
DNS or production-infrastructure action occurred. Scientific qualification remains
open. Phase 8 public hosting/HTTPS, independent recovery, real alert delivery,
publication/exact-commit CI and branch-protection gates remain separate milestones.
