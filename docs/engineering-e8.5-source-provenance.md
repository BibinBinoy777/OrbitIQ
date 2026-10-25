# E8.5 — Source provenance and independence assessment

Study **ORBITIQ-IGS-GPS-RETRO-001**. Assessed **24 October 2026**; acquisition
timestamps in the ledger are UTC. **BLOCKED — ADDITIONAL EVIDENCE REQUIRED**.
This documentation/evidence phase establishes source distinctions and outstanding
dependencies. It does not qualify a scientific comparison or independent accuracy.
The historical XML for NORAD **39533** has not been received or selected.

## Scope, evidence and status definitions

The [E8 feasibility report](engineering-e8-feasibility-report.md), locked
[protocol v0.1](engineering-e8-comparison-protocol.md),
[E8.2 reference qualification](engineering-e8.2-reference-qualification.md),
[E8.3 frame/EOP audit](engineering-e8.3-frame-eop-qualification.md) and
[E8.4 quality audit](engineering-e8.4-quality-qualification.md), including their
JSON ledgers and the private 96-epoch G30 quality record, were reviewed and
preserved. The [E8.5 ledger](engineering-e8.5-source-provenance-evidence.json)
records findings, source versions/locations, exact source hashes and closure needs.

Evidence categories are **direct observation** (retained bytes/metadata),
**authoritative documentation** (what the identified publisher states),
**inference** (reasoning with explicit limits) and **unknown** (absent evidence).
Reading a processing description does not verify that its software was executed
with those settings for this satellite/day.

Each independence status applies to its **explicit assessed proposition**:

- **SUPPORTED**: evidence supports that scoped proposition, not universal freedom
  from dependence or a scientific acceptance decision.
- **PARTIALLY SUPPORTED**: some links are evidenced; an essential record-specific
  link or qualification is absent.
- **UNKNOWN**: the proposition cannot be established or refuted from this evidence.
- **CONTRADICTED BY EVIDENCE**: a documented dependency conflicts with the stated
  independence proposition; it does not by itself invalidate a future comparison.

These are not the PASS/PARTIAL/BLOCKED prerequisite statuses from earlier phases.
No aggregate independence score is assigned. The missing GP's **record-level
provenance is BLOCKED**, even where a general distribution path is documented.

## IGS producer, archive and local chain

**Direct evidence:** the unchanged file is
`IGS0OPSFIN_20240010000_01D_15M_ORB.SP3.gz`, acquired from the
[BKG IGS mirror](https://igs.bkg.bund.de/root_ftp/IGS/products/2295/IGS0OPSFIN_20240010000_01D_15M_ORB.SP3.gz)
at **2026-10-24T05:00:22.757926Z**. Compressed: **102,609 bytes**, SHA-256
`26f16fa5f97cce851948fa88711aed47f60ee2e4ddfe36f0e98b1076e79fbe38`;
expanded: **253,250 bytes**, SHA-256
`8a638375273ab74011aebd9ffcc480df02b5718440c8fb7c51c408ff220d231c`.
The retained SP3-c header declares `IGS20`, `GPS`, `HLM`, `IGS`; there are
96 epochs, 32 identifiers, 3,072 P records and a 900-second cadence. No positions
were recomputed. G30 is the intended PRN for SVN G064/NORAD 39533/2014-008A;
the existing identity/continuity qualifications remain as documented in E8.2.

The associated retained report is
`IGS0OPSFIN_20233650000_07D_01D_SUM.SUM.gz`, **GPS week 2295**, Dec 31, 2023–Jan 6,
2024, **sum-file Version 2.0**. It was acquired from the same
[BKG week-2295 archive](https://igs.bkg.bund.de/root_ftp/IGS/products/2295/IGS0OPSFIN_20233650000_07D_01D_SUM.SUM.gz)
at **2026-10-24T05:00:22.758539Z**: **23,095 bytes**, SHA-256
`2c00cc06449ed72dcb13675813a14f6d8811928f4b84d98fe6aa1eac6cd11870`.
Its format version is not a producer executable version or immutable run manifest.
Day **1**, MJD **60310**, is the candidate GPS-calendar day, not a new UTC grid.

**Published documentation:** [IGS ACC](https://igs.org/acc/) identifies the Analysis
Center Coordinator, run by Geoscience Australia and MIT, as responsible for
official combined products. [NASA's precise-orbits description](https://www.earthdata.nasa.gov/data/space-geodesy-techniques/gnss/precise-orbits-product)
describes AC submissions, coordinator combination and CDDIS archival.
[IGS products](https://igs.org/products/) describes products derived from archived
GNSS data; the [May 2009 usage guide](https://files.igs.org/pub/resource/pubs/UsingIGSProductsVer21.pdf)
§2 describes the global tracking network and ACs, and §3 describes carrier-phase
and pseudorange measurements. Historic network counts in that guide are not
counts for 2024.

The documented chain is **GNSS tracking/AC solutions → IGS ACC combination →
archive/mirror → local original bytes**. BKG is the acquired mirror, not the
orbit-solution producer. Earlier CDDIS requests reached an Earthdata sign-in page;
no authenticated NASA product copy was acquired or hash-matched. Calling this
candidate “NASA-only”, “ESA-free” or independent truth would be unsupported.

## Combination lineage and G30 contributions

The week-2295 report, **COMBINATION STRATEGY**, states that ephemerides are combined
as weighted averages. Position weights use each centre's absolute deviation from
the unweighted average after a seven-parameter Helmert estimate. It describes
L1-norm robust estimation and a final centre-to-combined fit. The combination is
performed directly in ITRF without Bulletin-B alignment; REMARKS 7–8 describe
pre-alignment using daily SINEX rotations. These are producer statements, not an
OrbitIQ reproduction of the combination.

The SP3 comments list **cod, emr, esa, gfz, grg, jgx, jpl, mit, ngs, sio**.
REMARKS 9 excludes **JPL, SIO and EMR** from the orbit combination, retaining
comparison statistics as described; JGX is included with weight from week 2289.
IGR is statistics-only (REMARKS 2). Thus **COD, ESA, GFZ, GRG, JGX, MIT and NGS**
are the orbit contributors consistent with the reported general inclusion and
exclusion statements. This is not a recovered per-sample numerical weight vector.
Clock membership and clock exclusions are separate; the report's clock lists
must not be substituted for orbit contribution evidence.

**Direct observation:** Table **3.2295.1**, G30 row (expanded summary line **723**)
contains a value in each of the eleven AC/comparison columns and both IGS columns.
G30 has no `X`, `E` or `M` row suffix/prefix flag in that table. The following
values are **existing producer-reported statistics in mm**, transcribed without
calculating any new orbit differences:

| Column | Weighted Average side | Orbit Dynamics (7 days) side | Orbit-combination role evidenced by remarks |
| ------ | --------------------- | ---------------------------- | ------------------------------------------- |
| COD    | 7                     | 22                           | Included under general reported policy      |
| EMR    | 13                    | 34                           | Excluded; statistics retained               |
| ESA    | 6                     | 26                           | Included under general reported policy      |
| GFZ    | 6                     | 26                           | Included under general reported policy      |
| GRG    | 5                     | 24                           | Included under general reported policy      |
| IGR    | 3                     | 25                           | Rapid comparator; statistics only           |
| JGX    | 7                     | 25                           | Included with weight since week 2289        |
| JPL    | 11                    | 35                           | Excluded by report                          |
| MIT    | 5                     | 24                           | Included under general reported policy      |
| NGS    | 8                     | 27                           | Included under general reported policy      |
| SIO    | 10                    | 28                           | Excluded by report                          |
| IGS    | 2                     | 25                           | Combined-solution indicators; see below     |

A nonblank cell proves a reported statistic, not a nonzero combination weight.
The file/summary do not supply a G30 observation list, sensor/station-to-epoch
lineage, per-epoch contributor weights, complete covariance or exact generator
release/run settings. Station totals in Table 2 are not observation identities.

### What the reported statistics establish

- **Weighted Average, AC columns:** daily satellite fit statistics associated
  with comparison to the combination, following the described alignment/robust
  processing. They are not raw measurement errors or absolute truth errors.
- **Orbit Dynamics (7 days):** separate long-arc evaluation of the supplied
  ephemerides, using each centre's submitted EOP. The last IGS column is the
  combined orbit's fit through that evaluation. For G30/day 1 it reports **25 mm**;
  it is not a G30 accuracy certificate or a future GP residual.
- **WRMS:** the report says normalized weights are based on SP3 accuracy codes,
  limiting the impact of downweighted/problem satellites. That weighting is a
  different notion from a per-epoch covariance or a GP/reference error budget.
- **Tables 1/2:** weekly/daily transformation and fit summaries. **Tables 4/5:**
  navigation/positioning consistency. **Tables 6/7:** ERP consistency statistics,
  expressly not the official SINEX-based ERP combination product. Clock RMS and
  bias-removed clock standard deviation are distinct and unused here.

The report calls the long-arc and positioning evaluations “independent” of the
combination process. Their inputs still involve AC/combined products and, for
positioning, phase/pseudorange data. That wording does not establish independence
from the intended GP fit or independent external truth. The
[current ACC GPS page](https://igs.org/acc/gps-only/), Final and PPP sections,
likewise describes comparisons to IGS products and internal consistency. Its
“weighted as of today” plotting convention is not historical week-2295 evidence.

## G30 quality relationship: still partially explained

E8.4's exact raw-source checks were reused. The **three daily/header indicators**
remain:

| Source and locator                                           | Recorded value | Supported interpretation                                                                                   |
| ------------------------------------------------------------ | -------------- | ---------------------------------------------------------------------------------------------------------- |
| Summary Table 1.2295.b, G30/day 1, line 498 column 17        | `3`            | Reported combined position sigma, table units mm                                                           |
| Summary Table 3.2295.1, first IGS column, line 723 column 67 | `2`            | Caption links this column to header accuracy measures; exact statistic/encoding mapping remains unresolved |
| Actual SP3 header line 9 columns 46–48                       | raw `  2`      | SP3-c exponent n=2, format indicator **4 mm**; not a physical error bound                                  |

SP3 P-coordinate sigmas instead use the recorded **1.25 base**, per axis and epoch;
there are 288 populated G30 component fields. Their scope/base differs from the
header's satellite/file-wide **base-2** indicator. No EP covariance is present.

The summary says header codes are based on weighted RMS over a daily arc, calls
Table 1.b values sigmas “coded” in SP3, and describes the first IGS Table 3 column
as accuracy measures found in the header. It **does not supply enough definition
to derive the exact `3`/`2`/`4 mm` producer mapping** for these retained revisions.
G08 remains a counterexample to assuming a verbatim exponent copy: actual header
raw `  2` versus Table 3 first IGS `5` (line 701 column 67).

Different documented scopes explain why header and P fields are not interchangeable.
Quantization could explain some magnitudes, but the rounding, statistic and
revision relationship is not proven. The same archive/week naming is evidence
of association, not an immutable manifest tying generator intermediate values to
these exact files. No corruption or contradiction is established. Do not resolve
this by exponent-decoding every table value, applying an unsupported sqrt(3)
factor, equating the orbit-dynamics **25 mm** to one of these quantities, or
choosing the smallest number. Producer definitions and revision linkage remain
required. No uncertainty, covariance, confidence interval or bound is derived.

## Upstream observations, software and conventions

**Documented generally:** IGS solutions use the global GNSS network, with AC
observation reduction, orbit/clock estimation, reference-frame constraints and
combination. ACs can use overlapping observations and common geophysical models,
antenna calibrations, reference frames and EOP. A combined product therefore does
not imply that its inputs are statistically independent.

The retained week-2295 SOFTWARE section gives historical origins and references
for weighted-average and Bern long-arc evaluation software; it does not identify
the deployed executable/version. REMARKS 6/9 claim repro3 standards and IGS20/
igs20.atx adoption. The actual SP3 comment identifies `PCV:IGS20`,
`OL/AL:FES2014b NONE`, and `ORB:CMB CLK:CMB`. These labels are not a complete force
model or proof of the exact historical antenna-file revision.

E8.5 acquired **public documentation only**, retaining original response bytes
privately with URL, retrieval time, HTTP status, size and SHA-256:

- [CODE analysis strategy](https://files.igs.org/pub/center/analysis/code.acn):
  software field **Bernese GNSS Software 5.5**; last listed modification
  **21-Mar-2024**, describing model changes at week 2238. Basic observables include
  carrier phase, with code for receiver-clock synchronization/ambiguity resolution.
  The document describes numerical integration, EGM2008, FES2014b, third-body and
  radiation modelling, IERS conventions and ITRF2020-aligned C04. This is a
  published strategy, not a proven January-2024 executable/configuration manifest.
- [ESA analysis strategy](https://files.igs.org/pub/center/analysis/esa.acn):
  **NAPEOS 3.9**, preparation date **2012-10-26**, modifications through
  **2015-06-30**, with a stated final-product effective date `2015 179`.
  It describes undifferenced phase/pseudorange, numerical integration, force
  models and subdaily EOP treatment. This visibly old source is **not proof of
  week-2295 settings**. Its existence does not resolve E8.3's EOP gate.
- [IGS repro3 conventions](https://igs.org/acc/reprocessing/), “Conventions and
  Modelling”: IERS conventions, subdaily EOP recommendations, constellation/block-
  dependent radiation-pressure treatment, Earth albedo, ocean tides and antenna
  thrust. This is a campaign/model recommendation, not evidence every listed
  model was used in this operational G30 solution. Do not substitute its
  repro3 calibration file for the locked operational reference inputs.

These sources substantiate differences among documented processing approaches
and shared conventions. They do not recover all AC inputs, the actual historical
GPS station observations, normal equations, rejection masks, resource versions or
GP source dependencies. No source recommendation was installed or evaluated.
CODE's raw file fails UTF-8 decoding; a clearly identified **ISO-8859-1 review
view** was used, leaving original bytes/hash unchanged. Its HTTP MIME is recorded
as received (`audio/asc`), not treated as a scientific format declaration.

## Intended GP lineage and the missing record

The retained official [CelesTrak GP-format documentation](https://celestrak.org/NORAD/documentation/gp-data-formats.php),
dated **27 May 2020, updated 23 June 2026**, Background/Solution sections, states
that government GP data are produced by fitting **US Space Surveillance Network
observations** to **Brouwer mean elements using SGP4**. It describes the
18 SPCS/Space-Track distribution relationship and CelesTrak ingestion/format
distribution. The historical unit names on that page do not identify which unit,
software release or fitting settings generated an unreceived 2023 record.

The general documented path is **SSN observations → government GP generation →
Space-Track/CelesTrak distribution → original delivered record**. CelesTrak is
the intended request/distribution source, not evidence that it independently
observed GPS G30. XML/OMM representation does not turn mean elements into direct
observations or confer accuracy. The source page documents Earth/TEME/UTC/SGP4
conventions; future original XML declarations still require inspection.

**Model dependency:** planned OrbitIQ evaluation uses the existing SGP4 engine
(the preserved E8.3 audit records sgp4 2.27/WGS72). The GP generating fit and
evaluation model are deliberately related. Numerical implementation/reference
tests can establish conformance to a model, not independence from that model or
absolute orbit accuracy. Exact government generation software/version, tracking
times, individual sensors, weights, fitted physical point, covariance and fit
arc are unknown for the missing record.

### Ordinary GP is distinct from supplemental GP

The official [CelesTrak supplemental-data page](https://celestrak.org/NORAD/elements/supplemental/),
Introduction/Methodology, describes **SupGP** derived from owner/operator orbital
data using STK/SGP4 fits. Its GPS example uses a 2 SOPS almanac to generate
ephemerides that act as fit “observations”; it documents classification/source
and element-set conventions for that service. This supplies a concrete reason to
verify the product path before interpreting independence. It does **not** show
that the requested government historical GP file follows that path, that IGS is
used in its fit, or that a supplemental record is an acceptable substitute.
Classification and element-set numbers alone would not establish full lineage.
No supplemental orbital data was downloaded or selected.

The user reports submitting a CelesTrak Special Data Request for **NORAD 39533,
2023-12-25 through 2023-12-31**, XML/OMM. That is request context, not delivery
evidence. File name/hash/size, receipt time, returned count, exact epochs,
originator and creation/publication metadata are **unknown**. No eligible record
exists in the qualified evidence. The protocol's inclusive eligibility interval
remains **[2023-12-25T23:44:42Z, 2023-12-31T23:59:42Z]** and its one-fixed-record,
latest-unique-eligible rule remains unchanged. No GP record was selected.

Record epoch is not record creation, publication, historical availability or email
receipt. Even a future OMM `CREATION_DATE` must be interpreted using its actual
producer/format documentation; it cannot automatically certify government fit
time or Space-Track publication. Record actual receipt only from explicit,
traceable operator evidence. Use the existing E8.1.1 private offline inspector
when the attachment arrives; do not reconstruct the missing file from examples.

## Categorized dependency map

| Category / assessed proposition                                                                  | Status                       | Evidenced links, limits and next evidence                                                                                                                                                                                                                                                                              |
| ------------------------------------------------------------------------------------------------ | ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A. Observation sources:** independence of the actual GP/reference measurements                 | **UNKNOWN**                  | GNSS network vs general SSN radar/optical paths are documented. No actual GP observation inventory or exclusion of shared upstream data is available. Need the original record plus authoritative fit/source lineage and the applicable IGS input inventory.                                                           |
| **B. Processing/solution:** distinct processing paths for the intended pair                      | **PARTIALLY SUPPORTED**      | AC estimation/combination and government GP fitting are distinct documented processes. Shared IGS inputs/models and missing actual GP settings prevent a record-specific independence claim. Need historical AC/run details and GP generation evidence.                                                                |
| **C. Mathematical models:** the planned SGP4 evaluator is independent of the GP generating model | **CONTRADICTED BY EVIDENCE** | Government GP is documented as fitted using SGP4; OrbitIQ plans SGP4 evaluation. This is a known model link. IGS AC numerical-dynamics approaches differ, but that does not remove the GP fit/evaluation link or establish all assumptions independent.                                                                |
| **D. Frames/reference systems:** shared and differing conventions are fully qualified            | **PARTIALLY SUPPORTED**      | IGS20/GPS and intended TEME/UTC are identified; the E8.3 transform/EOP path is audited. A common frame/time basis is required for comparison and may share systematic errors; it neither proves nor alone refutes measurement independence. Actual realization/subdaily/point compatibility remains open.              |
| **E. Product/distribution:** complete producer-to-local chain for both inputs                    | **PARTIALLY SUPPORTED**      | The IGS ACC→BKG→local hash/receipt chain is supported. General government→Space-Track→CelesTrak distribution is documented. Actual historical GP delivery/hash/originator/publication chain is absent. Different archive names do not prove different upstream observations.                                           |
| **F. Validation:** an independent scientific accuracy-validation claim is supported              | **UNKNOWN**                  | No qualified pair or comparison exists; IGS internal checks are not external GP truth validation. Need complete lineage/dependency review, qualified frame/point/quality treatment, frozen protocol and explicit approval. Evidence of direct derivation/shared fit data would invalidate a strong independence claim. |

Within A/B, overlapping IGS observation resources and common processing standards
are possible/documented general dependency paths, not proven GP overlap. Within
C, shared gravity/third-body concepts do not imply identical force implementations
or fully correlated errors. Within D, mapping to one terrestrial frame is a
compatibility operation, not a new independent observation. No cross-source
covariance, effective independent sample count or uncertainty is inferred.

The current allowed interpretation remains only the protocol's proposed,
future **retrospective disagreement between estimated products**. Independent
prediction accuracy, historical forecasting, anomaly or safety claims remain
prohibited. The study remains blocked regardless of any scoped SUPPORTED finding.

## Evidence still required

**Requires the original historical XML and its associated acquisition evidence:**

1. Original bytes, hash/size, declared source/product path, explicit receipt
   evidence if available, returned record count and full identity/model metadata.
2. Exact epochs, mandatory fields, duplicates/ambiguity and eligibility under the
   unchanged interval and selection rule. A parse success is not qualification.
3. Actual originator/creation/publication fields and their source-defined meaning;
   a missing field remains unknown. The file alone may not establish availability.

**Requires documentation or producer clarification, not merely receipt of XML:**

1. Exact historical GP sensor/observation sources, fit arc/settings/software,
   upstream dependencies, fitted reference point and any covariance limitations.
   Ordinary OMM may not contain these details; absence must not be filled by guess.
2. Applicable historical IGS AC/run/model/resource manifests, G30 contribution/
   weight details and historical antenna/attitude/reference-point treatment.
3. The week-2295 Table 1/Table 3/header statistic, encoder/rounding and immutable
   revision relationship. Current documentation does not close E8.4's question.
4. E8.3 realization, subdaily EOP/ERP and transformation compatibility, and E8.4
   quality/uncertainty/claims policy. No generic zero alignment or new correction
   is approved here.
5. Review of source dependencies and the complete frozen protocol/manifest before
   explicit authorization for any real calculation. If full independence cannot
   be established, retain restricted product-disagreement language.

Documentation of model inventories, producer questions and protocol/control design
can advance before GP arrival. Full actual-pair lineage, eligibility and scientific
acceptance cannot. No provider was contacted and no account/authentication used.

## Local verification and preservation

E8.5 adds only this report and its JSON ledger. No application, test, dependency,
existing report or protocol was modified. All four worktrees retain their original
branch/HEAD; current work is in `engineering-e8.2-igs-reference-qualification` at
`b0a03205e3930b55651232d8b7ffbc9e879ae8c6`. Six prior E8.2–E8.4 documentation
additions and the separate three E8.1.1 additions are preserved.

Actual checks for this phase:

- Ledger schema/unique findings, six separate category statuses, source/version/
  location/category/limitation/next-evidence fields and report consistency.
- Source-backed week/day, contribution/exclusion text, 24 G30 daily-table cells,
  the preserved three summary indicator locators, header codes and the existing
  96-epoch private quality record's hash/metadata. These are transcription and
  evidence-consistency checks, not new orbit calculations.
- All seven new public-document captures passed HTTP-200, size/hash and receipt
  checks; raw bodies/receipts remain in ignored private `data/`. No reference
  product, GP data or EOP resource was downloaded. Source capture time is not
  historical product creation or publication time.
- Markdown/JSON formatting, JSON parsing, local links, code fences, whitespace
  and privacy-pattern review, plus a complete review of the two-file addition.
- All **380 originally tracked files** in the current worktree, prior reports,
  four branches/HEADs, **72 original private files**, and the original **53/8/20/4**
  E8/E8.2/E8.3/E8.4 private-manifest entries remain unchanged. Read-only database
  verification confirms schema **3**, **two** snapshots and SHA-256
  `ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
  Both original compressed/expanded SP3 hashes above still match.

The companion ledger records the verification results. No pytest, frontend,
browser/PDF, production build or remote CI was rerun for documentation-only
changes; earlier suites are not described as new verification. Nothing was staged,
committed, pushed or deployed. Local preservation is not independent backup;
E4 remains **OPEN**. Swarm-A Phase 11.3.1 remains **PARTIAL**, evaluation **BLOCKED**.

**No real-input propagation, spacecraft transformation, orbital interpolation/
extrapolation, residual calculation or uncertainty calculation occurred. The
scientific study remains BLOCKED while historical GP and essential qualifications
are missing.**
