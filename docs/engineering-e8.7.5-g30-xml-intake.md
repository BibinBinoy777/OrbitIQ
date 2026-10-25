# E8.7.5 — G30 historical XML intake and strict eligibility

Study `ORBITIQ-IGS-GPS-RETRO-001`. **Intake assessment complete; scientific study
BLOCKED.** Eleven records parse and match G30. Nine pass the original temporal
rule and two fail. **All eleven fail mandatory strict header-content checks:
zero static candidates, zero selected or scientifically accepted records.**

The [evidence ledger](engineering-e8.7.5-g30-intake-evidence.json) contains every
record's exact source epoch/identifiers, raw headers, failed rule IDs, all-epoch
guard counts, acquisition stages and private evidence hashes. This report uses
the unchanged [original G30 protocol v0.1](engineering-e8-comparison-protocol.md),
not the G05 proposal or its inactive admission exception.

## Original and existing capture verified

| Item                                          | Actual evidence                                                                  |
| --------------------------------------------- | -------------------------------------------------------------------------------- |
| Filename                                      | `sat000039533.xml`                                                               |
| Original path                                 | `/workspace/attachments/fb977528-2e35-495e-8654-1fbebd2088ff/sat000039533.xml`   |
| Size                                          | **11057 bytes**                                                                  |
| SHA-256                                       | `34ccec7bd8fd4be88346e03787027a5ecc71a6d75db75668bd4c641fcd713da5`               |
| Reused private original                       | `data/e8.7.5-g30-preflight/dac6dfa44a744a4f815c76915c0f46ee/attachment.original` |
| Original protocol SHA-256                     | `1343e5f145694bc68c49e3f1de2c1ed36009d2450a23ec4cdfe9a670c818cbbc`               |
| Source                                        | User-supplied original, user attributes fulfillment to CelesTrak                 |
| Exact email receipt / request submission time | **UNKNOWN**, not supplied for G30                                                |

Original hash, size and byte identity with the existing capture were checked
before further assessment; the existing capture's receipt and completion manifest
were verified and retained unchanged. No new copy replaced that original. Source
modification timestamp is unchanged. Existing capture time is a storage event,
not email receipt; the G05 request timestamp is not substituted for G30's.

The preliminary identity-only report remains an unchanged historical checkpoint.
This phase completes the remaining default-inspector and record-level assessment
in a separate private evidence directory. Original XML, full GP numerical fields,
private receipt, inspection and all 1056 detailed time checks remain outside Git
and routine CI. No private email account, credential or external scientific
service was accessed. Delivery attribution is not independently authenticated.

## Parsing, structure and identity

The existing `inspect_attachment` was called **without a target override**:
the original default **39533** and its strict rules apply. It reuses the locked
OMM reader, bounded structure checks, exact timestamps, typed numeric helpers and
`Elements.model_validate`. The existing safe capture/read path and original
manifest were reused. No real satellite was initialized or propagated.

- **11 records parsed**, matching the user-reported CelesTrak total **11**.
  No record was dropped or count imposed. No whole-document errors or mixed objects.
- All eleven identify **NORAD 39533 / OBJECT_ID 2014-008A**, name
  **NAVSTAR 69 (USA 248)**. None identifies NORAD 35752. The existing pure
  nominal-date lookup confirms **G30 / SVN G064**, retained assignment
  `2014:052:00000` to open `0000:000:00000`. This is nominal-calendar identity,
  not subsecond qualification of an assignment boundary or source authentication.
- Display name is retained as metadata, not matched to an invented required name.
  Actual COSPAR is present and matches the configured/official identity.
- All required orbital fields, finite numeric/model checks and explicit
  EARTH / TEME / UTC / SGP4 declarations pass; ephemeris type is 0 and
  classification U. No orbital numeric value is repaired or defaulted from the
  G05 case. All source field strings are preserved privately.
- Every EPOCH has exactly **six fractional decimal digits**, no offset suffix,
  with explicit TIME_SYSTEM=UTC. The original strings are preserved, including
  millisecond-separated epochs; no rounding or nearest-time interpretation.
- A **fresh offline schema check** of this actual G30 file and all **11 individual
  OMMs passed** the exact declared SANA NDM/XML 2.0.0 master and eleven pinned
  dependencies. This uses cached official schemas, not a replacement SP3 or GP
  input. No network/schema-hint retrieval occurred during validation.

Supported XML structure and required **orbital** fields pass. The inspector's
combined `structure_and_fields_valid` flag is nevertheless false for every record
because it also includes required **header content**. That combined flag is not
a claim that this well-formed XML failed parsing or its XSD.

## Header and provenance results

Every record's original header contains exactly:

```xml
<CREATION_DATE/>
<ORIGINATOR/>
```

Both are **present-empty**, without attributes or formal `xsi:nil`; neither is
an absent element or a populated invalid value. Raw representations and source
byte offsets for all 22 fields are retained in the ledger.

The exact schema permits empty content. The **active original G30 XML intake
policy** requires nonempty creation/originator values and supported exact creation
time. It therefore reports `missing_or_invalid_required_fields`,
`invalid_header_metadata` and `invalid_creation_date` on all eleven records.
The last error concerns blank message creation, **not invalid EPOCH, malformed
XML or invalid orbital numbers**. No G05 retrospective exception is applied.

Message creation, originator, historical publication/availability and complete
fitting lineage remain unestablished. Element epoch, file capture and the
fulfillment summary do not supply those facts. Independent source/dependency or
forecasting-accuracy claims are unsupported. The XML supplies no explicit
covariance, orbit-quality or manoeuvre flags in this supported profile; their
absence does not prove that no physical event occurred or establish uncertainty.

## Original rules applied and their sources

The original G30 v0.1 requires identity/static/provenance qualification before
record selection. The original E8.1.1 G30 XML adapter implements its active strict
header validation; v0.1 does not restate every adapter-level field check. These
are pre-existing requirements, not conditions imported from G05 or created after
seeing this file. Source/test hashes and complete rule IDs are in the ledger.

| Rule | Requirement / source                                                                   |
| ---- | -------------------------------------------------------------------------------------- |
| S0   | Match original size/hash/private capture and retain all source records                 |
| S1   | Existing bounded OMM structure, required GP fields and static model checks             |
| I1   | NORAD 39533 / COSPAR 2014-008A, nominal dated G30/G064 mapping                         |
| M1   | Active G30 XML inspector: nonempty CREATION_DATE with supported exact UTC parsing      |
| M2   | Active G30 XML inspector: nonempty ORIGINATOR                                          |
| P1   | Original protocol: separate epoch, availability and fitting/source provenance review   |
| T0   | Exact epoch and requested calendar `[2023-12-25T00:00:00Z, 2024-01-01T00:00:00Z)`      |
| T1   | Forward-only from the fixed **first original reference epoch**                         |
| T2   | Inclusive seven-day guard separately at **all 96 original reference epochs**           |
| D1   | Preserve duplicates/conflicts; no same-epoch tie-break or fallback                     |
| C1   | Existing strict static-candidate expression: no candidate if required validation fails |

The unchanged reference is `IGS0OPSFIN_20240010000_01D_15M_ORB.SP3.gz`:
compressed SHA-256
`26f16fa5f97cce851948fa88711aed47f60ee2e4ddfe36f0e98b1076e79fbe38`,
expanded SHA-256
`8a638375273ab74011aebd9ffcc480df02b5718440c8fb7c51c408ff220d231c`.
Both match. No download or replacement was performed.

Original UTC grid: **2023-12-31T23:59:42.000000Z through
2024-01-01T23:44:42.000000Z**, 96 epochs, 900-second cadence. Reused E8 UTC
diagnostics derive from the pinned split-second Astropy GPS/TAI-to-UTC convention
and local leap/EOP resources; no fixed 18-second conversion was introduced.
Only the time tags are reused, not old current-GP verdicts or another target's
quality conclusions. Original SP3 epoch count and endpoints were checked.

For GP epoch E, require `E <= first_reference` and
`abs(reference_i - E) <= 604800 seconds` for every i. Consequently the original
inclusive GP interval remains exactly:

**`[2023-12-25T23:44:42Z, 2023-12-31T23:59:42Z]`.**

The unchanged engine guard and existing G30 fixed-anchor/seven-day regression
test were reviewed. E8's metadata helper can expose partial diagnostic indices;
that does not authorize a reduced arc, changed anchor or relaxed guard.
Existing reference labels 1–96 are retained alongside normalized diagnostic
indices 0–95, without shifting epochs.

## Per-record disposition — all eleven messages

All rows have identity **39533 / 2014-008A**, name NAVSTAR 69 (USA 248), and
`ELEMENT_SET_NO=999`. S0/S1/I1/T0/T1 pass for every row. In the table,
**S/I** means orbital structure/static fields and identity; **M1/M2 fail** means
both required header contents are empty. Full failed IDs and identity fields
are repeated per record in the machine-readable ledger.

| Ordinal / zero-based index | Original EPOCH, UTC          | REV_AT_EPOCH | S/I  | Header M1/M2 | Guard passes / 96 | Temporal | Strict static disposition |
| -------------------------- | ---------------------------- | ------------ | ---- | ------------ | ----------------- | -------- | ------------------------- |
| 1 / 0                      | `2023-12-25T06:18:00.145152` | `7153`       | PASS | FAIL         | 26                | FAIL T2  | REJECTED: M1/M2/T2        |
| 2 / 1                      | `2023-12-25T06:18:00.149472` | `7153`       | PASS | FAIL         | 26                | FAIL T2  | REJECTED: M1/M2/T2        |
| 3 / 2                      | `2023-12-26T06:13:55.672032` | `7155`       | PASS | FAIL         | 96                | PASS     | REJECTED: M1/M2           |
| 4 / 3                      | `2023-12-26T18:11:53.409984` | `7156`       | PASS | FAIL         | 96                | PASS     | REJECTED: M1/M2           |
| 5 / 4                      | `2023-12-26T18:11:53.411712` | `7156`       | PASS | FAIL         | 96                | PASS     | REJECTED: M1/M2           |
| 6 / 5                      | `2023-12-28T06:05:46.637664` | `7159`       | PASS | FAIL         | 96                | PASS     | REJECTED: M1/M2           |
| 7 / 6                      | `2023-12-28T06:05:46.642848` | `7214`       | PASS | FAIL         | 96                | PASS     | REJECTED: M1/M2           |
| 8 / 7                      | `2023-12-29T06:01:42.253536` | `7161`       | PASS | FAIL         | 96                | PASS     | REJECTED: M1/M2           |
| 9 / 8                      | `2023-12-30T05:57:38.010240` | `7163`       | PASS | FAIL         | 96                | PASS     | REJECTED: M1/M2           |
| 10 / 9                     | `2023-12-30T17:55:35.952960` | `7219`       | PASS | FAIL         | 96                | PASS     | REJECTED: M1/M2           |
| 11 / 10                    | `2023-12-31T05:53:33.943200` | `7165`       | PASS | FAIL         | 96                | PASS     | REJECTED: M1/M2           |

All **1056** record/reference time checks were performed using exact datetime
differences, without orbital evaluation. The first two fail the guard at indices
**26–95**, seventy reference instants. The remaining nine satisfy all 96 guard
checks. All eleven lie inside the requested calendar dates and precede the fixed
first reference epoch. The observed date span matches the reported December 25–31
coverage; this does not prove complete archival history.

**Active strict static candidates: 0. Rejected static dispositions: 11.**
No disposition is left ambiguous merely because other provenance questions are
unknown: mandatory header failure is sufficient for rejection under this policy.
No record is nominated, even though the latest supplied epoch is distinct. The
latest-unique rule is only applicable after identity/static/provenance
qualification; source order, element-set/revolution values and expected or actual
residuals are not tie-breakers. No fallback or GP switching.

## Duplicate, identifier and precision review

There are **11 distinct exact epochs**, no exact parsed-record duplicates and no
equal-epoch conflict groups under the active rules. `ELEMENT_SET_NO=999` repeats
across all eleven; revolution values 7153 and 7156 also repeat. These identifiers
do not independently establish archive uniqueness or publication chronology and
are not a new standalone rejection criterion.

Three pairs share a whole-second display prefix but have distinct exact epochs:

- Indices **0/1** differ by **4320 microseconds**. Differing fields: EPOCH,
  ARG_OF_PERICENTER, ECCENTRICITY, MEAN_ANOMALY and MEAN_MOTION.
- Indices **3/4** differ by **1728 microseconds**. Differing fields: EPOCH,
  ARG_OF_PERICENTER, ECCENTRICITY, INCLINATION, MEAN_ANOMALY and MEAN_MOTION.
- Indices **5/6** differ by **5184 microseconds**. Differing fields: EPOCH,
  ECCENTRICITY, INCLINATION, MEAN_ANOMALY, MEAN_MOTION and REV_AT_EPOCH.

This is a source-text/time diagnostic, **not a new tolerance, duplicate definition
or eligibility rule**. No epoch is rounded or grouped for selection. Full original
fields remain private and every record is retained. Their historical generation/
archive relationship remains unknown; no cause, preferred member or physical
equivalence is inferred. These are not the G05 same-epoch revolution-only pairs,
and the separate G05 conflict decisions do not affect G30.

## Ten acquisition/intake stages and remaining science

1. Request submitted: **USER-REPORTED**, exact submission time unknown.
2. Fulfillment notification received: **USER-REPORTED**, reported total 11;
   exact email receipt time unknown.
3. Original attachment/capture verified: **PASS**, existing evidence reused.
4. XML parsed: **PASS for structure/schema**, 11 records; combined strict
   inspector parsing status PARTIALLY VERIFIED because of header content.
5. Satellite identity: **PASS for local metadata consistency**, not transport authentication.
6. Individual metadata: **FAIL required header content for all eleven**;
   broader provenance remains partial/unestablished.
7. Temporal eligibility: **ASSESSED**, nine pass and two fail.
8. Static disposition: **ASSESSED**, eleven rejected, zero candidates, no selected index.
9. Scientific prerequisites: **BLOCKED**.
10. Scientific comparison authorization: **NOT AUTHORIZED**.

Frame/datum realization, TEME-to-terrestrial compatibility, historical EOP/model
treatment, common spacecraft physical point and historical calibration remain
unqualified. G30's producer-statistic discrepancy remains **PARTIALLY RESOLVED**
as recorded in [E8.6](engineering-e8.6-g30-statistic-reconciliation.md); no numerical
uncertainty bound is inferred. Uncertainty/claims, historical creation/fit lineage,
source dependencies, any material archive-history questions, protocol review and
explicit scientific authorization remain separate gates. IGS includes ESA
contributions; separate provider names do not establish independence.

E8.2–E8.6 findings and both G30/G05 protocols remain unchanged. The G05 retrospective
proposal is neither activated nor imported. This report establishes local G30
input availability and its strict rejection outcome; it does not establish
historical forecasting availability or scientifically qualified comparison inputs.

## Actual verification and preservation

- **129 targeted synthetic/fixture tests passed in 11.56 seconds** across the
  historical XML module and IGS feasibility/G30 regression module. These are
  software controls, not acquired scientific evidence or an accuracy result.
- **Fresh G30 schema validation passed** for the original whole XML and all eleven
  OMMs with the cached, pinned 12-file official set. Temporary lxml 6.0.2 /
  libxml2 2.14.6 was reused without changing project dependencies or lockfiles.
- Relevant Ruff lint/Python formatting, Markdown/JSON formatting, local links,
  per-record/all-epoch rule consistency, default-target verification, hashes,
  private manifests/permissions/Git exclusion, privacy, whitespace and complete
  two-file diff checks passed. No application source/test change was needed.
  Full application/frontend/browser/PDF/build/remote CI suites were not run.
- A task-local helper initially used the name `inspect.py`, shadowing Python's
  standard library. It was renamed before private inspection outputs were
  created; no project code, tests, requirements or scientific rule was changed
  to resolve that harness failure.
- Only this report and `engineering-e8.7.5-g30-intake-evidence.json` are new
  repository files. Derived full GP/guard/schema evidence and task harnesses
  remain private and hash-manifested; the original preflight capture is intact.
  All previous reports/protocols/source/locks, branches/HEADs, research/reference
  files and original data remain unchanged. Read-only DB checks preserve schema
  **3**, two snapshots and SHA-256
  `ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
  Local preservation is not independent backup/recovery. Nothing was staged,
  committed, published or deployed.

**Study BLOCKED. No real GP initialization/propagation, spacecraft transformation,
orbital interpolation/extrapolation, residual or new uncertainty calculation.**
Swarm-A Phase 11.3.1 remains **PARTIAL**, scientific evaluation **BLOCKED**;
E4 production readiness remains **OPEN**.
