# E7 plan — historical window integrity and recovery

Baseline: clean `engineering-e6-onboarding-recovery`, commit
`5aec8ec3a8ac70f2fe113aef017aa81d31074c62`. Work branch:
`engineering-e7-history-contract`.

## Selected gap and priority

The [E5 roadmap](engineering-e5-roadmap.md) ranks targeted contract-drift protection
next after stored onboarding and portable recovery. [E6](engineering-e6-report.md)
implemented those first two user workflows. Broad collection/scheduling still
needs a defined provider/use case, and physical-device/screen-reader acceptance
needs human/device evidence unavailable to this task. Finding replay, accounts and
global catalog expansion are larger lower-priority capabilities.

Choose one bounded workflow: **trustworthy historical analysis page selection,
failure/retry and captured export**. A user selecting a one-record anchored page
must not receive a different window or inadvertently retry a previous full-history
request. That matters for coverage/completeness claims, source references and
reproducibility, and can be verified locally without production/provider resources.

## Evidence and current behavior

Inspection of `history-api.ts` shows `getHistory` checks response catalog but does
not bind the existing backend `request` echo, page size, anchor or before cursor to
the actual request. `parseHistory` checks many source/number/units constraints,
but ignores the request echo and its completeness relationship.

`HistoricalAnalysis.tsx` stores `params`/`back` only on success. The Retry control
passes those successful parameters to `load`, so a newly selected page size or
failed Next/Previous navigation can retry another window. Failing-before tests
will establish both behaviors before fixes.

The backend already emits version-1 request/pagination/coverage metadata and
validates exact orbital sources. Its historical route has no documented successful
response envelope in OpenAPI. Scientific rules, report hashing, source selection
and data storage must retain their behavior.

## Desired behavior and implementation boundary

Reuse the existing endpoint and version-1 historical report. Validate requested
catalog, limit, before cursor and supplied anchor against the response. Validate
internal window/count/completeness/source relationships without requiring all
records to be scientifically usable. Keep nullable/unknown metadata and explicit
partial coverage; do not infer chronology or fresh data in the browser.

Retry the exact failed parameter/navigation snapshot. A new user input cancels
obsolete requests and clears obsolete retry state. Rejected responses must not
expose findings or downloadable captured evidence. A subsequent valid response
must recover normally and export that capture without another API calculation.

Document the stable bounded envelope in OpenAPI without filtering/normalizing or
changing the existing payload/hash. Add backend-produced public synthetic contract
fixtures checked against the real endpoint and consumed by frontend validation
checks. Avoid generated-type infrastructure, new dependencies, a new schema
version, a database migration, or changes to historical scientific rules.

## Acceptance criteria

1. Regression tests fail before fixes for wrong-window acceptance and wrong-window
   Retry. Record their actual failures.
2. Matching full/partial/empty/single/invalid-source reports remain accepted;
   unknown counts and nullable metadata remain unknown.
3. Wrong request/window, inconsistent completeness/counts or source graph is
   refused before rendering/export. Exact timestamps retain six-digit precision;
   equivalent explicit offsets retain existing meaning.
4. Initial failure, failed Next and failed Previous retry their original window;
   input changes/cancellation prevent obsolete results or retries.
5. Actual browser selection, injected response mismatch, retry, pagination and
   native captured JSON export work in Chromium/Firefox/WebKit. Original saves
   and source archive remain unchanged. Errors/focus/keyboard remain accessible.
6. Backend OpenAPI documents the bounded envelope; real API outputs match shared
   fixtures/frontend expectations without payload/report-ID changes.
7. Relevant unit/API/frontend/browser/accessibility/PDF/recovery/release checks
   run with actual outcomes. Disclose local disk constraints; verify complete CI
   against the exact final published engineering commit.
8. Preserve all previous reports/branches, the database and 72 private files;
   publish only reviewed non-sensitive E7 work. No merge or deployment.

E4 remains **OPEN**. Phase 11.3.1 remains **PARTIAL**, scientific evaluation
**BLOCKED**. No genuine Swarm-A propagation/residuals, timestamp reinterpretation,
frame-alignment qualification or independent-accuracy/forecast claims are part of E7.
