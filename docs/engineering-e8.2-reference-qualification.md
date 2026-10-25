# E8.2 — IGS reference qualification assessment

Study **ORBITIQ-IGS-GPS-RETRO-001**, reviewed 24 October 2026.
**Scientific study: BLOCKED. Historical GP: not received or qualified.
Real-input propagation, spacecraft transformations and residual calculations: NOT PERFORMED.**

This assessment qualifies what the reference evidence supports and identifies
the remaining comparison gates. It does not approve the reference as absolute
truth or authorize a comparison. No application, inspector, test, dependency,
database or workflow code changed.

## Scope, baseline and evidence classes

Started from E8 commit `b0a03205e3930b55651232d8b7ffbc9e879ae8c6`, in new
worktree `/workspace/OrbitIQ-e82`, branch
`engineering-e8.2-igs-reference-qualification`. The original E7/E8 worktrees and
the E8.1.1 worktree, including its three uncommitted additions, are preserved.
E8.1.1 is not silently committed or incorporated into this separate branch.

Read the [E8 feasibility report](engineering-e8-feasibility-report.md),
[protocol v0.1](engineering-e8-comparison-protocol.md),
[source evidence](engineering-e8-source-evidence.json) and
[verification receipt](engineering-e8-verification.md). The new
[metadata-only evidence ledger](engineering-e8.2-reference-evidence.json) pins
the source captures, local recheck, citation correction and qualification matrix.
No raw GP, SP3 positions, ANTEX content, private correspondence or credentials
are included in the two new documentation files.

Findings below distinguish **D: directly verified**, **P: published documentation**,
**I: reasonable inference**, and **U: unknown/unresolved**. A published convention
is not a direct verification of every processing step in this particular file.
Matrix PASS applies only to its stated scope, never to overall scientific approval.

## Sources and a substantive citation correction

The following retained sources were read without downloading the orbit again.
Original URLs, actual capture times, sizes and hashes are in the evidence ledgers.

| ID  | Source and relevant locator                                                                                                                                                                        | Evidence scope                                                                              |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| S1  | [SP3-c specification](https://files.igs.org/pub/data/format/sp3c.txt); header, P-record, time and sigma definitions                                                                                | Applicable file-format semantics                                                            |
| S2  | [SP3-d specification](https://files.igs.org/pub/data/format/sp3d.pdf), compatible header/P-record explanations                                                                                     | Supporting field semantics; the actual product remains SP3-c                                |
| S3  | [IGS reference-frame page](https://igs.org/wg/reference-frame/), chronology and frame definition                                                                                                   | IGS20 use in weeks 2238–2351; ITRF2020 datum and antenna conventions                        |
| S4  | [IGSMAIL 8238](https://lists.igs.org/pipermail/igsmail/2022/008234.html), “Upcoming switch to IGS20/igs20.atx and repro3 standards,” frame-definition and transformation paragraphs                | Newly captured public notice; underlying datum parameters and station-specific adjustments  |
| S5  | [IGS products](https://igs.org/products/), GPS ephemerides table and Note 1                                                                                                                        | Published typical orbit-quality statistic, not per-epoch validation                         |
| S6  | [A Guide to Using IGS Products](https://files.igs.org/pub/resource/pubs/UsingIGSProductsVer21.pdf), May 2009, §§5.1.1 and 5.2.4                                                                    | Newly captured public guide; general CoM and ERP conventions, not a 2024 processing receipt |
| S7  | [Metadata SINEX 1.10](https://files.igs.org/pub/resource/working_groups/multi_gnss/Metadata_SINEX_1.10.pdf), §§1.1, 2.2–2.3, 2.7 and 3.5                                                           | Identity, CoM, antenna eccentricity and validity-interval semantics                         |
| S8  | [Week-2295 combination summary](https://igs.bkg.bund.de/root_ftp/IGS/products/2295/IGS0OPSFIN_20233650000_07D_01D_SUM.SUM.gz), strategy, products generated, remarks, Tables 1.2295.b and 3.2295.1 | Actual accompanying processing account and source quality indicators                        |
| S9  | [NASA precise-orbits overview](https://www.earthdata.nasa.gov/data/space-geodesy-techniques/gnss/precise-orbits-product)                                                                           | Combined operational products, latency and estimated-orbit status                           |
| S10 | [IGS satellite metadata](https://files.igs.org/pub/station/general/igs_satellite_metadata.snx), retained G064 identifier/PRN blocks                                                                | Nominal retrospective spacecraft mapping                                                    |
| S11 | [CelesTrak GP format documentation](https://celestrak.org/NORAD/documentation/gp-data-formats.php)                                                                                                 | GP format/source path; not the missing record's complete fit lineage                        |

**D:** the retained E8 capture labelled `igs-frame-8238` requested archive path
`2022/008238.html`, but its actual title/body is **IGSMAIL-8242, Delay in IGS Rapid
products**. A correct HTTP 200 and hash did not make it an IGS20 notice. That
capture is preserved; it is **not evidence for the frame claims**. The frame
page's link `2022/008234.html` actually contains IGSMAIL-8238 and is now separately
captured as S4: 18,912 bytes, SHA-256
`93a266b57862345e0a674e2b5790eb5f8c5423dd4dbf676564a6d4e0916fb3e0`.
This addendum corrects that citation without rewriting the previous reports.

**P/U:** S4 was an advance notice proposing week 2230. It does not prove the
actual switch occurred then. S3's retrospective chronology records week 2238
(27 November 2022) through week 2351 for IGS20; the candidate's week 2295 lies
inside that period. Preserve this distinction between plan and operational history.

S6 was acquired once from its public IGS archive: 888,722 bytes, SHA-256
`48f8f4f9a75d353a7382757df6e45fbbe65f8505d10299c3ad078e504ebbafed`.
Two attempted additional public IERS sources were **not acquired as scientific
documentation**: the Chapter 4 PDF URL returned HTTP 503, and the ITRS definition
page URL returned HTTP 404. Their failure receipts are retained, not counted as
references read. No private account or authentication was attempted.

## 1. Product identity, status and file integrity

- **D:** the preserved file is
  `IGS0OPSFIN_20240010000_01D_15M_ORB.SP3.gz`, acquired from the documented BKG
  IGS mirror in E8 at `2026-10-24T05:00:22.757926Z`. Compressed size **102,609
  bytes**, SHA-256
  `26f16fa5f97cce851948fa88711aed47f60ee2e4ddfe36f0e98b1076e79fbe38`.
  Local decompression gives **253,250 bytes**, SHA-256
  `8a638375273ab74011aebd9ffcc480df02b5718440c8fb7c51c408ff220d231c`.
  Both hashes and every previously recorded product-metadata field match the
  local bytes in the E8.2 recheck. No reference download or rewrite occurred.
- **D/P:** the name identifies an operational combined FIN orbit product; the
  actual header is `#cP`, 96 epochs, `ORBIT IGS20 HLM IGS`, with a “FINAL ORBIT
  COMBINATION FROM WEIGHTED AVERAGE OF” comment. S8 lists this output naming
  pattern. S9 distinguishes final from rapid and ultra-rapid products.
- **I:** these consistent source/name/header/summary facts support treating it
  as the intended IGS combined final estimate, rather than a predicted ULT half.
  They do not turn estimated orbits into direct observations or absolute truth.
- **U:** no exact product-processing software version, immutable release revision
  or original creation/publication timestamp has been established. SP3-c, HLM,
  FIN and the summary's “sum-file Version 2.0” are not such software identifiers.
  Mirror acquisition does not verify an unacquired authenticated CDDIS copy.

## 2. Satellite identifiers, continuity and completeness

- **D:** all **32 identifiers G01–G32** have **96 P records**, totaling **3,072**.
  The existing inspector verifies declared IDs, fixed-column records, unique
  complete ID sets at each epoch, regular unique increasing epochs and EOF.
  G30 has 96 records with no missing XYZ, maneuver, predicted-position or unknown
  XYZ-sigma exclusions under the existing profile. No V or EP records occur.
- **P:** S7 distinguishes PRN/slot labels from persistent spacecraft identifiers.
  S10 maps **G30 → SVN G064 → NORAD 39533 → COSPAR 2014-008A**, with retained PRN
  assignment from `2014:052:00000` to open-ended `0000:000:00000`.
- **I:** that assignment supports nominal continuity over this short 2024 arc,
  well away from the recorded start boundary. Missing maneuver flags do not prove
  that no physical maneuver or other event occurred.
- **U:** metadata validity-tag time scale is not independently qualified at
  subsecond boundaries. No actual historical GP identity or record continuity
  can be checked until the attachment arrives. No PRN-only substitution is allowed.

## 3. Frame, axes, units and realization

- **D:** the actual frame token is **IGS20**, not IGb08, IGb20 or IGc20. P fields
  provide Cartesian X/Y/Z in the file's declared terrestrial frame. S1 defines
  position units **km**, with six-decimal representation; clock fields are µs
  and unused here. Decimal resolution of 1 mm is not a 1-mm accuracy claim.
- **P:** S3 identifies IGS20 as aligned to the ITRF2020 datum with associated
  ground/satellite antenna models. S4 explicitly says ITRF2020 and IGS20 share
  the same underlying **origin, scale and orientation**, with zero transformation
  parameters between those named datums. It separately documents station-specific
  coordinate adjustments for antenna updates. Those station offsets are not a
  universal satellite-orbit correction.
- **I:** the intended convention is geocentric, Earth-fixed, right-handed XYZ:
  nominal +X toward the reference-meridian/equator intersection, +Y toward 90° E
  and +Z along the conventional north pole. This is an interpretation of the
  terrestrial Cartesian designation, not an independently measured axis alignment
  from the SP3 numbers. The terrestrial frame origin is separate from the point
  on the spacecraft being positioned.
- **U:** the IGS20 label is not a complete epoch-dependent processing or covariance
  specification. The current Astropy ITRS object has no selected ITRF-release
  attribute. The actual computed frame must be traced through its conventions and
  resources before the published named-datum zero transformation can be used.
  A justified zero additional alignment is possible; neither an arbitrary Helmert
  correction nor an unproved identity mapping is approved. Independent axis,
  origin, scale, epoch/rate and sign/order controls remain required. The failed
  IERS document retrievals do not provide that missing verification.

## 4. GPS time, UTC, grid and resource evidence

- **D:** `%c` declares **GPS**, not UTC or IGST. The header calendar, week **2295** /
  second **86400**, and MJD **60310** / fraction zero reconcile exactly under the
  existing parser. There are **96 epochs**, from GPS-calendar
  `2024-01-01T00:00:00.00000000` through `2024-01-01T23:45:00.00000000`, separated
  by **900 seconds**. There are no duplicate epochs or absent satellite records.
  A nominal 24-hour product has 95 intervals between these samples; it does not
  contain a fabricated sample at next-day 00:00.
- **P:** S1/S2 distinguish the epoch time-system indicator from satellite-clock
  corrections. S5 describes an IGS clock timescale; that is not permission to
  shift position epochs or subtract the clock fields.
- **D, reused E8 validation:** existing split-second Astropy TimeGPS conversion
  yields UTC **2023-12-31T23:59:42.000000Z** through
  **2024-01-01T23:44:42.000000Z**. The observed 18-second offset came from retained
  leap resources, not a hard-coded correction. Existing preflight of all 96 epochs
  and ±0.5-second support found IERS-B-final central UT1/polar-motion flags (192
  central flags). These results were reused, not recalculated in E8.2.
- **U:** GP time declarations/precision remain unverified without the original
  record. Reference time conversion alone does not establish pair compatibility.
  Freeze exact source indices and UTC instants, without rounding to UTC quarter
  hours, interpolation, extrapolation, nearest matching or filling gaps.

Pinned resources remain EOP SHA-256
`9fbc14ae5e71de96cc1e6b43b54a547acc80c7a6ce910c0209ad6230ff3d30cd`, leap SHA-256
`6cb6f5d4b819f2e568e25db4b0b26d89dedf031fdffb18bc94d40f4e94e268d7`, leap expiry
**2027-06-28**, `astropy-iers-data 0.2026.10.12.1.3.27`. Complete local software
versions and lock/resource identities remain in the E8 ledger. Resource presence
and status are not frame or uncertainty certification.

## 5. Earth orientation and the required comparison path

- **D, code inspection only:** OrbitIQ's existing transform constructs a
  same-epoch geocentric TEME Cartesian representation, then uses Astropy's
  TEME→ITRS transform with pinned UT1-UTC and polar motion. Its one-second velocity
  finite difference requires ±0.5-second resource support. This code was read,
  not executed on a real spacecraft state in E8.2. WGS72 belongs to the existing
  SGP4 model; the WGS84 geodetic display ellipsoid does not select an ITRF datum.
- **P:** S8 says the final combination has been performed directly in ITRF without
  alignment to Bulletin-B EOP since week 860. It describes a separate SINEX ERP
  combination. S6 §5.2.4 explains that terrestrial orbit products imply underlying
  ERP, and inertial use requires appropriate ERP and sub-daily conventions.
- **I:** adequate local IERS coverage is necessary but does not prove equality
  to the combination's ERP or consistency of regularization/sub-daily models.
  Any mismatch may enter a future frame comparison; its effect is not estimated
  here. A generic inertial-frame rotation or ad hoc tide correction is not justified.
- **U:** the applicable 2024 product ERP and sub-daily model chain has not been
  qualified against the precise TEME→ITRS implementation. No ERP product was
  acquired or substituted in this task. Review that relationship and its effect
  on allowed claims, rather than choosing resources to minimize future differences.

The proposed path remains **existing SGP4 TEME at the exact UTC instant → existing
geocentric ITRS → reviewed ITRF2020/IGS20 alignment → common spacecraft point**.
This is a requirement description, not an implemented or executed comparison.

## 6. Satellite reference point

- **D:** the actual SP3 header/records do not contain a standalone flag proving
  the spacecraft physical point or its exact historical antenna calibration.
- **P:** S6 §5.1.1 explicitly describes IGS precise GPS coordinates as **satellite
  center of mass**, and contrasts them with GPS broadcast-navigation antenna
  phase-center ephemerides. S7 §1.1 explains CoM dynamics, ANTEX phase-center
  offsets relative to CoM, possible CoM changes and ARP eccentricities. S4 connects
  IGS20 to updated satellite/ground antenna calibrations.
- **I:** these are affirmative published evidence for the intended precise-product
  CoM convention, stronger than treating the point as wholly undocumented. They
  do not make a GP/TLE input a broadcast navigation message or prove its fitted
  physical point. Do not automatically apply a broadcast-to-CoM antenna correction.
- **U:** S6 is a **May 2009 general guide**, not a 2024 product-specific receipt.
  Confirm applicability to this combination and the GP fitted-state interpretation.
  If a correction is necessary, pin the correct historical spacecraft/antenna/CoM
  and attitude conventions, or document why none is needed. The October-2026
  `igs20.atx` capture is not proven to be the exact 2024 processing file and was
  not applied. Earth geocenter and satellite CoM are distinct concepts.

## 7. Quality indicators and uncertainty limits

- **P:** S5's final-GPS table quotes approximately **2.5 cm**. Its Note 1 defines
  orbit accuracy as a **1D mean RMS over three XYZ geocentric components**, with
  the stated comparisons to laser-ranging results and consecutive-day
  discontinuities. This is a published product-class statistic, not a measured
  G30 error at each of these epochs, a 3D confidence radius or GP agreement.
  No matched independent G30 truth/SLR validation for this arc was acquired.
- **D/P:** G30's actual header exponent is **2**; S1/S2 decode this as a quantized
  **4-mm indicator**, with header zero meaning unknown. The format intends a
  whole-file one-standard-deviation error representation; S8 says its header codes
  are based on weighted RMS over daily arcs. Provider statistics are not thereby
  externally calibrated absolute errors.
- **D/P:** all G30 per-axis sigma fields are populated. The actual base is **1.25**;
  X exponents span **1–8**, Y **3–6**, Z **1–7**, each totaling 96 entries. S1/S2
  specify `1.25**n mm`, with zero equal to 1 mm, blank unknown, and saturation
  codes distinct from an ordinary finite uncertainty. These are per-epoch source
  indicators, not full joint or cross-time covariance. No EP covariance record
  is present. Other satellites have unknown sigmas; G27 lacks unused clocks.
- **D/U, source-statistic discrepancy:** S8 Table **1.2295.b** gives PRN30 day 1
  sigma **3 mm**. Table **3.2295.1** contains raw entry **`2`** in its first IGS
  column; the table has a “Units: mm” line but describes that column as the
  accuracy measure found in the header. The actual SP3 header code `2` decodes
  to **4 mm**. These entries must not be silently equated, reinterpreted, or
  resolved by choosing the smallest. Their exact reconciliation is not established
  by this review; clarify the statistic/coding/rounding meaning before using
  them in a numerical uncertainty budget. Different statistics or quantization
  are possible explanations (**I**, not established); this is not evidence of
  file corruption. No source value was changed.
- **I/U:** absence of basic G30 exclusion flags supports retaining the complete
  arc for review. It does not establish physical absence of errors/events, justify
  a numerical scientific threshold, or imply 96 independent samples. No GP
  covariance, cross-provider covariance or calibrated joint budget exists here.
  Do not convert the public 2.5-cm figure or the 4-mm code into a pass tolerance,
  normalize future differences, invent confidence intervals or claim cm agreement.

## 8. Contributors, dependencies and permitted claims

- **D:** the actual file lists `cod emr esa gfz grg jgx jpl mit ngs sio` as
  submissions. S8 documents JPL/SIO/EMR exclusions and JGX inclusion with weight
  from week 2289. Appearance in a header or comparison table does not prove
  nonzero orbit weight for every spacecraft/epoch. ESA involvement is documented.
- **P:** S8 describes robust L1/Helmert alignment and weighted combinations, plus
  separate internal arc/positioning consistency evaluations. S9 describes products
  derived from AC solutions. S11 describes the CelesTrak/Space-Track GP source path.
- **I:** sources can share observations, reference products or models. Different
  organization names and S8's use of “independent” for internal evaluation do not
  establish independence between a USSF GP fit and this IGS solution.
- **U:** the missing GP's sensors, fit interval, weights, processing version and
  shared dependencies are unestablished. Record-creation/publication/availability
  is a separate issue from element epoch and retrieval time. No historical
  forecasting or independently validated prediction-accuracy claim is supported.
  A future bounded retrospective disagreement study may retain explicitly unknown
  lineage under reviewed limited claims; it must not promote unknown independence
  into a fact. The reference is an international IGS combination with ESA
  contributions, not NASA-only truth or an ESA-free alternative.

## Comparison prerequisite matrix

| Requirement                                   | Status           | Evidence already available                                                                      | Specific evidence needed to close                                                                                                                                                                                                         |
| --------------------------------------------- | ---------------- | ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Reference-frame compatibility                 | **BLOCKED**      | Actual IGS20 token; S3 chronology; S4 named-datum zero parameters; inspected existing transform | Trace computed axes/origin/scale, EOP and model conventions to ITRF2020/IGS20; independently verify an applicable zero alignment or justified mapping, including epoch/rates and conventions. A software label alone is insufficient.     |
| Time-system compatibility                     | **PARTIAL**      | Reference GPS declaration and exact grid; reused resource-backed UTC conversion and preflight   | Actual GP UTC declaration, exact epoch and compatible time handling; review frozen same-instant conversion and any unsupported leap crossing. Reference-only conversion is verified; pair compatibility is not.                           |
| Satellite identity and continuity             | **PARTIAL**      | Complete G30 arc; S7/S10 nominal G064/39533/2014-008A mapping                                   | Cross-check actual GP identifiers, source record and provenance against that mapping; qualify any boundary/identity ambiguity without substitution.                                                                                       |
| Satellite reference-point compatibility       | **PARTIAL**      | Published general IGS precise-GPS CoM convention; SINEX/ANTEX point definitions                 | Applicable 2024 combination convention plus GP fitted-point evidence; justify no correction or pin an applicable historical attitude/CoM/antenna treatment.                                                                               |
| Reference-product quality and uncertainty     | **PARTIAL**      | G30 complete basic quality fields; published statistic meanings and actual summary entries      | Review source-statistic reconciliation if used numerically, per-sample acceptance, missing covariance and allowed claims; freeze a justified uncertainty/limitations policy without invented accuracy.                                    |
| GP source provenance and independence         | **BLOCKED**      | Source-path documentation and existing offline intake readiness; no historical GP               | Original bytes/hash/receipt claims, exact eligible epoch, identity and unique selection. Assess fit/dependency evidence or explicitly retain unknowns under approved retrospective limits; independent-accuracy claims remain prohibited. |
| Sampling and comparison-epoch selection       | **PARTIAL**      | Reference grid/completeness **PASS**; unchanged full-arc bounds                                 | Qualify actual GP against frozen window; review/freeze the exact source indices and exclusion mask. No interpolation, nearest matching, record switching or outcome-based trimming.                                                       |
| Protocol reproducibility and review           | **PARTIAL**      | Draft v0.1, pinned reference/resources/software; this evidence audit                            | Complete GP/reference/resource/software manifest, independent scientific review of frames/points/ERP/quality/claims, then explicit authorization before implementation or execution.                                                      |
| Product ERP and sub-daily model compatibility | **NOT ASSESSED** | E8 local IERS coverage; S6/S8 explain why the applicable conventions matter                     | Establish the 2024 combination's ERP/regularization/sub-daily chain and its relation to the exact TEME→ITRS implementation; justify consistency or an approved treatment. No blind EOP substitution.                                      |

## What can advance before the GP arrives

Reference bytes, identity/structure/completeness and exact reference time/grid
reconciliation are **PASS within those reference-only scopes**. They were
confirmed from retained evidence without new state calculations. Published CoM
and named-datum evidence now narrow two formerly broader questions.

The following can proceed without GP data: review applicable 2024 product/AC
conventions and ERP models; qualify terrestrial-frame controls using independent
non-spacecraft references; document the historical reference-point/antenna chain;
clarify the summary statistics; and review the reproducibility/uncertainty/claims
policy. These are next evidence tasks, not completed or newly authorized
transformations. Pair identity, GP eligibility/selection, fit lineage and final
joint qualification still require the actual historical response and review.

The frozen GP window remains
**[2023-12-25T23:44:42Z, 2023-12-31T23:59:42Z], inclusive**. No historical record
is selected. The existing fixed-input, latest-unique-epoch policy, same-epoch
ambiguity blocker, seven-day guard and reference grid remain unchanged.

## Protocol and verification decision

**No protocol change is necessary or made in E8.2.** S4's zero named-datum
parameters do not remove the existing computed-frame gate; S6's general CoM
convention does not establish pair compatibility. This report supplies evidence
and a corrected citation, not new sampling, alignment, threshold or selection
rules. Any later change requires a justified versioned proposal and review while
preserving v0.1, before outcomes exist.

## Actual verification and preservation

- **46 existing E8 synthetic tests passed in 3.86 seconds** with the parent
  `PYTHONPATH` removed. They exercise format, integrity, identity, exact epochs,
  quality flags, time/resources and the eligibility refusal boundary. They are
  software regressions, not acquired scientific validation or cm-accuracy tests.
- A local actual-product **metadata-only** recheck matched every recorded E8
  product field, original/expanded hashes, 96 unique regularly sampled epochs,
  3,072 P records and the G30 basic-quality/axis-exponent counts. No coordinates
  were exported, transformed, propagated, interpolated or subtracted.
- Retained source hashes, new public-document response metadata, the bad/correct
  notice titles, G30 summary entries and report/ledger scientific status passed
  consistency checks. Existing time/resource results were reused, not represented
  as a new conversion run. The two failed IERS retrievals remain explicit failures.
- Markdown/JSON Prettier, JSON parsing, local links, fences, whitespace and
  credential/contact-pattern review passed. External links were checked against
  retained/new acquisition records, not all refetched. The initial local matrix
  check assumed unpadded Markdown cells; it was made insensitive to formatter
  spacing, without changing any requirement, matrix status or scientific claim.
- All **380** pre-existing tracked files in this worktree match the E8 commit,
  including the protocol, previous reports, application code and lockfiles.
  The three prior worktrees retain their exact branches/HEADs, file contents and
  working-tree status. In particular, the three E8.1.1 uncommitted files remain
  untouched in their original worktree.
- All **53** E8 private evidence files and their existing preservation manifest
  remain unchanged. The original **72** private files and real database match
  the established baseline: schema **3**, **two** snapshots, database SHA-256
  `ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
  Database checks use a read-only transaction; no initialization, ingestion or
  migration occurred. The new public-source captures have a separate private
  eight-file preservation manifest under ignored `data/`; raw sources were not
  added to Git or routine CI. Local preservation is not independent backup.
- No repository code or tests changed, so no new unit tests were introduced.
  Full backend/frontend, numerical transformation audits, browser/PDF, builds and
  remote CI were not rerun. Earlier E8/E8.1.1 results are separate historical
  evidence, not fresh verification of this documentation task.

Only `docs/engineering-e8.2-reference-qualification.md` and
`docs/engineering-e8.2-reference-evidence.json` are new, unstaged/uncommitted
repository files. No publication, merge, deployment, production change or private
account access occurred. E4 remains **OPEN**; Swarm-A Phase 11.3.1 remains
**PARTIAL**, with scientific evaluation **BLOCKED** and no qualified residuals.

**NASA/IGS scientific study: BLOCKED — historical GP evidence and essential
frame/reference-point/ERP/quality/protocol qualification remain missing.**
