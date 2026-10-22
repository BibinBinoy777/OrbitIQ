# Phase 11.3.1 — scientific clarification checklist

Prepared on 21 October 2026; status updated **22 October 2026**.
**ESA: SUBMITTED, AWAITING RESPONSE. CelesTrak: RESPONSE RECEIVED,
user-reported summary.** Submission and reply dates/times were not supplied.
See [provider inquiry tracking](phase-11.3.1-provider-inquiries.md) for evidence
limits and outstanding subjects. This checklist is not a copy of the sent emails;
the assistant did not send a message. Do not include correspondence or credentials
in Git. The [scientific pairing report](phase-11.3.1-scientific-pairing-report.md)
contains the scientific evidence and unchanged BLOCKED decision.

## Exact reference to identify in a provider inquiry

Identifiers recorded in the [scientific pairing report](phase-11.3.1-scientific-pairing-report.md):

| Field | Exact recorded value |
| --- | --- |
| ESA archive filename | `SW_OPER_SP3AKIN_2__20131231T235944_20140101T235944_0201.ZIP` |
| Original SP3 member filename | `SW_OPER_SP3AKIN_2__20131231T235944_20140101T235944_0201.sp3` |
| Product identifier / spacecraft | `SP3AKIN_2_` / Swarm-A |
| Product/file version | `0201` |
| Processing software | `L2PS-DUT/44.88` |
| Creator / creator version | `SPC_DUT` / `44.88` |
| SP3 member SHA-256 | `c6c9c0c610c64258abf7b0e7c38d0429fb73a90768b0c600a43f6c3f1f43eb27` |

Use the recorded file version and processor identifiers when requesting
baseline-specific clarification; the report does not supply a separate
processing-baseline identifier. Sensing/validity is UTC 2013-12-31T23:59:44
through 2014-01-01T23:59:44.
Associated `SP3AVAL_2_` has the same interval/version/processor and upstream input
names. The XML cites `SW-DS-DTU-GS-0001`; the reviewed revision is 3.0,
2021-02-25, §§4.3.2 and 5.9.1. Identify the actual KIN product, rather than asking
about the related `SP3ACOM_2_` reduced-dynamic product in general.

## Time and format clarification

1. Does a baseline-specific specification/change note explicitly describe the
   SP3-d output used here, superseding revision 3.0's SP3-c declaration?
2. What is the supported meaning of zero in the nominal epoch-interval field
   for these observation-epoch kinematic records? SP3-d normally requires a
   positive value. Does a producer-specific convention apply?
3. What is the intended interpretation of `60.00000000` in ordinary GPS-calendar
   minutes? GPS time has no leap seconds. Is there an approved exact calendar
   carry convention for this writer/version, and independently checkable examples?
4. Should eight-decimal fractions such as seconds ending in `.99999999` or
   `.00000001` be interpreted literally? Is there documented writer quantization,
   or must the 10-ns distinctions be preserved? Supply uncertainty/clock semantics
   and examples rather than a request to round to a convenient ten-second grid.
5. Which timestamp representation is authoritative when the first calendar tag
   is GPS 00:02:20 but week 1773 / seconds-of-week 259220 identifies 00:00:20?
   The 120-second disagreement needs an erratum or exact producer interpretation;
   OrbitIQ has not shifted either representation. The redundant MJD fraction
   also differs from the calendar tag by +37.12 ns. Supply a disposition of both
   differences without introducing an arbitrary matching tolerance.

Current handling retains 1,806 submicrosecond and 723 second-60 exclusions, with
no repair or rounding. A provider clarification would require separate scientific
review and tests before changing that policy.

## Kinematic quality and uncertainty clarification

1. Which exact plots or numeric fields in the matching `SP3AVAL_2_` validate
   **this KIN member**? The reviewed page-6 ephemeris comparison names RDOD files;
   the SLR pages say “Swarm-A POD” without uniquely identifying the KIN member.
2. Is there an associated KIN-specific per-epoch accept/reject mask, known outage,
   ambiguity-resolution status or discontinuity list? What are the definitions
   and version applicability of XML error `0` and quality `000`?
3. What do the EP formal XYZ sigmas/correlations include or omit? Are they
   calibrated against external checks for this baseline, and how should systematic
   effects, common GNSS inputs and epoch-to-epoch correlations be treated?
4. Does the nominal “10 cm 3D” specification quantify a particular confidence
   level, aggregate metric and population for this baseline? It is not currently
   treated as an individual-epoch error bound or an OrbitIQ accuracy result.
5. Can the product-level report establish an accepted interval and uncertainty
   budget for a retrospective SGP4 comparison? Identify supporting data without
   inferring acceptance from small formal sigmas or printed coordinate precision.

## Frame and processing lineage clarification

1. Confirm the actual `IGb08` realization and how the 0201 processing aligned it:
   GNSS orbit/clock products, station frame/coordinates, antenna models, EOP
   series, software settings and applicable versions/reference epochs.
2. Is there an authoritative precision-scoped treatment for comparing that
   solution with an explicitly defined TEME→ITRS pipeline? Any proposed transform
   needs input/output realizations, parameters/rates, reference epoch, validity,
   uncertainty and independent verification. Station-specific IGb08 changes are
   not a satellite-wide Helmert transformation.
3. What direct or indirect observation/processing dependencies are known between
   this reference and the particular historical GP records? General provider
   descriptions cannot prove independence of the specific fit/reference pair.

OrbitIQ must separately define the scientific comparison objective and error
budget. An unspecified ITRS label and presumed “small” datum differences do not
approve an identity transformation.

## Historical GP provenance clarification

The separate CelesTrak-attributed CSV has three Swarm-A records, source indices
0–2, with `ELEMENT_SET_NO` values 35–37 (distinct from `REV_AT_EPOCH` 583/604/620).
The complete private source strings and hashes are retained. The provider response
as summarized by the user confirms CSV as supported/preferred, without a promised
JSON-fix timeline. Corrected JSON is no longer a prerequisite. It also states that
record-creation timestamps are not retained; orbital epochs do not establish
historical publication/availability, and available metadata does not establish
complete fitting lineage. Actual provider-email receipt/acquisition and historical
publication/archive-availability times remain unknown.

The reported explanation concerning use of 999 in GP data does not establish its
applicability to these historical rows. Preserve 35–37; do not replace them with
999 or interpret them as publication times or globally unique archive identifiers.
See the [response reconciliation](phase-11.3.1-provider-response-reconciliation.md)
for the inspected schema/evidence and remaining semantic uncertainty. These GP
clarifications do not answer the ESA time, quality or frame questions above.

If available, obtain non-sensitive provenance that links the exact records to the
provider return and distinguishes element epoch from creation/publication and
historical availability. Do not send credentials, IP addresses or private email
bodies to the repository. If availability cannot be established, preserve that
limitation and retain **retrospective-only** interpretation. Unknown sensor-level
GP fitting lineage must remain explicitly unknown, rather than inferred from the
fact that the reference came through a different organization.
