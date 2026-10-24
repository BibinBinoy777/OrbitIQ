# E8 — NASA/IGS reference-data feasibility

Study: **ORBITIQ-IGS-GPS-RETRO-001**, reviewed 24 October 2026. This is a feasibility
investigation; no scientific residual calculation or executable comparison is
implemented. All acquisition/calculation-resource timestamps below are UTC.

The candidate is an actual IGS combined final product obtained from the documented
BKG global data-centre mirror. Direct NASA CDDIS acquisition is authentication
blocked. Useful identity/format/time evidence exists, but no compatible historic GP
input is available in this investigation, and frame/physical-point/uncertainty
qualification is incomplete. This is a credible alternative to investigate without
waiting for ESA's reply, not a qualified accuracy-validation dataset yet.

## Baseline, separate workstreams and evidence

Started from the requested verified E7 branch `engineering-e7-history-contract`,
commit `309aa02826bc0ca36ce82ed31d14fb76dbeecbfb`; work branch:
`engineering-e8-nasa-igs-feasibility`, worktree `/workspace/OrbitIQ-nasa-igs`.
The initial E7-labelled attachment specified E6; the subsequent E8 request corrected
the starting point before implementation. The unused initial local E7 NASA branch
was preserved without commits/publication. Original E7 and all previous reports,
engineering/default branches, the real database and private research inputs remain
unchanged. See the [plan](engineering-e8-plan.md),
[proposed protocol](engineering-e8-comparison-protocol.md),
[metadata-only source evidence](engineering-e8-source-evidence.json) and
[engineering verification](engineering-e8-verification.md).

NASA/IGS is the active validation-feasibility path for this development effort.
The original Swarm-A/ESA study is preserved as an inactive workstream, **PARTIAL**
with scientific evaluation **BLOCKED**. No outstanding ESA question is answered by
switching workstreams, and no old report/protocol was rewritten. The new study
has its own target, sources, protocol, limitations and decision.

## Findings and qualification status

| Conclusion                                                               | Classification     | Evidence and limit                                                                                                                                                                      |
| ------------------------------------------------------------------------ | ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Official NASA/IGS product documentation was read                         | VERIFIED           | Actual retained HTTP captures, source URLs/times/hashes; NASA's requested orbit-products URL redirected to its precise-orbits-product page                                              |
| A genuine IGS final product was acquired                                 | VERIFIED           | HTTPS BKG file, gzip/ASCII/header/record inspection, compressed and expanded hashes below                                                                                               |
| The product was downloaded from NASA CDDIS                               | BLOCKED            | Exact candidate URL redirected to Earthdata authorization; final HTTP 200 was 11,043-byte HTML, not gzip/SP3                                                                            |
| Existing authorized NASA authentication is available                     | UNVERIFIED         | Runtime reported no Earthdata binding; standard netrc file absent; actual unauthenticated archive probe reached sign-in. This is not a claim that no other user access could exist      |
| Actual candidate format/interval/units are identified                    | VERIFIED           | SP3-c GPS-only P records, 96 epochs, 32 IDs, fixed-column declarations/cadence and SP3 specifications                                                                                   |
| G30/G10 identity correspondence is suitable to investigate               | PARTIALLY VERIFIED | Official SVN/PRN/COSPAR/NORAD metadata matches nominal 2024 identity and current GP entity; exact metadata interval time scale at boundaries is not established by the reviewed section |
| Current GP inputs support static existing-engine initialization          | VERIFIED           | Existing Elements validation, ephemeris 0 / UTC / TEME / SGP4 / WGS72, deep-space method d; no propagation executed                                                                     |
| Current GP inputs are eligible for this reference interval               | BLOCKED            | Both G30 and G10 exclude all 96 reference epochs under the unchanged seven-day guard and predeclared forward-only initial-condition policy                                              |
| Ordinary GPS-tag conversion and local resource support                   | VERIFIED           | All 96 exact tags converted through existing TimeGPS/leap handling; UTC interval below; every epoch's UT1/polar-motion/velocity-support preflight returned IERS_B_final flags           |
| TEME/generic ITRS and this IGS20 solution are aligned                    | BLOCKED            | Realization, origin/axes/scale/rates and satellite physical-point treatment lack a reviewed comparison-specific qualification                                                           |
| Reference uncertainty is completely characterized                        | PARTIALLY VERIFIED | Header/axis sigmas and weekly processing information inspected; no full joint/cross-time/GP covariance or calibrated combined error budget                                              |
| Statistical independence is established                                  | UNVERIFIED         | Different providers and internal IGS evaluation do not establish GP/reference lineage independence                                                                                      |
| Independent prediction accuracy or historical forecasting is established | BLOCKED            | No comparisons were calculated; original GP availability/complete fitting lineage remain unknown                                                                                        |

## Actual acquisition and product inspection

Official starting sources inspected:

- [NASA precise orbit product documentation](https://www.earthdata.nasa.gov/data/space-geodesy-techniques/gnss/precise-orbits-product),
  [CDDIS archive access](https://www.earthdata.nasa.gov/centers/cddis-daac/archive-access).
- [IGS products and global data-centre locations](https://igs.org/products/),
  [BKG access page](https://igs.bkg.bund.de/) and its public `root_ftp` directory.
- [SP3-c specification](https://files.igs.org/pub/data/format/sp3c.txt),
  [SP3-d specification/compatible field explanations](https://files.igs.org/pub/data/format/sp3d.pdf).
- [IGS frame history](https://igs.org/wg/reference-frame/),
  [IGS20 implementation notice](https://lists.igs.org/pipermail/igsmail/2022/008238.html),
  [satellite metadata](https://files.igs.org/pub/station/general/igs_satellite_metadata.snx),
  [Metadata SINEX 1.10](https://files.igs.org/pub/resource/working_groups/multi_gnss/Metadata_SINEX_1.10.pdf).
- [CelesTrak GP formats/defaults/provenance](https://celestrak.org/NORAD/documentation/gp-data-formats.php).

Acquired product:
`IGS0OPSFIN_20240010000_01D_15M_ORB.SP3.gz`, GPS-week directory **2295**.
Actual source:
[BKG HTTPS mirror](https://igs.bkg.bund.de/root_ftp/IGS/products/2295/IGS0OPSFIN_20240010000_01D_15M_ORB.SP3.gz).
Retrieval: **2026-10-24T05:00:22.757926Z**. Original gzip: **102,609 bytes**,
SHA-256 `26f16fa5f97cce851948fa88711aed47f60ee2e4ddfe36f0e98b1076e79fbe38`.
Expanded ASCII: **253,250 bytes**,
SHA-256 `8a638375273ab74011aebd9ffcc480df02b5718440c8fb7c51c408ff220d231c`.
Original bytes were preserved unchanged, including under the official filename.

Actual header declarations are `#cP`, 96 epochs, `ORBIT IGS20 HLM IGS`, GPS time,
week **2295**, first-week second **86400.00000000**, MJD **60310**, fraction zero,
and **900-second** sampling. All start-time representations agree exactly.
The source has **3,072** P records, exactly 32 different GPS satellites per epoch,
80-column position records, terminal EOF, no velocity records and no EP records.
The inspector verified all records, not only the filename/header.

The SP3 specifications establish position km, clock µs, and optional sigma/flag
semantics. No clock correction was applied to orbit epochs or positions. Original
SP3 position values are never exported by the inspector, normalized into observed
states, transformed or subtracted. Its output is metadata, preserved source
indices, diagnostics and exclusions only.

Direct CDDIS candidate probe at **2026-10-24T05:17:59.655554Z** returned a 302 to
Earthdata authorization and an HTML sign-in page with final HTTP 200. No gzip or
SP3 was acquired from CDDIS. Configure an authorized NASA Earthdata mechanism
privately if that archive is required; do not put credentials in Git or messages.
The BKG bytes establish mirror acquisition, not authentication of an unacquired
NASA copy. An IGN HTTPS directory probe returned 503; that is a scoped access
failure, not evidence the product does not exist there.

BKG GPS-week directory listings **2438** and **2439** were also inspected. Neither
returned listing contained a FIN filename, while RAP/ULT entries existed. No
predicted ultra-rapid or rapid product was substituted. These are observations of
those listings at acquisition, not a global claim that no newer finals exist.
The older week-2295 listing did contain final products and led to the actual
candidate above. NASA/IGS documentation explains final-product latency: IGS's
table gives 12–19 days and its prose 13–20; NASA describes approximately 13 days
after the solution week. None guarantees availability of a particular later file.

## GP compatibility and identifier checks

One bounded CelesTrak query was made:
`https://celestrak.org/NORAD/elements/gp.php?GROUP=gps-ops&FORMAT=JSON`.
Retrieval: **2026-10-24T04:58:29.302996Z**, **13,256 bytes**, original SHA-256
`8e1b961369ba5d083ec99b792453e26e82217f0ac609dc6f4eece432a0f5ef87`.
There are 32 records; their epochs range from
2026-10-19T07:47:32.523072Z through 2026-10-23T22:32:16.581120Z.
The response is retained privately and was reused, not repeatedly fetched.
No record was ingested into the application's real database.

| Investigated ID | Official identity facts                                                                     | Actual current GP                                                                                                                             | Outcome                                                       |
| --------------- | ------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| G30             | SVN G064, NORAD 39533, COSPAR 2014-008A; PRN assignment starts `2014:052:00000`, open-ended | Source index 14; epoch 2026-10-23T07:38:57.767424Z; canonical derived hash `da1c730d1fc16648e57d2954f3f7c7eb7d8c3c14a71522bde262022f41c6f70d` | Same nominal entity; all 96 epochs time-ineligible            |
| G10             | SVN G073, NORAD 41019, COSPAR 2015-062A; assignment starts `2015:304:00000`, open-ended     | Source index 20; epoch 2026-10-22T09:56:02.175648Z; canonical derived hash `3846a56ee8ca90efe4a3401df8b738e00c1978d2ed1e8c80f37f3e342ce6aab1` | Independent second compatibility check; same temporal blocker |
| G01             | At the reference date, SVN G063 / NORAD 37753 / 2011-036A, until `2024:103:00000`           | Current PRN 01 is NORAD 62339, a different spacecraft                                                                                         | PRN reuse; no alias-based substitution                        |

Source indices are zero-based within the unchanged response. Canonical derived
hashes are not hashes of a newly claimed provider response. Current G30/G10 GP
records passed schema/default/unit/model constraints and initialized the existing
SGP4 deep-space path, without calling propagation. This establishes supported
input initialization only. No suitable historical GP has been supplied or selected.
No GP/reference identity was inferred merely from a matching PRN string.

## Time, frame and reference-point findings

The 96 source GPS labels run from 2024-01-01 00:00:00.00000000 to
2024-01-01 23:45:00.00000000. Existing split-second Astropy TimeGPS conversion
under pinned local leap/EOP resources yielded the conditional UTC interval:

**2023-12-31T23:59:42.000000Z through 2024-01-01T23:44:42.000000Z**.

The 18-second offset is derived from those resources, not an assumed constant.
No rounding, nearest-time matching, interpolation, extrapolation or GPS second-60
rollover was performed. All epoch/source indices are preserved. The header comment
about IGST is a clock-reference declaration, not permission to relabel GPS epoch
tags. The code rejects unsupported time/precision/conflicting-header cases.

All 96 resource preflights checked the existing ±0.5-second support and returned
IERS_B_final for UT1 and polar motion (192 central resource flags). Bundled package
`astropy-iers-data 0.2026.10.12.1.3.27`, EOP SHA-256
`9fbc14ae5e71de96cc1e6b43b54a547acc80c7a6ce910c0209ad6230ff3d30cd`,
leap SHA-256 `6cb6f5d4b819f2e568e25db4b0b26d89dedf031fdffb18bc94d40f4e94e268d7`,
leap expiry **2027-06-28**. Resource flags are not a reference-frame or accuracy
certificate. Installed versions and source hashes are reproducibility inputs.

IGS frame history associates the actual IGS20 datum with ITRF2020 and its antenna
calibrations. It also documents later IGb20 and IGc20 changes; a current filename
or generic ITRS label must not override this historical product's actual IGS20
header. The existing TEME→ITRS implementation does not select an ITRF realization.
A justified IGS20 alignment is still required; none was invented or applied.

The satellite physical reference point also needs product-specific review.
Metadata SINEX documents CoM dynamics and antenna eccentricities. Earth-frame
origin, satellite CoM, antenna reference point and GP fitting/tracking point are
separate questions. The current October-2026 ANTEX capture is not proven to be the
exact historical 2024 calibration file and was not used. No unsupported
antenna/reference-point correction or spacecraft state transformation occurred.

## Reference quality, dependencies and permissible claims

The actual accompanying weekly summary
`IGS0OPSFIN_20233650000_07D_01D_SUM.SUM.gz` was acquired at
2026-10-24T05:00:22.758539Z, **23,095 bytes**, SHA-256
`2c00cc06449ed72dcb13675813a14f6d8811928f4b84d98fe6aa1eac6cd11870`.
It covers week 2295 including this day and describes weighted combinations of
analysis-centre solutions, robust L1 estimation, alignment and processing checks.
Its contributor exclusions and dated notices were reviewed; a submission appearing
in a header is not proof it contributed with weight. The summary specifically
records JPL/SIO/EMR exclusions and JGX inclusion from week 2289. Internal orbit/clock
consistency/arc evaluations do not prove independent validation of a USSF GP fit.

The header lists `cod emr esa gfz grg jgx jpl mit ngs sio`. Thus **ESA upstream
contribution is present** in this international service; no ESA response, account
or Swarm product is required for this investigation. It would be inaccurate to
call the reference an ESA-free solution. The file is an IGS estimated orbit
combination, not direct satellite observations or a NASA-only independent truth.
CelesTrak documents the GP/Space-Track source path, but the chosen GP fit's tracking
sensors, observation interval, weights and shared dependencies are not established.
Statistical independence and full fitting lineage remain **UNVERIFIED**.

G30 has 96 P records with populated XYZ sigma fields and no missing XYZ, maneuver
or orbit-prediction markers. The header accuracy code is 2: a quantized `2**2=4 mm`
indicator. Per-axis fields use `1.25**n mm`; zero means 1 mm, blank unknown. Header
zero has a different meaning: unknown accuracy. These are source uncertainty
indicators, not proof of calibrated absolute error or a scientific acceptance
threshold. Other satellites have blank sigma fields; G27 lacks all 96 unused
clock values. The global file must not be described as wholly quality-complete.
No velocity or EP covariance records are available in this profile. No full
cross-time/cross-provider/GP uncertainty budget is established. Source precision
or the IGS published typical accuracy does not establish an SGP4 prediction's
accuracy; representational resolution is not a physical-error bound.

After the prerequisite evidence is reviewed, a weaker descriptive retrospective
comparison could be meaningful with explicit limitations. Independent prediction
validation, historical forecasting, confidence/normalized-residual claims and
physical-event conclusions remain unsupported. No numerical scientific
acceptance threshold or uncertainty budget was invented, and the existing
numerical regression tolerances were not changed.

## Proposed protocol and minimum next evidence

The [separate protocol v0.1](engineering-e8-comparison-protocol.md) fixes the
reference bytes, primary target, original grid, conditional UTC interval, fixed
forward GP policy, exact epoch matching, exclusion rules, future transformation
path, sign convention, units, diagnostic outputs, descriptive statistics and
claims limits. Required missing inputs remain explicit rather than fabricated.
A current GP hash identifies an excluded investigation input, not an eligible
initial condition. An executable comparison cannot be enabled through a CLI flag.

Minimum next steps are:

1. Obtain an original historical GP response for NORAD **39533** with an eligible
   epoch in **[2023-12-25T23:44:42Z, 2023-12-31T23:59:42Z]**, retaining source,
   acquisition time, full-response hash and exact record. Recheck identity/model;
   do not backdate retrieval or infer historical availability from the epoch.
2. Qualify IGS20 realization alignment and the satellite physical reference point
   using applicable processing/convention/calibration evidence and independent
   transformation controls. Generic ITRS and current ANTEX alone do not do this.
3. Review per-sample quality, the uncertainty/claims policy and provenance limits;
   freeze the protocol/manifest/mask before viewing any outcomes.
4. Obtain explicit user approval before implementing/running the real comparison.
   E8 stops here. No approval is implied by software tests or a parsed SP3.

Alternatively, a versioned future study could retain today's GP and later acquire
an actual final covering its epochs; this was not scheduled and no availability
promise or forecasting claim is made. No additional account, paid resource,
provider message, real residual, database migration or production deployment
was created by this task.

The new private source captures and per-epoch inspection outputs are retained under
ignored `data/e8-nasa-igs/`, with a preservation manifest. They are excluded from
Git, Docker contexts and routine CI. This cloud filesystem is not an independent
durable backup; retain approved private copies separately before its disposal.
The public evidence contains only metadata/hashes/aggregate exclusions, no state
vectors, raw GP records, personal correspondence or credentials. Existing Swarm
files/reports remain intact; Phase 11.3.1 stays **PARTIAL**, scientific evaluation
**BLOCKED**, and E4 production readiness stays **OPEN**.

**BLOCKED — ADDITIONAL EVIDENCE REQUIRED**
