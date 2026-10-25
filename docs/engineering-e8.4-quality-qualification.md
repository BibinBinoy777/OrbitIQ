# E8.4 — IGS quality indicators and uncertainty qualification

Study **ORBITIQ-IGS-GPS-RETRO-001**, 24 October 2026.
**Scientific study: BLOCKED. Indicator reconciliation: PARTIALLY EXPLAINED.**
This is an audit of supplied reference-quality metadata, not a comparison or a
new measurement of orbital accuracy. No historical GP record has arrived or been
selected. No real-input propagation, frame transformation, orbital interpolation,
antenna correction or residual calculation is performed.

## Scope and source evidence

Work stays on `engineering-e8.2-igs-reference-qualification`, HEAD
`b0a03205e3930b55651232d8b7ffbc9e879ae8c6`, in `/workspace/OrbitIQ-e82`.
The four existing E8.2/E8.3 additions and all other worktrees are preserved.
Only this report and the [E8.4 evidence ledger](engineering-e8.4-quality-evidence.json)
are new repository files. No application, shared parser, test, dependency, workflow
or protocol is changed.

This extends the [E8.2 qualification](engineering-e8.2-reference-qualification.md),
[E8.3 frame/EOP audit](engineering-e8.3-frame-eop-qualification.md) and unchanged
[protocol v0.1](engineering-e8-comparison-protocol.md). It does not rewrite their
historical findings or promote any scientific gate because a field can be decoded.

Evidence categories are **D: directly verified**, **P: authoritative documentation**,
**I: inference**, and **U: unknown**. The ledger records these categories, exact
versions where available, raw-evidence locators, statuses and closure requirements.

| Source                                                                                                                                             | Applicable definition and scope                                                                                              |
| -------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| [SP3-c specification](https://files.igs.org/pub/data/format/sp3c.txt), **17 August 2010**                                                          | Primary format: introduction, header accuracy slots, P/EP tables and explanatory paragraphs. Actual file declares `#cP`.     |
| [SP3-d specification](https://files.igs.org/pub/data/format/sp3d.pdf), **21 February 2016**                                                        | Corroborates compatible fields; its increased satellite/comment limits do not change this file into SP3-d.                   |
| [IGS products](https://igs.org/products/), final-GPS table and Note 1                                                                              | General product-class statistic; retained capture, not a per-G30-epoch validation receipt.                                   |
| [Week-2295 summary](https://igs.bkg.bund.de/root_ftp/IGS/products/2295/IGS0OPSFIN_20233650000_07D_01D_SUM.SUM.gz), sum-file Version 2.0            | Products Generated, Tables 1.2295.b and 3.2295.1; a format version is not an exact generator software revision.              |
| [IGS products guide](https://files.igs.org/pub/resource/pubs/UsingIGSProductsVer21.pdf), **May 2009**, §5.1.1                                      | General precise-GPS center-of-mass convention, retained in E8.2.                                                             |
| [Metadata SINEX](https://files.igs.org/pub/resource/working_groups/multi_gnss/Metadata_SINEX_1.10.pdf), **1.10, 30 September 2024**, §§1.1 and 3.5 | CoM, eccentricity and antenna-reference-point conventions.                                                                   |
| [ANTEX specification](https://files.igs.org/pub/data/format/antex14.txt), **1.4, 15 September 2010**                                               | Newly retrieved public format definition: satellite-fixed PCO sign/units, identifiers, absolute/relative PCV and SINEX code. |
| Retained `igs20.atx` and correct IGSMAIL-8238                                                                                                      | Actual current calibration metadata and IGS20 antenna-model context, not proof of the exact 2024 processing input.           |

Existing source captures were reused, not downloaded again. The new ANTEX
specification is 23,668 bytes, SHA-256
`86458154367916d2fa6282ca2f8e5137c3d9663d7c18eb44eaf344c8e7eba621`.
Its server advertises UTF-8 but the original bytes do not decode as UTF-8. An
ISO-8859-1 review-only text view was used; original bytes and receipt were kept
unchanged. This document-decoding issue does not alter any scientific timestamp,
SP3 field or ANTEX model value.

## Actual product and the G30 raw evidence record

**D:** the retained file is `IGS0OPSFIN_20240010000_01D_15M_ORB.SP3.gz`: SP3-c
positions, IGS combined final, **IGS20**, **GPS time**, **900-second cadence**,
**96 epochs**, **32 IDs**, **3,072 P records**. All actual P records have 80 columns;
there are no V or EP records. No file was rewritten, regenerated or downloaded.

The intended study target remains **G30 / G064 / NORAD 39533 / 2014-008A** from
prior identity evidence. This does not qualify a missing GP record's identity.

A private, machine-readable actual-quality record is retained at:

`data/e8.4-quality-qualification/g30-quality-record.json`

It contains all **96 original G30 quality blocks**, raw GPS epoch tags, one-based
source line/column locators, exact header/base fields, raw flags and source-code
decodings. It exports **no XYZ coordinates or clock-correction values**. The
ledger records its size/hash; it is ignored, not a test fixture or ordinary CI
artifact. The original compressed source remains the authority for original bytes.

**D:** G30 covers the full original GPS-tag grid, from
`2024-01-01T00:00:00.00000000` to `2024-01-01T23:45:00.00000000`, without duplicate
epochs or missing P records. These are GPS labels, not UTC. The existing UTC
mapping is preserved in E8/E8.3; no conversion or new sampling is needed here.

## Formal fields, units and special values

All column numbers below are **one-based and inclusive**. Fixed-column widths
matter; missing values are not replaced with zero.

| Field                                 | Source location                                                   | Formal meaning                                                                                            | Zero, blank, sentinel and validity rules                                                                                                                                                       |
| ------------------------------------- | ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Satellite/file accuracy exponent      | SP3-c `++` header lines 8–12; same slot as ID in lines 3–7        | `2**n mm`; intended one-standard-deviation orbit-error indicator over the satellite's whole file          | **Zero means unknown**, not 1 mm. Blank/invalid active fields have no supported quantitative interpretation here. No producer encoder-rounding rule is specified by merely decoding the field. |
| Position sigma base                   | First `%f`, actual line 15, columns 4–13                          | Base `b` for component sigma codes; actual raw value is `1.2500000` with field padding retained privately | Unknown/invalid base prevents decoding. Do not assume a base from another file.                                                                                                                |
| Per-epoch X/Y/Z sigma exponents       | P **62–63 / 65–66 / 68–69**                                       | Reported component standard deviations at that epoch, `b**n mm`                                           | **Zero means 1 mm**; blank means unknown; **99 means too large to represent**, not `b**99`. Invalid codes stay unresolved.                                                                     |
| Clock sigma exponent                  | P **71–73**, base from `%f` **15–26**                             | Reported clock standard deviation, `b_clock**n` **picoseconds**; actual base 1.025                        | Zero gives 1 ps; blank unknown; **999** too large. This is distinct from the clock-correction field's µs and is not position uncertainty. No clock sigma is used in a position budget here.    |
| Optional EP X/Y/Z standard deviations | EP **5–8 / 10–13 / 15–18**                                        | Direct integer **mm**, not exponent codes                                                                 | Blank unknown; **9999** too large. The introduction states a 1..9999 positional range; zero is not assigned a zero-variance meaning here. No EP value exists in this product.                  |
| Optional EP clock standard deviation  | EP **20–26**                                                      | Direct **picoseconds**                                                                                    | Blank unknown; **9999999** too large. It is absent here.                                                                                                                                       |
| Optional EP correlations              | EP **28–35 xy, 37–44 xz, 46–53 xc, 55–62 yz, 64–71 yc, 73–80 zc** | Signed integer divided by **10,000,000**, dimensionless, representable range −0.9999999..+0.9999999       | Blank unknown. An explicitly supplied valid zero coefficient would be zero; absent EP/correlation fields are **not** zero.                                                                     |
| Bad/absent coordinates and clock      | P coordinate/clock value fields                                   | SP3-c specifies zero positional markers and clock `999999` with optional fractional nines                 | A coordinate zero is not used here to fabricate missing data; no G30 zero-coordinate candidate occurs. Clock absence does not create a missing position.                                       |

**P/D:** SP3-c permits omitted trailing P columns and defines them as blanks.
The actual file already has 80-column records, so no padding or source repair
was performed. The existing E8 inspector is a deliberately narrow profile, not
a general validator for every legal SP3-c variant.

SP3-d repeats the compatible sigma/correlation definitions but is corroborating
documentation only. The actual `c` version character controls this audit.

## G30 interpretation: resolved definitions, limited quantitative use

**D/P:** the raw G30 header field is **`"  2"`**, at actual source **line 9,
columns 46–48**. Its valid format decoding is **`2**2 = 4 mm`**. It is a satellite/
file-wide quality indicator, not a 4-mm bound at every epoch or a coordinate sigma.
The format says the quoted error should represent one standard deviation over
the file. The producer summary says header codes are based on daily-arc weighted
RMS. Neither statement independently calibrates this particular encoded value.

**D/P:** all **288** G30 coordinate-sigma fields are populated and contain ordinary
codes. X exponents span **1–8**, Y **3–6**, Z **1–7**, with 96 values per axis.
The first actual quality triple is raw **`" 8" / " 4" / " 5"`**, at source line 53;
it means the reported-code values `1.25**8`, `1.25**4`, `1.25**5` **mm** for X/Y/Z.
The private record decodes each valid code using Decimal arithmetic. Exact decimal
strings represent the code formula, **not measurement precision or physical truth**.
No variance, RMS from orbital differences, covariance or confidence interval is
calculated. A component/epoch code may decode above the whole-file indicator;
the whole-file standard-deviation intention is not an upper bound.

G30 has no blank, zero or 99 coordinate-sigma codes. Its 96 clock-sigma fields
are populated and retained raw; they are not used as coordinate uncertainty.
G30 has no missing-clock or zero-coordinate markers. There are **zero EP records**,
so same-epoch coordinate correlations and a full position/clock covariance remain
unavailable. Unknown correlations cannot be replaced with independence or a
diagonal covariance. Even valid EP would not itself supply cross-time or
cross-provider dependence.

**D:** availability is not uniform across the full file: blank XYZ sigma fields
total **40 X, 40 Y, 56 Z**, on other satellites. G27 has **96 missing-clock
markers**. These do not imply that G30 is missing records, and G30's complete
basic fields do not make the entire constellation quality-complete.

### Flags and the meaning of blank

| P flag           | Column | Marked value                                                | Blank meaning in SP3-c                          |
| ---------------- | ------ | ----------------------------------------------------------- | ----------------------------------------------- |
| Clock event      | 75     | `E`: discontinuity since previous epoch or at current epoch | No event **or unknown** whether one occurred    |
| Clock prediction | 76     | `P`: predicted correction                                   | “Observed” correction in the format             |
| Orbit maneuver   | 79     | `M`: maneuver since previous epoch or at current epoch      | No maneuver **or unknown** whether one occurred |
| Orbit prediction | 80     | `P`: predicted position                                     | “Observed” position in the format               |

**D:** all four G30 flag fields are raw **single blanks** at all 96 epochs.
**P/U:** the format's “observed”/prediction distinction does not turn a combined
estimated orbit into directly measured Cartesian positions, prove accuracy, or
establish that no physical event occurred. A summary-table eclipse suffix `E`
also is not the P-record column-75 clock-event flag.

## The differing 3 / 2 / 4 indicators

| Actual source                              | Raw evidence                                     | Established interpretation                                                                                                                                       |
| ------------------------------------------ | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| G30 SP3 header                             | `"  2"`, source line 9, columns 46–48            | Exponent **2**, valid format indicator **4 mm**                                                                                                                  |
| S8 Table 1.2295.b, PRN30, day 1            | Raw **`3`**, summary line **498**, column **17** | The table explicitly labels daily satellite-position sigmas in **mm**. Do not decode this reported value as exponent 3.                                          |
| S8 Table 3.2295.1, first IGS column, PRN30 | Raw **`2`**, summary line **723**, column **67** | Caption calls it a satellite accuracy measure found in the header; the table labels units **mm**. Exact mapping to this SP3's code/statistic remains unresolved. |

**Resolved (D/P):** the SP3 header and per-epoch coordinate indicators have
different definitions, scope, bases and zero semantics. They are not contradictory
merely because their decoded numbers differ. The Table 1 value is labelled in mm,
not as an exponent. The Table 3 raw integer must not be interpreted as an exponent
solely because G30's raw header happens also to contain `2`.

**D:** a literal-copy sanity check on this same file/table pair finds **G08 header
raw `"  2"` versus Table 3 first-IGS raw `5`** (summary line 701, column 67).
Therefore a verbatim header-exponent interpretation of that entire table column
is not justified from the G30 coincidence. This is a metadata check, not an orbit
comparison or a satellite substitution.

**I/U:** coarse encoding could explain some numerical differences, but the actual
producer's rounding/encoding rule, exact statistic relationship and immutable
generation/revision linkage for the supplied SP3/SUM pair are not established.
Nominal week/day agreement is not that provenance. The format alone does not
prove that a particular rounding rule produced code 2 from reported 3 mm, or
explain the Table 3 entry. No contradiction or corruption has been established.

The result is **PARTIALLY EXPLAINED**: formal SP3 field questions are resolved;
the exact weekly-summary-to-SP3 processing relationship is not. Needed evidence
is a product-specific producer definition or versioned generator/encoding account
and revision linkage. Do not choose the smallest value, treat the summary's `2`
as a code, or introduce a `sqrt(3)` factor to force agreement without that evidence.

## Product-class accuracy versus a comparison uncertainty

**P:** the retained IGS final-GPS table quotes approximately **2.5 cm**. Note 1
defines orbit accuracies as **1D mean RMS over the three XYZ geocentric components**
and describes validation using laser-ranging comparisons and consecutive-day
discontinuities. This is the published product-class description, not a newly
measured result, a guarantee for G30 at each epoch, a 3D radius, or a historical
2024 product-specific calibration. No matched independent G30 truth/SLR arc was
acquired here.

Keep five levels separate:

1. The published class-level figure and its stated validation scope.
2. This file's G30 whole-file header indicator.
3. Its source-reported per-coordinate/per-epoch sigma codes.
4. A future **pair's** uncertainty, which is not established by any of the above.
5. Unquantified frame/EOP, model, reference-point, calibration, fit and shared-source
   effects that those fields do not demonstrably cover.

**U:** GP covariance, GP/reference cross-covariance, joint/time-dependent reference
covariance, error calibration and distribution assumptions are unavailable or
unqualified. Different provider names or IGS internal checks do not prove
independence. No calibrated combined uncertainty budget, normalized residual,
confidence interval, “95%” statement, three-dimensional error bound, 96-independent-
sample inference, collision/anomaly conclusion or cm-agreement claim is supported.
Do not promote code quantization or output decimal resolution to physical accuracy.

## Reference point and antenna calibration

**P:** the May-2009 IGS guide §5.1.1 says precise-GPS coordinates refer to the
satellite CoM; Metadata SINEX 1.10 §§1.1/3.5 supplies further CoM/eccentricity
context. The new ANTEX 1.4 definition explicitly relates satellite mean phase
center to **CoM plus an offset in a satellite-fixed, right-handed frame**. Its
`NORTH / EAST / UP` record uses satellite X/Y/Z offsets in **mm** for satellites,
not a terrestrial NEU correction. PCO/PCV, frequency, attitude and historical
calibration matter; the model's existence alone does not define an arbitrary
orbit product's physical point.

**D:** the already retained current `igs20.atx` declares format **1.4**, mixed
system **M**, absolute PCV code **A**. Its inspected entry identifies **BLOCK IIF /
G30 / G064 / 2014-008A**, with raw validity starting **2014-02-21**, method-date
field **29-JAN-17**, and **`SINEX CODE IGS20_2437`**. These metadata are preserved
privately without exporting or applying numeric PCO vectors. `G01`/`G02` in its
frequency blocks are frequency codes, not different satellites.

**U:** the pre-2024 validity start and old method date do not prove historical
availability, exact calibration revision or use by the week-2295 combination.
The October-2026 capture is not established as its exact 2024 ANTEX input. The
SP3 has no standalone physical-point flag providing that processing proof.
Published general CoM evidence is affirmative but pair compatibility remains
**PARTIAL**: the actual precise-product convention and GP fitted point need
applicable evidence. A GP/TLE state is not automatically GPS broadcast-navigation
APC, and an antenna file cannot establish its fitted point.

Before any physical-point correction, establish the needed historical calibration,
frequency combination, attitude and CoM conventions, or justify no correction.
No offset, point transformation or generic broadcast-to-CoM correction is applied.
Earth geocenter, satellite CoM, mechanical ARP and mean phase center are distinct.

## Qualification matrix and next work

The ledger's 14 items include raw-evidence locators, sources/versions/categories,
known limitations and required next evidence. Summary statuses are:

| Requirement                              | Status      | Scope of the finding                                                        |
| ---------------------------------------- | ----------- | --------------------------------------------------------------------------- |
| SP3 version applicability                | **PASS**    | Actual c file and applicable specification identified                       |
| Header accuracy semantics                | **PASS**    | Formal decoding resolved, not calibrated absolute error                     |
| P sigma semantics                        | **PASS**    | Valid raw codes/base identified and decoded as source indicators            |
| EP availability/meaning                  | **PASS**    | Absence and unknown correlations established, not zero covariance           |
| Special values/flags                     | **PASS**    | Formal distinctions resolved; absence of physical events not proved         |
| G30 reconciliation                       | **PARTIAL** | Scope differences explained; summary/producer/revision mapping unresolved   |
| File versus epoch quality scopes         | **PASS**    | Distinct meanings established, no substitution permitted                    |
| Product-class statistic                  | **PASS**    | Published meaning/scope established, not a G30 guarantee                    |
| Satellite reference point                | **PARTIAL** | General CoM evidence; product/pair-specific point qualification missing     |
| Antenna relevance                        | **PARTIAL** | Format/model roles identified; exact 2024 input and treatment unproved      |
| Per-epoch uncertainty                    | **PARTIAL** | Reported marginal sigmas available; full calibrated covariance/model absent |
| Future SGP4 comparison applicability     | **BLOCKED** | Missing GP and unresolved essential physical/quality qualifications         |
| Provenance/independence                  | **BLOCKED** | No qualified GP source pair, fit or cross-source dependence evidence        |
| Final uncertainty/claims/protocol review | **BLOCKED** | Final inputs, interpretation and explicit authorization remain missing      |

PASS rows resolve scoped **field-definition or evidence-availability** questions;
they do not pass the study. Without GP data, producer statistic/encoding
clarification, exact historical calibration/processing evidence, correlation/
calibration limitations, and the uncertainty/claims review can still advance.
Actual GP identity, model/time/eligibility, fitted point and source-pair lineage
remain dependent on an original historical response and further review. Receipt
alone will not resolve every unknown.

No comparison-protocol change is needed or made for these field definitions.
The frozen input/grid/guard/selection policies, previous reports and E8.3 EOP
questions are preserved. Any later change needs its own justified proposal and
review before outcomes exist.

## Verification and preservation

Actual local verification:

- All **96 raw G30 quality blocks**, raw epoch tags, header/base fields, flags and
  one-based source locators matched the original source slices. All **288** valid
  reported component-code decodings passed an independent rational-base check.
  This verifies source extraction and format arithmetic, not physical uncertainty.
- **Seven deterministic synthetic format-control assertions passed**, explicitly
  labelled synthetic and separate from acquired evidence. They distinguish header
  zero, header code 2, P zero, blank, saturation 99, invalid text and an ordinary
  P code. No synthetic source is presented as acquired scientific evidence.
- The **14-item matrix** passed category, version/source, raw-evidence, status,
  limitation and next-evidence checks. Summary cell locations, the G08 literal-copy
  counterexample and actual G064 antenna metadata matched retained source bytes.
- Markdown/JSON Prettier, JSON parsing, local links, fences, whitespace and
  credential/contact-pattern checks passed. The new private four-file manifest,
  private-record size/hash, restricted file permissions and Git exclusion passed.
- Compressed reference SHA-256 remains
  `26f16fa5f97cce851948fa88711aed47f60ee2e4ddfe36f0e98b1076e79fbe38`; expanded
  SHA-256 remains
  `8a638375273ab74011aebd9ffcc480df02b5718440c8fb7c51c408ff220d231c`.
  Previous E8/E8.2/E8.3 private files/manifests, reports and protocol are unchanged.
- All **72 original private files** retain the trusted baseline. Read-only
  database checks confirm schema **3**, **two** snapshots and SHA-256
  `ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
  Existing branch/HEAD and pre-existing file contents/status are preserved in all
  four worktrees, except the intended addition of these two E8.4 documentation
  files in the current worktree. No existing file was replaced.
- No repository code or tests changed. A bounded local extraction/review script
  produced private metadata using the established SP3 field layout; no duplicate
  application parser or scientific calculation engine was added. No pytest,
  numerical spacecraft audit, frontend/browser/PDF, build or remote CI run is
  claimed for this documentation/evidence-only phase. Earlier results are prior
  evidence, not fresh E8.4 verification.

Current Git status contains four preserved E8.2/E8.3 additions plus exactly these
**two new, unstaged/uncommitted E8.4 files**. No publication, account access,
authentication, production change, deployment or database mutation occurred.
Private cloud-file preservation is not independent backup; E4 remains **OPEN**.
Swarm-A Phase 11.3.1 remains **PARTIAL**, with evaluation **BLOCKED**.

**Overall scientific study: BLOCKED — historical GP, compatible physical-point
treatment and essential frame/EOP/quality/provenance/review evidence remain missing.**
