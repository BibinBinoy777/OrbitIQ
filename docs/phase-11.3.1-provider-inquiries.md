# Phase 11.3.1 — provider clarification tracking

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
