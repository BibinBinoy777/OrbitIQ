# Phase 11 follow-up: validation dataset source review

Review performed on 20 October 2026 UTC. This is a source/compatibility assessment,
not an accuracy result. HTTP receipts, document hashes, selected short excerpts,
and failed discovery attempts are in
[the follow-up evidence](phase-11-followup-integration-results.json). A successful
HTTP request alone is not evidence that a page contains the expected documentation.

**No independently validated benchmark dataset has been selected.** None of the
investigated sources supplies an established independent Cartesian reference paired
with the two archived ISS inputs. This does not prove such data does not exist.
ESA Swarm POD is a documented candidate for a *different, paired reference-product
comparison*, subject to the gates below. No observation or orbit-product payload
was ingested. Documentation, object metadata and bounded directory listings were
retrieved for this review only.

## Actual OrbitIQ scientific scope

| Item | Inspected implementation and limit |
| --- | --- |
| Objects | Catalogued Earth-orbiting objects satisfying `Elements`, NORAD 1–339999, unclassified, elliptical `0 <= e < 1`, mean motion `(0,100]` rev/day. The engine is not restricted to LEO: the library selects near/deep-space SGP4 behavior; published cases exercise both. Actual archived coverage is only ISS, NORAD 25544. No solar-system N-body or GNSS precise-orbit engine exists. |
| Inputs | CelesTrak GP JSON using OMM fields, `EPHEMERIS_TYPE=0`, Earth/TEME/UTC/SGP4 conventions; source bytes, raw and normalized records, validation, payload hashes, retrieval and element epochs are retained. This is not a general OMM/XML/SP3/TLE-upload parser. |
| Initial conditions | The mean elements and drag terms of one explicitly identified immutable GP snapshot, initialized through `sgp4.omm.initialize` with WGS72. No OrbitIQ orbit fit or parameter estimation takes place. |
| Model | Locked python-sgp4, SGP4 with WGS72; no selectable alternate force model. Software versions, backend/lock hashes and calculation resources are captured in existing replay evidence. Producer fit version, fit interval, sensor/observation IDs, weights and full lineage are not present in the GP archive. Recording OrbitIQ's version does not fill that gap. |
| Time | UTC-aware requests; CelesTrak's documented timezone-free epoch means UTC. Application report timestamps support at most microsecond precision. SGP4 nominal-day convention and leap-crossing restrictions are retained. No normalized observation GPS/TAI/TDB input conversion exists. |
| Outputs | Calculated Earth-centered TEME Cartesian position km and velocity km/s at the requested time; existing Astropy TEME→ITRS transformation uses strict local IERS/EOP and leap resources. ITRS→WGS84 geodetic output supports existing tracks; no arbitrary reference-frame adapter exists. |
| Bound | Propagation within ±7 nominal days of the element epoch; this is a product limit, not an accuracy guarantee. Freshness and strict transformation-resource restrictions can also make results unavailable. |
| Preservation | The snapshot archive preserves inputs. Predictions are computed on request, not automatically saved as a historically issued forecast. Explicit Phase 9 reports / Phase 10 bundles and extension packages preserve requested definitions, calculated states, generation times and provenance when captured. |
| Uncertainty | GP prediction covariance is absent. `not_quantified` remains explicit. Optional reference axis sigmas are preserved, not converted into joint covariance or confidence. |
| Reference contract | At most ten records / 64 KiB per capture; same catalog, exact UTC epoch, geocentric Cartesian position, Earth center, TEME or ITRS, m or km. Supported kinds are measurement or observation-derived state; `model_output` is excluded. Ranges, angular observations, elements, unknown frames/units and future/inconsistent epochs are not subtracted. |

Source inspection: `backend/orbitiq/orbits/{elements,engine,coordinates,earth_orientation}.py`,
`backend/orbitiq/services/{analysis,reports,observation_validation}.py`,
`backend/orbitiq/observation_validation.py`, `backend/orbitiq/replay*.py`,
`backend/orbitiq/storage.py`, existing tests and phase reports.

The unchanged ordinary schema-3 archive contains two ISS GP snapshots (IDs 1/2),
epochs 2026-10-18 11:12:47.040768 UTC and 18:57:18.892800 UTC. Retrievals were
2026-10-18 17:14:39.983172 UTC and 2026-10-19 07:58:23.407349 UTC. The second
record's insertion ledger exists; the first record's insertion time is unknown.
These are two propagation inputs, not two independent observations. No configured
independent observation archive or full fitting-observation lineage was found.

## Candidate assessment

### CelesTrak GP / Space-Track-derived mean elements

Authoritative [GP format documentation](https://celestrak.org/NORAD/documentation/gp-data-formats.php)
describes fitting SSN observations to Brouwer mean elements with SGP4, including
the omitted Earth/TEME/UTC/SGP4 invariant fields. The
[TLE FAQ](https://celestrak.org/columns/v04n05/index.php) explains why mean elements
are model-specific and why prediction accuracy varies with sensors, orbit and
conditions. Both documents were retrieved successfully.

This source matches the prediction model and catalog domain. It provides model
inputs, not independent physical positions or a sensor-level fit ledger. Later
element sets, different payloads and a second provider redistributing the same
elements do not establish independence. Numerical comparison remains useful for
historical model changes. Existing GP JSON lacks prediction covariance. Public
current-data access is supported; the documented update/error limits must be
respected. No historical data entitlement or blanket redistribution license is
inferred from public availability. Reuse of existing retained inputs requires no
new acquisition here. **Reject as independent validation reference.**

### NASA CDDIS / IGS GNSS orbit products

The old CDDIS precise-orbit page now contains an HTML refresh pointing to
[NASA Earthdata's precise-orbits product documentation](https://www.earthdata.nasa.gov/data/space-geodesy-techniques/gnss/precise-orbits-product).
That actual destination was followed and read. It documents analysis-center and
combined GNSS solutions, final/rapid/ultra-rapid products, product summaries and
historical/reprocessed archives. They are **processed orbit products**, not raw
position observations. Ultra-rapid predicted segments must not become observations.

[IGS SP3-d specification](https://files.igs.org/pub/data/format/sp3d.pdf) documents
position units km, frame descriptors, mandatory declared time systems (no default),
orbit type and prediction flags, optional accuracy/sigma/correlation fields, and
missing/unknown conventions. SP3 is a container, not an assurance that every file
is an observed precise orbit. A listed example can even contain broadcast orbits.
GPS time must not be relabelled UTC. IGS/ITRF realization and precise target identity
(PRN/SVN/NORAD over the evaluation period) need explicit mapping. Absent accuracy
fields or unknown accuracy codes do not mean zero uncertainty.

GNSS objects can potentially be propagated by this SGP4 implementation if valid
matching GP inputs exist; GNSS products are not automatically compatible with the
current ISS-only archive. No GNSS GP snapshot, paired product or mapping is present.
Producer analyses/summaries must identify upstream GNSS observations and models;
these do not disclose the SSN GP fit's complete lineage. Distinct organizations
therefore leave independence uncertain.

[CDDIS HTTPS access documentation](https://cddis.nasa.gov/Data_and_Derived_Products/CreateNetrcFile.html)
describes Earthdata Login credentials. None are configured for this task and none
were requested or read. Archive authentication was not attempted, so accessibility
of a particular product remains unverified. NASA's
[data guidance](https://www.earthdata.nasa.gov/engage/open-data-services-software-policies/data-information-guidance)
does not substitute for checking a selected third-party product's terms/citation.
IGS `products/` and `data/` returned 503 during this review; their contents were
not used as successfully retrieved evidence. Small fixtures are feasible only
after selecting the product, retaining metadata/summary and resolving reuse rights.
**Candidate for a separate GNSS reference-product study; no current ISS pair.**

### NASA/JPL Horizons, including its ISS entry

The [Horizons manual](https://ssd.jpl.nasa.gov/horizons/manual.html) documents
natural bodies, a limited set of spacecraft trajectories, user-supplied TLE
propagation, coordinate centers/frames and time systems. Spacecraft products have
source-dependent quality; small-body covariance support does not imply ISS
covariance. Vector frame/center, geometric versus light-time-corrected state,
time convention and target source must all be verified. ICRF, J2000 and TEME are
not interchangeable labels. Horizons has no general promise of an independent
physical reference for every NORAD object.

A bounded [ISS object-metadata request](https://ssd.jpl.nasa.gov/api/horizons.api?format=text&COMMAND=%27-125544%27&MAKE_EPHEM=%27NO%27&OBJ_DATA=%27YES%27)
was executed with `MAKE_EPHEM=NO`. Its actual response explicitly states:
**“Trajectory is TLE-based.”** It also warns about low accuracy beyond a few days
past the revision date. No vectors or statistical accuracy benchmark were requested.
Different output frames would not remove this dependency. The
[API documentation](https://ssd-api.jpl.nasa.gov/doc/horizons.html) was also read.
Public metadata access succeeded, but no independent ISS observation lineage or
prediction covariance was established. **Reject this ISS entry as an independent
reference; do not build an adapter to repackage the same type of model input.**

### NASA SSCWeb ISS trajectories

The [current homepage](https://sscweb.gsfc.nasa.gov/) links its
[data provenance table](https://sscweb.gsfc.nasa.gov/sscweb_data_provenance.html).
The actual table identifies ISS with TLE inputs, including entries labelled
definitive/predictive. “Definitive” does not by itself mean an independently
measured orbit. The output service's coordinate conversions cannot establish
independence from that underlying trajectory. Public documentation was accessible;
no spacecraft states were acquired. Two stale discovery URLs returned 404 and
are retained as failed attempts. **Reject ISS as an independent reference here.**

### NASA ISS OEM trajectory links

The previously known Spot the Station trajectory page and `ISS.OEM_J2K_EPH.txt`
URL both returned **404**. A NASA search URL returned HTTP 200 with a “Page Not
Found” title and was also rejected as source evidence. No current authoritative
payload, time coverage, fitting lineage, uncertainty or reuse terms were
established from these endpoints. Do not classify an unavailable OEM as observed
ground truth; OEM describes an ephemeris message format, not independence. A future
J2000/EME2000 product would also need an explicitly validated transformation rather
than a TEME label. **Unavailable candidate, not a benchmark.**

### ILRS satellite laser ranging and CPF predictions

Authoritative [CRD overview](https://ilrs.gsfc.nasa.gov/data_and_products/formats/crd.html)
and its linked [CRD 2.01 specification](https://ilrs.gsfc.nasa.gov/docs/2022/crd_v2.01e3.pdf)
describe genuine laser full-rate/normal-point data: time of flight, station,
timing, calibration, correction and quality information. They are range-related
observations, **not three-dimensional Cartesian satellite positions**. A valid
evaluation requires a station/observable model with timing, light travel,
atmospheric and center-of-mass corrections; OrbitIQ has no such comparison model.
Squeezing ranges into three numbers would be scientifically invalid. Catalog,
station and mission identity/availability must be verified for any selected arc.

[CPF overview](https://ilrs.gsfc.nasa.gov/data_and_products/formats/cpf.html)
and [CPF 2.00 specification](https://ilrs.gsfc.nasa.gov/docs/2018/cpf_2.00h-1.pdf)
describe **predictions** used for ranging operations. Cartesian format does not
make them measured independent positions. Frame, time, center and prediction
producer lineage still matter. Documentation was accessible; no ranging or CPF
product was acquired and mission-specific data-use constraints were not cleared.
**Raw CRD needs a different observable model; CPF is not the required observation.**

### ESA Swarm precise orbit determination (recommended candidate for planning)

ESA's [mission data page](https://earth.esa.int/eogateway/missions/swarm/data),
[daily products catalogue](https://earth.esa.int/eogateway/catalog/swarm-level-2-daily),
[handbook documentation](https://swarmhandbook.earth.esa.int/article/documentation)
and linked [Level 2 product specification](https://earth.esa.int/eogateway/documents/d/earth-online/swarm-level-2-product-specification)
were retrieved and read. The specification is SW-DS-DTU-GS-0001 revision 3.0,
25 February 2021, §§4.3.2 and 5.9.1, printed pp.28 and 93–95. Current individual
products may use newer baselines; the specification is not a runtime version receipt.

`SP3xKIN_2_` is a kinematic center-of-mass position product; `SP3xCOM_2_` is
reduced-dynamic position/velocity. Both use onboard GPS data, attitude/spacecraft
information and external IGS/IERS/CODE inputs. They are **observation-derived,
processed reference orbits**, not direct XYZ sensor observations. Shared external
EOP and upstream GNSS resources must be recorded. Kinematic and reduced-dynamic
solutions from the same inputs are not two independent validation sources.

The specification declares ITRF Earth-fixed positions, GPS time, km position,
SP3-c files, separate `SP3xVAL_2_` quality reports and a nominal 10-cm 3D uncertainty.
That nominal product statement is **not** three per-axis sigmas, a per-record
covariance, or an OrbitIQ prediction-error bound. Do not populate the optional
axis-sigma field with it. A selected file's frame realization, quality and sigma
fields require inspection. SP3-c parsing must follow its actual specification;
the SP3-d document alone is not a provider-specific parser contract.

Bounded, read-only [ESA dissemination](https://swarm-diss.eo.esa.int/) listings
confirmed POD/KIN and POD/RD directories for Swarm A/B/C. The first five Swarm-A
files in each listing cover early January 2014 (names/paths retained in evidence).
This establishes catalogue availability, not successful download/validation or
complete historical coverage. No ZIP was downloaded and no Swarm position was
calculated. Swarm is the appropriate *LEO candidate domain*, not the same object
as ISS; an authoritative mission/SP3-ID/NORAD mapping is still required.

The specification lists **21-day latency** for final POD, exceeding OrbitIQ's
±7-day propagation window if paired with a GP input acquired only at product
publication. Therefore a new current GP fetch is not a replacement for a matched
historical input. Obtain a genuine historical Swarm GP with documented provenance,
or archive GP prospectively and wait for the matching final POD. Never invent an
earlier retrieval time or relax the propagation bound to force a result.

ESA's [linked terms, issue 1.1 of 20 September 2023](https://earth.esa.int/eogateway/documents/20142/1564626/Terms-and-Conditions-for-the-use-of-ESA-Data.pdf)
include duplication provisions, onward-distribution conditions (§B.5), attribution
(§B.10), retained rights and copyright marking (§C). The dissemination service
says access/use acknowledges the terms. Public access is not an unconditional
GitHub fixture license. Confirm the selected product's current applicable terms
and recipient conditions before distributing original data. No agreement was
created, account registered, or data redistributed as part of this task.

**Recommended for a reviewed, paired reference-product study; not selected for
ingestion now.** Missing: matching archived Swarm GP, target mapping, exact product
and quality report, retained source bytes, applicable reuse decision, processor
baseline and lineage assessment. SSN fitting lineage still prevents automatic
independence establishment. See the [protocol](scientific-benchmark-protocol.md).

## Selection decision

The two available ISS inputs do not have an established independently measured
counterpart in the investigated sources. Useful authoritative products exist,
but a complete compatible input/reference pair does not exist in this repository.
No adapter, migration, new service, synthetic accuracy benchmark or unsupported
conversion was added. The next task is to freeze a real paired Swarm dataset and
its provenance/terms, then review a narrow SP3-c adapter and reference-product
labelling. If historical GP cannot be obtained legitimately, use prospective
collection with later reference release; do not backfill fictional acquisition
history. Independent physical accuracy remains a separate, harder gate.
