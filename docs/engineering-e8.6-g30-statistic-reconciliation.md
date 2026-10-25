# E8.6 — G30 quality-statistic reconciliation

Study **ORBITIQ-IGS-GPS-RETRO-001**, reviewed **24 October 2026**. This is a
documentation and metadata audit. **Scientific study: BLOCKED.** The historical
GP XML for NORAD 39533 remains absent; no GP record was selected or qualified.

Formal SP3 definitions, G30's header indexing, the correct daily table and the
separate global-statistic scopes are resolved. The exact producer-specific
relationship among **Table 1's `3`, Table 3's `2`, and the header's decoded
`4 mm` requires producer clarification**. The available evidence establishes no
data corruption. No orbital comparison or new physical uncertainty was computed.

## Evidence and preservation baseline

This follows the preserved [E8.2 reference qualification](engineering-e8.2-reference-qualification.md),
[E8.4 quality audit](engineering-e8.4-quality-qualification.md) and
[E8.5 provenance assessment](engineering-e8.5-source-provenance.md), their ledgers
and the private `data/e8.4-quality-qualification/g30-quality-record.json`.
The [E8.6 ledger](engineering-e8.6-g30-statistic-evidence.json) contains exact
raw cells, one-based source locators, definitions, parser evidence and outcomes.
No prior report, protocol, data file or source capture was rewritten or downloaded.

The original files were hash-checked **before interpretation**:

| Retained source                             | Bytes  | SHA-256                                                            |
| ------------------------------------------- | ------ | ------------------------------------------------------------------ |
| `IGS0OPSFIN_20240010000_01D_15M_ORB.SP3.gz` | 102609 | `26f16fa5f97cce851948fa88711aed47f60ee2e4ddfe36f0e98b1076e79fbe38` |
| Expanded SP3 bytes                          | 253250 | `8a638375273ab74011aebd9ffcc480df02b5718440c8fb7c51c408ff220d231c` |
| `IGS0OPSFIN_20233650000_07D_01D_SUM.SUM.gz` | 23095  | `2c00cc06449ed72dcb13675813a14f6d8811928f4b84d98fe6aa1eac6cd11870` |
| Existing private G30 quality record         | 213489 | `56a356d883d67a70f3f4b0722f4885343f3b1ca6b553c60926635e03476178bf` |

Original acquisition was through the documented BKG IGS mirror, at
**2026-10-24T05:00:22.757926Z** for SP3 and **05:00:22.758539Z** for the summary;
these are acquisition times, not generation/publication times. The full receipts
are reused in the ledger. Raw products remain private and Git-ignored.

The actual first bytes are **`#cP`**: SP3-**c**, positions. The primary authority is
the retained official [SP3-c specification](https://files.igs.org/pub/data/format/sp3c.txt),
**17 August 2010**, SHA-256
`ac844f38cd1c1a1eafbaa45d7ba0baf89b0787cf307fb42ba645b03dc195da9d`.
The retained [SP3-d specification](https://files.igs.org/pub/data/format/sp3d.pdf),
**21 February 2016**, corroborates compatible fields; it does not change the
actual file's version. The weekly report declares **sum-file Version 2.0**,
which is not a version identifier for its producer executable.

Evidence categories are **direct observation**, **authoritative documentation**,
**inference** and **unknown**. A reported statistic remains a producer statement;
this review did not independently recreate its calculation.

## G30 header mapping and the correct day

The satellite list contains 32 identifiers. **G30 is zero-based index 29,
one-based ordinal 30**. SP3-c has 17 three-character slots per list/header row.
G30 is slot **13** of the second list row, actual SP3 **line 4, columns 46–48**,
raw **`G30`**. Its corresponding accuracy slot is actual **line 9, columns
46–48**, raw **`"  2"`**. This is an index/slot match, not a search for a nearby
number. Header exponent **n=2** decodes by the specification as `2**2 = 4 mm`.
It is the satellite/file-wide standard-deviation-intended orbit-error indicator;
it is not a per-axis sigma or a maximum error guarantee. Header **zero means
unknown**, despite the arithmetic expression `2**0` equalling one.

The original header identifies GPS week **2295**, week-seconds **86400**, MJD
**60310**, GPS-calendar **2024-01-01**, 96 epochs at 900-second intervals.
The matching summary section is **Table 3.2295.1**, heading at expanded summary
**line 689**, explicitly **Day 1 / MJD 60310.000**. Source line numbers refer to
the exact decompressed ASCII bytes, not rendered webpage lines.

**Table 3.2295.0** at line 648 is the preceding GPS day, MJD 60309. Its G30
orbit-dynamics IGS entry is **22**, and its total/non-eclipsing IGS entries are
**38/31**. They are retained only as a wrong-day control. The correct January 1
values are **25** and **33/29**. These are GPS-calendar day labels; no UTC
relabeling or fresh epoch conversion occurred.

## Per-satellite values and their definitions

All columns are one-based and inclusive. The weekly table explicitly declares
**mm**; that printed unit does not by itself prove how every integer was encoded
or derived in the generator.

| Source / row / column                                  | Exact source value and location                                    | Statistic and scope                                                                 | Interpretation status                                                                   |
| ------------------------------------------------------ | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| SP3 `++` header / ordinal 30                           | Raw `"  2"`, line 9 cols 46–48                                     | Header exponent; decoded format indicator **4 mm**                                  | **RESOLVED** definition and indexing; no empirical calibration inferred                 |
| Table 1.2295.b / PRN30 / day 1                         | `3`, line 498 col 17                                               | Combined-orbit satellite position sigma, labelled mm                                | **PARTIALLY RESOLVED**: reported meaning known; exact mapping to Table 3/header unknown |
| Table 3.2295.1 / PRN30 / Weighted Average → IGS        | `2`, line 723 col 67                                               | Caption calls this the resulting satellite accuracy measure found in the SP3 header | **REQUIRES PRODUCER CLARIFICATION** for raw exponent vs decoded/derived statistic       |
| Table 3.2295.1 / PRN30 / Orbit Dynamics (7 days) → IGS | `25`, line 723 cols 130–131                                        | RMS fit of the combined IGS orbit through the seven-day evaluation                  | **RESOLVED** as a distinct reported fit statistic, not a true-error bound               |
| First G30 P record / X, Y, Z sigma fields              | Raw `" 8"`, `" 4"`, `" 5"`, SP3 line 53 cols 62–63 / 65–66 / 68–69 | Per-coordinate, per-epoch exponents, using the file's base **1.25**                 | **RESOLVED** format interpretation only                                                 |

For completeness, the G30 AC/comparator entries at summary line 723 are preserved
in the ledger with their column names and exact field locations. In column order
**cod, emr, esa, gfz, grg, igr, jgx, jpl, mit, ngs, sio, IGS**, they are:

- Weighted Average: **7, 13, 6, 6, 5, 3, 7, 11, 5, 8, 10, 2**.
- Orbit Dynamics (7 days): **22, 34, 26, 26, 24, 25, 25, 35, 24, 27, 28, 25**.

These are transcriptions of existing statistics, not new calculated differences.
The AC weighted-average entries describe daily fits relative to the combination;
the final first-side IGS column has its special accuracy-indicator caption.
Do not interpret that `2` as an ordinary AC-to-combination RMS. Nonblank values
also do not prove nonzero contribution weight; E8.5's exclusions remain in force.

## Global RMS/WRMS: read each half of the table separately

The global rows aggregate satellite/evaluation statistics for each column's
solution. They are not G30-only indicators. Crucially, the row labels on the two
halves differ:

- **Line 727:** left **RMS** under Weighted Average; right **T** under Orbit
  Dynamics. The caption defines T as total long-arc orbit RMS for all satellites.
- **Line 728:** left **WRMS** under Weighted Average; right **NE** under Orbit
  Dynamics. NE means long-arc RMS for non-eclipsing satellites. **NE is not WRMS.**

Exact day-1 entries, all table-labelled **mm**:

| Solution column | Weighted Average: RMS | Weighted Average: WRMS | Orbit Dynamics: T | Orbit Dynamics: NE |
| --------------- | --------------------- | ---------------------- | ----------------- | ------------------ |
| COD             | 7                     | 6                      | 34                | 29                 |
| EMR             | 9                     | 9                      | 36                | 32                 |
| ESA             | 8                     | 8                      | 35                | 30                 |
| GFZ             | 11                    | 9                      | 35                | 29                 |
| GRG             | 8                     | 7                      | 35                | 30                 |
| IGR             | 4                     | 3                      | 34                | 29                 |
| JGX             | 9                     | 9                      | 35                | 30                 |
| JPL             | 25                    | 25                     | 38                | 34                 |
| MIT             | 7                     | 6                      | 32                | 28                 |
| NGS             | 10                    | 9                      | 34                | 29                 |
| SIO             | 9                     | 8                      | 36                | 31                 |
| IGS             | blank                 | blank                  | **33**            | **29**             |

The left-hand IGS RMS/WRMS fields are **blank**, not zero or the G30 `2`.
The IGS right-hand values are at **line 727 cols 130–131 (`33`)** and
**line 728 cols 130–131 (`29`)**. Calling the latter a global IGS WRMS would
misread the table. No new RMS, weighted average or aggregation was calculated.

The report's statistics discussion says WRMS uses normalized weights based on
SP3 accuracy codes. It flags `X` rows as excluded from statistics but retained
in the orbit file; missing values and evaluation eligibility also matter. The
exact population/normalization and producer algorithm are not reconstructed here.
“All satellites” is the source's T-caption description, not a new assertion that
every one of the file's 32 objects contributes to every statistic with equal
weight. Neither these aggregates nor their numerical relationship to G30 supplies
a per-epoch reference uncertainty, calibrated truth error or GP comparison bound.

## Formal field rules and the installed inspector

SP3-c introduction and explanatory paragraphs, and compatible SP3-d definitions,
establish separate representations:

| Representation               | Rule                                                                     | Special values and limit                                                                                     |
| ---------------------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------ |
| Header satellite accuracy    | `2**n mm`, same slot as satellite ID                                     | n=0 means unknown; file-wide, one-standard-deviation intention, not a bound                                  |
| P coordinate sigma           | `b**n mm`; base at `%f` line 15 cols 4–13, actual raw `" 1.2500000"`     | n=0 gives 1 mm; blank unknown; **99** too large to represent, not a finite decoded sigma                     |
| P clock sigma                | Clock base **1.025** at line 15 cols 15–26; code in cols 71–73; units ps | Zero gives 1 ps; blank unknown; **999** too large; unused for position interpretation                        |
| Optional EP coordinate sigma | Direct integer mm in cols 5–8 / 10–13 / 15–18                            | Blank unknown; **9999** too large; no zero-variance inference                                                |
| Optional EP correlation      | Integer / **10,000,000**, dimensionless                                  | Blank/absent unknown; not assumed zero; correlation fields do not establish cross-time/provider independence |

There are **96 G30 records, 288 populated ordinary coordinate-sigma codes**,
and **zero EP records**. The original 96 raw quality blocks remain in the private
hash-pinned record; no duplicate public ephemeris or private evidence bundle is
created. The first code triple represents `1.25**8`, `1.25**4`, `1.25**5` mm by
format only. G30's lack of unknown/censored fields does not qualify its physical
uncertainty or prove consistency with a generator statistic.

The available parser is the unchanged
[IGS feasibility inspector](../scripts/inspect_igs_reference.py), function
`inspect_sp3`. Static source inspection confirms that it:

- Requires `#cP`, the supported IGS20/GPS/FIN profile and the expected header
  structure; flattens ID and accuracy slots in corresponding order.
- Exports **raw header exponents**, with the rule `2**exponent mm` and explicit
  zero-as-unknown semantics. It does not replace raw exponent 2 with a literal
  2-mm error.
- Reads the actual base and requires 1.25; extracts P-axis fields at the correct
  fixed columns, retaining code counts and blank-sigma exclusions. Its output
  rule correctly distinguishes P zero from header zero.
- Does not decode a weekly SUM table, compute scientific errors, construct
  covariance or accept scientific epochs. It cannot settle producer encoding.

This is a **narrow feasibility profile**, not full SP3 conformance: it requires
80-column P records, does not parse optional EP, and its short axis-rule text
does not enumerate the **99** censoring case. Such a code is retained as a raw
count, not decoded; future quantitative use would need the full specification
and explicit exclusion handling. G30 has no such code. These limitations prevent
a blanket parser/uncertainty qualification; **no demonstrated misinterpretation
of the acquired G30 fields requires a source change in this phase**.

Twenty-five existing deterministic synthetic parser tests passed. They check
layout, zero-code handling, unsupported/malformed profiles, hashes, flags and
explicit missing-sigma handling. They do not certify producer processing or
scientific accuracy. No real GP was initialized or selected by these tests.

## Reconciliation outcomes

Statuses mean: **RESOLVED** — definitions and source fields agree for the stated
question; **PARTIALLY RESOLVED** — some meanings are established but a material
relationship remains unknown; **REQUIRES PRODUCER CLARIFICATION** — retained
specifications/reports do not establish the exact producer relationship.

| Question                                                | Outcome                             | Remaining qualification                                                                    |
| ------------------------------------------------------- | ----------------------------------- | ------------------------------------------------------------------------------------------ |
| Correct version, G30 slot and daily table?              | **RESOLVED**                        | `#cP`, ordinal 30, Day 1/MJD 60310; not Day 0                                              |
| Raw header `2` meaning?                                 | **RESOLVED**                        | Valid exponent → 4-mm format indicator; no calibrated bound                                |
| Weekly G30 values and reported scope?                   | **PARTIALLY RESOLVED**              | Raw 3 and 2 retained; Table 3's exact encoding/statistic link unknown                      |
| Seven-day IGS G30 `25` meaning?                         | **RESOLVED**                        | Distinct long-arc fit statistic, not absolute error                                        |
| Global RMS/WRMS vs T/NE scope?                          | **RESOLVED**                        | AC aggregates; IGS weighted-side fields blank; dynamics T=33, NE=29                        |
| Per-epoch sigma/EP definitions and availability?        | **RESOLVED**                        | Field meaning/absence, not uncertainty calibration                                         |
| Existing inspector agrees with actual supported fields? | **PARTIALLY RESOLVED**              | Correct slots/rules for this file; documented narrow-profile limitations                   |
| Exact `3`/`2`/`4 mm` relationship?                      | **REQUIRES PRODUCER CLARIFICATION** | Statistic/encoding/rounding and immutable run/revision linkage missing                     |
| Quantitative scientific use without further evidence?   | **PARTIALLY RESOLVED**              | Format decoding/transcription allowed; comparison bounds/covariance/confidence unsupported |

Different scopes fully explain why **25**, **33**, **29**, a per-axis sigma and a
file-wide header indicator are not interchangeable. They do **not** establish
whether Table 3's G30 `2` is an exponent, a decoded quantity or another generator
statistic, or how it relates exactly to Table 1's `3` and the encoded header.
The G08 control remains header raw `"  2"` vs Table 3 first-IGS `5` (line 701
col 67); it rejects assuming a verbatim exponent column from G30 alone.

Quantization is a possible explanation of some magnitudes, not a demonstrated
producer rule. No forced sqrt(3) conversion, guessed rounding convention,
smallest-value selection or uncertainty estimate is justified. **No data
corruption or inconsistency is established.** No correction to E8.4's recorded
values or formal decoding is warranted. This dated E8.6 follow-up adds global
scope and parser-limit detail; E8.4/E8.5 remain unchanged.

### Prepared question to IGS ACC — not sent

> For `IGS0OPSFIN_20240010000_01D_15M_ORB.SP3.gz` (GPS week 2295, day 1,
> MJD 60310, compressed SHA-256
> `26f16fa5f97cce851948fa88711aed47f60ee2e4ddfe36f0e98b1076e79fbe38`),
> G30 is satellite ordinal 30 and its `++` field is raw `  2`, decoded by
> SP3-c as 4 mm. The associated
> `IGS0OPSFIN_20233650000_07D_01D_SUM.SUM.gz` (SHA-256
> `2c00cc06449ed72dcb13675813a14f6d8811928f4b84d98fe6aa1eac6cd11870`)
> reports G30/day 1 as `3` in Table 1.2295.b and `2` in the first IGS column
> of Table 3.2295.1, whose caption links it to header accuracy measures and
> labels the table mm. What exact statistic, unit, encoding and rounding does
> each value use, and what generator version/revision links these files?
> G08's header code is also `2`, whereas its first IGS table entry is `5`;
> is that column a physical-mm statistic, raw code or another derived measure?
> Please distinguish these from G30's last-IGS seven-day RMS `25`, global
> IGS T `33` and NE `29`, and confirm the populations/normalization used for
> global RMS/WRMS/T/NE. Is there a versioned algorithm/encoder description?

No email, provider request, login or external-service access occurred in E8.6.

## Verification and remaining boundaries

Only this report and its ledger are new repository files. The branch remains
`engineering-e8.2-igs-reference-qualification`, HEAD
`b0a03205e3930b55651232d8b7ffbc9e879ae8c6`. No application, parser, test,
dependency, protocol or existing report changed.

Actual verification:

- **25 passed, 21 deselected** in the existing E8 test module, using only
  deterministic synthetic parser fixtures; JUnit evidence is explicitly named
  `SYNTHETIC-parser-tests.xml`. No synthetic fixture is acquired science.
- Source/ledger checks covered G30 indexing, 24 per-satellite and 48 global table
  fields (including two blanks), correct/wrong-day anchors, definitions, all
  96 private raw G30 quality blocks and 288 axis-code slices, parser source
  locations/hash and the recorded reconciliation statuses.
- JSON, Markdown/JSON formatting, local links, whitespace, privacy-pattern and
  complete two-file diff checks passed. No new network acquisition was needed.
- All **380 originally tracked files**, eight prior E8.2–E8.5 additions and the
  separate E8.1.1 additions remain unchanged. The four worktree branches/HEADs,
  **99** earlier private-manifest entries and **72 original private files** are
  preserved. Read-only database checks confirm schema **3**, two snapshots and
  SHA-256 `ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
  Original reference hashes above remain unchanged.
- Full backend/frontend suites, browser/PDF, build and remote CI were not rerun;
  earlier verification is not claimed as fresh. Nothing was staged, committed,
  pushed or deployed. Local preservation is not independent backup.

**No propagation, spacecraft-state transformation, orbital interpolation/
extrapolation, residual or new uncertainty calculation occurred.** Producer
clarification, the missing historical GP and essential frame/EOP/point/quality/
provenance/protocol qualifications still block the study. Source independence is
not inferred. Swarm-A Phase 11.3.1 remains **PARTIAL**, evaluation **BLOCKED**;
E4 production readiness remains **OPEN**.
