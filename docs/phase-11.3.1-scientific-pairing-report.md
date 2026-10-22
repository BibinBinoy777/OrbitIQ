# Phase 11.3.1 — scientific reference qualification and historical pairing

Assessment: **21 October 2026**. Phase status: **PARTIAL**. Historical scientific
pairing decision: **BLOCKED**. No Swarm-A propagation, coordinate-state
transformation or ESA residual calculation was performed. This checkpoint extends
the [CSV intake checkpoint](phase-11.3.1-csv-intake-report.md), preserves prior
findings and does not authorize evaluation. Supporting execution evidence:
[scientific pairing verification](phase-11.3.1-scientific-pairing-verification.json).

## Exact source and applicable documentation

The existing private originals were reread with their independent hash anchors,
ZIP CRC, XML member lengths and POSIX checksums. No ESA product was downloaded
again and no historical GP source was replaced. The CSV was statically validated
and reconciled again: three target candidates, 51 equal values, preserved order,
six exponent-case differences, zero source precision/unexplained value changes.
Three internal JSON-integer/CSV-Decimal comparison-type differences remain
explicitly separate from source precision. The original JSON remains malformed.

| Verified property | Actual retained source |
| --- | --- |
| Product | `SW_OPER_SP3AKIN_2__20131231T235944_20140101T235944_0201` |
| Identifier / spacecraft | `SP3AKIN_2_`; Swarm-A; SP3 `L47`, NORAD 39452, designator 2013-067B |
| Version / processing | File version `0201`; creator `SPC_DUT`, version `44.88`; software `L2PS-DUT/44.88` |
| XML description | Kinematic center-of-mass position in ITRF, Earth-fixed |
| XML reference document | `SW-DS-DTU-GS-0001` |
| XML validity and sensing interval | Explicit UTC 2013-12-31T23:59:44 through 2014-01-01T23:59:44 |
| Creation / underlying execution | KIN XML 2022-05-17T12:08:43 UTC; SP3 comment identifies an October 2021 `RDOD_AR_WGT` execution; neither is the sensing or availability clock |
| Actual SP3 | `#dP`, SP3-d; frame `IGb08`; type `KIN`; agency `TUD`; explicit GPS time |
| Actual records | 7,647 epoch tags, 7,647 P records and 7,647 EP records; no V/EV records |
| Position / clock units | P XYZ km; P clock microseconds. No reference velocity exists; do not interpret clock as velocity |
| Nominal interval | `0`; actual observation epochs have gaps and 10-ns field differences; not an accepted complete regular grid |
| First / last source calendar tag | GPS 2014-01-01T00:02:20.00000000 / 23:58:10.00000000 |
| Quality metadata | XML product error `0`, quality `000`; header orbit-accuracy exponent `0` (unknown accuracy under SP3-d) |
| Matching validation product | `SP3AVAL_2_`, same interval/version/processor/upstream inputs; XML created one second later; nine-page PDF |
| KIN ZIP SHA-256 | `a62164ca7940d415d63a81518a974422d7868b285abc2509423bac96bd9048b3` |
| VAL ZIP SHA-256 | `e258ea6afb9bc998e406c5d2f7a26369d716d958da7d2961eb273b645adfeca2` |
| KIN SP3 member SHA-256 | `c6c9c0c610c64258abf7b0e7c38d0429fb73a90768b0c600a43f6c3f1f43eb27` |
| CSV original SHA-256 | `2b5712d5c2fe3fd6f8106633cb84780d6562eb455f49922fbbbbe9d09a26f1c4` |

Eleven authoritative documents/pages were actually retrieved with TLS verification,
read and hash-preserved privately. Their URLs, receipt times, sizes and hashes are
in the execution evidence. They include:

| Reference | Precisely supported finding |
| --- | --- |
| [ESA Swarm L2 specification, revision 3.0, 2021-02-25](https://earth.esa.int/eogateway/documents/d/earth-online/swarm-level-2-product-specification), §§4.3.2, 5.9.1, printed pp.28, 94–95 | **Explicit KIN table**, GPS observation epochs, center-of-mass ITRF position, KIN inputs/units and nominal specifications; not COM assumptions transferred to KIN |
| Same specification, detailed `SP3xVAL_2_` table, printed p.95 | Defines validation for **both COM and KIN**, with both orbit solutions, ILRS tracking and processing diagnostics as inputs |
| [IGS SP3-d, 21 February 2016](https://files.igs.org/pub/data/format/sp3d.pdf), pp.14–17 and Appendix A | Time indicators, positive interval requirement, frame label, position/clock/velocity units, missing-value and uncertainty conventions |
| [IGS Reference Frame chronology](https://igs.org/wg/reference-frame/) and [IGS Mail 6663](https://lists.igs.org/pipermail/igsmail/2012/000497.html) | IGb08 aligned to ITRF2008 datum; adopted from GPS week 1709 and applicable in the 2014 period; station discontinuity/tie updates are not a global satellite transform |
| [Official ITRF2008 description](https://itrf.ign.fr/en/solutions/ITRF2008) and [IERS Conventions, chapter 5](https://iers-conventions.obspm.fr/content/chapter5/icc5.pdf) | Terrestrial realization and Earth-orientation concepts; do not supply a qualified mapping for this specific GP/KIN pair |
| [ESA GNSS time references](https://gssc.esa.int/navipedia/index.php/Time_References_in_GNSS) and [USNO TAI–UTC history](https://maia.usno.navy.mil/ser7/tai-utc.dat) | Continuous GPS, no GPS leap seconds; historical TAI–UTC offsets used for an independent January 2014 calendar check |
| [Astropy TimeGPS](https://docs.astropy.org/en/stable/api/astropy.time.TimeGPS.html), [satellite coordinate guide](https://docs.astropy.org/en/stable/coordinates/satellites.html) | GPS epoch/TAI definition and documented TEME→ITRS method; installed source was separately inspected |
| [CelesTrak GP format documentation](https://celestrak.org/NORAD/documentation/gp-data-formats.php) | UTC/TEME/Earth/SGP4 omitted-field conventions and general SSN observation fitting description; not record-specific fit or availability proof |

The ESA detailed KIN table itself lists GPS **observation epochs**, SP3-c, km
position/dm/s velocity, nominal “10 cm 3D” position uncertainty and 21-day latency.
These apply as **documented KIN specifications**, not measured performance or a
guaranteed bound for each 0201 epoch. Its nominal resolution includes 1 ps time,
whereas the actual epoch tags have eight decimals (10 ns text resolution) and the
current software contract supports microseconds. Actual clock-field resolution
is a separate quantity. The table's velocity units do not establish velocities
in a position-only file.

The summary inventory on printed p.43 labels VAL for COM only; the detailed p.95
table expressly includes KIN. This resolves **documented VAL applicability** but
not a KIN-specific quality decision from the acquired PDF. Revision 3.0 describes
SP3-c while the actual baseline produces SP3-d; no baseline-specific change note
was established. The actual named realization is more specific than generic ITRF
in the XML/specification, rather than an automatic frame-label contradiction.

Two search-engine requests returned HTTP 429 and were not retried. A guessed ESA
Docs directory returned 404, an Astropy online-source route returned 404 (installed
source was read instead), and a guessed ESA catalogue route returned HTTP 200 with
an `undefined` shell and no product content. None was used as supporting evidence
or proof that documentation does not exist. Official POD navigation did confirm
separate KIN, RD and VAL directories. No contact message or data request was sent.

## Timing and candidate assessment

All three GP rows retain the original numeric strings and complete parsed-model
traceability in the unchanged private CSV capture. No creation, publication,
archive-availability, provider-email receipt or acquisition timestamp is present.
Local storage time and the request timestamp do not fill these fields. The source
is user-attributed to CelesTrak; sender authenticity was not independently checked.

Offsets below are **reference UTC minus GP epoch**, in seconds, computed using
exact integer microseconds. First/last refer only to the ordinary converted
subset, UTC 2014-01-01T00:02:04 through 23:57:54. No scientifically accepted
reference epochs or evaluation interval have been selected.

| Source index | GP epoch text, UTC convention | Element set / revolution | First offset (s) | Last offset (s) | Reference before / after GP epoch |
| --- | --- | --- | ---: | ---: | --- |
| 0 | `2013-12-30T20:24:39.765600` | 35 / 583 | +99444.234400 | +185594.234400 | 0 / 5,118 |
| 1 | `2014-01-01T05:30:45.095904` | 36 / 604 | −19721.095904 | +66428.904096 | 1,223 / 3,895 |
| 2 | `2014-01-02T06:43:57.421344` | 37 / 620 | −110513.421344 | −24363.421344 | 5,118 / 0 |

Every candidate fits the unchanged inclusive ±7-day source-epoch constraint at
all 5,118 ordinary epochs; none has an exactly coincident reference epoch. Those
are software-bound and calendar facts, not evidence of accuracy or availability.
Datetime offsets use the existing nominal UTC-calendar convention; there is no
UTC leap insertion between these specific dates. They are not a new propagation
or receiver-clock model.

For an initial condition preceding the **first ordinary calendar epoch**, only
record 0 has an earlier element epoch. Record 1 could meet that epoch-order
condition for a later interval; record 2 implies backward propagation throughout
this ordinary day. No nearest-record choice, moving reference interval or
future-record substitution is approved. A scientifically justified quality/time
selection must be declared before an initial record can be accepted. All three
remain timing candidates; none is selected. Unknown historical availability means
any later justified comparison is **retrospective**, never a demonstrated forecast.

## Time qualification and new header contradictions

Fresh source audit retains **5,118 converted, 1,806 submicrosecond exclusions,
723 second-60 exclusions: 7,647 accounted for, 2,529 excluded**. Each excluded row
retains its source index and reason. No rounding, second-60 rollover, grid snap,
interpolation or substituted timestamp was introduced.

The converted epochs were independently cross-checked using historical calendar
arithmetic for this limited interval. USNO lists TAI−UTC=35 s from 2012-07-01
until 2015-07-01; GPS has TAI−GPS=19 s. Thus January 2014 nominal GPS−UTC=16 s.
All 5,118 accepted actual source tags are integral seconds and match that separate
literal calendar calculation. This is **not a hard-coded production converter**,
not a repair for excluded tags, and not evidence of physical GPS/receiver clock
accuracy. The production diagnostic still uses Astropy split TimeGPS→UTC under
explicit local leap resources. GPS has no leap seconds; ordinary-minute GPS
second-60 fields are not approved leap events.

The new exact redundant-header check found:

| Header relation | Actual result |
| --- | --- |
| First `#dP` calendar and first `*` epoch | Agree at GPS 00:02:20 |
| `##` GPS week / seconds-of-week | Week 1773, second 259220 identifies GPS 00:00:20; **120 s earlier** than the first calendar epoch |
| `##` MJD day / fraction | Day 56658, fraction `0.0016203703708` gives 140.00000003712 s into the day; **37.12 ns later** than the first calendar epoch |
| Nominal interval | `0`, contrary to normative SP3-d positive interval; KIN's observation-epoch sampling does not alone approve this zero encoding |

No tolerance was introduced to erase either discrepancy. The `##` values were
not used to shift or replace calendar epochs. The earlier 5,118 conversions remain
**conditional diagnostics under the explicit calendar-tag/GPS interpretation**,
not a resolution of the source's internal inconsistency. The header validity
period is UTC, a separate metadata clock; it is not substituted for record tags.
The exact source member hash remains unchanged. Producer/version clarification
or an authoritative erratum with independent examples is needed before approving
a scientific time policy, even for a selected ordinary subset.

All **5,118 converted epochs** now pass the existing EOP/leap preflight, including
±0.5-second velocity support, rather than just interval endpoints. This establishes
resource coverage and flags, not a spacecraft transformation or realization
alignment. Local resources remain:

- Astropy `7.2.3`, PyERFA `2.0.1.5`, sgp4 `2.27`;
  `astropy-iers-data 0.2026.10.12.1.3.27`.
- EOP SHA-256 `9fbc14ae5e71de96cc1e6b43b54a547acc80c7a6ce910c0209ad6230ff3d30cd`.
- Leap SHA-256 `6cb6f5d4b819f2e568e25db4b0b26d89dedf031fdffb18bc94d40f4e94e268d7`,
  expiry 2027-06-28.

Auto-download and degraded EOP fallbacks remain disabled; no resource or range
policy was changed. Full-source time qualification remains **PARTIAL**, with
scientific epoch selection **BLOCKED**.

## Frame compatibility decision

Current calculated state convention is SGP4/WGS72, geocentric TEME, km and km/s,
using nominal UTC calendar days. Existing Astropy handling produces geocentric
ITRS at the same `obstime`. Installed code uses UT1-driven ERFA GMST82 and polar
motion, omitting the TIO locator s′ in accordance with the documented Vallado
TEME convention. Velocity uses the existing finite-difference support. The
application rejects unvalidated leap-spanning terrestrial calculations. No such
state calculation was run on genuine Swarm inputs in this task.

| Candidate operation | Method / parameters / validity | Verification and unresolved uncertainty |
| --- | --- | --- |
| Existing TEME→ITRS | Vallado/Astropy sidereal rotation and polar motion at the epoch; strict local UT1−UTC, xp, yp and leap resources; same observation time | Published numerical reference audit rerun; all actual ordinary-epoch resource preflights pass. These do not quantify physical orbit or realization errors |
| ITRS→actual IGb08 realization | **No approved operation**; input terrestrial realization, target alignment, epoch treatment and precision-scoped method must be established | No qualified parameters/rates, reference epoch, covariance/error budget, applicability interval or independent realization test exists for this pipeline/reference pair |
| Identity approximation | **Not adopted**; would require a stated comparison precision and defensible datum/alignment/model error budget | No assumption that an unspecified ITRS label equals IGb08; no invented tolerance |
| Station offsets / arbitrary Helmert | **Not applicable without a justified satellite-state mapping** | IGS station discontinuities/ties and other-realization parameters are not repurposed |

IGb08's documented ITRF2008 datum alignment is established; it does not supply the
missing application-specific realization/error treatment. Conversely, lack of an
Astropy class named IGb08 does not prove comparison impossible. The actual
scientific precision objective and approved mapping/approximation must be stated
and independently verified. IERS GCRS↔ITRS conventions are explanatory references,
not permission to substitute GCRS for TEME. **Frame alignment remains BLOCKED.**

## Kinematic quality, provenance and independence

All 7,647 P/EP pairs were checked. No zero XYZ component/missing-position sentinel
was found, no EP axis overflow/zero sigma or out-of-range correlation was found,
and no extended P quality flags are present (the P records end at column 60).
Header accuracy exponent zero means **unknown**, not a perfect reference. EP
formal uncertainty ranges are X 5–95 mm, Y 5–85 mm and Z 6–97 mm; clock sigma
36–311 ps. They are formal source estimates, not empirical error bounds. The six
correlation integers retain the SP3-d scaling of 10^7. No covariance, independence
assumption, quality threshold or prediction uncertainty was inferred from them.
Actual coordinate text resolution is 1 mm; printed precision does not establish
physical accuracy.

The hash-matching nine-page VAL PDF was newly rendered and visually reviewed in
full. Page 1 concerns GNSS visibility/tracking; page 2 explicitly shows RDOD fit
residuals/clock/accelerations; pages 3–4 show GNSS pseudorange/carrier-phase plots;
page 5 has tracking/status color blocks without a sufficient acceptance legend;
page 6 names RDOD ephemeris files, not an identified KIN-member comparison; page 7
is blank apart from its number; pages 8–9 show “Swarm-A POD” SLR plots without an
unambiguous mapping to the exact KIN member. Provider residual plots were read as
existing evidence; **OrbitIQ calculated no real residuals**. No plot statistics
were digitized or turned into OrbitIQ accuracy metrics. Broad VAL applicability
is documented, but that alone does not make every plot KIN-specific or supply an
accepted epoch mask. No separate baseline-specific KIN quality approval was
established in this bounded investigation.

Actual XML lineage lists onboard GPS RINEX (`GPSA_RO_1B`), attitude
(`STRAATT_1B`), spacecraft model (`MODA_SC_1B`) and dynamics (`SC_ADYN_1B`), all
0401-named products. These upstream files were not acquired or inspected here.
The **KIN-specific** table also lists external IGS, IERS and CODE contributions;
it does not identify the exact external product versions used in this run.
GP documentation describes general SSN-observation fitting, but these three
records contain no sensor/fit ledger. ESA processing is external to OrbitIQ;
statistical independence of this specific GP/reference pair remains
**NOT ESTABLISHED**. Different providers, formal correlations within EP, and
provider SLR plots cannot establish that independence. Prediction uncertainty and
unmodelled reference systematic effects remain unquantified.

Payload integrity, identifier agreement, provider attribution, historical
availability, observation origin and processing independence are separate facts.
A product reprocessed in 2021/2022 and downloaded later is appropriate evidence
for a retrospective investigation, not proof of an OrbitIQ forecast made in 2014.

## Scientific gates and exact prerequisites

| Gate | Status | Evidence still required before real evaluation |
| --- | --- | --- |
| Source identity | PARTIAL | IDs agree; independently support exact GP delivery/provider provenance, retaining remaining limitations |
| Historical GP structure / static model | PASS | Three accepted-format records; dynamic operational input check belongs to a separately authorized evaluation stage |
| Initial-record selection | BLOCKED | Predeclare an objective-based rule, evaluation anchor and handling of future/older records; no nearest-record convenience selection |
| Qualified reference epochs / temporal pairing | BLOCKED | Accepted time/quality policy and indexed reference selection; exact offsets alone do not select epochs |
| Time conversion | PARTIAL | Retain all 2,529 exclusions; disposition of 120-s header conflict, 37.12-ns fractional discrepancy, zero interval, SP3-c/d and GPS second-60 conventions |
| Coordinate alignment | BLOCKED | Defined precision objective, realizations, method/parameters or justified approximation, reference epoch/validity/error budget and independent checks |
| Sufficient reference quality | BLOCKED | KIN-specific interpretation of applicable VAL/EP information, accepted epoch/interval criteria and uncertainty limits for version 0201 |
| Provenance / independence limits | PARTIAL | Record availability remains unknown; actual-pair fit/reference dependencies must be assessed and disclosed; do not claim independent accuracy |
| Reproducible evaluation configuration | BLOCKED | Freeze all original/member/selection/resource hashes, exact units/frames/times, method/version/limits and interpretation **after** the scientific gates pass |
| Operational evaluation | BLOCKED | Qualified input/reference pair and separate authorization; no current operational adapter, normalized observations, predictions or residuals |

No evaluation configuration is approved; `selected_source_index=null`,
`accepted_reference_indices=[]`, `comparison_ready=false`,
`adapter_operational=false`, predictions and coordinate transformations zero,
residuals null. These controls are not affected by successful parsing. A proposed
future comparison may be called retrospective only after its other scientific
gates pass; “retrospective” does not excuse bad time/frame/quality handling.

For continuity with the original 22-criterion Phase 11.3.1 assessment:

| AC | Current status / precise scope |
| --- | --- |
| 1 implementation/reports inspected | PASS — current 58-path starting tree and actual evidence audited |
| 2 authentic ESA files verified | PASS — pinned original ZIP/member integrity and acquisition provenance retained |
| 3 product/spacecraft/quality/provenance documented | PASS — specific KIN semantics, applicability and limitations above |
| 4 authorized historical-source investigation | PASS — supplied CSV inspected; no account/form/contact bypass |
| 5 historical GP acquired/validated | PARTIAL — actual CSV passes static checks; authentication, availability and operational qualification incomplete |
| 6 spacecraft identifier matching | PASS — source labels L47 / 39452 / 2013-067B agree; not provider authentication |
| 7 temporal overlap/pair suitability | BLOCKED — all offsets fit software bounds, but no approved scientific selection |
| 8 lineage/independence limits | PASS — NOT ESTABLISHED clearly recorded; not an independence pass |
| 9 actual GPS timestamp conventions | PARTIAL — source declaration and conditional calendar semantics checked; discrepancies unresolved |
| 10 required conversions tested | PARTIAL — ordinary subset and independent arithmetic checked; full-source policy unqualified |
| 11 frames/realizations identified | PASS — actual TEME/ITRS/IGb08 identified; not an alignment pass |
| 12 realization alignment qualified | BLOCKED — missing precision-scoped treatment and independent verification |
| 13 EOP/leap requirements preserved | PASS — all ordinary-epoch preflights, explicit resources and existing refusal tests |
| 14 invalid-residual gate | PASS — offline failure guards record zero attempts |
| 15 actual-source adapter requirements | PASS — explicit prerequisites, not a working scientific adapter |
| 16 qualified operational adapter | BLOCKED — deliberately not activated |
| 17 no fabricated residuals/results | PASS — genuine evaluation counts zero, uncertainty limits explicit |
| 18 existing data/evidence preserved | PASS — originals, prior implementation and DB fingerprints checked; only an additive report pointer changes an earlier report |
| 19 scientific regressions | PASS — fresh backend/scientific/golden checks listed below |
| 20 new checks where verified gaps existed | PASS — new timing, header-consistency, all-epoch EOP and quality-field checks with synthetic tests |
| 21 quality/build/regression checks | PASS — fresh build/tests/lint; earlier browser/PDF evidence source hashes checked, those flows not rerun |
| 22 remaining limitations/actions | PASS — exact unsatisfied prerequisites and manual clarification checklist |

This is **16 PASS / 3 PARTIAL / 3 BLOCKED** within the named legacy criteria;
several PASS items concern documentation or protection of a blocked condition.
It is not a declaration that the scientific pair is accepted.

## Implementation, reproduction and executed checks

Added `scripts/assess_swarm_pairing.py` and
`backend/tests/test_swarm_pairing_assessment.py` (**22 synthetic cases**).
The offline script composes the existing source inspector, CSV model validation,
GPS conversion and EOP scope; it does not modify them or introduce another
propagator. New checks address previously untested full-epoch EOP coverage,
redundant GPS header consistency, exact signed pairing offsets, fixed-width EP
interpretation, single zero-component flags and correlation/sigma boundaries.
There is no HTTP client, database writer, approval flag or real calculation path.
Full per-source-row reports remain private; public tests contain no actual source
coordinates or GP payload.

With retained originals and the locked development environment, run:

```sh
PYTHONPATH=backend uv run --locked python scripts/assess_swarm_pairing.py \
  --kinematic /absolute/private/SW_OPER_SP3AKIN_2__20131231T235944_20140101T235944_0201.ZIP \
  --kinematic-sha256 a62164ca7940d415d63a81518a974422d7868b285abc2509423bac96bd9048b3 \
  --validation /absolute/private/SW_OPER_SP3AVAL_2__20131231T235944_20140101T235944_0201.ZIP \
  --validation-sha256 e258ea6afb9bc998e406c5d2f7a26369d716d958da7d2961eb273b645adfeca2 \
  --gp-csv /absolute/private/sat000039452.csv \
  --gp-csv-sha256 2b5712d5c2fe3fd6f8106633cb84780d6562eb455f49922fbbbbe9d09a26f1c4 \
  --output /absolute/private/NEW-pairing-assessment.json
```

Optional `--csv-metadata` uses the existing bounded metadata schema. Unknown times
remain unknown. The output directory must already be owned mode 0700, without
symlinks; output is exclusive mode 0600. Exit 0 means an assessment completed,
**with a BLOCKED pairing decision**, never scientific approval. Keep outputs in
private Git-ignored storage. The report retains source indices, errors/uncertainty
fields and ordinary/excluded time rows; it is not a portable observation package.

| Newly executed check | Actual outcome |
| --- | --- |
| Focused source/time/CSV/reconciliation/pairing tests | 303 passed, including 22 new cases |
| Final full backend | 1,177 passed; two warnings: Starlette/httpx deprecation and an intentional duplicate-ZIP fixture |
| Frontend | 344 passed, 25 files |
| Locked sync, Ruff lint/format, ESLint, Prettier, TypeScript, Vite production build, whitespace | PASS |
| SGP4 / earth-fixed / expanded-science audits | 40 / 6 / 32 passed, zero failed |
| Independent geodesy / round-trips | 28 / 28 passed |
| Golden evidence lifecycle | Six published components and three exact offline replays passed |
| Actual-source offline audit | All 7,647 source rows assessed; 5,118 conversions, independent historical arithmetic checks and all-epoch EOP preflights pass; zero network/DB/process/propagation/transform/residual attempts |
| Preservation | All 39 preexisting private files, original CSV/JSON/ESA files and full ordinary DB fingerprint preserved; prior implementation and earlier evidence unchanged |
| Browser/PDF regressions | **Not rerun**; the prior 77 flows and seven PDFs remain earlier evidence, with application/browser source hashes verified unchanged |

The initial 19 new cases passed. An expanded header test then failed because its
expected GPS-week agreement was incorrect: independent calendar arithmetic
confirmed the actual 120-second discrepancy. The expectation was corrected to
assert the discrepancy, and a separate consistent-week synthetic control was
added. Final focused and full suites reran after the test changes. No original
test, scientific limit or data field was relaxed. Early failing logs were retained.
The earlier 19-case full-suite run and first expanded failing run are not reported
as final verification. Application/runtime/frontend sources were unchanged by the
subsequent operator-only header diagnostic; frontend/build/science/golden results
remain applicable, and final backend/lint cover the final files.

Private document captures and full diagnostics use new ignored directories;
task logs are in `/tmp/orbitiq-reference-qualification/`. They are local evidence,
not off-machine backup or production recovery verification. Original database
SHA-256 remains `ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`,
schema 3, two genuine ISS snapshots and no Swarm snapshot. No initialization,
migration, ingestion, restore or ordinary database write was performed.

## Next scientific task and operational boundary

Use the [manual scientific clarification checklist](phase-11.3.1-scientific-clarification-request.md)
to obtain a baseline-specific disposition of the **120-second header conflict**,
fraction/second-60/interval conventions, KIN-specific quality evidence and IGb08
processing/realization assumptions. In parallel, define the intended scientific
precision and predeclare quality/temporal inclusion rules. Only then can a
realization/error-budget treatment and frozen retrospective input configuration
be independently reviewed. If these inputs cannot be supplied, retain the BLOCKED
decision or acquire a separately justified reference; do not patch source times or
choose another interval to force a result. No request was submitted by this task.

Branch/HEAD and empty index remain unchanged. No commit, push, publication, remote
CI, deployment, DNS or production action occurred. Phase 8 public HTTPS/hosting,
independent recovery, alert delivery and production verification remain separate
open milestones. Local scientific diagnostics do not close them.

## Provider response checkpoint — 22 October 2026

See the [provider response reconciliation](phase-11.3.1-provider-response-reconciliation.md)
for the user-reported CelesTrak findings and exact `ELEMENT_SET_NO` review.
CSV is the supported format path; corrected JSON is no longer a prerequisite.
The provider does not retain record-creation timestamps, and the reported metadata
does not establish historical availability or complete record-specific fitting
lineage. Any future qualified comparison remains retrospective unless separate
availability evidence is obtained; independence remains **NOT ESTABLISHED**.
ESA's response remains pending under the existing exact product reference.
None of the scientific gates, timing diagnostics, exclusions or execution results
above changed. Phase 11.3.1 remains **PARTIAL**, scientific evaluation **BLOCKED**.
