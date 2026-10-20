# Phase 10 — Reproducible evidence replay

Phase 9 was fast-forwarded into `main` at
`d9f85d5d6e28cea90f25965c761422f16705eea8` with authorization. Main's exact-SHA
[CI run 39389781990](https://github.com/BibinBinoy777/OrbitIQ/actions/runs/39389781990)
passed backend, frontend and release-image jobs. Phase 10 is local work on
`phase-10-evidence-replay`; its new implementation is not authorized for publication.
Hosting/domain/HTTPS and all other Phase 8 infrastructure gates remain separate.

## Scope and design

Add an operator CLI to capture a new Phase 9 report and immutable replay bundle
from an exact schema-1 investigation definition. Preserve original archived source
response bytes/metadata, exact applicable EOP/leap files, dependency lock, installed
software identities, backend source hashes and scientific policy settings. Never
initialize, migrate, modify or restore the ordinary database. No ingestion occurs.

Verification reads only the bundle and matching installed code/software. Reuse
existing SGP4, coordinate, sampling, element-difference and state-comparison logic.
Historical replay uses an explicitly captured policy-evaluation time; it does not
certify current EOP readiness or refresh old predictions. Normal API resource and
clock behavior remains unchanged. Restore scoped resources/leap state after replay.

Compare source identities, epochs, units, all requested state vectors, geodetic
values, comparison differences and EOP provenance. Distinguish source-only,
matched, numerical mismatch, unavailable original calculation and blocked replay.
Execution times/freshness presentation are not falsely expected to repeat exactly.
Fixed documented absolute replay tolerances are separate from scientific accuracy.

Use bounded, fixed-name regular files in an exclusively created private directory;
reject symlinks, unknown files, malformed/nonfinite/duplicate-key JSON, unsafe paths,
bad hashes and incompatible software/code/lock/policy. No archive extraction,
dependency installation, executable deserialization, public upload API or frontend
math. A separately retained manifest checksum can pin a trusted capture; local
checksums alone do not authenticate the provider or resist a complete forged bundle.

Old Phase 9 JSON alone cannot retroactively provide unrecorded resources/runtime.
Capture a new bundle from its definition rather than inventing historical metadata.

## Acceptance criteria

| Criterion | Required evidence |
| --- | --- |
| P10-01 capture | Four actual investigation modes; exact sources and applicable resource files retained |
| P10-02 offline | Replay succeeds without database configuration or source network access |
| P10-03 identity | Changed/missing files, source, lock, software and backend code fail closed |
| P10-04 numerics | Existing science services reused; all requested states/track rows/comparisons checked with explicit tolerances |
| P10-05 honesty | Source-only/unavailable/mismatch/blocked are distinct; no observation/accuracy/current-readiness claim |
| P10-06 safety | Existing destinations/results refused; bounded non-executable inputs; original DB/bundle preserved |
| P10-07 policy | Historical replay clock/resources explicitly scoped; normal API policy and leap state preserved |
| P10-08 regressions | Full backend tests and science audits; frontend tests/build remain passing |
| P10-09 documentation | CLI, bundle/hash/version/resource/tolerance semantics and limitations documented |

Run meaningful isolated-fixture tamper/failure tests and a genuine-archive offline
capture/replay rehearsal. Record only executed results. Add no dependencies,
migrations or production configuration. Keep Phase 10 changes uncommitted for review.
