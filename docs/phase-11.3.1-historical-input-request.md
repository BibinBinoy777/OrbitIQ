# Historical Swarm-A input request — prepared, not submitted

**Human action required. No request, CAPTCHA interaction or email submission has
been performed by OrbitIQ or this task. No account credentials are needed here.**

Verified target: **Swarm-A / SWARM A**, NORAD **39452**, international designator
**2013-067B**, SP3 identifier **L47**, ILRS identifier **1306702**. Sources:
[ILRS correspondence table](https://ilrs.gsfc.nasa.gov/missions/correspondence_table.html)
and the retained [CelesTrak SATCAT response](https://celestrak.org/satcat/records.php?CATNR=39452).
Their actual retained payload hashes and the identity match are in the integration
evidence. Neither catalogue response is a GP input.

Use the provider's supported [CelesTrak historical GP request form](https://celestrak.org/NORAD/archives/request.php).
The retained form documentation specifies CAPTCHA and email delivery. The user
must enter their own contact information, complete CAPTCHA and submit through the
provider. This prepared specification does not authorize automated submission.
Alternatively, an authorized account holder can obtain the same historical GP
through Space-Track's documented `gp_history` interface under its access policy.
The retained earlier request returned 401; it was not retried in this phase.

## Specification to enter

| Field | Requested value |
| --- | --- |
| NORAD catalogue number | `39452` — Swarm-A only |
| Start date | `2013-12-30` |
| Stop date | `2014-01-02` |
| Preferred format | Original provider **GP JSON**, using OMM-compatible fields; not SupGP, propagated XYZ, precise ephemerides or a current element set |
| Purpose | Reproducible, bounded comparison of historical SGP4/WGS72 mean-element propagation with an external ESA Swarm-A kinematic reference product for 1 January 2014; independence remains subject to lineage assessment |
| Intended reference interval | Header UTC validity `2013-12-31T23:59:44` to `2014-01-01T23:59:44`; actual ordinary convertible reference epochs span `2014-01-01T00:02:04` to `2014-01-01T23:57:54` UTC |
| Input selection need | Genuine source records whose source/availability metadata can be checked before the intended evaluation cutoff; preserve later records too, but do not use them to claim a historical forecast |

The short range includes earlier initial conditions and limited surrounding
history. Retain the provider's interpretation of inclusive/exclusive dates and
timezone. Do not expand to bulk/constellation requests or repeatedly request the
same data. Observe the provider's published limits; the retained form states
10 requests per 24 hours, up to 100 satellites and 20,000 records per request.
Only one satellite and this finite interval are required here.

Suggested purpose text:

> Please provide original historical GP JSON records for SWARM A, NORAD 39452,
> covering 2013-12-30 through 2014-01-02. The data will support a reproducible
> retrospective SGP4/WGS72 reference-orbit comparison with ESA Swarm-A kinematic
> product SP3AKIN_2_, version 0201, for 1 January 2014. Please retain the original
> orbital epochs and any available creation/publication/archive timestamps,
> source identifiers and applicable reuse/attribution information. No current
> element set or propagated position substitute is requested.

## Metadata required with the returned attachment

- Original unedited attachment bytes, provider/source identity, exact acquisition
  method, actual receipt/retrieval time and SHA-256 of the entire payload.
- NORAD ID, object name/designator, element epoch, mean elements/drag terms and
  applicable Earth/TEME/UTC/SGP4 conventions. Retain all original fields and numeric
  precision, validation notices, record/set/revolution identifiers and warnings.
- Available provider publication, creation or archive times, with their meaning
  and time scale. Unknown values remain unknown. The element epoch is not proof
  that the input was available at that time; an email received now is not proof
  of availability in 2013/2014.
- Available fit lineage, including sensor/measurement sources, fit interval,
  processing/model version and any relationship to ESA/GNSS/IGS/IERS/CODE inputs.
  Missing lineage must be disclosed, not filled in from assumptions.
- Applicable access, citation and redistribution conditions. A permitted private
  research attachment is not automatically licensed for public GitHub fixtures.

Keep private email contents and personal contact information out of Git and public
reports. Source-relevant provenance may be retained privately under the operator's
data policy; a public summary need not reproduce private correspondence.

## Validation on receipt

1. Preserve the original attachment in a **new private validation location**;
   never replace an earlier file, original ESA product or orbital database.
2. Record bytes, SHA-256, provider and actual receipt timestamp before parsing.
   Confirm that the payload contains real GP records, not a request confirmation,
   authentication error, metadata page or synthetic example.
3. Verify target 39452 and designator 2013-067B, valid epochs/units/conventions,
   finite fields and consistency with the existing `Elements`/GP JSON parser.
   Do not manufacture missing OMM fields or pretend the attachment came from
   today's current-GP endpoint.
4. Preserve a multi-record JSON attachment intact. The current diagnostic wrapper
   reuses the existing **single-record** GP parser; it cannot turn an arbitrary
   historical array or TLE file into a qualified input. If multiple records are
   returned, review a bounded record-selection mechanism retaining original bytes,
   source index and hashes before integration. Do not hand-edit the original.
5. Select input/evaluation rules before computing any errors. Require same target,
   genuine provenance, source-epoch offsets inside the existing ±7-day bound,
   supported exact times and acceptable reference quality/frame treatment.
6. If availability before evaluation cannot be established, label an otherwise
   valid future comparison **retrospective**. Do not promote an epoch or parsed
   record into proof of prospective prediction.
7. Record GP/reference lineage, frame/time qualification and every exclusion.
   **Do not calculate residuals until the remaining gates pass.**

Current result: **no historical GP/TLE acquired**. The source/identity/time/frame
diagnostic tool and synthetic tests are not a replacement for that attachment.
