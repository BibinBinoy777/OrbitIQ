# Swarm-A frame and time qualification

Local assessment: **21 October 2026**. Data provided by the European Space Agency
(ESA). © ESA 2026. This is an input-qualification record, not an accuracy benchmark.
The original Phase 11.3 inspector, source products and reports are unchanged.

## Actual source audit and discrepancies

The retained KIN/VAL ZIPs were read completely with SHA-256 anchors, ZIP CRC and
POSIX header-checksum/size validation. Repeated current inspection exactly matches
the previous captured inspection. There are 7,647 P/EP records, no velocities,
GPS calendar timestamps, km positions and declared frame **IGb08**. Source/member
identities and processing/quality metadata are retained in the evidence and
[earlier provenance report](phase-11.3-dataset-provenance.md).

| Item | Actual retained evidence |
| --- | --- |
| KIN ZIP | `a62164ca7940d415d63a81518a974422d7868b285abc2509423bac96bd9048b3` |
| VAL ZIP | `e258ea6afb9bc998e406c5d2f7a26369d716d958da7d2961eb273b645adfeca2` |
| KIN/VAL processing | Version 0201, `L2PS-DUT/44.88`; header creation 17 May 2022 for historical sensing data |
| Header coverage | Explicit UTC `2013-12-31T23:59:44` through `2014-01-01T23:59:44` |
| Actual SP3 | SP3-**d**, first GPS record `2014 01 01 00 02 20.00000000`, last `2014 01 01 23 58 10.00000000`; nominal interval **0** |

The reviewed general [ESA L2 specification](https://earth.esa.int/eogateway/documents/d/earth-online/swarm-level-2-product-specification),
revision 3.0, describes SP3-c. The actual file is SP3-d. The retained
[SP3-d specification](https://files.igs.org/pub/data/format/sp3d.pdf) describes a
positive nominal epoch interval, whereas the source stores zero. GPS second-60
fields also lack a reviewed provider interpretation. These discrepancies remain
explicitly **unresolved**. Parsing the specimen does not resolve them. Overall
dataset qualification stops here; time-conversion diagnostics below do not
authorize a comparison or silently change the inspector's earlier interpretation.

The matching quality PDF and its headers/upstream filenames remain intact. The
retained nine-page visual review contains GPS-fit/tracking, ephemeris and SLR
plots; its header error `0` and quality `000` are not automatic per-epoch acceptance.
No defensible selected KIN interval acceptance or rejection threshold was
established from these plots/codes. The absence of a qualified quality decision
remains a mandatory gate, independent of source integrity.

## Time conversion: a qualified ordinary subset, not the full source

`scripts/qualify_swarm_inputs.py` adds a separate offline diagnostic component.
It retains the source's declared GPS time; it does not relabel GPS as UTC or
modify source records. It reuses the existing inspector's exact Decimal calendar
diagnostic and then applies additional strict checks:

1. Require explicit GPS scale, valid date/calendar and seconds in `[0,60)`.
   A source seconds field of exactly 60 is excluded pending provider clarification;
   it is not automatically rolled into the following GPS minute or called a leap.
2. Require the original eight-decimal fraction to be exactly representable at
   microsecond resolution. Submicrosecond values are excluded **before** conversion;
   they are not rounded into the existing report contract.
3. Construct GPS elapsed SI seconds from its defined calendar epoch with separate
   whole and fractional parts. Use Astropy `Time(..., format="gps", scale="tai")`
   and `.utc` under OrbitIQ's existing explicit `orientation()` resource scope.
   Astropy supplies GPS/TAI and historical leap semantics. No hard-coded GPS–UTC
   offset is applied in the new code.
4. Require the existing local leap resource and validity interval. Auto-download,
   degraded EOP results and implicit resource replacement remain disabled. The
   existing scope loads the configured EOP/leap bundle even for this time-only
   diagnostic; it does not fetch a replacement if either required file is unavailable.
5. If conversion lands on UTC second 60, reject it for propagation compatibility:
   the existing Python datetime request contract cannot represent a UTC leap second.
   Tests cover this refusal around the 2015 and 2016 leap insertions.

Astropy uses split Julian-date floating representations internally. Six-decimal UTC
output is used only after the source passes the microsecond representability check;
it does not assert unlimited precision or perfect receiver clock accuracy.
Documented literal reference instants and microsecond examples test the boundary.

Actual complete source-time audit:

| Outcome | Actual count / result |
| --- | --- |
| Ordinary timestamps converted for diagnostics | **5,118** |
| Excluded submicrosecond timestamps | **1,806** |
| Excluded source second-60 encodings | **723** |
| Total accounted for | **7,647**, each counted once in this audit |
| First converted UTC | `2014-01-01T00:02:04.000000Z` |
| Last converted UTC | `2014-01-01T23:57:54.000000Z` |
| State positions imported / prediction evaluations | **0 / 0** |

Time status is **QUALIFIED_WITH_LIMITATIONS for the ordinary subset only**. The
full dataset is not time-qualified. The 2,529 exclusions do not imply missing
physical observations or bad orbital positions; they identify unsupported time
encodings/precision for this contract. Current helper diagnostics use source
order, not residual magnitude. A future bounded evaluation can predeclare
“earliest ten otherwise qualified exact epochs inside the chosen interval,” retain
every exclusion and separately approve source quality/frame/GP lineage. No such
scientific evaluation set is approved now, and no interpolation or nearest-time
tolerance has been introduced.

The diagnostic records reference times, header interval and actual audit time
separately. GP epoch, availability, retrieval and requested scientific evaluation
are absent because no authentic GP was supplied. They are not substituted with
one of the reference or audit clocks.

## Independent time references and resource checks

The [Astropy TimeGPS documentation](https://docs.astropy.org/en/stable/api/astropy.time.TimeGPS.html)
defines seconds from 1980-01-06 00:00:00 UTC, an epoch represented as
1980-01-06 00:00:19 TAI, and gives **630720013.0 → 2000-01-01 UTC midnight**.
The explicit local IERS table supplies historical TAI–UTC rows: 35 seconds from
2012-07-01, 36 from 2015-07-01, 37 from 2017-01-01. Expected test strings were
written as independent literals from those definitions, not generated by the
conversion under test. Cases include the GPS epoch, the documented 2000 anchor,
the actual 2014 interval, date rollover, exact microseconds and leap boundaries.

Resource identities remain:

- `astropy-iers-data` version `0.2026.10.12.1.3.27`.
- EOP SHA-256 `9fbc14ae5e71de96cc1e6b43b54a547acc80c7a6ce910c0209ad6230ff3d30cd`.
- Leap SHA-256 `6cb6f5d4b819f2e568e25db4b0b26d89dedf031fdffb18bc94d40f4e94e268d7`,
  through IERS Bulletin 72, expiry 2027-06-28.

Existing strict EOP preflight succeeded at the first/last converted UTC instants,
including its ±0.5-second velocity support. This checks endpoint resource coverage,
not all 5,118 timestamps or a reference-frame transformation. Every future actual
calculation must still pass the existing per-epoch checks. Missing resources,
expired leap bounds and EOP failures are tested as refusals without fallback.

Three fresh offline audits retain separate full-report hashes. Their invariant
source/time/frame/gate projection matches exactly, with zero network/database/
process attempts. The only projection exclusions are the recorded audit clock and
its derived live `prediction_table_age_days`. Full reports differ in those fields;
they are **not** claimed byte-identical. This is reproducible input diagnostics,
not numerical propagation replay or physical accuracy validation.

## Frame definition and qualification decision

The official [IGS Reference Frame working-group chronology](https://igs.org/wg/reference-frame/)
states that IGb08 was used from GPS weeks 1709–1933 and is **aligned to the ITRF2008
datum**. [IGS Mail 6663](https://lists.igs.org/pipermail/igsmail/2012/000497.html)
describes the update from IGS08, including post-discontinuity coordinates, station
ties and antenna-related changes. [Mail 6354](https://lists.igs.org/pipermail/igsmail/2011/000188.html)
describes IGS08's relationship to ITRF2008 and antenna calibration effects.

The correct [IGb08 directory](https://files.igs.org/pub/station/coord/IGb08/)
was located; its small [station-change table](https://files.igs.org/pub/station/coord/IGb08/IGS08-IGb08.dat)
was actually read. The roughly 110-MB SINEX covariance file was not downloaded.
The earlier guessed top-level 404 does not imply the frame documentation is
unavailable. These station-specific changes are not a global satellite-state
Helmert transformation. Mail 6354's IGS05→IGS08 parameters also are not an approved
IGb08→this-pipeline mapping. They were not repurposed.

The [official ITRF2008 description](https://itrf.ign.fr/en/solutions/ITRF2008)
describes a terrestrial frame solution and its station positions/velocities/EOP.
Its datum relationships refer to epoch 2005.0; that is not a replacement for a
2014 state observation time. The acquired SP3 header does not separately supply
a realization-alignment reference epoch or transformation parameters.
OrbitIQ instead propagates SGP4/WGS72 into **TEME**, then uses Astropy's documented
[TEME→ITRS pipeline](https://docs.astropy.org/en/stable/coordinates/satellites.html)
with strict local EOP. Installed Astropy exposes `ITRS` attributes `obstime` and
`location`; this application has no explicit ITRF realization selector or IGb08
transform. The installed graph contains TEME→ITRS and no named IGb08 frame.
Absence of a built-in class does not prove transformation impossible; it establishes
that no such realization-aware operation is currently implemented or tested here.

**Frame status: BLOCKED.** Source realization is identified and its datum relationship
is documented. A precision-specific treatment relating this terrestrial output to
the acquired IGb08 product has not been approved. No target realization, justified
identity approximation/error budget, or required transformation/epoch parameters
and independent tests were established. Generic ITRS cannot silently fill these
missing assumptions. No identity, station-offset or Helmert operation was applied;
no new numerical tolerance was invented to make the alignment acceptable.

## Qualification gate and adapter contract

The new audit emits source integrity/identity, historical candidate, time, frame,
quality, documentation and lineage conditions. It remains **BLOCKED**, with
`comparison_ready=false`, `adapter_operational=false`, no normalized observations,
zero prediction evaluations and null residuals. There is no CLI approval flag.
Tests replace propagation/residual functions with failure sentinels and verify
they are never called, even when a synthetic GP record parses successfully.
Existing Phase 11 operator functionality is preserved; this gate governs the new
Swarm qualification path and does not disable established workflows/tests.

Future adapter inputs are the pinned original KIN/VAL pair, actual GP source with
genuine provenance and availability assessment, exact target mapping, selected
time interval, quality decision and approved realization treatment. Output may
reuse the existing `observation_derived_state` model in explicit UTC, supported
ITRS/TEME and km/m only after these gates; preserve original record/time/frame,
payload/member/selection hashes, processing/resource identities and uncertainty
limits. No velocity is supplied by this KIN specimen. Unsupported precision,
frame, quality, provenance or source format must remain an explicit exclusion.
No new generic format or propagation framework is justified.

The optional GP diagnostic reuses the existing one-record GP JSON parser and
checks a caller-supplied SHA anchor/target/epoch. It cannot authenticate a source,
infer publication from epoch, accept arbitrary TLE text, or qualify a multi-record
historical attachment. Parsed candidates stay PARTIAL, without a source cutoff
or forecast eligibility. No genuine candidate was available to exercise this
path; its tests are labelled synthetic format cases.
