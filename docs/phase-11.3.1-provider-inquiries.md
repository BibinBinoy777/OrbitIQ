# Phase 11.3.1 — provider clarification tracking

**Publication review — 26 October 2026:** the owner authorized publishing this
verified documentation on `publication/v1-verified-docs-2026-10-26`. Earlier
"local/unpublished" statements describe their dated verification checkpoints.
The publication commit and its remote CI must be verified separately; no new CI
success is asserted by this pre-publication snapshot. Scientific validation and
production readiness remain **NO-GO**; no deployment is authorized.

**Latest input-acquisition checkpoint: 26 October 2026.** See
[the additional fulfillment record](#additional-swarm-a-fulfillment-evidence--26-october-2026).
The 22 October clarification checkpoint below is retained as historical evidence;
the new data-request timestamp does not replace a clarification-submission clock.

Current checkpoint: **22 October 2026**, scoped CelesTrak follow-up closure.
The user supplied pasted CelesTrak reply text and authorized using the available
information to close that follow-up for the current retrospective study. The text
was reviewed, but authenticated delivery headers and full dated/time-zoned reply
timestamps are unavailable. These are **user-supplied provider replies**, not
independently authenticated correspondence. ESA's supplied acknowledgement says
technical answers will follow; substantive clarification remains pending. This
update sends no messages and does not assert that either provider closed a ticket.

| Provider | Technical subject | Submission | Submission date/time | Response | Outstanding questions |
| --- | --- | --- | --- | --- | --- |
| ESA / Swarm product support, reference `RITM0144536` (user-supplied) | Swarm-A `SP3AKIN_2_`, file version `0201`, processor `L2PS-DUT/44.88`; reference time, quality and realization semantics | SUBMITTED — user reports the email was sent | Unknown; not supplied | ACKNOWLEDGEMENT RECEIVED — user-supplied text; SUBSTANTIVE CLARIFICATION PENDING | 120-s calendar/week-seconds conflict; +37.12-ns MJD difference; SP3-c/d, zero interval, second-60 and fractional-time conventions; KIN-specific VAL/EP acceptance and uncertainty; IGb08 processing/alignment lineage |
| CelesTrak | Historical Swarm-A GP records, NORAD 39452 / 2013-067B; format, availability and record interpretation | SUBMITTED — user-reported | Unknown; not supplied | CLOSED FOR CURRENT RETROSPECTIVE SCOPE — available clarification reviewed; limitations retained | Reply supplies no JSON fix or promised date; use supported CSV. Creation timestamps unavailable; historical availability, complete fitting lineage and independence unestablished. Historical `ELEMENT_SET_NO` semantics remain uncertain; no further CelesTrak response is a prerequisite for this scope |

The user's general submission statement does not establish the exact wording of
either email or that every checklist question was included. The
[technical checklist](phase-11.3.1-scientific-clarification-request.md) records the
open subjects, not a transcript of sent correspondence. The earlier historical
data-request timestamp must not be reused as the clarification-submission time.
Receipt of the CSV is separate from receiving a clarification response.

The [response reconciliation](phase-11.3.1-provider-response-reconciliation.md)
records the supported findings and identifier review. CSV is the supported format
path for this investigation; corrected JSON is no longer a prerequisite. This
does not resolve source authentication, historical availability, fitting lineage
or any ESA-dependent gate. The [scoped closure decision](phase-11.3.1-provider-response-reconciliation.md#celestrak-follow-up-closure-for-the-current-retrospective-scope)
closes the local follow-up, not those scientific unknowns or the upstream JSON
defect. Phase 11.3.1 remains **PARTIAL**, scientific
pairing/evaluation **BLOCKED**.

Keep ESA tracked under `RITM0144536`, supplied by the user in the comparison
protocol request, and the existing exact product reference in the
[technical checklist](phase-11.3.1-scientific-clarification-request.md). A tracking
reference or acknowledgement does not resolve technical issues. The supplied
acknowledgement text provides no technical answer; its displayed date/time has no
verified timezone and is not recorded as a UTC receipt timestamp.
Assess any eventual technical reply
against the preserved product, applicable specification and independent checks
before changing a gate. Original correspondence, if later supplied, belongs in
private storage. No personal contact details, email bodies, credentials or
unrelated mail metadata belong here. The 21 October publication report retains
its historical pending-response checkpoint.

The [comparison protocol](phase-11.3.1-comparison-protocol.md) and
[frame investigation](phase-11.3.1-frame-alignment-investigation.md) predeclare the
proposed study and record independently checked arithmetic. They do not close
ESA's time, KIN-quality or alignment gates and do not authorize real evaluation.

## Additional SWARM-A fulfillment evidence — 26 October 2026

**Owner-supplied fulfillment metadata**, separate from the clarification-submission
and receipt clocks above: CelesTrak (notice contact Dr. T. S. Kelso) reports fulfillment
of the historical GP **JSON** request dated **`2026-10-25T06:25:38Z`**, for SWARM A /
NORAD **39452** / COSPAR **2013-067B**. Requested coverage and the reported actual
period are both **2013-12-30 through 2014-01-02**, with **three element sets**.
The owner supplied this notice metadata on **2026-10-26**; no exact provider-email
receipt time or authenticated transport headers are available here. This is not
a replacement timestamp for any earlier request or clarification correspondence.

The [file-specific formatting/fulfillment record](phase-11.3.1-provider-response-reconciliation.md#swarm-a-json-fulfillment-and-inspected-file--26-october-2026)
records the actual owner-uploaded `sat000039452 (1).json`: **1,236 bytes**, computed
SHA-256 `8720c8db31451a121b0b3f2333063165d0cc6dea1c71edec187dbcdd3ac34fb5`.
Strict JSON and the named numeric-format checks passed; the three records' **51**
values match the existing selected CSV. These are direct uploaded-file checks,
not proof that the notice authenticates those exact bytes or that the provider's
entire JSON service has been verified. Original malformed JSON and CSV remain intact.

Classification is **provider-formatting/input-acquisition evidence**, not approval
of a scientific comparison input. The selected CSV and existing retrospective
follow-up disposition stay unchanged. Phase 11.3.1 is **PARTIAL** and scientific
evaluation **BLOCKED — NO-GO**. ESA time/KIN-quality/IGb08 questions and independent
IGS frame/EOP clarification remain pending. No G05/G30 substitution, policy or
candidate change, scientific calculation, publication or deployment is authorized
or performed by this update. No unnecessary personal request metadata is retained.
