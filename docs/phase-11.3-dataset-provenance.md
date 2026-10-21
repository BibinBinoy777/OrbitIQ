# Phase 11.3 dataset provenance and qualification

Data provided by the European Space Agency (ESA). © ESA 2026.
Local investigation: **21 October 2026**. Acquisition timestamps below are UTC.
This document reports acquired metadata separately from documentation and unresolved
assumptions. **A real reference product was acquired; a qualified historical
GP/reference pair was not.** No OrbitIQ accuracy result was generated.

## Actual source acquisition

Official service: <https://swarm-diss.eo.esa.int/>. Bounded HTTPS GET requests used
the managed proxy with TLS verification, no login, credentials or access bypass.
One KIN ZIP and one matching VAL ZIP were downloaded once. Original bytes and
acquisition receipts are retained privately in ignored
`data/validation-phase-11.3/` (directory 0700, files 0600). No source positions,
product files, PDF plots or synthetic substitutions were added to Git.

The common filename stem interval is
`20131231T235944_20140101T235944_0201`. Identity and coverage were checked against
the **XML header contents**, not inferred solely from that filename.

| Acquired item | Actual receipt |
| --- | --- |
| `SW_OPER_SP3AKIN_2__20131231T235944_20140101T235944_0201.ZIP` | HTTP 200; 473,868 bytes; completed `2026-10-21T05:09:01.385175+00:00` |
| KIN ZIP SHA-256 | `a62164ca7940d415d63a81518a974422d7868b285abc2509423bac96bd9048b3` |
| `SW_OPER_SP3AVAL_2__20131231T235944_20140101T235944_0201.ZIP` | HTTP 200; 433,479 bytes; completed `2026-10-21T05:09:38.202969+00:00` |
| VAL ZIP SHA-256 | `e258ea6afb9bc998e406c5d2f7a26369d716d958da7d2961eb273b645adfeca2` |

Exact download routes:

- [KIN product](https://swarm-diss.eo.esa.int/?do=download&file=swarm%2FLevel2daily%2FLatest_baselines%2FPOD%2FKIN%2FSat_A%2FSW_OPER_SP3AKIN_2__20131231T235944_20140101T235944_0201.ZIP)
- [VAL product](https://swarm-diss.eo.esa.int/?do=download&file=swarm%2FLevel2daily%2FLatest_baselines%2FPOD%2FVAL%2FSat_A%2FSW_OPER_SP3AVAL_2__20131231T235944_20140101T235944_0201.ZIP)

Each ZIP has exactly its matching HDR and data member. ZIP CRC validation and
SHA-256 checks passed. The XML size and checksum fields also passed. The XML CRC
is the **POSIX `cksum` checksum including file length**, distinct from ZIP CRC32.
It was independently checked with the installed `cksum` utility; the inspector
implements the POSIX calculation and tests literal independent checksum cases.

| Member | Bytes | SHA-256 |
| --- | ---: | --- |
| KIN `.HDR` | 2,625 | `3607191f0a525e664a3453f96e7f03caf5876bc276f617bf0b376f019981cc69` |
| KIN `.sp3` | 1,554,264 | `c6c9c0c610c64258abf7b0e7c38d0429fb73a90768b0c600a43f6c3f1f43eb27` |
| VAL `.HDR` | 2,589 | `db48d16156e4673d15181b85c5566825909f7e9c03a3408caf58cd00089922f7` |
| VAL `.pdf` | 829,415 | `ce2158a025430bea6fe856a905f9671060a181d42b8226b30287f7437de020e7` |

The two member POSIX checksums are 3267709387 (SP3) and 2624079523 (PDF).
Hashes establish the identity of the retained bytes, not independent provider
authentication or physical accuracy. HTTPS provenance and the acquisition receipts
are separate evidence. No full-dataset backup/off-machine recovery is claimed.

## Acquired metadata and actual records

Both headers declare Mission `Swarm`, products `SP3AKIN_2_` / `SP3AVAL_2_`,
version `0201`, creator version `44.88`, software `L2PS-DUT/44.88`, identical
explicit UTC validity/sensing interval, product error `0` and quality indicator
`000`. Codes are retained; their presence alone does not certify a usable interval.

KIN header creation is `UTC=2022-05-17T12:08:43`; VAL is one second later.
These are reprocessed products, not files known to have existed in January 2014.
The KIN comments identify `RDOD_AR_WGT` and an execution in October 2021.
Creation, processing, sensing and retrieval are distinct clocks.

The [official ILRS correspondence table](https://ilrs.gsfc.nasa.gov/missions/correspondence_table.html)
explicitly maps **Swarm-A → L47 → NORAD 39452**, ILRS ID 1306702. A separate
[CelesTrak SATCAT lookup](https://celestrak.org/satcat/records.php?CATNR=39452)
identified `SWARM A`, object `2013-067B`, owner ESA. This is identity evidence,
not a GP/TLE record or a source-availability cutoff.

Actual SP3 inspection found:

- **SP3-d**, beginning `#dP`, not SP3-c as assumed from the older general product
  specification. Only P position/clock and EP uncertainty/correlation records occur;
  **no velocity records** occur. The clock field is not velocity.
- **7,647 epochs, 7,647 L47 position records, 7,647 EP records**. XYZ positions use
  km under the inspected SP3-d specification. The XML describes center-of-mass
  kinematic positions in an Earth-fixed frame.
- Explicit time-system field **GPS** and frame declaration **IGb08**, processing
  type `KIN`, agency `TUD`. These declarations must survive any later normalization.
- First actual record `2014 01 01 00 02 20.00000000` GPS calendar; last actual
  record `2014 01 01 23 58 10.00000000`. Header validity is instead explicitly
  `UTC=2013-12-31T23:59:44` through `UTC=2014-01-01T23:59:44`. Neither header
  endpoints nor filenames substitute for actual available records.
- Nominal interval field **0**; actual diagnostic intervals vary. The source
  therefore cannot be treated as a complete regular ten-second series. The
  SP3 specification normally bounds a positive interval; this zero value is an
  additional source-specific conformance/interpretation issue, not an endorsed
  general SP3 convention.
- **1,806** records have nonzero submicrosecond parts; **723** encode seconds as
  `60.00000000`, including ordinary GPS minutes. These counts can overlap and
  must not be added to obtain excluded-sample totals. All 7,647 are withheld from
  comparison; no rounding, leap-second interpretation or UTC conversion occurred.

The inspector uses exact Decimal arithmetic for source-calendar *diagnostics*,
including rollover arithmetic when reporting adjacent field differences. That is
explicitly not an approved GPS→UTC alignment or an endorsement of the second-60
encoding. It does not emit positions into the current microsecond observation
contract. Original values remain in the private SP3 member.

EP records supply per-axis/reference clock sigmas and correlation information under
SP3-d. They were structurally checked and retained in the original file. They
were not coerced into an independent-error covariance or a prediction covariance.
No nominal product accuracy was assigned to individual records.

## Quality product and lineage

The acquired VAL header matches the KIN spacecraft, interval, processing baseline
and all four upstream filenames:

1. `SW_OPER_MODA_SC_1B_20140101T000000_20140101T235959_0401.sp3`
2. `SW_OPER_STRAATT_1B_20140101T000000_20140101T235959_0401_MDR_SAT_AT.cdf`
3. `SW_OPER_SC_ADYN_1B_20140101T000000_20140101T235959_0401_MDR_SC_DYN.cdf`
4. `SW_OPER_GPSA_RO_1B_20140101T000004_20140101T235954_0401.rnx`

The nine-page PDF was actually inspected. Its plotted content was rendered for
visual review because `pdftotext` returned only page numbers; OCR was also run but
was noisy and was not treated as authoritative numeric extraction. Page 1 shows
GPS visibility/tracking; page 2 reduced-dynamic fit residuals/clock/accelerations;
pages 3–4 pseudorange/carrier-phase directional plots; page 5 tracking/status-like
color blocks without a sufficient textual acceptance legend; page 6 an ephemeris
comparison; page 7 is blank apart from its page number; pages 8–9 show SLR residual
plots, including station-specific plots. No global accept/reject decision for every
KIN epoch was inferred from these images. Provider plot statistics were not copied
into OrbitIQ accuracy metrics. The CLI links and hashes this PDF but does not
interpret its plots automatically.

Official [ESA product specification](https://earth.esa.int/eogateway/documents/d/earth-online/swarm-level-2-product-specification),
revision 3.0, §§4.3.2/5.9.1, documents onboard GPS, attitude/spacecraft information
and external IGS/IERS/CODE contributions, final product latency, nominal uncertainty
and a separate validation report. The current headers establish the *actual*
baseline and inputs; a general specification does not prove the full runtime
lineage of every source. The [SP3-d specification](https://files.igs.org/pub/data/format/sp3d.pdf)
documents its frame/time/units and EP fields. IGb08 is an IGS realization related
to ITRF2008; it is not simply the current application's unspecified ITRS label.
No approved realization-alignment parameters or precision-scale error treatment
were established. A guessed IGS coordinate-file URL returned 404 and was rejected
as evidence rather than replaced with assumed parameters.

Classification: **external, observation-derived processed precision-orbit estimate**,
produced by ESA's processing chain independently of OrbitIQ's software. It is not a
raw XYZ sensor measurement, a GP element set, or a synthetic fixture. Independence
from an eventual GP fit remains **uncertain**: no historical GP payload or SSN
sensor-level fit ledger is present, and shared upstream/processing information
cannot be excluded. Provider SLR checks do not establish independence of an
unobtained GP/reference pair.

## Historical GP/TLE acquisition and precise blockers

No Swarm-A GP/TLE was found in the original two-record ISS-only archive.
No current GP was downloaded as a substitute. The actual public routes checked:

- [CelesTrak archive index](https://celestrak.org/NORAD/archives/) points beyond
  its public historical files to the [special data request form](https://celestrak.org/NORAD/archives/request.php).
  The current form says records from 1957 onward can be requested, delivered by
  email, with **CAPTCHA** and stated request limits. It is not an unattended
  historical-download API. No form was submitted, message sent or CAPTCHA bypassed.
- The documented Space-Track `gp_history` route was requested once, bounded to
  catalog 39452 / epochs 2013-12-31 through 2014-01-02. It returned **HTTP 401**,
  JSON `You must be logged in to complete this action`. No configured identity or
  credentials were available; none were requested, read or exposed. No login or
  repeated request was attempted.
- Bounded ESA product navigation did not expose a GP/TLE product in the inspected
  Level-1B/Level-2 categories. This limited inspection is not proof that no
  historical element source exists elsewhere. GPS navigation/precise positions
  are not substitutes for SGP4-fitted mean elements.

Consequently there is no GP source hash, element epoch, retrieval/publication time,
or verified prediction data-availability cutoff. The dataset-pair success condition
is **not met**. An eventual GP epoch alone will not establish publication time.
The fact that the ESA reference was reprocessed later is allowed for retrospective
reference assessment, but cannot establish that OrbitIQ historically issued a
forecast. Genuine historical GP provenance or prospective capture and later POD
release are required; the documented final-POD latency exceeds the current ±7-day
window if a new GP is fetched only at reference release.

Additional gates: approved IGb08/ITRS treatment; GPS epoch encoding and precision
policy; quality interpretation and inclusion rules; and fit/reference lineage.
No EOP coverage policy, propagation range, exact-time requirement or tolerance was
changed to bypass them. The installed EOP/leap identities and coverage are recorded
in the integration evidence; their availability does not settle frame realization.

## Terms, retention and reproduction

The service's linked [ESA terms](https://earth.esa.int/eogateway/documents/20142/1564626/Terms-and-Conditions-for-the-use-of-ESA-Data.pdf)
were reacquired and inspected. They permit work-related duplication (§B.4), impose
conditions on onward distribution (§B.5), require attribution (§B.10), and retain
rights/copyright requirements (§C). Public downloads succeeded without registration.
Only private local retention for this authorized investigation was used. Onward
distribution of raw products through GitHub has **not** been cleared. No raw or
derived source-coordinate fixtures are committed. The automated tests are labelled
synthetic format tests and never download data.

An authorized operator can obtain the two exact linked files under the applicable
terms, preserve the unmodified ZIPs and acquisition receipts in a newly created
private directory, and verify the hashes above. From this checkout:

```sh
PYTHONPATH=backend uv run --locked python scripts/inspect_swarm_reference.py \
  --kinematic /absolute/private/SW_OPER_SP3AKIN_2__20131231T235944_20140101T235944_0201.ZIP \
  --validation /absolute/private/SW_OPER_SP3AVAL_2__20131231T235944_20140101T235944_0201.ZIP \
  --kinematic-sha256 a62164ca7940d415d63a81518a974422d7868b285abc2509423bac96bd9048b3 \
  --validation-sha256 e258ea6afb9bc998e406c5d2f7a26369d716d958da7d2961eb273b645adfeca2 \
  --output /absolute/private/new-inspection.json
```

Input and output paths must be absolute. Existing outputs, symlink inputs, changed
hashes, unsafe ZIP members, unsupported layouts and contradictory metadata are
refused. No extraction, HTTP access, database access, propagation or import occurs.
Exit 0 means **inspection completed with benchmark blocked**, not scientific
validation success. A fresh checkout can reproduce synthetic tests without ESA
data; authentic inspection additionally needs the authorized retained products.
