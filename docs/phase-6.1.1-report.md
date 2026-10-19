# Phase 6.1.1: high-altitude geodetic precision remediation

Local verification: **19 October 2026**, timestamps UTC. See
[structured evidence](phase-6.1.1-scientific-evidence.json) for exact inputs,
reference provenance/build, before/after residuals, executed commands and
preservation hashes. Earlier Phase 6 and Phase 6.1 reports are unchanged.

## Outcome

**The original geodetic precision criterion is now satisfied without changing
its input, expected coordinates or tolerances. All 18 remediation criteria PASS.**

The latitude error fell from **1.0106546710630937e-9°** to
**7.105427357601002e-15°**, against the unchanged **1e-9°** limit. The original
test runs normally; its strict XFAIL marker was removed. A residual-checked
exterior correction of the existing ERFA result addresses a measured numerical
approximation limit. This is mathematical WGS84 precision, not measured satellite
position accuracy.

Final backend **582 passed**, with no XFAIL/skip/failure; frontend **180 passed**.
Original SGP4 **40/40**, original terrestrial **6/6**, expanded Phase 6.1 numerical
audit **32/32**, new independent geodetic comparisons **28/28**, and separate
forward reconstruction checks **28/28** pass. An additional **528-case** independent
reference grid passes. Lint, format, TypeScript, production build, read-only HTTP
and real-browser checks pass. Observation validation remains **BLOCKED** and
prediction uncertainty remains unquantified; that separate issue is not resolved.

## Inspection and baseline

Repository `BibinBinoy777/OrbitIQ`, branch `main`, HEAD
`6c60655402b70306f654c3f9b30f79ff6c7c3e45`. The task began with **46 dirty entries**
from existing work, not a fresh checkout. A **145-file** SHA-256 manifest,
database byte hash and schema/table fingerprints were recorded before edits.
All nine requested report/evidence files existed, were read and hashed, including
Phase 6 and Phase 6.1 artifacts. Examined the original criterion 20, exact fixture
and expected-failure implementation, geodetic/ground-track/terrestrial services,
frame/unit contracts, reference scripts, time/EOP boundaries and dependency locks.

Installed: Python 3.12.14; Astropy **7.2.3**; PyERFA **2.0.1.5**; SGP4 **2.27**;
NumPy **2.5.4**; astropy-iers-data **0.2026.10.12.1.3.27**. Existing dependencies
contain no independent geocentric inverse implementation. Python GeographicLib's
geodesic functionality is not a substitute for its C++ Geocentric inverse.
`GeoConvert`, PROJ CLI and CMake were unavailable; **g++ 14.2.0** was available.
The existing environment required no dependency, lockfile or saved configuration
change. Runtime/setup skills were used to inspect tools and ready configuration.

Executed before changing code:

| Command | Exit | Actual result |
| --- | --- | --- |
| `uv run --locked pytest -q -rx` | 0 | 519 passed, one strict XFAIL, 7.96 s |
| `uv run --locked pytest -q --runxfail 'backend/tests/test_phase61_science.py::test_independent_mathematical_wgs84_anchors[non_equatorial_high_altitude-latitude_deg]'` | **1** | Original assertion fails, 0.92 s; XFAIL deliberately unmasked |
| `cd frontend && npm test` | 0 | 180 passed |

The earlier intermittent history-test failure was not observed in this baseline
or final suites. Its previously unproven cause is not claimed fixed by this work.

## Exact original failure

Input is geocentric Earth-fixed XYZ aligned with the WGS84 axes, **km**:
`[-14911.057075195353, -25826.708448797748, 29791.87168040771]`.
It is a mathematical ellipsoid anchor, not an observed satellite position.
Expected: geodetic latitude **45°**, longitude **-120°**, ellipsoidal height
**35786 km**. WGS84 a=6378.137 km, f=1/298.257223563. No time-scale/EOP rotation
is involved in this pure Cartesian-to-geodetic operation.

The original test compares each coordinate independently with **rtol=0**:
latitude/longitude **1e-9°**, height **1e-7 km (0.1 mm)**. The failed latitude
criterion does not use Cartesian norm or substitute a round-trip metric.
Longitude residuals in the new audit use `abs(remainder(actual-expected,360))`,
preserving even tiny differences without the cancellation of adding 180°.
Application longitude normalization remains the existing [-180,180) convention.

| Quantity | Original expected | Before | After | Absolute error after |
| --- | --- | --- | --- | --- |
| Latitude (deg) | 45 | 45.000000001010655 | 45.00000000000001 | 7.105427357601002e-15 |
| Longitude (deg) | -120 | -119.99999999999997 | -119.99999999999997 | 2.842170943040401e-14 |
| Ellipsoidal height (km) | 35786 | 35785.99999999999 | 35786.0 | 0 |

Before: latitude error **1.0106546710630937e-9°**, failure margin
**1.0654671063093639e-11°** above the threshold; longitude error
2.842170943040401e-14°, height error 7.275957614183426e-12 km. The failure is
repeatable. Coordinate binary64 ULPs are about 1.82e-12–3.64e-12 km; their
rounding cannot account for the much larger angular discrepancy.

The original expected anchor came from independent standard WGS84 forward
equations. A new independent inverse confirms its precision is adequate:
GeographicLib long-double reverse of these exact binary64 kilometre inputs gives
latitude **45.0000000000000003539°**, longitude **-119.999999999999984797°**,
height **35785.9999999999982663 km**. These tiny input-representation effects are
far below the original criterion. No reference convention mismatch or threshold
relaxation is justified.

## Algorithm investigation and focused correction

The prior path was Astropy `EarthLocation.to_geodetic(WGS84)`, using ERFA's
`eraGc2gde` finite Halley approximation (Fukushima 2006). Its constants and units
are correct; geodetic latitude is not confused with geocentric latitude. The
source and Phase 6.1 altitude scan identify a small high-altitude approximation
limit. Independent GeographicLib results support that finding. This is a product
numerical limitation relative to the now-explicit target, not evidence of an
SGP4, time, EOP or TEME-to-ITRS defect or a general failure of ERFA.

Keep the established library as the initial solution. For exterior points only,
measure the residual of the exact WGS84 normal equation and correct it when it
exceeds binary64 round-off. With rho=hypot(x,y), s=sin(phi), c=cos(phi),
e²=f(2-f), q=1-e²s², N=a/sqrt(q), the forward ellipsoid equations imply:

```text
F(phi)  = rho*s - z*c - e²*N*s*c = 0
F'(phi) = rho*c + z*s - e²*N*(c² - s² + e²*s²*c²/q)
phi_new = phi - F/F'
h_new   = rho*cos(phi_new) + z*sin(phi_new) - a*sqrt(1-e²*sin(phi_new)²)
```

This removes height from the latitude solve. The height expression is normal
projection, avoiding division by nearly zero sine/cosine near the equator/poles.
Constants come from `erfa.eform(1)`, the same WGS84 definition used by Astropy;
metres are explicitly converted to km. Calculations remain binary64.

Original case: F=**7.435484654649827e-7 km**, F'=**42153.38181562068 km/rad**,
measured Newton step **1.7639117751388752e-11 rad**. **One** correction reduces F
to **5.073275133327115e-12 km**. Further iterations only move at the final binary64
ULP; the measured error reduction supports one checked correction, not arbitrary
iteration counts or a precision/dependency upgrade.

The implementation skips correction when |F|≤8 ULPs of geocentric radius.
After one correction it requires a finite residual ≤16 ULPs; an invalid derivative
or unmet postcondition fails explicitly. These are arithmetic round-off checks,
not relaxed test targets or physical error bounds. Invalid seed/failure-path tests
verify that the routine cannot silently return an unconverged result.

Only exterior seeds (nonnegative ellipsoidal height) are refined. Deep-interior
ellipsoid inverses can have multiple branches and ill-conditioned normal
equations; their existing ERFA behavior is preserved, with three explicit branch
regressions. Negative heights -0.25 and -10 km are independently checked too.
The existing rejection within 1 km of the geocentre, malformed/nonfinite/bool
inputs, pole-longitude convention and longitude normalization remain unchanged.
Already negligible seed residuals retain the original result.

There is no change to TEME/ITRS Cartesian positions or velocities, WGS72 SGP4,
time scales, EOP/leap policies or ingestion/history. Only exterior geodetic
latitude/height and their derived WGS84 footpoints can change at this small
numerical scale. The terrestrial method string now states that refinement.

## Independent reference methodology and provenance

Reference: **GeographicLib C++ 2.5, tag r2.5**, Geocentric::Reverse, Karney's
modified Vermeille closed-form method. Its algorithm/code path is separate from
ERFA's Fukushima seed and the new local Newton correction. Both implement the
same normative WGS84 ellipsoid; that is numerical implementation independence,
not an independent Earth model or measurements.

Source acquired through verified HTTPS, HTTP 200 on 2026-10-19:

- [r2.5 source archive](https://codeload.github.com/geographiclib/geographiclib/tar.gz/refs/tags/r2.5),
  1,725,627 bytes, SHA-256
  `4b646358189799491e669f0de5072e94e3988d4a7486823344d182d57665ed35`.
- [Official geocentric documentation](https://geographiclib.sourceforge.io/C++/2.5/geocentric.html),
  SHA-256 `a0cdaa7244ee93c86f82029cdb738296d8defb9c5bed772607d84e3f0d03db7d`.
- Source member hashes, exact wrapper, generated configuration, compiler version
  and build commands are embedded in the new JSON. Full MIT/X11 notice is retained
  in `backend/tests/fixtures/phase611-source-notices.txt`.

Only `Geocentric.cpp`, `Math.cpp` and a small input/output wrapper were compiled
in `/tmp`, twice: **53-bit double** and **64-bit-mantissa long double**. The
wrapper parses original kilometre values as binary64, promotes them, then converts
to metres before calling the independent inverse. Output is degrees and height
converted back to km, printed with `max_digits10`. Frozen references retain the
full decimal strings and binary64 expected values. The library did not use
OrbitIQ, Astropy or ERFA outputs to generate expected coordinates.

No GeographicLib runtime/development dependency was added. Ordinary tests use
frozen offline fixtures; no compiler, live reference service or download is needed.
Source rerun explicitly compares all 28 full decimal outputs with the fixture
using the recorded long-double executable. This matched exactly on this host.
Different compiler/platform long-double results need numerical comparison, not an
assumption that every final printed digit is portable.

The documented 7-nm GeographicLib bound for |h|<5000 km is not generalized to the
GEO/high-altitude domain. Cross-checks here measure actual reference sensitivity:
maximum double/long-double differences over the 528-case grid are about
1.42e-14° latitude/longitude and 1.164e-10 km height, far below the test targets.
The full upstream C++ library suite was not run; these are focused builds and
comparisons, not a new certification of GeographicLib.

### Representative cases and sensitivity

`phase611-geodesy.json`: **28 comparison cases**, including the exact original
input, the existing SOFA Cartesian input, an explicit non-ellipsoid anchor and
25 independently generated control geometries. Forward-generated inputs use
GeographicLib Forward, rounded once to binary64 km, then its independent Reverse
for those actual Cartesian values. They are not fabricated satellite observations.

Cases cover zero/low/negative heights, 400–1000-km LEO-like geometry,
10000/20000/35786/100000/1000000 km, both latitude signs, equator, mid/high
latitudes, both poles, and longitude wrap/antimeridian boundaries. Some cases
overlap physically at canonical wrap boundaries; counts are comparison cases,
not 28 unrelated reference publications. Each latitude/longitude/height is checked
against the independent inverse with the unchanged 1e-9°/1e-7-km targets.

Additional grid: 12 latitudes × four longitudes × 11 heights = **528 cases**,
covering -10 to 1,000,000 km. Expected values come from the independent long-double
inverse, actuals from the corrected production function. All pass. Maximum errors:

| Metric | Maximum |
| --- | --- |
| Latitude | 5.684341886080802e-14° |
| Wrapped longitude | 2.842170943040401e-14° |
| Height | 1.1641532182693481e-10 km |

The pre-correction grid reached 1.3681287214240001e-9° latitude error. The controlled
experiment corrected 164 of 528 seeds; most already satisfied the round-off gate.
The final grid uses the real production function, not just the prototype. It
overlaps the frozen case coverage; do not sum these as unique independent sources.

Separate algebraic consistency: convert each corrected result back to XYZ using
explicit WGS84 forward equations; **28/28** vector norms satisfy 1e-7 km.
Original input's norm improves from **7.435459437363588e-7 km (~0.744 mm)** to
**1.373306883628311e-11 km (~13.7 nm)**. These consistency checks do not replace
the original component criterion or constitute an independent observation test.

## Reproduction and executed regressions

Commands run from repository root used
`UV_CACHE_DIR=/tmp/orbitiq-phase61-uv-cache`; scientific scripts also used
`PYTHONPATH=backend`. Outputs went to `/tmp/orbitiq-phase611/`, never old reports.

| Command/check | Exit | Actual result |
| --- | --- | --- |
| Original latitude node, unchanged threshold, without XFAIL | 0 | One passed |
| `uv run --locked pytest -q -rx` | 0 | **582 passed**, 10.04 s, no XFAIL/skip/failure |
| `uv run --locked python scripts/verify_scientific_references.py --output /tmp/orbitiq-phase611/sgp4.json` | 0 | Original 40/40 |
| `uv run --locked python scripts/verify_earth_fixed_references.py --output /tmp/orbitiq-phase611/terrestrial.json` | 0 | Original 6/6 |
| `uv run --locked python scripts/verify_phase61_science.py --output /tmp/orbitiq-phase611/phase61.json` | 0 | 32/32; observational validation still BLOCKED |
| `uv run --locked python scripts/verify_phase611_geodesy.py --output /tmp/orbitiq-phase611/geodesy.json --reference-executable /tmp/orbitiq-phase611/geocentric-long-double` | 0 | 28 independent comparisons, 28 separate reconstructions; frozen decimal references reproduced |
| `uv run --locked ruff check .` | 0 | All checks passed |
| `uv run --locked ruff format --check .` | 0 | Formatting passed |
| `cd frontend && npm test` | 0 | 180 passed, 15 files, 13.47 s |
| `cd frontend && npm run lint` | 0 | ESLint passed |
| `cd frontend && npm run format:check` | 0 | Prettier passed |
| `cd frontend && npx tsc --noEmit` | 0 | TypeScript passed |
| `cd frontend && npm run build` | 0 | Production build passed |
| 528-case actual production grid | 0 | 528 independent-reference comparisons pass |
| Read-only HTTP integration | 0 | Eight status/body checks plus three independent geodetic ground-track comparisons |
| Chromium browser harness | 0 | Real stored-data flows at three viewports |
| Preservation assertions | 0 | DB/report hashes, schema/tables, original residual/SGP4 results, HEAD/remotes/staging unchanged |

The full suite includes TEME-to-ITRS, old SOFA/analytic WGS84, time/EOP support
and expiry boundaries, leap-crossing rejection, negative/invalid input behavior,
ingestion/history and source-provenance regressions. New geodesy module adds
**62 tests** (28 independent cases, 28 reconstructions, three interior branches,
two seed-failure checks, one longitude residual check). Removing the old expected
failure adds the remaining ordinary pass: 519 + 1 + 62 = 582.

During development, Ruff flagged a new long metadata string; it was wrapped and
lint/format rerun passed. Audit review also found that adding 180° to wrap tiny
longitude residuals could erase an ULP; the new residual metric uses remainder
and has a regression test. This is an audit measurement correction, not a change
to application longitude normalization. Final full backend/audits were rerun.
No tolerance/assertion was weakened. Existing TestClient deprecation and the
558.60-kB lazy renderer Vite warning remain visible; no dependency upgrades or
warning suppression were used.

HTTP integration used existing genuine ISS snapshots, read-only servers on
127.0.0.1:8066/:5196, common epoch 2026-10-18T18:57:18.892800Z. Health, TEME,
ITRS, three-point ground track, readiness and comparison returned 200; second-60
and unsupported frame returned 422. All three actual ITRS ground-track positions
also agree with the independent geodetic inverse within the component limits.
These are calculated GP positions, not independently observed satellite positions.

Actual Chromium **154.0.8037.57**, WebGL2/SwiftShader, 1440×1000, 820×1180,
390×844: readiness/refresh, genuine archive search, A1/B2 ITRS comparison, exact
source handoff/TEME calculation and retained comparison on return. No mocked API
or canvas, zero page errors, zero external browser requests, no horizontal overflow.
Both local servers were stopped; closed ports were verified. An initial teardown
PID filter missed the Python-wrapped backend process; corrected process selection
and the final closed-port assertion verified shutdown. No application was deployed.

### Optional independent source rerun

For ordinary reproduction, use the offline command without
`--reference-executable`. To recheck source-derived values, acquire the pinned
archive above, verify its SHA-256, and extract it safely outside the checkout.
The JSON `independent_reference_build` includes the **exact** wrapper source,
generated `GeographicLib/Config.h` and full g++ commands. Reconstruct those two
files, then compile the two source members using `-std=c++17 -O2`,
`-DGEOGRAPHICLIB_PRECISION=3` (or 2 for the double cross-check), the include
directory and wrapper, `src/Geocentric.cpp` and `src/Math.cpp`. No CMake is needed.
Run the geodesy audit with that executable. JSON also includes the reference
fixture-generation source and the sensitivity experiment source/results so
inputs and grid values can be independently regenerated without OrbitIQ outputs.

## Changed files and preservation

Six existing files changed in this remediation only:

- `backend/orbitiq/orbits/coordinates.py`: checked exterior correction and method
  description; existing Earth rotation/Cartesian transform equations untouched.
- `backend/tests/test_phase61_science.py`: remove the original XFAIL, retain exact
  inputs and all three component thresholds/assertions.
- `scripts/verify_phase61_science.py`: report current geodesy outcome dynamically
  and identify the refined algorithm; original residual investigation unchanged.
- `README.md`, `docs/scientific-conventions.md`, `backend/tests/fixtures/README.md`:
  distinguish historical failure from current remediation, document conventions.

Six new files: `backend/tests/test_phase611_geodesy.py`,
`backend/tests/fixtures/phase611-geodesy.json`,
`backend/tests/fixtures/phase611-source-notices.txt`,
`scripts/verify_phase611_geodesy.py`, this report and its JSON evidence.
No dependency declaration, lockfile, existing reference input/expected value,
original SGP4/transform tolerance, Phase 6 ingestion/history code or old report changed.

All **145 pre-existing file hashes** were compared; only the six intentional
existing-file edits differ. Every requested prior report and both Phase 6.1
artifacts remain byte-identical. Database schema **3**, two genuine snapshots,
one ingestion attempt, one insertion record and one collection gate remain.
Whole DB SHA-256 before/after:
`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
All schema/table fingerprints agree, integrity/foreign keys are ok. No initialization,
migration, ingestion, restore or historical rewrite occurred. Original SGP4 audit
JSON and the **entire Vallado 1.317-cm residual investigation** match Phase 6.1
exactly. The two numerical issues remain separate; no updated explanation is needed.

## All acceptance criteria

| # | Criterion | Status and evidence |
| --- | --- | --- |
| 1 | Original evidence inspected | PASS — all requested artifacts exist/read/hash baseline |
| 2 | Exact failure reproduced | PASS — unmasked unchanged original assertion exits 1 before edits |
| 3 | Inputs/frames/units/outputs/residuals documented | PASS — exact original and independent results above/JSON |
| 4 | Algorithm and sensitivity investigated | PASS — ERFA seed/source, normal equation, measured one-step effect and grid |
| 5 | Suitable independent comparison performed | PASS — GeographicLib 2.5 closed-form inverse, double/long-double builds |
| 6 | Provenance/precision limitations documented | PASS — version/hash/license/build/units, input rounding and limited numerical scope |
| 7 | Cause identified or uncertainty explicit | PASS — finite approximation limit, independent reference supports original criterion; not a frame/unit/time mismatch |
| 8 | Justified correction made | PASS — exterior residual-checked Newton step with stable height, measured effect and guards |
| 9 | Original case passes or failure retained | PASS — 7.105427357601002e-15° error against unchanged 1e-9°; no XFAIL |
| 10 | Representative geometries verified | PASS — 28 frozen comparisons and 528-case grid; ordinary/interior/negative/invalid behavior tested |
| 11 | Independent references distinguished from consistency | PASS — independent component tests and separate forward norm tests/metrics |
| 12 | SGP4/terrestrial references valid | PASS — original 40/6, expanded 32 pass; Vallado investigation unchanged |
| 13 | Data/prior reports preserved | PASS — byte hashes, schema/table fingerprints and prior report hashes |
| 14 | Backend/frontend suites pass | PASS — 582/180, no expected failures or skips |
| 15 | Quality/build/browser checks pass | PASS — final lint/format/TS/build and actual local browser/integration checks |
| 16 | No unjustified tolerance weakening | PASS — all old inputs/expected values/component tolerances unchanged |
| 17 | No unrelated functionality changed | PASS — six scoped existing-file edits; ingestion/history/EOP/SGP4 untouched |
| 18 | Separate report/structured evidence complete | PASS — new artifacts with exact references/results/commands and preservation trail |

## Recommendation and remaining limits

The original **numerical geodetic precision criterion is satisfied** for its exact
input and the representative domain tested. Retain the regression, independent
fixtures and residual guards. The shared ellipsoid definition and finite selected
references do not prove universal accuracy for every floating-point vector.
Deep-interior branches are intentionally not refined; extreme domains and future
ellipsoid/coordinate extensions need separate requirements and validation.

Observation-based satellite prediction validation remains **BLOCKED**, with zero
independent observations used. No covariance or quantified prediction uncertainty
was added. Follow the Phase 6.1 proposed matched independent tracking/precise-orbit
experiment before making stronger prediction claims. No Phase 7 work began.
Prior operational/public-launch limitations remain outside this focused task.

**Nothing was committed, pushed, deployed or published. Repository remotes were
unchanged; no remote workflow was triggered or rerun.**
