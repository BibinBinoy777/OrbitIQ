# Phase 11.3.1 — provider response reconciliation

Documentation checkpoint: **22 October 2026**. Phase status **PARTIAL**;
scientific pairing/evaluation **BLOCKED**. Documentation only: no source-data,
adapter, scientific calculation, runtime, dependency or database changes.

## Evidence and format decision

The current user request supplies a summary of CelesTrak's response. Original
correspondence, authenticated headers, and submission/reply dates were not
supplied. The findings below are attributed to **user-reported provider
clarification**, without inventing a direct quote or independent authentication.
No message was sent or requested by this task. ESA's separate reply remains
pending; [provider inquiry tracking](phase-11.3.1-provider-inquiries.md) retains
the existing reference and evidence limits.

| Item | Current decision / evidence |
| --- | --- |
| Original JSON | Still fails strict JSON parsing; preserved unchanged. The reported response promises no particular timeline for a system-wide fix, not a completed fix |
| Separate CSV | Supported and preferred by CelesTrak according to the supplied summary; use this format path for the investigation |
| Existing CSV adapter | Already supports the verified 17-column format. Earlier evidence records three static element-model passes and 51 matching values; no adapter change is needed |
| Prospective corrected JSON | Optional future evidence, no longer a prerequisite for continuing qualification. Never replace the preserved original with a derivative |
| Scientific approval | Not granted by format acceptance. No historical record or reference interval selected; no propagation, state transform or real residual performed |

The [CSV intake report](phase-11.3.1-csv-intake-report.md),
[reconciliation evidence](phase-11.3.1-csv-verification.json) and
[scientific pairing assessment](phase-11.3.1-scientific-pairing-report.md)
retain their original execution results. The earlier historical attachment
assessment's corrected-JSON follow-up is a historical proposal, superseded for
the current format decision by this checkpoint. No claim is made that its JSON
defect was repaired.

## Distinct clocks and provenance

| Fact | Supported status |
| --- | --- |
| Element epoch | Source `EPOCH`, interpreted as UTC under the documented CelesTrak GP convention; the three exact strings are listed below |
| Actual GP receipt/acquisition | Unknown in the supplied evidence. Local capture/audit times and the earlier request time are separate clocks |
| Source/provider identity | User attributes the GP attachments and response to CelesTrak; exact-record sender/delivery authentication remains unestablished |
| Record identifiers | NORAD 39452, designator 2013-067B, source indices 0–2, source epoch, `ELEMENT_SET_NO` and `REV_AT_EPOCH`; preserve original attachment hash and field strings |
| Record creation | Provider reportedly does not retain creation timestamps in its data; these records do not provide them |
| Historical publication/availability | Unknown. Neither orbital epoch nor today's provider response proves an operator could obtain a record on 1 January 2014 |
| Fitting lineage | Complete lineage of these specific records is not established by available metadata; sensor inputs, fit interval and processing dependencies remain unknown |
| Independence | **NOT ESTABLISHED** for this GP/ESA pair. Separate providers and matching identifiers do not prove statistical independence |

If the other scientific gates later pass, a comparison without separate historical
availability evidence must be labelled **retrospective**. It cannot demonstrate a
forecast made or available in 2014. The response explains a metadata limitation;
it does not turn the unavailable creation timestamp into a passed availability
gate. Do not infer an entire historical archive's conventions from current GP
practice, or general SSN fitting documentation into a record-specific fit ledger.

## Element-set identifier review

Reviewed the actual captured header and original decoded field strings in the
existing private **inspection report**, without reopening JSON/CSV/ESA source
attachments. The inspection SHA-256 is
`15817e1db842f6515870d909a402627da66b12e933772d43ae4cb3e85749ac7c`;
it matches both the capture manifest and the earlier public CSV verification
record. The manifest SHA-256 also matches that earlier record. The inspection
anchors the original CSV at SHA-256
`2b5712d5c2fe3fd6f8106633cb84780d6562eb455f49922fbbbbe9d09a26f1c4`.
This is a review of preserved inspection evidence, not a new raw-file intake.

The exact 17-column header is:

```text
OBJECT_NAME,OBJECT_ID,EPOCH,MEAN_MOTION,ECCENTRICITY,INCLINATION,RA_OF_ASC_NODE,ARG_OF_PERICENTER,MEAN_ANOMALY,EPHEMERIS_TYPE,CLASSIFICATION_TYPE,NORAD_CAT_ID,ELEMENT_SET_NO,REV_AT_EPOCH,BSTAR,MEAN_MOTION_DOT,MEAN_MOTION_DDOT
```

| Zero-based source index | `EPOCH` source text (UTC convention) | `ELEMENT_SET_NO` | `REV_AT_EPOCH` |
| --- | --- | --- | --- |
| 0 | `2013-12-30T20:24:39.765600` | 35 | 583 |
| 1 | `2014-01-01T05:30:45.095904` | 36 | 604 |
| 2 | `2014-01-02T06:43:57.421344` | 37 | 620 |

**35–37 are values of `ELEMENT_SET_NO`**, not row indices or revolution values.
The adapter's declared schema maps that column to `Elements.element_set` through
the existing GP field mapping, and treats it as an unsigned integer. Earlier
exact reconciliation found all 51 source values equal, with no unexplained value
or source-precision change. These facts establish source-field consistency, not
provider authentication or the identifier's historical semantics.

The request mentions the provider's explanation concerning use of **999** in GP
data, but supplies no exact wording or historical applicability rule. It cannot
establish why these particular 2013/2014 rows contain 35–37, whether 999 applies
to them, or that their values are erroneous. Preserve 35–37 unchanged, with their
meaning beyond the source field explicitly uncertain. Do not substitute 999,
infer chronology/availability from the sequence, or promote these values into
globally unique archive identifiers. A later exact historical-convention
clarification can be recorded separately if needed; it does not block the CSV
format decision and does not authorize scientific evaluation.

## Remaining scientific gates and next task

ESA remains **AWAITING RESPONSE** under the exact `SP3AKIN_2_` product reference
in the [existing checklist](phase-11.3.1-scientific-clarification-request.md):
file version `0201`, processor `L2PS-DUT/44.88`. No new ticket number or processing
baseline is inferred. The CelesTrak findings resolve none of these independent
qualification issues:

- The **120-second** calendar versus GPS week/seconds conflict and **+37.12-ns**
  MJD discrepancy; no timestamp shift, rounding or arbitrary tolerance.
- Time qualification, including SP3-c/d, zero interval, GPS second-60 conventions
  and submicrosecond fields. The earlier 5,118 conversions remain conditional
  diagnostics; all 2,529 exclusions remain in place.
- KIN-specific VAL/EP quality acceptance, accepted reference epochs and uncertainty.
- Reference-frame/IGb08 alignment with a defined precision objective, applicable
  method/error budget and independent checks.
- Historical record selection, evaluation interval and temporal pairing, requiring
  a predeclared objective and qualified reference time/quality policy.
- Actual GP/reference observation and fitting lineage, independence assessment
  and independent prediction-accuracy validation.

Next task: reconcile the actual ESA reply, when received, against the preserved
0201 product, applicable specification and independent diagnostics. Record which
technical claims it supports before changing any gate. Define the comparison
objective and proposed temporal/quality rules for review; do not run genuine GP
propagation or ESA residuals while evaluation remains BLOCKED. Retain an explicit
retrospective interpretation if historical availability stays unknown.

## Change management and verification scope

Started on branch `phase-11.3.1-verified-publication`, HEAD
`baee19558f547f36fad8adea2f35a5f6b0c5232d`, with **42** preexisting unstaged
modified/untracked paths and an empty index. Those paths remain outside this
documentation update. Six documentation files constitute this update: this new
report, the provider inquiry tracker, scientific clarification checklist, CSV
intake guide, and additive checkpoints in the main Phase 11.3.1 and scientific
pairing reports. Earlier execution evidence and historical report bodies are
preserved. The publication report's pending-response statement remains its dated
historical checkpoint.

Verification for this documentation-only task checks relative links, Markdown
fences, factual consistency with captured inspection/public evidence, final diff,
source/report preservation and the database byte hash. Private-file metadata is
compared without rereading raw source attachments. Application tests, browser/PDF
checks, scientific calculations and builds are **not rerun**; earlier results
remain evidence for their recorded code states. No code or test guard changed.
Executed checks **PASS**: all 25 relative documentation links resolve; Markdown
fences are balanced; the captured header, three identifier/epoch rows, manifest
and inspection hashes agree with existing evidence; the six changed documents
contain no detected email addresses or private-key/GitHub-token patterns; and
`git diff --check` reports no whitespace errors. This pattern check is scoped
to these documents, not a general security certification.

All **311** other preexisting nonignored files remain byte-identical. Both report
addenda preserve the complete earlier bodies as exact byte prefixes. All **56**
private files retain identical size, timestamps, permissions and inode metadata;
raw attachment contents were not reread. The database byte hash remains
`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
Branch/HEAD, empty index and all 42 preexisting dirty paths are unchanged. Local
verification details are retained under `/tmp/orbitiq-provider-reconciliation/`;
they are task-local evidence, not an independent backup.

Nothing was staged, committed, pushed, published, merged or deployed. No remote CI
was initiated. Phase 8 production hosting/public HTTPS, independent off-machine
recovery, actual alert delivery and branch-protection verification remain separate
open milestones; this status update does not change them.
