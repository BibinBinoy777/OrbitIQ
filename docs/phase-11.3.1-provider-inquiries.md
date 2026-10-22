# Phase 11.3.1 — provider clarification tracking

Current checkpoint: **22 October 2026**, provider response reconciliation.
The user reports that CelesTrak has answered the formatting and GP provenance
inquiries; ESA's separate reply remains pending. The supplied task summarizes
the response, without original correspondence, reply timestamps or authenticated
delivery headers. Record the findings as **user-reported provider clarification**,
not independently authenticated correspondence. This task sent no messages.

| Provider | Technical subject | Submission | Submission date/time | Response | Outstanding questions |
| --- | --- | --- | --- | --- | --- |
| ESA / Swarm product support | Swarm-A `SP3AKIN_2_`, file version `0201`, processor `L2PS-DUT/44.88`; reference time, quality and realization semantics | SUBMITTED — user reports the email was sent | Unknown; not supplied | AWAITING RESPONSE — no reply supplied | 120-s calendar/week-seconds conflict; +37.12-ns MJD difference; SP3-c/d, zero interval, second-60 and fractional-time conventions; KIN-specific VAL/EP acceptance and uncertainty; IGb08 processing/alignment lineage |
| CelesTrak | Historical Swarm-A GP records, NORAD 39452 / 2013-067B; format, availability and record interpretation | SUBMITTED — user-reported | Unknown; not supplied | RESPONSE RECEIVED — user-reported summary; reply date/time unknown | CSV supported/preferred; no promised JSON-fix timeline; creation timestamps not retained. Historical availability and complete fitting lineage remain unestablished; historical `ELEMENT_SET_NO` interpretation remains uncertain |

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
or any ESA-dependent gate. Phase 11.3.1 remains **PARTIAL**, scientific
pairing/evaluation **BLOCKED**.

Keep ESA tracked under the existing exact product reference in the
[technical checklist](phase-11.3.1-scientific-clarification-request.md); no ESA
ticket/case number was supplied, so none is invented. Assess any eventual reply
against the preserved product, applicable specification and independent checks
before changing a gate. Original correspondence, if later supplied, belongs in
private storage. No personal contact details, email bodies, credentials or
unrelated mail metadata belong here. The 21 October publication report retains
its historical pending-response checkpoint.
