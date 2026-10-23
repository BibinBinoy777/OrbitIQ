# E5 prioritized remaining roadmap

Assessment: **23 October 2026 (IST)**. This is a bounded roadmap derived from the
[implementation audit](engineering-e5-product-audit.md), not authorization to
implement or deploy every item. E5 completion means the audit/acceptance milestone
is complete; the long-term OrbitIQ product remains under development. No arbitrary
number of future phases can prove product or production completion.

## Fixed defect and current acceptance

E5 fixes demonstrated TEME response/request time mismatch, including sub-millisecond
values, with failing-before/passing-after regressions. Cross-workflow restart,
new-input and separate restore tests protect existing exact-source investigations.
The [report](engineering-e5-report.md) records actual verification and any failures.
No additional reproducible application defect was established in this audit's
bounded journeys. That does not imply the absence of defects or complete coverage.

## Priority 0: preserve blocked release and scientific gates

| Work / owner dependency                                                                          | Minimum completion evidence                                                                                                                                                                                   | Work possible before ESA replies                                                                                                             |
| ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| ESA time, KIN quality and realization alignment; provider clarification plus scientific reviewer | Resolve the documented conflicts with version-specific references, accepted epoch/quality rules, precision objective/error budget and independent frame/time checks before authorizing any genuine comparison | Maintain protocol/diagnostics; do not reinterpret timestamps, qualify a product from acknowledgement, or calculate genuine Swarm-A residuals |
| Historical availability, fitting lineage and independence; provider/evidence constraints         | Keep unknowns/limits explicit; narrow any future retrospective claim accordingly. Closed CelesTrak follow-up with limitations does not establish missing creation clocks or independent forecasting evidence  | Continue clearly labelled numerical/reference and software tests; no historical forecast or independent-accuracy claim                       |
| E4 A: hosting, trusted HTTPS, persistent runtime; owner-approved target                          | Real authorized staging host/URL, durable storage/identity, certificate/renewal and actual replacement/restart evidence                                                                                       | Container/configuration/release rehearsals only; no public deployment, paid provisioning or DNS                                              |
| E4 B: independent backup/recovery; approved destination and key recovery                         | Owner-approved failure domain/retention/RPO/RTO, least-privilege access, actual upload/retrieval/new-target restore and schema/payload/audit/API proof                                                        | Local non-destructive fixture recovery; never upload private archives to an unapproved destination                                           |
| E4 C: monitoring and alert delivery; receiver and running monitor                                | Approved destination/schedule/operator and actual failure/recovery delivery receipt                                                                                                                           | Local fake receiver and operator runbook tests                                                                                               |
| E4 E: branch protection/required checks; owner plan and administrative access                    | Readable authoritative settings for default branch, required exact job names and evidence that bypass/merge behavior matches policy                                                                           | Keep engineering publication separate from merge; passing CI is not branch protection                                                        |

E4 D bounded CI artifact retention already has actual upload/download/digest/expiry
metadata evidence. Maintain its 7/90-day policy and manual selected-image archive;
it is not independent database backup, permanent archival or production approval.
No E4 or historical report is overwritten by this roadmap.

## Priority 1: focused local product milestones

1. **Stored catalog onboarding and operator collection usability.** The default
   explorer requires a NORAD ID, discovery returns bounded stored records rather
   than a deduplicated global satellite catalog, and ingestion is one object per
   explicit operator command. Agree which public objects/retention are intended,
   then add an honest stored-coverage overview and actionable empty-state/operator
   guidance. Preserve fixed-source selection, insertion versus retrieval clocks,
   consent/redistribution and provider cooldown. Verify empty/single/multiple
   histories and offline/failure journeys. A scheduler/bulk collector is a separate
   requirement; never infer it from a collection command.
2. **Portable local investigations and recovery.** Browser-local saves work and
   have limits/conflict protection, but there is no application export/import of
   the saved list, titles and notes. Report JSON deliberately excludes those
   fields; share links are not backups. Define a bounded versioned local backup
   format, explicit user download/import/duplicate policy and preview without
   silent overwrite. Test corrupt/versioned/oversized imports, conflict handling,
   privacy and original preservation before claiming portable recovery. No cloud
   account or backend schema is necessary for that focused milestone.
3. **Contract drift protection.** Discovery/comparison/history/observation routes
   use manually maintained response envelopes and frontend validators. Audit
   stable wire schemas against OpenAPI; add targeted cross-boundary contract cases
   or generate shared types only where it reduces demonstrated drift. Preserve
   existing API compatibility, integer bounds, exact six-digit times and explicit
   partial/unknown/error states. Avoid a broad stylistic rewrite.
4. **First-release human acceptance.** Run complete workflows with a user on real
   desktop/mobile hardware and at least one screen reader. Check the globe and
   2D alternatives, readable metadata, keyboard/zoom/reduced motion, save/export
   understanding, resource/provider failure and return after restart. Keep axe
   incompletes and Firefox fallback visible. Automated passing scans cannot
   substitute for this evidence.

## Priority 2: larger capabilities requiring a defined use case

- **Finding replay:** historical findings export rule versions, inputs and source
  references, but the Phase 10 format does not replay findings. Define evaluation
  clock/policy capture and a versioned finding replay contract, with tampering and
  resource-change tests, separately from existing comparison replay.
- **Scale and performance:** benchmark cold starts/networks, representative larger
  bounded histories/scenes, device GPUs, browser-profile lifecycle and longer
  sessions. Retain informational timing distributions and reproducible conditions;
  optimize only demonstrated user-impacting bottlenecks. No fragile CI frame-rate
  threshold or loss of precision/provenance.
- **Cross-device/private investigations:** currently absent. Establish identity,
  ownership, authorization, disclosure, abuse and migration requirements before
  adding accounts or server saves. The present edge strips credentials and is
  explicitly not an authentication design.
- **Global/bulk discovery, multi-satellite visualization, pass/visibility or
  additional analysis tools:** long-term product opportunities, not verified
  existing features. Define a focused user problem, scientific contract, provider
  cost/limits and acceptance cases before scheduling implementation. No collision,
  maneuver/anomaly classifier or AI claim is implied.
- **Production security/capacity:** review final image/OS advisories, perimeter
  limits/NAT/load behavior, user-data disclosures and operator privileges on the
  selected target. Managed PostgreSQL needs a measured multi-writer/multi-host or
  recovery requirement, a reviewed migration and demonstrated recovery; it is not
  required solely to complete this local audit.

Recommended next local milestone: **stored catalog onboarding and portable local
investigation recovery**, scoped and tested incrementally. Scientific provider
clarification and E4 infrastructure work can proceed independently when the
necessary evidence and authorization become available. They remain release gates.
