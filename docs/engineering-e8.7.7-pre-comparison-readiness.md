# E8.7.7 — Pre-comparison readiness decision

**G05 and G30 remain BLOCKED for scientific comparison.** Neither has a
scientifically qualified or selected record, and no comparison is authorized.

**Next action:** resolve E8.3's two specific frame/EOP questions: the justified
computed-ITRS-to-IGS20 realization treatment and the applicable 2024 IGS
ERP/subdaily convention treatment. Reuse its existing inventory. Closure requires
an independently supported compatibility disposition; if retained sources cannot
establish a product-era convention, obtain that specific IGS/analysis-centre
evidence. Do not repeat intake or start real spacecraft calculations.

Prioritize **G30's qualification review** for continuity with its original
protocol and deeper E8.2–E8.6 target-specific audit. A shorter **fully qualified
scientific path has not been established** for either case. Admission counts and
G05's older held records do not establish scientific superiority or readiness.

The [machine-readable matrix](engineering-e8.7.7-candidate-readiness-matrix.json)
retains all **15 admitted records' identifiers, exact source epochs, policy
version, PARTIAL provenance and 12 record-scoped gate statuses**. It also records
sources, affected scope, minimum closure evidence and ordered next actions.

## Current admission and readiness

| Case        | Admitted for further qualification | HOLD | Rejected | Qualified / selected / authorized |
| ----------- | ---------------------------------- | ---- | -------- | --------------------------------- |
| G05 / 35752 | 6                                  | 2    | 2        | 0 / none / no                     |
| G30 / 39533 | 9                                  | 0    | 2        | 0 / none / no                     |

Both original hashes/sizes and captures were reverified. Active policy,
activation record and inspector fingerprints match [E8.7.6](engineering-e8.7.6-retrospective-admission-evidence.json).
Strict remains the default; no admission replay or policy change was needed.
PASS below is restricted to the stated scope, not whole-case qualification.

| Gate                                          | G05                   | G30                      | Precise remaining requirement / evidence                                                                                                                              |
| --------------------------------------------- | --------------------- | ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| G01 File integrity and acquisition provenance | PARTIAL               | PARTIAL                  | Integrity passes; source attribution is user-reported, receipt/full delivery lineage incomplete. Review limits for the intended claim.                                |
| G02 Identity and element integrity            | PASS                  | PASS                     | Correct NORAD/COSPAR, dated mapping and supported fields; not physical accuracy or fit lineage. E8.7.2/E8.7.5/E8.7.6.                                                 |
| G03 Active static admission                   | PASS                  | PASS                     | Exact hash-scoped v1 admits the listed records. Headers stay PARTIAL; strict rejections remain recorded.                                                              |
| G04 Temporal eligibility                      | PASS                  | PASS                     | Every admitted record passes forward-only/seven-day guard at all 96 original instants, without rounding/subsetting.                                                   |
| G05 Frame/datum compatibility                 | BLOCKED               | BLOCKED                  | IGS20 metadata and Astropy ITRS naming do not establish realized-coordinate compatibility. E8.2/E8.3.                                                                 |
| G06 Time/EOP compatibility                    | BLOCKED               | BLOCKED                  | UTC/GPS mapping and resource coverage supported; product-era ERP/regularization/subdaily-model consistency unresolved. E8.3.                                          |
| G07 Spacecraft physical point                 | BLOCKED               | BLOCKED                  | General CoM/current ANTEX is not exact 2024 processing or GP fitted-point proof; G050 IIR-M and G064 IIF need separate assessment.                                    |
| G08 Quality/uncertainty                       | PARTIAL               | PARTIAL                  | Own quality fields inspected; reference-quality/claims acceptance and calibrated joint uncertainty unestablished. G30 statistic relationship still partly unresolved. |
| G09 Creation/fitting provenance               | PARTIAL               | PARTIAL                  | Creation/publication/full fit history unknown. Review bounded retrospective limits; do not reconstruct unavailable timestamps.                                        |
| G10 Dependencies/independence                 | PARTIAL               | PARTIAL                  | Known source/model links and unknown overlap documented; no independent-accuracy or zero-covariance assumption. E8.5.                                                 |
| G11 Duplicate/conflict resolution             | PARTIAL at case level | PASS within intake scope | G05 pairs preserved, but its six admitted records individually pass known-conflict checks. G30 exact epochs distinct.                                                 |
| G12 Protocol/authorization                    | BLOCKED               | BLOCKED                  | No qualified selected record, independently reviewed final run packet or explicit scientific authorization.                                                           |

## Candidate-specific consequences

G05 pair **[0,1]** remains REJECTED by time; in-window pair **[3,4]** remains
HOLD. Admitted indices **[2,5,6,7,8,9]** are unaffected by these known conflicts.
The [G05 protocol](engineering-e8.7.1-g05-protocol-proposal.md) blocks ambiguity
at a proposed selection epoch, not every record because an older unselected pair
conflicts. No merge, preference or release occurs. A provider response revealing
a broader export/lineage problem could reopen the whole artifact assessment.

G30's lack of exact conflicts does not resolve physical conventions, history or
quality. Its [E8.6 statistic question](engineering-e8.6-g30-statistic-reconciliation.md)
remains open; G05's own indicator question is assessed separately. The
[original G30 protocol](engineering-e8-comparison-protocol.md) and G05 proposal
stay unchanged. No latest admitted epoch is nominated or selected here.

## Minimum clearance work, ordered by dependency

1. **Frame/time/EOP — start now.** Existing source/docs support the convention
   crosswalk and identification of missing facts. Close E8.3's realization and
   product-era ERP/subdaily questions with authoritative evidence and independent
   support. No blind station Helmert, assumed-zero correction or double addition.
2. **Common spacecraft point — parallel evidence work.** Reuse general CoM and
   satellite-specific metadata, then establish applicable historical processing,
   attitude/calibration and GP point interpretation, or independently justify a
   treatment. Current ANTEX validity dates alone do not close this gate.
3. **Quality and bounded claims — draft locally, finalize after physical gates.**
   Review target-specific flags/mask and retained provenance/dependency unknowns.
   A future approved unweighted product-disagreement scope could leave uncertainty
   unquantified and exclude unresolved indicators from weighting/bounds/thresholds.
   That acceptance is **not made here**. Numerical indicator use needs producer
   mapping/calibration evidence; G30's discrepancy remains unresolved.
4. **CelesTrak clarification — useful parallel, record-scoped evidence.** Reuse
   the [existing draft](engineering-e8.7.4-provider-clarification-draft.md) for
   header/source and G05-pair interpretation. Repository evidence says UNSENT and
   contains no reply; external dispatch is unestablished. Do not expect a response
   to recover unretained timestamps or resolve IGS frame/ERP/statistic questions.
   It is not a universal prerequisite for unaffected admitted records under v1.
5. **Final selection/run packet — waits for essential clearances.** After
   qualification apply the unchanged latest-unique/single-record rule, freeze the
   final packet, obtain independent review and explicit scientific authorization.
   Packet fields can be prepared now; no record can be chosen here.
6. **Independent observations/reference data — claim-dependent.** These are
   needed for independent-accuracy/truth claims, or a specific requirement from
   scientific review, not automatically for restricted retrospective comparison
   of estimated products. Matching identity/time/frame/point/uncertainty and
   demonstrated source independence are necessary; another provider name is not
   proof. No additional GP/reference data are acquired here.

Missing creation/full lineage or independence must remain explicit. Independent
scientific review must decide whether those unknowns are acceptable for a
specific restricted retrospective claim; intake authorization is not that review.
Do not invent timestamps/covariance or waive essential physical gates to close a
checklist. No numerical ranking score is assigned.

## Authorization conditions — not satisfied

Before the first real comparison: verify immutable input/policy bindings and the
full original temporal grid; independently qualify case-specific frame/EOP and
physical-point compatibility; approve reference quality/mask and bounded
uncertainty/provenance/dependency claims; then apply the original selection rule
to scientifically qualified, conflict-free eligible records. Freeze raw/derived
hashes, reference/indices/grid/units, frame/point/EOP treatment, software/locks,
resources, exclusions and claims in an independently reviewed packet. Obtain
explicit user scientific authorization naming that exact packet and scope before
propagation, transformation or comparison. No fallback or residual-driven choice.

The matrix records these conditions separately: scientific qualified count **0**,
selected index **null**, authorization **false**, gate **BLOCKED**. No automatic
execution trigger exists. G05 conflict clearance remains specific to affected
records and can require separately reviewed policy/protocol action.

## Verification and preservation

Only this report and `engineering-e8.7.7-candidate-readiness-matrix.json` are new.
Evidence/source/policy consistency, both original/captured hashes, all 15 admitted
identifiers/epochs, 24 candidate gates, 180 record-scoped statuses, conflict scope,
authorization conditions, source locators/manifests, formatting, links, privacy,
whitespace and the complete two-file diff passed review. No code changed.

No application/browser/PDF/build/CI or numerical scientific tests were rerun;
the E8.7.6 160-test result is historical evidence, not fresh E8.7.7 validation.
No schema/admission/EOP replay was needed. Original XML/SP3, database, policy and
activation, protocols, prior reports, branches/HEADs and private inputs remain
unchanged. Read-only DB verification retains schema 3, two snapshots and SHA-256
`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
No publication, deployment, account access or message sending occurred.

**Study BLOCKED. No real propagation, spacecraft transformation, orbital
interpolation, residual or new uncertainty calculation.** Swarm-A Phase 11.3.1
remains **PARTIAL**, scientific evaluation **BLOCKED**; E4 production readiness **OPEN**.
