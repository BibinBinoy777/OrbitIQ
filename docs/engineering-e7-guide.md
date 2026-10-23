# E7 — historical windows, recovery and captured export

Open **Discovery & history → Historical analysis**, enter a stored NORAD ID and
select a timeline page size. Analyze reads existing archive records; it does not
collect provider data. An empty archive stays empty.

Each response describes a bounded window. The server chooses an anchor on the
first request unless one is supplied. Next pins that anchor and advances the
insertion-ID cursor. Previous restores the earlier window with its resolved anchor, even when
newer records have since been inserted. Refresh starts a new
anchor. IDs describe insertion boundaries, not retrieval chronology. Only an
initial page with no continuation can describe complete anchored history; the
last continuation page is still partial. Counts can remain unknown when the
bounded count budget is exceeded. Unusable records remain visible without usable
orbital elements; unknown clocks do not become known.

E7 closes two bugs: a same-catalog response for a different window could previously
be displayed/exported, and Retry could use the last successful window instead of
the failed request. The client now binds catalog, limit, before cursor and any
supplied anchor to the response's existing request echo. It also checks bounded
count/completeness and source-reference relationships. A mismatch produces an
error with no findings or export controls. **Retry historical analysis** retries
the failed window and navigation stack. Editing either input cancels obsolete
requests and clears stale results/retry state. The controls fit a 320-pixel view.

After recovery, **Export historical analysis JSON** downloads the captured report
and its request metadata/source references. Export does not call the API again.
A timestamped report ID can change on a later analysis; this does not identify
an immutable provider acquisition. Retry before receiving a first anchor permits
the server to choose one; it does not freeze records inserted during that failure.
A retry on an established anchored continuation preserves that boundary.

## Contract and reproduction

The endpoint and report remain version 1; no payload, hashing, storage, dependency
or migration changes. OpenAPI now describes the stable request/pagination/coverage
envelope and array bounds. Nested scientific evidence stays opaque in that model;
the existing backend rules and client source validators remain authoritative.
The model is attached through `responses`, not `response_model`: FastAPI does not
filter/coerce the already-hashed response. This is targeted runtime drift
protection, not generated cross-language types or a complete scientific schema.

The shared fixture `frontend/src/test-fixtures/history-windows.json` is generated
from the real API against isolated, public Vallado-derived synthetic inputs. It
includes full, first, older, single, empty, damaged/nullable and unknown-count
cases. Test-only clocks and insertion timestamps are explicitly synthetic. The
unknown-count case temporarily lowers the isolated count budget; no production
limit changes. Damaged data is confined to a separate fixture copy. Real/private
archives and provider attachments are never fixture inputs.

From the repository root after locked installation:

```sh
uv run --locked pytest backend/tests/test_history_contract.py backend/tests/test_e4_release.py
npm --prefix frontend test -- src/history-api.test.ts src/HistoricalAnalysis.contract.test.tsx src/HistoricalAnalysis.test.tsx
uv run --locked ruff check .
uv run --locked ruff format --check .
npm --prefix frontend run lint
npm --prefix frontend run format:check
npm --prefix frontend run build
```

Inspect drift before deliberately regenerating the shared synthetic fixture:

```sh
ORBITIQ_UPDATE_HISTORY_FIXTURE=1 uv run --locked pytest backend/tests/test_history_contract.py
```

The [existing browser/PDF runner](engineering-e1-browser-pdf-ci.md) now includes
seven additional E7 checks per browser in the history stage. Its original API
journey is preserved. A separate context explicitly injects transport failures
and a valid wrong-window response, then recovers through the real fixture API.
It verifies Next/Previous Retry, input clearing, keyboard download, unchanged
browser storage, responsive layout and two axe scans. Native downloaded bytes
must equal the actual response. Diagnostics can contain fixture DOM/network data;
use only disposable public/synthetic inputs.

The first E7 CI run found genuine gateway HTTP 429 responses in Firefox history
and WebKit report generation: dense synthetic journeys exceeded the unchanged
one-calculation-per-second budget. The history/report browser journeys now opt in
to fixture request scheduling (1.05-second spacing across calculation routes and
contexts), before sending requests. They never retry responses or relax gateway
limits/assertions. Other journeys, failure probes and E2 performance measurements
retain their behavior. Pacing decisions are retained in diagnostics; report
journey timing includes this test overhead and is not a latency benchmark.

The existing release evidence gate requires all seven named E7 cases in each
engine, accessibility/layout evidence and the selected-window download's digest
and request identity. It retains these in both full and compact sealed evidence.
Failure probes reject missing/failing evidence, changed downloads, altered request
metadata and storage/accessibility/layout failures. No duplicate CI workflow was
created. See the [E7 verification report](engineering-e7-report.md).

Automated accessibility is not physical-device or screen-reader certification.
Scientific source qualification remains separate: E4 **OPEN**, Phase 11.3.1
**PARTIAL**, scientific evaluation **BLOCKED**. No real Swarm-A residuals or
independent accuracy/forecast claims are produced by this workflow.
