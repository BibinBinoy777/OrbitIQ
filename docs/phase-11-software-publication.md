# Phase 11 software publication review — 22 October 2026

This records the local review before committing the remaining historical-analysis
and observation-validation implementation. Publication, exact-commit remote CI,
scientific qualification and production deployment are separate milestones.
It does not claim that a future commit or workflow has already succeeded.

## Scope and preserved work

Starting branch: `phase-11.3.1-verified-publication`.
Starting HEAD: `48683a356d79102eab0219acc208c9c99821a667`.
The tree contained 42 unstaged modified/untracked paths and an empty index.
Their implementation bytes match the full workspace verified during the earlier
[Phase 11.3.1 publication review](phase-11.3.1-publication.md).
They were excluded from that narrower publication; this task explicitly authorizes
publishing the verified remaining work. No new feature is implemented here.

The 42 original paths contain:

- Bounded, read-only historical analysis, shared comparison helpers, API admission
  and gateway routing, accessible frontend presentation and JSON export.
- Optional operator-captured observation-validation packages, compatibility and
  discrepancy arithmetic, read-only API/UI inspection and offline verification.
- Unit/API/frontend tests, clearly identified synthetic numerical fixtures,
  loopback browser verification scripts and methodology/operator documentation.
- Dated Phase 11, extension, follow-up and Phase 11.3 reports and execution
  evidence. These retain their historical findings and test counts; current
  scientific status is documented separately below.
- A credential-free `.env.example` template and an ignore rule for local
  validation packages. No actual environment file is included.

This additional review document is the only new file created for publication.
All 317 starting nonignored source/report files retain their exact bytes. No
existing test, calculation, scientific tolerance, dependency, lockfile, migration
or workflow was changed to obtain a pass. Existing reports were not rewritten.

## Content review and private evidence

All 42 candidate contents were read, including structured JSON evidence and
embedded execution logs. Numerical fixtures are published reference cases or
explicit synthetic arithmetic/UI examples. Historical ISS results describe the
existing archive, with provider and source hashes; they are not independent
observations. ESA sections retain product metadata, hashes and diagnostic counts,
without SP3 position records or original product payloads. Local service addresses
and dotted software versions in logs are not provider-email metadata.

No personal email addresses, credential tokens or private keys were detected in
the publication candidates. This scoped pattern check supplements content review;
it is not a complete security audit. Raw historical GP JSON/CSV, ESA ZIP/SP3/PDF
products, correspondence, research captures, databases, credentials, actual local
environment files and private replay/validation packages remain excluded under
existing ignore rules. Source products without redistribution clearance are not
added as fixtures. The `.env.example` file contains configuration examples only.

Private-file size, timestamps, permissions and inode metadata and the ordinary
database byte hash are checked against the starting baseline. Original source
attachments are not reopened for this review. The ordinary database remains
SHA-256 `ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
Tests use separate fixtures; browser rehearsals use a separate read-only ISS copy
and explicitly synthetic catalog-6251 packages. No ordinary initialization,
migration, restore or database write is performed.

## Fresh local verification

| Executed check | Result |
| --- | --- |
| `uv sync --locked` | PASS; Python dependencies remain locked |
| Complete backend suite | 1,178 passed; two existing warnings |
| Complete frontend suite | 344 passed, 25 test files |
| Ruff lint/format; ESLint/Prettier; TypeScript; production build; whitespace | PASS |
| Published SGP4 / terrestrial / expanded scientific audits | 40 / 6 / 32 passed |
| Independent geodesy / separate round-trips | 28 / 28 passed |
| Golden reference lifecycle | Six published components and three exact offline replays passed |
| Relative documentation links in original candidates | 62 resolve locally |
| Chromium / Firefox / WebKit regression flows | 77 passed across all three engines, using unmocked local APIs |
| Chromium PDF inspection | Seven passed, including all 361 maximum-track rows |

Browser runs used byte-matching backend and built frontend copies on a temporary
internal Docker network, with no published host ports. History checks used the
separate genuine ISS archive copy. Observation fixture checks used explicitly
synthetic catalog-6251 arithmetic/UI inputs with zero independently verified
observations. Firefox/WebKit checked report/download and offline HTML behavior;
native PDF generation and inspection used Chromium. Containers and the temporary
network were removed after completion. Semantic controls, keyboard focus and
responsive layout were checked; no complete WCAG/screen-reader audit is claimed.

Locked frontend installation will also run in remote CI; local `npm ci` was not
repeated because the lockfile and installed dependency inputs are unchanged.
Local logs and verification artifacts are under
`/tmp/orbitiq-unpublished-publication/`; these are not independent backups.

## Scientific and operational boundary

Phase 11.3.1 remains **PARTIAL**; genuine Swarm-A scientific evaluation remains
**BLOCKED**. See the current
[provider reconciliation](phase-11.3.1-provider-response-reconciliation.md) and
[scientific pairing report](phase-11.3.1-scientific-pairing-report.md).
The dated Phase 11.3 reports correctly describe their earlier acquisition state;
they do not supersede the subsequent CSV receipt and provider clarification.

CSV is the supported historical-input format; the original JSON remains malformed.
The user-reported CelesTrak response says creation timestamps are not retained.
Historical availability and complete fitting lineage remain unknown, and
independence is not established. ESA clarification remains pending. The 120-second
SP3 time conflict, 37.12-ns MJD discrepancy, unsupported time encodings, KIN-specific
quality, IGb08 alignment and temporal pairing remain unresolved. No genuine
Swarm-A propagation, transformation or ESA residual is run or approved here.
Synthetic discrepancy results are not physical prediction-accuracy evidence.

The optional observation archive requires explicit local operator configuration;
it does not download observations or make the Swarm reference eligible. Public
access control and abuse protection remain production concerns. No production
configuration is enabled by publication.

## Publication and remote verification

Stage only the reviewed 42 paths and this review document, inspect the full staged
diff and commit using the account's GitHub noreply identity. Push normally to the
existing dedicated branch. Do not force-push, merge, release, change visibility,
deploy or modify DNS/infrastructure.

The existing `OrbitIQ checks` push workflow has three jobs: backend (locked Python
installation, tests, scientific audits, migration/backup/restore fixtures and
Ruff); frontend (`npm ci`, tests, lint, formatting, TypeScript/build); and
release-images (local Docker builds, Nginx and isolated fixture API checks).
It needs no private GP/ESA products or production secrets. Expected full-scope
counts are now 1,178 backend / 344 frontend; the previous 1,089 / 307 counts
belonged to the narrower publication. Browser/PDF checks are additional local
verification and are not part of this workflow.

After push, verify the remote branch SHA and all three jobs against the exact
new commit, and inspect their actual logs. Earlier CI success is not evidence for
this expanded commit. Phase 8 public hosting/HTTPS, off-machine recovery, actual
alert delivery and branch-protection verification remain separate open milestones.
