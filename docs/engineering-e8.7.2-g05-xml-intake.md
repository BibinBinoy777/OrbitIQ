# E8.7.2 — G05 historical XML intake and static eligibility

Study `ORBITIQ-IGS-GPS-RETRO-001`. **PARTIALLY VERIFIED: original supplied XML
captured, parsed and identity matched; strict static eligibility BLOCKED.**
The scientific study remains **BLOCKED**. No real-input propagation, spacecraft
transformation, orbital interpolation/extrapolation, residual calculation or new
uncertainty estimate occurred.

The [evidence ledger](engineering-e8.7.2-g05-intake-evidence.json) records all ten
source-indexed decisions, source hashes, acquisition stages and remaining gates.
The [G05 proposal](engineering-e8.7.1-g05-protocol-proposal.md) and original
[G30 protocol](engineering-e8-comparison-protocol.md) were read before inspection
and are unchanged. XML content was treated as data, not instructions.

## Located original and provenance

| Item                      | Actual evidence                                                                   |
| ------------------------- | --------------------------------------------------------------------------------- |
| Original filename         | `sat000035752.xml`                                                                |
| Size                      | **10072 bytes**                                                                   |
| SHA-256                   | `c398ecdc707013d0c9bf245b9eeb1894aef1f2a7bafd60f9a687ce797e0a0828`                |
| Supplied original         | `/workspace/attachments/fe927def-24b1-44f2-b5ae-8d538be8190e/sat000035752.xml`    |
| Private preserved copy    | `data/e8.7.2-g05-xml-intake/82caacb215304190ab4e33b536e3ad93/attachment.original` |
| Source                    | User-supplied original attachment, asserted CelesTrak fulfillment                 |
| Request submitted         | **2026-10-24T18:08:31Z**, user-reported                                           |
| Actual email receipt time | **UNKNOWN**: reliable message headers/receipt metadata not supplied               |

The attachment's size/hash and original modification timestamp were checked before
and after intake. The source bytes were not rewritten or converted. The existing
safe capture path made a new exclusive private directory, with original, receipt,
inspection and completion manifest. Additional static guard details and a top-level
preservation manifest are private. Capture/storage time is not email receipt.
The user-reported provider origin is not independent authentication of email
transport or the complete GP fitting lineage. No private email/account was accessed.

Raw XML, full GP fields, receipt claims and detailed inspection remain excluded
from Git and routine CI. Public documentation contains the requested identity,
epoch metadata, hashes and assessment, not the original XML or numerical GP sets.
No personal contact information is copied into these documents.

## Actual parsing versus the fulfillment summary

The existing inspector was run with **`--norad-id 35752`**, without `--synthetic`,
using the locked `sgp4.omm.parse_xml` reader and unchanged validation/capture code.
Its exit code **0** means intake completed, not scientific or static acceptance.

- Well-formed namespace-free `ndm`, ten OMM **2.0** messages, ten segments.
  No whole-document parsing errors, unknown structure or mixed objects found.
  This is validation of the existing supported profile, not full CCSDS XSD certification.
- **10 records observed**, matching CelesTrak's **user-reported count of 10**.
  No record was dropped to force agreement. There are **8 distinct epochs**.
- Every record identifies **NORAD 35752 / COSPAR 2009-043A**, name
  **NAVSTAR 64 (USA 206)**. This agrees with retained dated **G05 / SVN G050**
  IGS metadata. The OMM name is not used as the machine identity key, nor are
  PRN/SVN inferred from the display name.
- All explicit declarations are EARTH / TEME / UTC / SGP4, ephemeris type 0,
  classification U. Required GP fields and existing finite/numerical/model
  validation pass. No satellite was initialized.
- Original EPOCH values have exactly **six fractional decimal digits**, no timezone
  suffix, and explicit `TIME_SYSTEM=UTC`. Existing conventions interpret them
  as UTC; no rounding, repair or local-time assumption was applied.
- Actual earliest epoch: **2023-12-25T21:13:18.902784 UTC**. Latest:
  **2023-12-31T20:06:29.141856 UTC**. Their calendar dates agree with the reported
  December 25–31 coverage. That date-range agreement does not establish complete
  history, historical availability or absence of additional producer records.

**Important validation finding:** every OMM header contains blank `CREATION_DATE`
and blank `ORIGINATOR`. These fields are required by the existing strict profile.
The inspector therefore reports `PARTIALLY VERIFIED`, with errors
`missing_or_invalid_required_fields`, `invalid_header_metadata` and
`invalid_creation_date` on every record. The last error refers to the blank
creation field, **not an invalid EPOCH or malformed XML**. Missing publication
or availability timestamps are not fabricated from epochs, submission, receipt
or filesystem time. No validation requirement or test was weakened.

## Every-record eligibility under unchanged rules

The proposed reference is the original 96-epoch, 900-second grid with UTC anchor
**2023-12-31T23:59:42.000000Z** and last epoch
**2024-01-01T23:44:42.000000Z**. The inclusive GP window remains:

**`[2023-12-25T23:44:42Z, 2023-12-31T23:59:42Z]`.**

Each original epoch was tested against **all 96 reference instants** using exact
datetime differences and the inclusive 604800-second guard: **960 static time
checks**, no orbital calculations. All ten GP epochs precede the fixed first
reference epoch and lie inside the requested calendar dates. The first two fail
the all-epoch age requirement; the remaining eight pass the temporal-only test.

| Record / zero-based index | Original EPOCH text, UTC     | Guard passes / 96 | Temporal result          | Additional source finding                      | Strict static result         |
| ------------------------- | ---------------------------- | ----------------- | ------------------------ | ---------------------------------------------- | ---------------------------- |
| 1 / 0                     | `2023-12-25T21:13:18.902784` | 85                | FAIL: before lower bound | Same epoch as record 2, different REV_AT_EPOCH | FAIL: blank required headers |
| 2 / 1                     | `2023-12-25T21:13:18.902784` | 85                | FAIL: before lower bound | Same epoch as record 1, different REV_AT_EPOCH | FAIL: blank required headers |
| 3 / 2                     | `2023-12-27T05:25:27.694272` | 96                | PASS                     | No repeated epoch                              | FAIL: blank required headers |
| 4 / 3                     | `2023-12-28T04:47:54.504096` | 96                | PASS                     | Same epoch as record 5, different REV_AT_EPOCH | FAIL: blank required headers |
| 5 / 4                     | `2023-12-28T04:47:54.504096` | 96                | PASS                     | Same epoch as record 4, different REV_AT_EPOCH | FAIL: blank required headers |
| 6 / 5                     | `2023-12-29T06:11:47.963328` | 96                | PASS                     | No repeated epoch                              | FAIL: blank required headers |
| 7 / 6                     | `2023-12-29T18:40:53.635584` | 96                | PASS                     | No repeated epoch                              | FAIL: blank required headers |
| 8 / 7                     | `2023-12-30T04:33:03.375360` | 96                | PASS                     | No repeated epoch                              | FAIL: blank required headers |
| 9 / 8                     | `2023-12-31T04:19:53.685408` | 96                | PASS                     | No repeated epoch                              | FAIL: blank required headers |
| 10 / 9                    | `2023-12-31T20:06:29.141856` | 96                | PASS                     | Latest supplied epoch, descriptive only        | FAIL: blank required headers |

All records pass numeric NORAD/COSPAR identity consistency; all fail the strict
required-header check. **Temporal-only passes: 8. Strict static candidates: 0.
Scientifically accepted records: 0. Selected source index: null.**

The first two records fail the guard at normalized reference indices **85–95**,
eleven instants. The existing E8 diagnostics label the same 96 reference rows
1–96; the G05 proposal uses normalized indices 0–95. Both labels are retained
in private checks; there is no shifted time grid. Only the existing UTC time
diagnostics are reused, not G30's GP eligibility/exclusions or quality conclusions.
The original SP3 epoch count/endpoints and original hashes were rechecked.

## Repeated epochs, metadata limitations and selection

No identical **parsed-field** duplicate group was found. Two same-epoch pairs,
zero-based **[0,1]** and **[3,4]**, differ only in **`REV_AT_EPOCH`**. This is
revolution metadata, not a basis to prefer either record or a reason to discard
one. The full originals and both records remain preserved. No physical/model
equivalence or scientific independence is inferred from the other fields matching.

The unchanged rule would rank only identity/static/provenance-qualified records
by decreasing epoch and require a unique latest one. Same-epoch ambiguity at
that selection point blocks without fallback or revolution-number tie-break.
Older repeated epochs do not by themselves make every later distinct epoch
ambiguous. Here the header failures leave **no static candidate**, so no record
is nominated, including record 10. No nearest-record, residual-size or scientific
outcome selection occurred. No ambiguity or metadata policy was changed after
seeing the attachment.

The received file resolves the prior absence of a locally inspectable G05
historical-epoch input. It does **not** establish availability in December 2023,
the complete fitting lineage or full scientific eligibility. Blank creation
metadata may reflect unavailable source metadata or the export convention;
this file alone cannot establish the cause. Do not insist a provider can recover
timestamps it does not retain. A useful next step is to clarify the absent-header
semantics and source provenance, or separately review a justified limited
retrospective-intake policy. Any such policy review must preserve original bytes,
unknown timestamps, predeclared temporal/ambiguity rules and restricted claims;
it is not performed by this task.

## Acquisition stages and unresolved science

The E8.7.1 ledger retains its pre-inspection snapshot and now has an additive
`acquisition_follow_up` pointer to this assessment. The current stages are separate:

1. Request submitted: **USER-REPORTED**.
2. Fulfillment notification received: **USER-REPORTED**, receipt time unknown.
3. Original XML captured/hashed: **VERIFIED LOCALLY**.
4. XML parsed: **YES, required-header validation failures remain**.
5. Satellite identity: **PASS for local metadata consistency**, not independent
   source authentication.
6. Static eligibility: **ASSESSED, zero strict candidates** despite eight temporal passes.
7. Scientific prerequisites: **BLOCKED**.
8. Scientific comparison authorization: **NOT AUTHORIZED**.

Remaining requirements are explicitly tracked in the ledger: missing required
message metadata and source provenance, historical availability/full fit lineage,
documented same-epoch multiplicity, IGS20 realization and EOP/subdaily model
compatibility, historical G050 calibration/attitude and common physical point,
G05-specific quality/uncertainty interpretation, source dependencies, protocol
review and explicit calculation authorization. Parsing and matching names do not
establish independence. IGS includes ESA contributions. No independent validation,
forecasting accuracy, absolute truth or safety claim follows from this intake.

## Verification and preservation

- **83 synthetic XML tests passed in 10.61 seconds**, including unchanged G30
  regressions and G05 controls. These tests are not acquired scientific evidence;
  the genuine XML was inspected separately and never copied into test fixtures.
- Existing inspector/test source and dependencies are unchanged. Relevant Ruff
  lint and Python formatting checks passed. Markdown/JSON formatting, local
  links, evidence/source/receipt/manifest hashes, every-record/all-epoch
  decisions, privacy, whitespace and complete diff checks passed.
- Full application/frontend/browser/PDF/build/remote CI suites were **not run**.
  No source-code change required broader application verification.
- The original attachment bytes and modification timestamp, original IGS data
  and both protocol hashes, all previous research inputs, original database,
  branches and HEADs remain unchanged. The database was checked read-only:
  schema **3**, two snapshots, SHA-256
  `ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
  Private capture/inspection/guard files are mode 0600 in 0700 directories and
  are Git-ignored. Local preservation does not prove independent backup/recovery.
- Repository changes: this report and the new intake evidence JSON; one additive
  follow-up in `engineering-e8.7.1-readiness-evidence.json`, with all prior fields
  preserved. The earlier uncommitted implementation/reports are retained.
  Nothing was staged, committed, pushed, deployed or published.

**Scientific study BLOCKED. No propagation, spacecraft transformation, orbital
interpolation/extrapolation, residual or new uncertainty calculation occurred.**
Swarm-A Phase 11.3.1 remains **PARTIAL**, scientific evaluation **BLOCKED**;
E4 production readiness remains **OPEN**.
