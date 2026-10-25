# E8.7.3 — OMM header semantics and retrospective intake proposal

Study `ORBITIQ-IGS-GPS-RETRO-001`, 25 October 2026. **Scientific study BLOCKED.**
Outcome: **CONDITIONAL_RETROSPECTIVE_ADMISSION**, a narrowly scoped **proposal,
not activated**. Six records meet the proposed conditional-review rules, two
remain held for same-epoch conflict and two fail the unchanged temporal window.
Actual admissions: **0**. The unchanged strict inspector still reports **0 static
candidates**. No GP record is scientifically qualified or selected.

The original XML **passes its declared official schema**, including all ten
individual OMM messages. This finding is separate from complete message semantics,
OrbitIQ's stricter populated-header policy and scientific qualification.
The [evidence ledger](engineering-e8.7.3-header-semantics-evidence.json) records
raw representations, precise source locations, schema identities, every-record
proposed decisions, source limitations and actual checks.

## Original bytes and exact representation

The original `sat000035752.xml` remains **10072 bytes**, SHA-256
`c398ecdc707013d0c9bf245b9eeb1894aef1f2a7bafd60f9a687ce797e0a0828`.
The supplied original and its private E8.7.2 capture are byte-identical. Original
path, capture provenance and unknown email receipt time are retained in
[E8.7.2](engineering-e8.7.2-g05-xml-intake.md). No rewrite, repair or conversion.

All ten raw headers contain exactly:

```xml
<CREATION_DATE/>
<ORIGINATOR/>
```

Both elements are **present but empty** in each message. They have no attributes:
there is no `xsi:nil="true"`, no literal `null`, no populated invalid value and
no absent element. The ledger records all twenty exact field representations
and original byte offsets. An XML parser returning `None` for empty text, or a
JSON representation displaying `null`, does not turn this into formal XML nil.

The actual root declares this schema hint:

`https://sanaregistry.org/r/ndmxml_unqualified/ndmxml-2.0.0-master-2.0.xsd`.

The hint was inspected as data. It was not automatically fetched by an XML parser.
The known official SANA URI and each dependency were acquired explicitly and
hash-pinned before offline validation. No private input was uploaded to a validator.

## Applicable schemas and prose standards

**Direct source/schema evidence:** the actual SANA unqualified **NDM/XML 2.0.0**
master, revision 0, and eleven dependency files were acquired successfully.
The master comments name compatibility with ODM **502.0-B-2 (November 2009)**
and the NDM/XML **505.0-P-1.0.3 (2020)** schema lineage. The OMM schema fixes
`id="CCSDS_OMM_VERS"`, `version="2.0"`, and uses the common `ndmHeader` type.
These are the exact deployed files named by this input, not a substituted 3.0 schema.

The [official common schema](https://sanaregistry.org/r/ndmxml_unqualified/ndmxml-2.0.0-common-2.0.xsd)
defines the following at lines 203–210:

| Field         | Required presence                | Type / content rule                                                              | Actual result                      |
| ------------- | -------------------------------- | -------------------------------------------------------------------------------- | ---------------------------------- |
| CREATION_DATE | Required; default minOccurs is 1 | `ndm:epochType`; its regex at lines 683–688 permits an empty numeric alternative | Present-empty accepted by this XSD |
| ORIGINATOR    | Required; default minOccurs is 1 | `xsd:string`, no nonempty restriction in this declaration                        | Present-empty accepted by this XSD |

Neither declaration is nillable. Absent elements and formal nil are different
cases; synthetic controls confirm that omission and `xsi:nil="true"` fail under
this exact schema. Empty self-closing and explicit empty start/end tags pass.
Do not replace the actual tags with nil to “repair” them. A synthetic impossible
calendar date shaped like a timestamp also passes this schema's string pattern:
XSD success does **not** replace exact calendar validation or provenance review.

**Published prose, with version limits:** the current official
[CCSDS 502.0-B-3](https://public.ccsds.org/Pubs/502x0b3e1.pdf), April 2023 with
editorial change 1 (May 2023), was retrieved and read. Section 4.2.2/Table 4-1,
printed pages 4-2/4-3, marks both headers mandatory. It defines CREATION_DATE as
file creation date/time in UTC and ORIGINATOR as creating agency/operator.
Sections 7.5.10–11 specify absolute-time form and UTC for creation time.
This is current **OMM 3.0 prose**, useful semantic context, not authority to
silently validate an OMM 2.0 file as 3.0.

The current official
[CCSDS 505.0-B-3](https://public.ccsds.org/Pubs/505x0b3e2.pdf), May 2023 with
EC1 (February 2024) and EC2 (October 2024), was also read. Section 3.1.3 and
Annex G1 identify SANA's unqualified/qualified schema repositories; section 3.1.4
explains versioned schema naming. It does not justify silently substituting the
current schema generation for the input's declared older generation.

**Access limitation:** four candidate official URLs for older 502.0-B-2 prose
returned 404; they were not treated as documents read. The exact OMM 2.0 schema's
required presence/content rules were verified directly. Full older-prose semantic
conformance is not certified from a newer prose table. The SANA index initially
timed out; the exact master and all dependencies subsequently returned 200.
All outcomes, including failures, are preserved in the evidence receipts.

**Meaning and limits:** even a valid message-creation timestamp would not by itself
establish the orbital-element fit time, observation times, archive insertion,
public availability or whether a forecast was possible historically. A populated
message originator would not alone prove the complete element producer/sensor/fit
chain. Here neither value is known. **Exact XSD conformance: PASS. Complete
semantic/provenance qualification: PARTIAL, not established.**

## What official CelesTrak documentation establishes

The current official
[GP format documentation](https://celestrak.org/NORAD/documentation/gp-data-formats.php)
was freshly retrieved, HTTP 200; it displays **Updated 2026 Jun 23**.
The retained HTML line 128 recommends OMM XML 2.0 and links current CCSDS prose.
Line 130 says mandatory elements are supplied and some unavailable TLE fields
may be blank in KVN or “null” in XML; its explicit examples are OBJECT_NAME and
OBJECT_ID for certain analyst objects. Line 134 separately describes omission
of null/blank/redundant mandatory fields from **JSON/CSV**, including invariant
metadata examples.

The page does **not explicitly name CREATION_DATE or ORIGINATOR in that
unavailable-field explanation**, define “null” as `xsi:nil`, or explain these
historical G05 header contents. Do not extend JSON/CSV omission rules to XML
headers, relabel mandatory headers as optional or claim a specific historical
export convention from this generic paragraph. The observed present-empty
representation passes the exact official schema; that is stronger evidence of
schema acceptability than the provider's informal use of “null”. It still does
not supply the missing header meanings.

The preserved [earlier provider reconciliation](phase-11.3.1-provider-response-reconciliation.md)
records **user-reported** CelesTrak clarification that record-creation timestamps
are not retained, and cautions against equating Space-Track CREATION_DATE with
orbit-solution generation. That report concerned the earlier Swarm-A inquiry;
it is neither independently authenticated correspondence nor a G05-specific
explanation of this XML serializer. It supports keeping unknowns explicit and
avoiding repeated demands for timestamps a provider may not retain. No new
provider message, account access or authentication was attempted here.

## Three separate decisions

| Question                                         | Finding                                                                             | Limit                                                                                                         |
| ------------------------------------------------ | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| A. Safe parsing and required GP-field validation | PASS: ten supported messages, consistent target identity, numeric fields and epochs | The strict header policy still rejects candidate status                                                       |
| B. Retrospective candidate admission             | PARTIAL: conditional exception is defensible as the versioned proposal below        | Claimed-source review only; not activated, provenance PARTIAL                                                 |
| C. Scientific qualification for comparison       | BLOCKED                                                                             | Frame/EOP, physical point, quality/uncertainty, source dependencies, protocol review and authorization remain |

The acquisition packet contains byte-preserved original/hash/capture, matching
NORAD/COSPAR, required orbital fields and exact epochs, and **user-reported**
CelesTrak request/fulfillment/count evidence. That is sufficient to propose
review of a claimed-source retrospective candidate. It is not independent sender
authentication, an authenticated record-level originator or full fitting lineage.
Exact email receipt remains unknown; the fulfillment summary is not a creation
time or a substitute for original message headers.

## Versioned policy proposal and explicit rules

Policy **`ORBITIQ-RETRO-INTAKE-G05-1.0-PROPOSED`**.
Outcome **CONDITIONAL_RETROSPECTIVE_ADMISSION**. Status **PROPOSED, NOT ACTIVATED**.
This is a separate admission/provenance proposal in this document. It changes
neither the [original G30 protocol](engineering-e8-comparison-protocol.md) nor
the historical [G05 proposal](engineering-e8.7.1-g05-protocol-proposal.md).
It is motivated by raw representation/schema/provenance evidence, not expected
or calculated orbital results. It does not alter any algorithm or selection guard.

Scope is **only this exact hash-pinned 10-record G05 export** and the frozen
January-1 reference. Another attachment, satellite, schema version or provider
requires separate review. This is not a class-wide assertion that CelesTrak's
headers are optional. No command-line waiver or application behavior is added.

Apply these ordered rules to each original source record:

1. **Integrity/source packet:** require the original hash, complete response,
   exclusive private capture/manifest and explicit claimed CelesTrak request/
   fulfillment evidence. Missing integrity or source linkage gives
   **INSUFFICIENT_EVIDENCE**. Source sufficiency here permits further examination
   of claimed-source data only, not authentication or scientific endorsement.
2. **Supported profile and identity:** require safe structure/locked parsing,
   exact pinned-schema validation, numeric NORAD 35752, COSPAR 2009-043A and
   consistent dated G05/G050 identity. Required GP numbers, UTC epoch precision,
   Earth/TEME/UTC/SGP4 declarations and existing model checks must pass. Failure
   gives **STRICT_REJECTION** for this proposed admission, retaining the record.
3. **Narrow content exception:** waive only the strict nonempty CREATION_DATE/
   ORIGINATOR checks when both are present-empty without nil attributes, as in
   this exact export. Do not waive absent/unsupported structures, malformed
   populated timestamps, other missing fields, invalid numbers or source changes.
   Any such difference requires separate review, not this exception.
4. **Temporal rule unchanged:** calendar request and exact inclusive window
   `[2023-12-25T23:44:42Z, 2023-12-31T23:59:42Z]`, forward-only from the fixed
   first reference epoch, seven-day guard at **all 96 original epochs**. Failure
   gives **STRICT_REJECTION** for the proposed comparison window. No partial
   grid, nearest-record substitution, interpolation or rounding.
5. **Ambiguity hold:** preserve every duplicate/conflict and source index. For
   this conservative admission proposal, a temporally passing member of an
   unresolved same-epoch pair is held as **INSUFFICIENT_EVIDENCE**, rather than
   independently advanced. Do not merge, discard, prefer a revolution count,
   fall back following latest-epoch ambiguity or use residual size. This
   additional intake hold does not rewrite the existing single-latest selection rule.
6. **Conditional review only:** a record passing rules 1–5 may be recommended for
   **CONDITIONAL_RETROSPECTIVE_ADMISSION** with provenance **PARTIAL**, missing
   creation/originator/publication/receipt and full lineage flagged explicitly.
   Do not backfill the XML, infer timestamps or relabel it strictly qualified.
   Activation/implementation requires a separately reviewed policy change.
7. **Scientific boundary unchanged:** even after future activation, admission
   permits only further qualification. Keep full frame/EOP, physical-point,
   quality/uncertainty, dependency and protocol-review gates. The predeclared
   latest-unique rule can be applied only after required qualifications, with
   separate scientific authorization before any computation.

No complete-provenance, historical-forecasting, independent-accuracy, statistical
independence, absolute-truth, anomaly, collision or operational-safety claims.
Any eventual authorized comparison would be bounded retrospective disagreement
between estimated products, with unresolved dependencies explicitly stated.

## Application of proposed rules, not a changed strict result

Every row retains the original record and exact epoch. Integrity, claimed-source
packet, profile, numeric identity/GP fields and the narrow empty-header form pass
the proposal's document-only assessment for all ten. The unchanged temporal and
explicit conflict rules produce:

| Original record / zero-based index | Temporal rule | Same-epoch issue | Proposed outcome                    |
| ---------------------------------- | ------------- | ---------------- | ----------------------------------- |
| 1 / 0                              | FAIL          | Pair [0,1]       | STRICT_REJECTION for this window    |
| 2 / 1                              | FAIL          | Pair [0,1]       | STRICT_REJECTION for this window    |
| 3 / 2                              | PASS          | None             | CONDITIONAL_RETROSPECTIVE_ADMISSION |
| 4 / 3                              | PASS          | Pair [3,4]       | INSUFFICIENT_EVIDENCE, held         |
| 5 / 4                              | PASS          | Pair [3,4]       | INSUFFICIENT_EVIDENCE, held         |
| 6 / 5                              | PASS          | None             | CONDITIONAL_RETROSPECTIVE_ADMISSION |
| 7 / 6                              | PASS          | None             | CONDITIONAL_RETROSPECTIVE_ADMISSION |
| 8 / 7                              | PASS          | None             | CONDITIONAL_RETROSPECTIVE_ADMISSION |
| 9 / 8                              | PASS          | None             | CONDITIONAL_RETROSPECTIVE_ADMISSION |
| 10 / 9                             | PASS          | None             | CONDITIONAL_RETROSPECTIVE_ADMISSION |

Thus **six conditional recommendations, two holds, two temporal rejections**.
These are results of applying the documented proposal, not newly activated
eligibility. No latest record is nominated. **Actual admissions 0; strict static
candidates 0; selected source index null; scientific accepted count 0.**
E8.7.2 remains an accurate historical result under its unchanged strict policy;
no earlier report is rewritten to imply these records were already eligible.

## Same-epoch differences and evidence needed

Original pairs **[0,1]** and **[3,4]** have matching epochs and differ only in
`REV_AT_EPOCH` in their parsed GP fields. Exact values and source-field hashes
are retained in a new private comparison record, without publishing numerical
GP sets. Current CCSDS Table 4-3 calls the field **Revolution Number**; it is not
a revision ordering or scientific-quality rank. The XML, fulfillment count and
generic unavailable-field guidance do not explain the differing values. The
schema permits both records but does not resolve the conflict.

Cause and affected admission decisions remain unresolved. No rollover,
serializer fault, replacement chronology or model equivalence is inferred.
If required, a targeted explanation linked to the exact original hash/pair could
clarify multiplicity. Do not assume one member is preferable. Six distinct,
unaffected recommendations do not depend on resolving the older pairs or imply
that the paired records have been discarded.

Provenance could be strengthened by authenticated delivery/hash linkage, reliable
receipt metadata, provider clarification of missing-header semantics, and any
retained record publication/fit/source lineage. Evidence that was never retained
may remain unknown. Even populated message fields would not establish full
lineage or independence. Preserve limited claims and reopen review if the goal
changes to historical forecasting or evidence contradicts this packet.

## Verification, preservation and remaining work

- Original complete XML and **10 individual OMMs pass** the exact **12-file** SANA
  schema set. Validation used **lxml 6.0.2 / libxml2 2.14.6**, no network/entity
  resolution during validation and a resolver accepting only pinned dependencies.
  The temporary validator was installed under `/tmp`, without changing the
  project environment, dependency declarations or lockfiles.
- **12 synthetic schema controls passed**, covering empty/present/absent/nil,
  ordering, duplication and the calendar-pattern limitation; they use a test
  wrapper importing the unchanged official header type. One initial expectation
  concerning `xsi:nil="false"` was corrected after the pinned validator explicitly
  rejected a nil attribute on a non-nillable element. No application/schema rule
  was weakened. **9 synthetic proposal-rule controls passed**. These controls
  are not acquired scientific evidence or an operational policy adapter.
- **83 existing synthetic XML tests passed in 11.02 seconds**, including G30/G05
  regressions. Strict header failures remain expected. Relevant lint/format,
  Markdown/JSON formatting, source/schema/evidence/decision consistency, local
  links, privacy/whitespace and complete two-file diff checks passed. Full
  application/frontend/browser/PDF/build/remote CI checks were **not run**.
- Only this report and `engineering-e8.7.3-header-semantics-evidence.json` are new
  repository files. New official-document/schema receipts, private validation/
  conflict evidence and harnesses are ignored and hash-manifested. Original
  XML/SP3, all prior protocols/reports/inputs, source, locks and four worktree
  branches/HEADs remain unchanged. Read-only DB checks preserve schema 3,
  two snapshots and SHA-256
  `ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
  Local preservation is not independent backup/recovery. No publication occurred.

Remaining work is a separately reviewed decision on activating this bounded
intake proposal, continued provenance/claims review and the still-open scientific
frame/EOP, historical physical-point, G05 quality/uncertainty and source-dependency
qualifications. No new correction model or comparison is implemented.

**Study BLOCKED. No real GP propagation, spacecraft-state transformation, orbital
interpolation/extrapolation, residual or new uncertainty calculation.** Swarm-A
Phase 11.3.1 remains **PARTIAL**, scientific evaluation **BLOCKED**; E4 **OPEN**.
