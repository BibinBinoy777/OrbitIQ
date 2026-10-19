# Phase 6.1: scientific verification and accuracy assessment

Verified locally on **19 October 2026**; scientific timestamps below are UTC.
See [structured evidence](phase-6.1-scientific-evidence.json) for complete inputs,
expected/actual values, residuals, source acquisitions, command output and hashes.

## Outcome

The assessment and justified improvements are implemented. **21 criteria PASS,
one FAIL, one BLOCKED**; this is not an all-green scientific certification.

- The original fixed-EOP residual is reproduced: **1.3173657407605788 cm** maximum
  position component; **1.328680090619432 cm** Euclidean norm. Controlled date
  precision/evaluation-order experiments explain its dominant position term.
  No runtime position-transform defect was demonstrated; no tolerance changed.
- Ten additional distinct published SGP4 vectors pass through both TLE and OMM.
  Four cases computed by a separate mathematical transform implementation pass. One new
  high-altitude geodetic latitude research target is **not met** and remains
  explicitly failed. The library calculation was not rewritten to hide it.
- Full backend: **519 passed, 1 strict XFAIL**; frontend: **180 passed**.
  Original 40 SGP4 and six terrestrial comparisons pass unchanged. New standalone
  audit: **31 comparison cases PASS, one FAIL, exit 1**. XFAIL is not a pass.
- Observation-based prediction validation is **BLOCKED**: zero independent
  satellite observations were used. Real GP snapshots are orbital inputs, not
  observations. No prediction uncertainty, universal accuracy or confidence
  percentage is established.
- Phase 6 artifacts, database bytes, snapshots and ingestion ledger are preserved.
  No commit, push, deployment, publication, remote change or workflow action ran.

## Baseline and inspected implementation

Repository: `BibinBinoy777/OrbitIQ`, `main`, HEAD
`6c60655402b70306f654c3f9b30f79ff6c7c3e45`. There were **36 pre-existing dirty
files** from Phase 6, not a clean checkout. A 138-file content manifest and
database/schema/table fingerprints were captured before changes. Repository
instructions, all requested Phase 2–6 reports/evidence, readiness and controlled
EOP maintenance documentation existed and were inspected. No missing report was
assumed to exist. Runtime/setup skill guidance was applied; network policy was
unrestricted through the session proxy, with no observation-archive credentials
configured. No environment configuration or dependency upgrade was needed.

Inspected `orbits/engine.py`, `elements.py`, `coordinates.py`,
`earth_orientation.py`, sampling/freshness, scientific services/schemas, readiness,
ingestion/storage, fixtures, reference scripts and associated tests. Installed:
Python **3.12.14**, SGP4 **2.27**, Astropy **7.2.3**, PyERFA **2.0.1.5**,
astropy-iers-data **0.2026.10.12.1.3.27**, NumPy **2.5.4**. Both lockfiles and
dependency declarations remain unchanged.

Initial executed baseline:

| Check | Exit | Actual result |
| --- | --- | --- |
| `uv run --locked pytest -q` | 1 | 459 passed, one failed |
| Isolated failing history test rerun | 0 | One passed |
| `cd frontend && npm test` | 0 | 180 passed, 15 files |
| Original SGP4 audit | 0 | 40 comparisons passed |
| Original terrestrial audit | 0 | Six comparisons passed |

The initial failure was
`test_phase5.py::test_history_beyond_100_and_bounded_unknown_count`, a
`KeyError: scanned_count` after parsing the history response without checking its
HTTP status. It ran concurrently with other baseline work; the initial response
status/body were not captured. A resource/read-budget failure is plausible but
**not proven**. The isolated rerun passed before changes. Added only a status/body
assertion before JSON access so recurrence is diagnosable; no retry, budget,
expected result or scientific assertion was weakened. Two subsequent complete
suites passed apart from the disclosed new XFAIL. The intermittent baseline
failure's underlying cause remains undetermined; it is not claimed fixed.
Phase 6's recorded 460/180 result is historical evidence, not substituted for this
phase's initially imperfect run.

## Fixed-EOP Appendix C residual

Source: Vallado et al., *Revisiting Spacetrack Report #3*,
[AIAA-2006-6753-Rev2](https://celestrak.org/publications/AIAA/2006-6753/AIAA-2006-6753-Rev2.pdf),
Appendix C, printed page 32. The PDF was independently reacquired (HTTP 200), SHA-256
`538a5c0ea174eb569bbc258011717142a26d72871ab07cc64ee5fa3773164b16`.
Paper input digits are retained, including y=6127.64465950 km (slightly different
from upstream Astropy's transcription).

This is a **standalone Cartesian TEME state**, not a propagated TLE case. The
paper does not supply corresponding orbital elements/element epoch for this
vector. Those fields are null in the evidence, not invented from adjacent cases.
The frame state epoch equals the transformation evaluation time:
**2004-04-06T07:51:28.386Z**.

| Quantity | Position (km) | Velocity (km/s) |
| --- | --- | --- |
| TEME input | [5094.18016210, 6127.64465950, 6380.34453270] | [-4.746131487, 0.785818041, 5.531931288] |
| Published ITRF expected | [-1033.47938300, 7901.29527540, 6380.35659580] | [-3.225636520, -2.872451450, 5.531924446] |
| Current ITRS output | [-1033.4793961736575, 7901.295273670422, 6380.356595751121] | [-3.225636449045851, -2.872451446066407, 5.5319244463025825] |

Reference EOP: DUT1=-0.439961 s; xp=-0.140682 arcsec; yp=0.333309 arcsec;
TAI−UTC=32 s. These are reference-only fixed parameters, never an application
fallback. Sequence: TEME → GMST82 Earth rotation → polar motion → ITRS, sp=0,
same instant. Astropy's velocity uses a one-second finite difference, with EOP
at -0.5, 0, +0.5 seconds. No precession to GCRS is added to this TEME convention.
The printed ITRF reference is compared under the existing ITRS convention; this
does not verify every terrestrial reference-frame realization.

UTC→TAI: 07:52:00.386; UTC→TT: 07:52:32.570; UT1: 07:51:27.946039.
TT−TAI=32.184 s. UT1 two-part JD is
`[2453102.0, -0.17259321714120376]`. Each signed residual is actual minus
expected; the criterion is max absolute Cartesian component, with relative
tolerance zero. Original tolerances remain **2e-5 km (2 cm)** and
**1e-6 km/s (1 mm/s)**. They accommodate finite reference/convention precision and
finite-difference velocity, not every printed digit or real prediction error.
Current maximum velocity residual is **0.07095414922275722 mm/s**.

Controlled investigation, reproducible by the new offline script:

| Position calculation | Max paper residual | Finding |
| --- | --- | --- |
| Existing two-part Astropy/ERFA | 1.3173657407605788 cm | Original result reproduced |
| Independent 50-digit Decimal C-1 + explicit rotations | 1.3173693105272832 cm | Agrees with current position within 3.57e-11 km; GMST differs by -4.44e-15 rad |
| Collapse formed UT1 JD, then polynomial | 2.32126883474848 cm | Different rounding order worsens agreement; UT1 error -17.4431405 microseconds |
| Round UTC JD, add DUT1/86400, then polynomial | 0.048867150326259434 mm | Reproduces the printed position very closely; UT1 error +22.7899947 microseconds |

The last experiment explains more than 99.5% of the original maximum component.
It uses the paper's equation and independently acquired official CelesTrak ZIP
`gstime.m` convention. The ZIP also supplies `teme2ecef.m` with nominal Earth spin
adjusted by LOD; controlled velocity variants are recorded. With nominal spin
7.292115e-5 rad/s and LOD=0, max velocity residual is 0.0012640844 mm/s. Other
documented spin/LOD combinations differ. The paper does not specify LOD here;
the archive contains later code revisions, not proof of the authors' exact
2006 execution. Remaining submillimetre/velocity terms and exact historical
arithmetic are not certified.

**Conclusion:** evidence supports a dominant reference numerical precision/order
mismatch, rather than a demonstrated OrbitIQ position defect. The independent
high-precision calculation agrees with the existing two-part calculation. Keep
the original test and runtime equations. This does not establish a universal
centimetre accuracy claim or justify reducing runtime precision to match print.

## Coverage audit and justified additions

Original **40 SGP4 comparisons = 20 distinct published vectors × two input
paths**, not 40 independent references. Six satellite inputs: 5, 4632, 8195,
14128, 6251, 28057. Coverage includes near/deep-space, resonance, negative
offsets, low-perigee and nearly circular LEO, position and velocity. Separate
existing science/API tests cover timezone normalization, fractional epochs,
inclusive ±7-day product window and immediate rejection beyond it, nonfinite
and malformed inputs, SGP4 failures, deterministic output, provenance and
atomic bounded sampling. Those are contracts, not extra published orbit states.

New `phase61-sgp4.json` supplies **ten additional distinct vectors / 20 checks**:

| Input | Offsets, minutes | Coverage reason |
| --- | --- | --- |
| 8195, 14128 | 2880 each | Later 12-hour resonance and synchronous deep-space propagation |
| 26900 | 9300, 9400 | Near-GEO Lyddane/inclination-sensitive branch, within seven days |
| 28129 | 0, 1440 | Nonresonant GPS regime |
| 28350 | 0, 1440 | Very low perigee / modified drag terms |
| 28626 | 0, 1440 | Near-zero GEO inclination |

Expected vectors are literal rows of published `tcppver.out` from pinned
python-sgp4 2.27 (hash and 1-based source line recorded), not OrbitIQ-generated.
TLE bytes match the independently retrieved official CelesTrak ZIP. OMM inputs
are a one-time export of the same TLE, not independent expectations. All use
WGS72, improved mode, TEME, km/km/s, nominal UTC days. Printed precision is eight
position and nine velocity decimal places. Absolute tolerances remain
**1e-5 km / 1e-8 km/s**, allowing printed precision and microsecond datetime epoch
representation; rtol=0. Total: **30 distinct vectors, 60 comparisons, ten satellite
inputs**. This remains verification of selected published SGP4 cases, not a full
branch proof, alternative physical model, observations or forward error bound.

Original six terrestrial cases are **not six independent end-to-end pipelines**:
one Vallado vector under fixed/bundled EOP (two comparisons), the official
Astropy satellite example (one), SOFA geodesy (one), and UTC→TAI/UT1 component
constants (two). There are only two distinct full-chain input scenarios; the
Astropy example and SOFA components share the production library stack.

New terrestrial verification uses four explicit mathematical transform controls
(published Cartesian input, equatorial, polar-adjacent, distant non-equatorial)
at four epochs. A separate Decimal/math implementation evaluates C-1 with 50
digits, explicit R3 and polar matrices, analytic derivative with constant EOP.
It never uses an OrbitIQ/Astropy/ERFA transform output to generate expectations.
These are independently implemented normative equations, **not historical EOP
measurements or satellite observations**, and not a second dynamical model.
New absolute component targets: **1e-7 km / 1e-7 km/s**, allowing binary64 rotations
and Astropy finite-difference truncation/cancellation. All four pass.

Five independent WGS84 forward-equation anchors exercise near both poles, both
sides of the antimeridian, negative ellipsoidal height, and non-equatorial
GEO-height geometry. Three extra published SOFA constants exercise GMST82,
TAI→TT and UT1→TT. The SOFA comparisons use the same ERFA implementation under
test; they are published numerical component checks, not independent pipeline
implementations. Hashes, versioned sources, exact values, assumptions, precision,
tolerances and license notices are in fixtures/evidence. Tests never download.

### Unmet high-altitude geodesy target

Independent WGS84 forward specification: latitude=45°, longitude=-120°,
height=35786 km; Cartesian km:
`[-14911.057075195353, -25826.708448797748, 29791.87168040771]`.
Astropy/ERFA inverse returns latitude **45.000000001010655°**, longitude
-119.99999999999997°, height 35785.99999999999 km.
Latitude error **1.0106546710630937e-9°** exceeds the new **1e-9°** research target.
The longitude/height checks pass. Target and fixture values are unchanged.

A separate iterative inverse returns 45°; independent forward reprojection of
the library result has vector residual **7.435459437363588e-7 km (~0.744 mm)** at
this altitude. An altitude scan and the ERFA 2.0.1 `gc2gde.c` source identify its
finite Halley correction (Fukushima 2006) as an approximation limit. This is a
numerical ellipsoid calculation discrepancy, not satellite prediction uncertainty.
It is not a regression introduced here. The tighter target was a new probe,
not a pre-existing universal library/product requirement. No justified runtime
replacement of the established geodetic library was found at this display scale.

The latitude assertion executes as a **strict XFAIL** restricted to
`AssertionError`; unexpected success fails the test and any other exception is
not excused. The standalone audit still exits **1**, with this case **FAIL**.
Criterion 20 is conservatively **FAIL**, rather than counting an XFAIL as a pass.
Revisit a precise geodesy requirement and authoritative higher-altitude references
before any future algorithm change; do not silently relax this target.

## Time scales and Earth orientation

Existing UTC/epoch/retrieval/request/execution/insertion timestamps remain
separate. Any future observation timestamp is another independent field, not
inferred from retrieval or source epoch. Source epoch is not observation time;
recent retrieval does not make old elements fresh. Legacy missing insertion time
remains null. Scientific-resource validity is independent of all satellite ages.

SGP4 uses nominal UTC calendar days and split JD. Across 2016-12-31 23:59:59 to
2017-01-01 00:00:00, nominal SGP4 input elapsed time is one second whereas TAI
elapsed time is two. The existing terrestrial guard rejects such intervals in
both directions; same-side adjacent times pass. Python datetime cannot represent
second 60; the API rejects it with 422 without creating a database. Raw TEME
SGP4 leap-crossing accuracy remains unvalidated. Do not switch propagation to
TAI/TT without a model-level justification.

UT1 drives GMST82; TAI/TT conversions use controlled local leap data. Local
IERS-A combines final IERS-B, rapid nonpredicted IERS-A, and predicted regions.
Astropy 7.2.3 source flags distinguish them; nonprediction is not proof that a
rapid value is final. Added **only metadata** `earth_orientation.source_quality`
for central UT1/polar motion and all three velocity support samples. Values are
`final`, `rapid_nonprediction`, `prediction`. Existing wire strings and aggregate
status remain compatible; `IERS_A_measured` must not be read as final or as a
satellite observation.

Any predicted support sample triggers the existing prediction policy even with
a final central sample. New tests exercise either ±0.5-second side independently
for UT1/polar motion, `measured_only` rejection, leap expiry ±1 microsecond around
the half-second support boundary, forward/reverse leap crossing and published
time constants. Existing tests cover missing/out-of-range/nonfinite EOP,
prediction age, bad configuration, concurrency and state restoration. Prediction
table age (assessment clock minus first predictive MJD, maximum 30 days) is not
satellite age or an orbital accuracy bound. Coverage/expiry checks are separate.
No defaults, extrapolation, network downloads, degraded results, source selection,
30-day limit or controlled maintenance/rollback procedure changed.

## Observation validation feasibility: BLOCKED

The archive has two genuine ISS GP snapshots and no independently measured
positions. Numerical fixtures, controlled EOP and repeated CelesTrak sets do not
fill this gap. No observational residual was calculated. Bounded external
research on 2026-10-19 verified the following sources; exact URLs, HTTP outcomes,
dates and SHA-256 values are in the evidence.

| Source | Verified semantics/access | Assessment |
| --- | --- | --- |
| NASA ILRS data/normal-point guidance and CRD v2.01e3 | HTTP 200; laser time-of-flight/range observations, station/time/normal-point records | Genuine measurements, not direct satellite XYZ; require station coordinates, calibration, meteorology, centre-of-mass/light-time corrections and matched satellite/orbital input |
| Officially linked EDC `pub/slr/data/npt_crd_v2/` archive | HTTP 200 directory listing | Public access works; an earlier guessed path was 404, superseded by the correct link. No claim that all SLR data are authentication-blocked |
| IGS products and SP3-d specification | HTTP 200 | Tracking-derived precise orbit solutions can support independent orbit comparison; they are estimates, not raw observed XYZ. SP3 can also carry broadcast/predicted values, so extension alone is insufficient |
| CDDIS GNSS week 1381 archive | HTTP 302 to `urs.earthdata.nasa.gov`; current NASA archive guidance confirms Earthdata Login | Selected archive acquisition requires access not configured here; login was not followed and no credentials requested/used |
| IGS terms, dated 5 August 2020 | HTTP 200; open scientific/educational/commercial use with provider/IGS attribution, no quality guarantee | Verified terms, not an invented CC license |
| ILRS terms of reference | HTTP 200, organizational terms inspected | No explicit measurement redistribution license established by that page; do not assert a license or redistribute measurements without further source-specific verification |

No matched measurement/precise-orbit file with verified frame, identity, time
scale and uncertainties was acquired. The public EDC directory does not itself
solve range modelling or pair an independently measured position to the ISS
archive. CDDIS login is one access blocker, not a claim that every possible
alternative dataset is unavailable. Absence of matched evidence blocks validation
here; no synthetic observations or broad validation framework was introduced.

**Next feasible experiment:** obtain a final, nonpredicted IGS SP3 segment for
one GNSS satellite, with verified IGS/ITRF realization, time scale (e.g. GPS),
uncertainty/quality flags, provenance and stable date-specific NORAD↔SVN↔PRN
mapping. Pair it with an immutable GP set actually available/retrieved **before**
the evaluated interval (epoch alone is insufficient to prevent look-ahead bias).
Use exact common epochs or a specified, checked interpolation, convert times and
frames consistently, and assess signed Cartesian/RTN residuals, RMS/bias versus
lead time on held-out epochs. Carry measurement/solution and transformation
limitations; one satellite/interval cannot certify every orbit. This is an
independent tracking-derived orbit comparison, not automatically raw-observation
truth or uncertainty calibration. A true ILRS experiment instead needs a focused
two-way range model and matched station/calibration/met/target records.

## Accuracy and uncertainty claims

API schemas/engine, source panels, ground-track/timeline, discovery/comparison,
readiness, README and scientific guides were checked. They retain calculated
status, frame/units/source provenance, `uncertainty.status=not_quantified`,
`covariance_available=false`, `observation_validated=false`; freshness is not an
accuracy guarantee. A ground track is sampled model output, not a guaranteed
overflight, visibility assessment or safety prediction. GP differences do not
establish a maneuver/anomaly/collision. Readiness is a resource assessment.

| Evidence category | What this phase establishes |
| --- | --- |
| Software tests | Tested contracts and failure/policy behavior for specified cases |
| Published numerical references | Agreement with selected published outputs and stated tolerances |
| Independent mathematical implementation | Agreement with separately coded normative transforms under controlled assumptions; one disclosed geodesy target not met |
| Observation-based validation | BLOCKED; zero observations compared |
| Uncertainty quantification | Not performed; no covariance, calibrated distribution or confidence score |

Quantification needs representative independent tracking evidence, a defined
error model, known measurement/transform uncertainties, sampling and lead-time
methodology, biases and hold-out validation. Do not substitute implementation
residuals or freshness thresholds for a satellite location error distribution.

## Final executed verification

From repository root, scientific scripts used `PYTHONPATH=backend`; uv commands
used writable `UV_CACHE_DIR=/tmp/orbitiq-phase61-uv-cache`. Reference outputs went
to `/tmp/orbitiq-phase61/`, never to old report paths. Full commands/output/exit
statuses are embedded in the JSON.

| Command/check | Exit | Result |
| --- | --- | --- |
| `uv run --locked pytest -q -rx` | 0 | 519 passed, one strict XFAIL, 9.34 s; one existing TestClient deprecation warning |
| `uv run --locked python scripts/verify_scientific_references.py --output /tmp/orbitiq-phase61/final-sgp4.json` | 0 | Original 40/40 |
| `uv run --locked python scripts/verify_earth_fixed_references.py --output /tmp/orbitiq-phase61/final-earth-fixed.json` | 0 | Original 6/6 |
| `uv run --locked python scripts/verify_phase61_science.py --output /tmp/orbitiq-phase61/final-audit.json` | **1** | **31 PASS / one FAIL**; observation validation BLOCKED |
| `uv run --locked ruff check .` | 0 | All checks passed after correcting new long strings |
| `uv run --locked ruff format --check .` | 0 | Formatting check passed |
| `cd frontend && npm test` | 0 | 180 passed, 15 files, 12.95 s |
| `cd frontend && npm run lint` | 0 | ESLint passed |
| `cd frontend && npm run format:check` | 0 | Prettier passed |
| `cd frontend && npx tsc --noEmit` | 0 | TypeScript passed |
| `cd frontend && npm run build` | 0 | Production bundle built; existing 558.60-kB renderer chunk warning retained |
| Eight real local HTTP checks | 0 | Health/TEME/ITRS/three-point track/readiness/comparison 200; second-60 and unsupported frame 422; new EOP metadata survives response schema |
| Real Chromium browser flows | 0 | Three responsive viewports; genuine stored-source flows, actual WebGL, no API/canvas mocks |
| Preservation fingerprint/assertions | 0 | Database bytes, all table fingerprints, old reports, lockfiles, HEAD/remotes/staging preserved |

Chromium **154.0.8037.57**, WebGL2/SwiftShader, viewports 1440×1000, 820×1180,
390×844: five readiness sections and read-only historical refresh; genuine ISS
search, source A1/B2 common-time ITRS comparison, source-A handoff/TEME calculation,
return retaining comparison. Zero JS page errors, zero external browser requests,
no horizontal overflow. Mobile readiness screenshot inspected. Browser-check
source is embedded in the JSON for reproduction; it requires local Chromium and
Playwright, which were available in the environment and are not added to runtime
dependencies. It is not a screen-reader, device GPU or production load audit.

Integration used read-only local servers at 127.0.0.1:8066 / :5196 and existing
snapshots, not provider acquisition. Exact request queries/responses are recorded.
Both local servers were stopped and ports verified closed. No remote CI was
queried/triggered/rerun in Phase 6.1, and no local result is labelled remote CI.
Earlier lint failures were confined to new long strings and corrected; no warning
or failed numerical target was suppressed. All scientific comparisons are offline.

## Changed files and preservation

Only these **12 files** were added/changed by Phase 6.1 (separate from preserved
pre-existing Phase 6 changes):

- `backend/orbitiq/orbits/earth_orientation.py`: additive resource-quality metadata;
  no calculation, readiness decision, source, identity or policy change.
- `backend/tests/test_phase5.py`: diagnostic HTTP status assertion only.
- `backend/tests/test_phase61_science.py`: 60 cases, including the strict XFAIL.
- `backend/tests/fixtures/phase61-sgp4.json`: new published vectors/provenance.
- `backend/tests/fixtures/phase61-terrestrial.json`: new controlled mathematical
  and published component references, including the failed target.
- `backend/tests/fixtures/phase61-source-notices.txt`: upstream license texts.
- `scripts/verify_phase61_science.py`: reproducible offline numerical assessment.
- `backend/tests/fixtures/README.md`, `docs/scientific-conventions.md`, `README.md`:
  evidence scope, metadata and limitations.
- This new report and `docs/phase-6.1-scientific-evidence.json`.

Database schema stays **3**, genuine snapshots stay **2**, ingestion attempts
stay **1**, snapshot insertions **1**, collection gate **1**. No ingestion,
migration, initialization, restore or deduplication change was performed. Whole
database SHA-256 before/after:
`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
All schema/table digests agree, integrity/foreign keys are ok. Among 138 existing
files only the five intentional existing-file edits above differ. All other
previous files, including old scientific fixtures/scripts and Phase 6 artifacts,
are byte-identical. Phase 6 report SHA-256:
`85efd7f30cfefcc0ddb42aa534b71358b9ba48180d6458c46a9d037f37ab72ee`;
Phase 6 JSON:
`a125a28ff59525645f2077e83f087d1fbbaf09370474464c0a11f8041cb935a1`.

## Every requested acceptance criterion

| # | Criterion | Status and evidence |
| --- | --- | --- |
| 1 | Existing science/reports inspected | PASS — baseline manifest and inspection scope |
| 2 | Initial backend/frontend/reference baseline recorded | PASS — 459+one failure, isolated pass, 180, 40/6; initial limitation disclosed |
| 3 | Approximately 1.32-cm residual reproduced | PASS — exact max component and norm above |
| 4 | Inputs/frames/units/time/EOP/method documented | PASS — standalone state, null unavailable elements, exact reference/evidence |
| 5 | Cause/significance investigated | PASS — precision-order ablations; historical runtime uncertainty retained |
| 6 | Existing SGP4 coverage reviewed | PASS — 20 distinct vectors / 40 paths, gaps and contract tests separated |
| 7 | Justified published SGP4 additions | PASS — ten new vectors, 20 passing comparisons |
| 8 | Existing transform coverage reviewed | PASS — six comparisons classified by independence scope |
| 9 | Justified independent transform additions | PASS — four cases using a separate mathematical implementation, not observations |
| 10 | Provenance/versions/assumptions/tolerances recorded | PASS — pinned references, acquisition hashes, literals, licenses and no original tolerance changes |
| 11 | Time/EOP assumptions audited | PASS — scales, flags, distinct clocks, strict policies preserved |
| 12 | Boundaries/leap limitations verified | PASS — support sides/expiry, forward/reverse crossing, API rejection and full regressions |
| 13 | Observation feasibility investigated | PASS — authoritative formats/access/terms and next experiment |
| 14 | Actual observation validation with suitable measurements | **BLOCKED** — no verified matched independent measurement/position file; zero observations used |
| 15 | Missing evidence blocked, not fabricated | PASS — explicit BLOCKED result and no synthetic observations |
| 16 | Accuracy/uncertainty claims match evidence | PASS — calculated, not quantified, no guarantee or anomaly claim |
| 17 | Phase 6 ingestion/dedup/readiness/EOP policies preserved | PASS — unchanged source/policy paths, full regressions, additive metadata only |
| 18 | Snapshots and ingestion ledger preserved | PASS — exact bytes and schema/table fingerprints |
| 19 | Existing scientific tests pass or failures explained | PASS — final original 40/6 and all existing tests pass; initial intermittent cause explicitly unproven |
| 20 | New tests pass where implemented | **FAIL** — high-altitude latitude target not met; strict XFAIL and standalone numerical FAIL retained, not counted as PASS |
| 21 | Lint/format/TypeScript/build pass | PASS — final executed exit-zero checks |
| 22 | No unresolved regression concealed | PASS — initial transient failure, unmet new precision target and observational blocker disclosed; no introduced runtime calculation regression demonstrated |
| 23 | Separate Phase 6.1 report/structured evidence complete | PASS — new artifacts, reproducible inputs/results/commands and preservation record |

## Remaining limitations

The high-altitude geodetic target, unproven initial intermittent history failure,
absence of independently aligned measurements, unquantified prediction error and
limited regime/reference coverage remain explicit. New control tables are not
real EOP observations. Leap-crossing terrestrial propagation remains unsupported.
Strict scientific-resource expiry still requires controlled maintenance. Two ISS
snapshots and numerical vectors do not establish multi-satellite operational
accuracy. Follow the focused GNSS/IGS experiment above before stronger claims.

Phase 6 operational limitations remain unchanged: remote CI for uncommitted work,
branch-protection enforcement, durable off-machine persistence/backups,
production recovery, authentication/abuse controls, deployment/load/accessibility
verification were not established here. This phase neither reopens nor rewrites
that milestone. **Nothing was committed, pushed, deployed or published; remotes
were unchanged and no remote workflow was triggered or rerun.**
