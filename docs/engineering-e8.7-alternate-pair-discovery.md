# E8.7 — Alternate historical comparison-pair discovery

Reviewed **24 October 2026**. **Scientific study: BLOCKED. No qualified
alternative comparison pair has been established.** G30 and January 1 are no
longer mandatory discovery targets, but no actual replacement GP record is selected.

**Recommended first acquisition target:** **G05 / SVN G050 / NORAD 35752 /
COSPAR 2009-043A**, for the already acquired IGS GPS-calendar day
**2024-01-01**. This is a request priority among tied metadata-screened cases,
not a claim that its historical GP exists or that it is the most accurate orbit.
The useful next step is one provider-supported historical export for this catalog
identity, **2023-12-25 through 2023-12-31**, preserving the complete original
response. No request was submitted by E8.7.

The [candidate matrix](engineering-e8.7-candidate-matrix.json) records all 32
January-1 PRNs, two listing-only date alternatives and one published verification
input lead. Sources, identifiers, quality screens, ranking dimensions, limits and
required next evidence are explicit. There are **31 alternative PRNs** in the
acquired product; the original G30 is retained separately as a baseline.

## Inventory and evidence reused

The [E8 report](engineering-e8-feasibility-report.md), unchanged
[protocol v0.1](engineering-e8-comparison-protocol.md),
[E8.2 qualification](engineering-e8.2-reference-qualification.md),
[E8.3 frame/EOP audit](engineering-e8.3-frame-eop-qualification.md),
[E8.4 quality audit](engineering-e8.4-quality-qualification.md),
[E8.5 provenance assessment](engineering-e8.5-source-provenance.md) and
[E8.6 reconciliation](engineering-e8.6-g30-statistic-reconciliation.md), their
matrices/ledgers and private reference metadata were reviewed. Previous numerical
results are reused as prior evidence, not described as freshly executed science.

The inventory covered the existing research-data areas of the four worktrees and
the non-instruction scientific uploads. **178 pre-existing files** were hashed
for preservation. Pasted request texts, credentials and private correspondence
were not used as scientific data. Test-fixture metadata was separately reviewed
because a published GPS test input is present there.

| Local evidence                     | Finding and limitation                                                                                                                                                                                                                                                                                                                              |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| IGS SP3 product                    | One distinct acquired GPS final-orbit day: `IGS0OPSFIN_20240010000_01D_15M_ORB.SP3.gz`. The named file and acquisition-body copy have the same compressed hash. 32 IDs, 96 epochs, 3,072 P records, IGS20/GPS/900-second grid.                                                                                                                      |
| Original product hashes            | Compressed **102609 bytes**, SHA-256 `26f16fa5f97cce851948fa88711aed47f60ee2e4ddfe36f0e98b1076e79fbe38`; expanded **253250 bytes**, SHA-256 `8a638375273ab74011aebd9ffcc480df02b5718440c8fb7c51c408ff220d231c`. Rechecked unchanged.                                                                                                                |
| Week-2295 summary                  | Already acquired `IGS0OPSFIN_20233650000_07D_01D_SUM.SUM.gz`; SHA-256 `2c00cc06449ed72dcb13675813a14f6d8811928f4b84d98fe6aa1eac6cd11870`. Table 3.2295.1, Day 1/MJD 60310, used for each PRN's own flags.                                                                                                                                           |
| Historical provider GP attachments | Three private archive copies of the same 644-byte Swarm-A CSV, each with three records for NORAD **39452**, spanning 2013-12-30 to 2014-01-02. The 1227-byte original JSON fails strict parsing at byte offset 128; it is **not an empty response** and no valid JSON record count is assigned. These are not GPS inputs and cannot be substituted. |
| Current GPS GP capture             | One original 32-record CelesTrak array, acquired 2026-10-24. Element epochs span **2026-10-19T07:47:32.523072** through **2026-10-23T22:32:16.581120**. It is outside the January-2024 interval. Current presence, absence or identity does not establish historical availability.                                                                  |
| Published GPS verification input   | NORAD **28129** has a 2006-epoch TLE in `phase61-sgp4.json` and the installed SGP4 verification distribution. It is a published numerical-test input, not an acquired original historical-provider export or an independently qualified orbit. See the separate lead below.                                                                         |
| Synthetic IGS fixtures             | Explicitly synthetic positions/metadata and constructed GP controls are not acquired reference products or genuine historical GP evidence. They were not ranked as comparison inputs.                                                                                                                                                               |
| Other products                     | Private ESA Swarm products are preserved; they are not alternate GPS IGS references. No historical GPS XML attachment was found in the inventoried locations. This is not a claim about files outside those locations.                                                                                                                              |

The current GPS capture SHA-256 remains
`8e1b961369ba5d083ec99b792453e26e82217f0ac609dc6f4eece432a0f5ef87`.
There is **no acquired, qualified historical GPS GP dataset** in this inventory.
There **is** a local GPS verification TLE with a historical epoch; its test-source
provenance must not be conflated with historical operational-data qualification.

## Identity lookup and PRN reuse

The retained official
[IGS satellite metadata](https://files.igs.org/pub/station/general/igs_satellite_metadata.snx),
SHA-256 `ac93d053eac7d8b08ce129b6af98667e1867296e1685417d38c081cd046558ae`,
was used through the existing `nominal_identity` function in
[the IGS inspector](../scripts/inspect_igs_reference.py). No duplicate identity
implementation or GP initialization was added.

All 32 PRNs have one nominal-date SVN/COSPAR/NORAD mapping for the reference day.
Checks at December 25, December 31, January 1 00:00 and January 1 23:45 retain
the same physical mapping for each case. The matrix preserves raw assignment
intervals and source lines. This is the existing **nominal civil-calendar**
lookup; the metadata interval time scale is not newly qualified to sub-second
precision. An open `0000:000:00000` end is an open interval, not proof of
permanent future assignment. Actual GP identity must still match NORAD and COSPAR.

For G05, `SATELLITE/IDENTIFIER` **line 1027** identifies **G050 / 2009-043A /
35752 / GPS-IIR-M**. `SATELLITE/PRN` **line 1634** assigns G050 to G05 from
**`2009:229:00000`** to **`0000:000:00000`**. Earlier G05 assignments belong to
G005 and G035. A request must identify **NORAD 35752**, not merely “GPS G05”.

PRN reuse is observable in this retained metadata: **G13 in January 2024 is
G043 / NORAD 24876**, ending `2026:114:79200`; the later G083 assignment begins
`2026:115:00000`. Using a current PRN-to-satellite relationship for the historical
day would substitute a different spacecraft. Similarly, the 2006 G22 lead below
maps to G047/28129, whereas January-2024 G22 maps to G044/26407.

## Transparent acquisition-priority ranking

No numerical independence/accuracy score is assigned. The matrix records six
dimensions for every case: historical-data acquisition feasibility, nominal-date
identity confidence, actual reference availability, potential epoch eligibility,
scientific qualification risks and unresolved dependencies.

The ranking rule uses evidence availability and metadata, before any comparison
outcome exists:

1. An already acquired reference outranks a listing-only or unconfirmed reference.
2. Within that day, **Tier A** means 96 P records, no stored missing-position
   exclusion, no blank/censored XYZ sigma fields, no marked maneuver/predicted
   orbit, and no `X`/Earth- or Moon-eclipse flag in the matching summary row.
3. **Tier B** has complete supported P quality fields but a summary eclipse or
   statistics-exclusion flag requiring review. **Tier C** has missing required
   quality fields or another supported-profile issue needing further assessment.
4. Historical GP feasibility and the potential interval are tied/unknown for all
   these January-1 alternatives. Within each tier, ascending PRN is an
   **administrative request order**, not a physical accuracy ranking or a GP-record
   selection tie-breaker. It does not alter the protocol's ambiguity rule.

Reported sigma magnitudes, header exponents, orbit-dynamics fit magnitudes and
eventual residuals are **not ranking inputs**. A blank event flag does not prove
no physical event; absence of an eclipse flag is not a new eclipse calculation.
Tier A is a metadata-completeness screen, not scientific PASS. Eclipse flags are
extra review needs, not a newly invented absolute scientific rejection rule.

| Acquisition order  | Candidate on GPS day 2024-01-01 | SVN / NORAD / COSPAR         | Screen and remaining issue                                       |
| ------------------ | ------------------------------- | ---------------------------- | ---------------------------------------------------------------- |
| 1                  | G05                             | G050 / **35752** / 2009-043A | Tier A; original historical GP missing                           |
| 2                  | G09                             | G068 / **40105** / 2014-045A | Tier A; original historical GP missing                           |
| 3                  | G11                             | G078 / **48859** / 2021-054A | Tier A; original historical GP missing                           |
| 4                  | G12                             | G058 / **29601** / 2006-052A | Tier A; original historical GP missing                           |
| 5                  | G13                             | G043 / **24876** / 1997-035A | Tier A; historical mapping differs from later PRN assignment     |
| 6                  | G16                             | G056 / **27663** / 2003-005A | Tier A; original historical GP missing                           |
| 7                  | G18                             | G075 / **44506** / 2019-056A | Tier A; original historical GP missing                           |
| 8                  | G23                             | G076 / **45854** / 2020-041A | Tier A; original historical GP missing                           |
| 9                  | G25                             | G062 / **36585** / 2010-022A | Tier A; original historical GP missing                           |
| 10–12              | G08, G10, G19                   | Full identities in matrix    | Tier B; matching summary has Earth-eclipse flags                 |
| 13–31              | Remaining 19 alternatives       | Full identities in matrix    | Tier C; blank XYZ quality codes require assessment               |
| Baseline, unranked | G30 / 39533                     | G064 / 2014-008A             | Original investigation preserved; no replacement record selected |

The first nine are scientifically **tied at this screening level**. There is no
evidence that G05 historical GP is easier to obtain than G09 or the others.
G10 remains a useful already-investigated identity (41019/G073), but its day-1
`E` flag gives an additional review need; prior static current-GP checks do not
establish a 2023 element set. A better-delivered genuine input can legitimately
change acquisition priorities before any comparison outcomes, with documentation.

## What the G05 evidence does and does not establish

G05 has 96 records, no blank or censored XYZ sigma codes, no stored missing
position, no marked maneuver/predicted orbit, and no missing-clock marker.
Its Table 3 day-1 row, **line 698**, is labelled `5`, without `X`, `E` or `M`.
These facts were checked against this product, not inherited from G30.

G05's own header is raw **`"  2"`** at SP3 **line 8, columns 22–24**. Its own
summary entries are recorded separately: Table 3 first IGS **`3`**, last IGS
**`82`**. The latter is an existing seven-day fit statistic, not an 82-mm truth
error or a newly computed residual. No candidate is preferred because of a
smaller or apparently matching number. These fields do not supply calibrated
uncertainty, a full covariance or producer-specific encoding proof.

The G30 `3`/`2`/`4 mm` investigation remains **PARTIALLY RESOLVED**, with the
producer-specific mapping open. It is not a universal prohibition on obtaining
or investigating another case. Conversely, choosing G05 does not resolve its own
quality/uncertainty/encoding questions. Any later quantitative use must state
exactly which reference indicators/statistics are used and their supported scope.
No E8.4–E8.6 findings were rewritten and no G30 acceptance was transferred.

## Other dates and the published-input lead

The retained week-2295 BKG index explicitly lists final products for
**2023-12-31 through 2024-01-06**. G05 on **2023-12-31** or **2024-01-02** is a
possible date alternative: the nominal metadata relationship is stable, but
those SP3 bodies have **not** been acquired here. Their actual time/frame/grid,
target coverage and quality remain unverified. The matrix calls them
**LISTED ONLY**, below the acquired-reference cases. A filename or listing is
not a substitute for reading the original product. No dates were changed solely
to obtain a lower fit statistic.

There is also a concrete older lead: the published verification TLE for
**NORAD 28129 / COSPAR 2003-058A**, nominally **G22 / SVN G047** on
**2006-06-25**. Its first 69-character TLE lines in the existing fixture match
the installed `SGP4-VER.TLE`; that file's SHA-256
`d246d1d9d768ace445a38a965713fa9ba52d80fd8a41a0502ff83d7acffe2881`
matches the pinned fixture provenance. No TLE, fixture or expected vector changed.

The official [Vallado et al. paper](https://celestrak.org/publications/AIAA/2006-6753/AIAA-2006-6753-Rev2.pdf)
was read in E8.7: **HTTP 200**, **667568 bytes**, SHA-256
`538a5c0ea174eb569bbc258011717142a26d72871ab07cc64ee5fa3773164b16`,
matching the earlier recorded paper hash. Appendix D, printed **page 35**, names
NAVSTAR 53/USA 175 as a non-resonant GPS test case. Its introduction to Appendix D
explains that appended start/stop/step values are verification-file extensions,
not normal downloaded TLE fields. This supports **published test-input lineage**;
it does not establish the complete government fit lineage or certify that the
original 69-character case is an unmodified operational historical export.
No general claim that this particular TLE was fabricated or modified is made.

An additional precision limitation was found without evaluating an orbit:
the raw TLE epoch **`06175.57071136`** decodes with exact decimal calendar
arithmetic to **`2006-06-24T13:41:49.461504Z`**. The fixture's one-time exported
OMM stores **`2006-06-24T13:41:49.461503`**, one microsecond earlier. Both strings
are retained unchanged. This difference is **not silently repaired or accepted**
for a new scientific pairing. Future intake must establish an exact original-
input representation and supported precision rather than copying that OMM value.

No matching 2006 IGS SP3 is local. One anonymous probe of the BKG week-1381
directory returned **HTTP 404**. It does not prove absence from every IGS archive;
CDDIS is a documented archive route but authorized access was not established,
and no login was attempted. The older case stays an **UNQUALIFIED RESEARCH LEAD**,
below cases with an actual reference. Product/frame/quality, exact temporal
eligibility and operational GP authenticity all need evidence. A public test TLE
does not automatically resolve the missing historical GP gate.

## Smallest complete-window acquisition request

Prepare one request, **not sent by this task**:

> Historical government GP element sets for **NORAD 35752**, COSPAR
> **2009-043A**, GPS SVN **G050** (PRN **G05** during the target period).
> UTC element-epoch dates **2023-12-25 through 2023-12-31**, inclusive. Please supply
> all returned records in the provider's original supported JSON/CSV format or
> OMM XML if available, with any retained source/originator/publication metadata.
> If no data are available, please state that limitation. Do not create or infer
> historical timestamps or reformat data merely to resemble an original export.

The known route is the official
[CelesTrak GP Special Data Request](https://celestrak.org/NORAD/archives/request.php),
linked by the retained GP documentation and already used by the user for G30.
That establishes a request route, **not record availability, delivery time or
format availability** for this object. The original Swarm-A CSV is evidence of
a different object's delivered data, not proof that GPS history will be delivered.
An authorized account holder's original Space-Track history export is another
possible route; no credentials, account, authentication or private query were used.

For the **same acquired 96-epoch reference grid**, the potential GP interval from
the existing forward-only, inclusive ±7-day rule remains
**[2023-12-25T23:44:42Z, 2023-12-31T23:59:42Z]**. The seven calendar dates are
the smallest date-only request enclosing that entire interval. A shorter request
might provide a candidate but would not cover the full locked search window.
Do not repeatedly query, impose a latest-one limit or drop competing records.

On delivery, preserve original bytes, receipt/source evidence, size and SHA-256
privately, without database ingestion. Review every record's NORAD/COSPAR,
epoch/model/required fields, creation/publication semantics, duplicate and same-
epoch ambiguity. Epoch does not prove historical availability; receipt is recorded
only from explicit evidence. No implicit format conversion manufactures missing
metadata. Latest unique eligible selection and refusal on ambiguity remain required
in any approved replacement protocol; no record is selected here.

## Proposed protocol change and remaining gates

The existing v0.1 document is still G30-specific and **unchanged**. E8.7 proposes
a future versioned replacement-target review: **G05/G050/35752/2009-043A**, same
hash-pinned January-1 product, exact 96 source indices, time/resource chain,
potential epoch window, inclusive guard, forward-only single GP, latest-unique
rule, ambiguity refusal, no interpolation and restricted claims. This proposal
is justified by G05's inspected identity/metadata and missing G30 delivery, not
numerical comparison outcomes. It is not approval for computation or an executed
protocol amendment.

The E8.1.1 XML inspector is explicitly configured for G30/39533; it must not be
used to certify a G05 file by relabeling inputs. A future reviewed target-aware
intake/protocol change with deterministic tests is required before qualification.
No such implementation was added in this discovery phase.

Remaining gates for **every** proposed case:

- Genuine historical GP delivery/provenance, exact identity/model/epoch validity,
  complete response and unique eligibility. None is established by current GP.
- Actual reference quality/flags and any quantitative-indicator interpretation;
  target-specific historical antenna/attitude/CoM treatment. G05 is GPS-IIR-M,
  whereas G30 is GPS-IIF; G30's physical-point evidence cannot simply be copied.
- Reviewed TEME→terrestrial/IGS realization and subdaily EOP/ERP treatment, exact
  time/precision/resources and satellite physical reference-point compatibility.
- Reference/GP uncertainty and claims policy, shared-source/fitting lineage and
  source dependencies. Statistical independence remains unestablished.
- Versioned target/protocol/intake review, final immutable inputs/resources/mask
  and explicit authorization before real propagation or comparison. Later
  descriptive product disagreement would not establish independent forecasting
  accuracy, absolute truth, anomaly or operational safety.

## Verification and final state

- The original pure nominal-identity lookup was reused for all 32 PRNs and
  nominal calendar controls; all source identity rows and interval locators were
  checked. Per-satellite quality counts were checked against original P fields
  and the existing E8 inspection. The 32×96 records were inspected only as
  metadata; no Cartesian states were exported or calculated.
- **Three existing synthetic identity tests passed, 43 deselected**. They cover
  time-dependent PRN mapping, half-open assignment boundaries and malformed/
  ambiguous metadata. They are synthetic metadata controls, not acquired evidence.
- Matrix/ranking, source and date/eligibility distinctions, cached archive links,
  published-input provenance/precision limitation, Markdown/JSON formatting,
  local links, privacy patterns, whitespace and complete two-file diff checks
  passed. Existing full suites/browser/PDF/build/remote CI were not rerun.
- The two new public-source receipts retain actual **200/404** outcomes. Four
  private capture/receipt files have their own ignored preservation manifest.
  No historical-provider GP dataset, IGS orbit product, EOP resource or private
  account data was downloaded in E8.7.
- The original **178-file** inventory, **72 original private files**, **99** prior
  private-manifest entries, all previous reports, four worktree branches/HEADs
  and **380 originally tracked files** remain unchanged. Database schema **3**,
  two snapshots and SHA-256
  `ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`
  were confirmed using read-only checks. Existing reference hashes are unchanged.
- Work remains in `engineering-e8.2-igs-reference-qualification` at
  `b0a03205e3930b55651232d8b7ffbc9e879ae8c6`. Ten earlier E8.2–E8.6 additions
  and the separate E8.1.1 additions are preserved. Only this report and the
  candidate JSON are new repository files; nothing was staged, committed,
  pushed or deployed. Local preservation is not independent backup.

**No historical GP was selected or qualified; no real-input propagation,
spacecraft transformation, orbital interpolation/extrapolation, residual or new
uncertainty calculation occurred. The study remains BLOCKED.** The separate
Swarm-A Phase 11.3.1 remains **PARTIAL**, scientific evaluation **BLOCKED**;
E4 production readiness remains **OPEN**.
