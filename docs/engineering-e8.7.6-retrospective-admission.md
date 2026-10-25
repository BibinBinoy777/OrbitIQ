# E8.7.6 — Activated retrospective admission and blocker resolution

**Implemented and explicitly applied:** `historical-retrospective-admission-v1`.
The authorized zero-admission blocker is resolved for **six G05 records and nine
G30 records**, admitted **only for further scientific qualification**. Missing
message provenance remains **PARTIAL**. The scientific study remains **BLOCKED**;
no record is scientifically qualified, selected or authorized for comparison.

The [versioned policy](historical-retrospective-admission-v1.md) and
[immutable machine definition](../config/historical-retrospective-admission-v1.json)
specify the scope and executed rules. The
[execution/evidence ledger](engineering-e8.7.6-retrospective-admission-evidence.json)
pins activation, code/definition/source hashes and private result captures.

## Authorization, original data and scope

The user explicitly authorized an executable alternative policy for the two
genuine supplied CelesTrak exports, not another proposal. Both original user
attachments, preserved captures and existing manifests were verified before
policy implementation/application:

| Artifact                                          | Bytes / records | Original SHA-256                                                   |
| ------------------------------------------------- | --------------- | ------------------------------------------------------------------ |
| `sat000035752.xml`, G05 / NORAD 35752 / 2009-043A | 10072 / 10      | `c398ecdc707013d0c9bf245b9eeb1894aef1f2a7bafd60f9a687ce797e0a0828` |
| `sat000039533.xml`, G30 / NORAD 39533 / 2014-008A | 11057 / 11      | `34ccec7bd8fd4be88346e03787027a5ecc71a6d75db75668bd4c641fcd713da5` |

The policy binds each hash to its satellite, size, count and the size/hash of
its existing acquisition ledger. It retains the submitted-request and fulfillment
evidence as **user-reported**, with independent sender authentication, receipt
time, historical publication/availability and full fitting lineage unestablished.
The policy is a bounded OrbitIQ risk-management decision; it does not assert
that empty headers fulfill all semantic OMM requirements.

Definition SHA-256:
`617b281feaa8a8e53338d2bbe7ea8144fca96c4d201c245686b1ef3ac84002d4`.
The inspector enforces this immutable version fingerprint. No unknown/future hash
or provider can inherit the exception. Activation is traceable to the user's
E8.7.6 instruction, date **2026-10-25**, and fresh explicit-policy executions for
both artifacts; private receipts retain actual execution/storage times separately
from email receipt.

## Implementation and preserved strict behavior

The existing [XML inspector](../scripts/inspect_historical_xml.py) still runs its
original strict reader/validators first. Strict mode is the default; G30 remains
the default target. New explicit selection is
`--admission-policy historical-retrospective-admission-v1`, with the existing
`--norad-id 35752` or `39533` target selection.

The added code checks original-byte hash, size, count, identity and pinned
acquisition evidence, applies only the specified present-empty-header exception,
and separately evaluates the unchanged all-96-epoch temporal rule and conflict
holds. It reuses existing exact-epoch/numeric/model helpers and capture/manifest
machinery. It adds no propagation, transformation, database or selection feature.

Every result names the policy/version, strict-policy ID and definition fingerprint.
Each record retains its strict result and gains a separate retrospective outcome.
Legacy strict fields/counts still report **zero static candidates** for these
artifacts; the separately labelled v1 counts report actual admission. This is not
a silent replacement of strict outcomes. Current strict replays and the v1
reports' strict fields were compared with the earlier genuine G05/G30 inspection
results: all prior fields match, apart from the new policy audit fields and the
expected changed source-code fingerprint. Original historical files remain intact.

Empty CREATION_DATE/ORIGINATOR remain unchanged in the XML and report, with
metadata status **PARTIAL — PROVIDER-EXPORTED MESSAGE PROVENANCE UNAVAILABLE**.
Creation/publication/historical-availability values remain null. That status is
separate from admission; it is never converted to PASS. Other missing/invalid
fields, malformed timestamps, identity mismatch or changed input are not waived.

## Actual per-record decisions

All records below remain **REJECTED_STATIC_CANDIDATE under strict mode**.
The v1 column is a separate, active admission result, not scientific selection.

| G05 ordinal / index | Original EPOCH, UTC          | REV_AT_EPOCH | V1 disposition | Reason                                                  |
| ------------------- | ---------------------------- | ------------ | -------------- | ------------------------------------------------------- |
| 1 / 0               | `2023-12-25T21:13:18.902784` | `10520`      | REJECTED       | Outside all-epoch temporal window; also in pair [0,1]   |
| 2 / 1               | `2023-12-25T21:13:18.902784` | `10522`      | REJECTED       | Outside all-epoch temporal window; also in pair [0,1]   |
| 3 / 2               | `2023-12-27T05:25:27.694272` | `10525`      | ADMITTED       | Otherwise valid, all 96 epochs pass; provenance PARTIAL |
| 4 / 3               | `2023-12-28T04:47:54.504096` | `10524`      | HOLD           | Unresolved in-window same-epoch pair [3,4]              |
| 5 / 4               | `2023-12-28T04:47:54.504096` | `10527`      | HOLD           | Unresolved in-window same-epoch pair [3,4]              |
| 6 / 5               | `2023-12-29T06:11:47.963328` | `10529`      | ADMITTED       | Otherwise valid, all 96 epochs pass; provenance PARTIAL |
| 7 / 6               | `2023-12-29T18:40:53.635584` | `10530`      | ADMITTED       | Otherwise valid, all 96 epochs pass; provenance PARTIAL |
| 8 / 7               | `2023-12-30T04:33:03.375360` | `10531`      | ADMITTED       | Otherwise valid, all 96 epochs pass; provenance PARTIAL |
| 9 / 8               | `2023-12-31T04:19:53.685408` | `10530`      | ADMITTED       | Otherwise valid, all 96 epochs pass; provenance PARTIAL |
| 10 / 9              | `2023-12-31T20:06:29.141856` | `10534`      | ADMITTED       | Otherwise valid, all 96 epochs pass; provenance PARTIAL |

**G05: six admitted, two held, two rejected.** The two conflict pairs are not
interchangeable with the two HOLD records: pair [0,1] fails time and remains
REJECTED; only pair [3,4] is in-window and on HOLD. Both members of both pairs
remain individually preserved. Revolution values are not corrected, merged,
preferred or used as a tie-break. No G05 conflict is treated as a G30 issue.

| G30 ordinal / index | Original EPOCH, UTC          | REV_AT_EPOCH | V1 disposition | Reason                                                  |
| ------------------- | ---------------------------- | ------------ | -------------- | ------------------------------------------------------- |
| 1 / 0               | `2023-12-25T06:18:00.145152` | `7153`       | REJECTED       | Only 26 of 96 reference epochs pass age guard           |
| 2 / 1               | `2023-12-25T06:18:00.149472` | `7153`       | REJECTED       | Only 26 of 96 reference epochs pass age guard           |
| 3 / 2               | `2023-12-26T06:13:55.672032` | `7155`       | ADMITTED       | Otherwise valid, all 96 epochs pass; provenance PARTIAL |
| 4 / 3               | `2023-12-26T18:11:53.409984` | `7156`       | ADMITTED       | Otherwise valid, all 96 epochs pass; provenance PARTIAL |
| 5 / 4               | `2023-12-26T18:11:53.411712` | `7156`       | ADMITTED       | Otherwise valid, all 96 epochs pass; provenance PARTIAL |
| 6 / 5               | `2023-12-28T06:05:46.637664` | `7159`       | ADMITTED       | Otherwise valid, all 96 epochs pass; provenance PARTIAL |
| 7 / 6               | `2023-12-28T06:05:46.642848` | `7214`       | ADMITTED       | Otherwise valid, all 96 epochs pass; provenance PARTIAL |
| 8 / 7               | `2023-12-29T06:01:42.253536` | `7161`       | ADMITTED       | Otherwise valid, all 96 epochs pass; provenance PARTIAL |
| 9 / 8               | `2023-12-30T05:57:38.010240` | `7163`       | ADMITTED       | Otherwise valid, all 96 epochs pass; provenance PARTIAL |
| 10 / 9              | `2023-12-30T17:55:35.952960` | `7219`       | ADMITTED       | Otherwise valid, all 96 epochs pass; provenance PARTIAL |
| 11 / 10             | `2023-12-31T05:53:33.943200` | `7165`       | ADMITTED       | Otherwise valid, all 96 epochs pass; provenance PARTIAL |

**G30: nine admitted, none held, two rejected.** Its exact epochs are distinct;
the millisecond-separated source records are not rounded, merged or placed on a
G05-derived conflict hold. Repeated ELEMENT_SET_NO=999 is retained for both files
and is not a unique archive identifier or selection rank.

## Time, selection and scientific boundary

Both source protocols remain unchanged. The frozen reference grid has 96 UTC
epochs, 900-second cadence, from **2023-12-31T23:59:42Z** through
**2024-01-01T23:44:42Z**. Forward-only uses the first original epoch; the inclusive
seven-day guard applies at **every** reference epoch. The unchanged GP interval
is **[2023-12-25T23:44:42Z, 2023-12-31T23:59:42Z]**. No guard, precision rule,
source identity, grid, quality anchor or single-record/latest-unique rule changed.

The first G05 pair passes only 85/96 age checks; the first G30 pair only 26/96.
All other admitted/held rows pass all 96. Those exact guard outcomes agree with
the earlier ledgers. No expected/calculated residual, interpolation or scientific
performance affected admission. No admitted record is automatically selected.

The eight stages are recorded separately in the ledger: original/hash verification,
XML/identity, strict static assessment, explicit policy application, admission for
further qualification, scientific qualification, comparison-record selection,
comparison authorization. Only the first five advance where supported. Scientific
qualified count stays **0**, selected index **null**, authorization **false**.

Still unresolved: frame/datum compatibility; TEME-to-terrestrial and historical
EOP conventions; spacecraft physical reference point/historical calibration;
quality-statistic interpretation and uncertainty limits; record creation/full fit
lineage; source dependencies and independence; G05 conflict explanation; final
protocol review and scientific authorization. G30's E8.6 statistic relationship
remains partially resolved. IGS includes ESA contributions; independent-validation
or historical-forecasting claims remain prohibited. Admission has not recovered
missing provenance or demonstrated orbital accuracy.

## Verification and preservation

- Final targeted run: **160 tests passed in 13.74 seconds**, consisting of the
  existing 129 XML/IGS regressions plus **31 new synthetic policy controls**.
  The earlier 156-test development run preceded four added coverage cases; it is
  not the final verification count. No strict test was weakened or removed.
- Synthetic tests exercise reviewed registry bindings, explicit selection,
  unknown/changed hashes, identity/mixed-content/count/size/evidence mismatch,
  exact full-grid boundaries, missing/invalid fields, partial metadata, duplicate
  holds, G05 conflict/time separation, G30 guard failures, immutable definition,
  CLI refusal/reporting, deterministic outputs and original-file preservation.
  Test-only dependency injection authorizes synthetic byte hashes in memory;
  production config/CLI has no such override. No private GP bytes enter fixtures.
- Real policy execution is separately verified evidence: explicit inspector
  invocations for both actual hash-bound files completed successfully and wrote
  new private exclusive captures, strict replays, result manifests and an
  activation record. Source/code/definition hashes and every disposition are
  cross-checked against original fields and earlier guard findings.
- Relevant lint, Python/Markdown/JSON formatting, local links, source/policy/evidence
  consistency, scope/refusal checks, privacy, whitespace, complete source delta
  and final Git-state checks passed. Full application/frontend/browser/PDF/build/
  remote CI suites were not run. No dependency, lock, database or frontend change.
- Task files: updated inspector; new synthetic test module, machine policy,
  versioned policy document, this report and the evidence ledger. Earlier reports,
  strict results, comparison protocols, existing private data and original XML/SP3
  remain unchanged. Original DB remains schema **3**, two snapshots and SHA-256
  `ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
  No branch/HEAD change, staging, commit, publication or deployment occurred.

**The policy is implemented and applied; the admission blocker is resolved for
15 records with PARTIAL provenance. Scientific comparison remains BLOCKED.**
No real-input propagation, spacecraft transformation, orbital interpolation,
residual or new uncertainty calculation occurred. Swarm-A Phase 11.3.1 remains
**PARTIAL**, scientific evaluation **BLOCKED**; E4 production readiness **OPEN**.
