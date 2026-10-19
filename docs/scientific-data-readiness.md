# Scientific-data readiness

Readiness is a calculated assessment of local resources and stored metadata. It
is not a satellite observation, an orbit-accuracy measurement, full archive
integrity verification, a deployment probe, or a guarantee for every epoch.

## API contract

`GET /api/health` retains its database-independent liveness contract:
`{"status":"ok","service":"OrbitIQ"}`. Informational scientific warnings do
not change liveness.

`GET /api/readiness` assesses the current UTC time. Optional `at` must be an ISO
8601 timestamp with an explicit timezone, for example
`/api/readiness?at=2004-04-06T07%3A51%3A28.386Z`. The existing time validator
rejects naive timestamps, numeric epochs and leap-second spellings with the
existing safe 422 error contract. Readiness returns HTTP 200 even when a component
is unavailable: consumers must inspect the statuses. It sends `Cache-Control:
no-store`. There is no maintenance HTTP endpoint.

The response contains:

- `kind: calculated_readiness_assessment`, `status`, `scope`,
  `automatic_updates: false`, `time_system: UTC`.
- `evaluated_at`: actual assessment time, including timezone.
- `requested_at`: calculation epoch being assessed, normalized to UTC.
- `components.database`, `orbital_data`, `eop`, `leap_seconds`: each has `status`,
  stable `code`, safe actionable `message`, and supported facts.

All reported times are timezone-aware ISO strings with UTC offset `+00:00`;
absent metadata are `null` or explicitly unknown. The source leap-expiry label
is separately retained with its original scale. Durations name their units in
the field: `_seconds`, `_hours`, `_days`. No internal file paths, connection
strings, raw SQL errors, credentials or orbital payloads are returned.

## Status semantics

| Status | Meaning and action |
| --- | --- |
| healthy | Supported local checks passed for this component/time; continue within the stated scope. |
| degraded | Reads/calculations may remain possible, but data are absent, aging/stale, predicted, or need maintenance; read the component explanation. |
| unavailable | A required local resource/schema/read or requested-time policy check failed; correct configuration, maintain resources or select a supported time. |
| unknown | Metadata or verification are insufficient; refresh and investigate before asserting readiness. |

Overall severity is `unavailable`, then `unknown`, then `degraded`, then
`healthy`. Thus a missing DB can make the overall status unavailable while
historical scientific resources remain usable. A stale snapshot does not make
liveness fail. Component facts and per-calculation validation remain authoritative;
overall status is deliberately conservative.

## Database and stored orbital metadata

The service opens only the explicitly configured `ORBITIQ_DATABASE_PATH` in
SQLite `mode=ro`, sets query-only mode and checks schema version 2 plus the
columns needed for metadata reads. It does not initialize, migrate or write a DB.
A missing file remains missing. The normal endpoint does not run `COUNT`, full
archive verification, integrity scans, raw-payload reads or a timestamp sort.

The primary-key query reads at most **101** small metadata rows in descending
insertion ID order. The extra row detects a history larger than the **100**-row
assessment limit. SQLite has a 250 ms busy timeout and a progress handler budget
of 5,000 VM instructions / 100 ms (checked every 100 instructions). These are DB
work budgets, not an end-to-end latency guarantee. Initial local Astropy parsing
and concurrent scientific locks can add latency; production concurrency/load
limits remain an operational task.

For a complete archive of at most 100 records with valid retrieval metadata,
`latest_retrieval_at` is the actual maximum parsed retrieval timestamp; insertion
ID is **not** treated as retrieval order. Database facts separately identify the
latest inserted snapshot ID and that record's stored retrieval timestamp. A
separate insertion timestamp was never recorded and is reported as such.

For larger archives, or invalid retrieval timestamps, `global_latest_known` is
false, global latest/freshness are unknown, and the bounded-history explanation
is shown. The service does not substitute the newest insertion or a sampled
maximum for a globally known latest retrieval. A future explicit migration could
add maintained retrieval metadata or an appropriate time index. That migration
and any historical backfill require separate work; this task changes no schema.

Freshness reuses the existing `FreshnessPolicy`: orbital **epoch** age is fresh
through 24 hours, aging through 72 hours, then stale, by default. Configure
`ORBITIQ_FRESH_HOURS` / `ORBITIQ_STALE_HOURS` with finite
`0 < fresh < stale <= 168` hours. Retrieval age is reported separately and does
not refresh old elements. Future/invalid timestamps are unknown. These thresholds
are presentation policy, not measured prediction error. Stale data can still
support historical calculations under the existing propagation guards.

No ingestion-attempt/error history or source availability probe is stored by the
current schema. `ingestion_error_status: not_recorded` and null error do not
assert that ingestion succeeded. Readiness neither fetches CelesTrak nor validates
every snapshot's full provenance; existing archive verification remains separate.

## EOP and leap-second resources

The existing loader obtains explicit installed paths from `astropy_iers_data`,
loads `IERS_A` and `LeapSeconds`, hashes their bytes, and caches them per process.
The installed package is the resource authority; this change adds no runtime
file override or automatic refresher. Astropy auto-download and remote leap
URLs remain disabled inside the existing locked calculation context. No
ordinary readiness, propagation, transformation or track request runs maintenance.

EOP facts distinguish:

1. **Identity/release age**: source description, installed package version and
   SHA-256 are known. Actual release timestamp/age are not recorded; null is
   returned. A date-looking version or filesystem modification time is not
   manufactured into a release date.
2. **Coverage**: first/last MJD converted to UTC, and the package's first predicted
   MJD. `covered` means inside the file's central-epoch range; it alone does not
   mean a calculation is usable. UT1/polar-motion sources and ±0.5-second velocity
   support are checked by the existing `parameters` function.
3. **Prediction freshness**: `(assessment UTC MJD - predictive_mjd)` in days,
   maximum 30 days. This is table-age policy, not release age or forecast error.
   Exactly 30 days is allowed; greater is rejected when predicted values are used.

Measured/final requests can remain valid with an aging prediction region, reported
as degraded when its age exceeds policy. Predicted requests are labelled degraded
within policy, unavailable when expired or under `measured_only`. Missing/corrupt
resources, invalid flags/non-finite values and out-of-range support fail strictly.
No extrapolation, clamping, assumed DUT1, or degraded-accuracy fallback is added.
The physical meaning remains calculated orbital positions, never direct observations.

Leap validity comes from the parsed resource's actual expiry `Time`. Unknown
expiry is unknown, with calculation-resource usability withheld. Requested-time
expiry makes the resource unavailable; an earlier historical request with
current-time expiry exhausted is degraded, with the two facts separated.
For this installed version the source label is `2027-06-28` in **TAI**. The
existing application's comparison consequently has an effective UTC cutoff of
`2027-06-27T23:59:23+00:00`, with a ±0.5-second support guard for calculations.
Both label/scale and normalized cutoff are shown. This records the existing
conservative application policy; it does not reinterpret the source date, revise
leap physics or assert validity beyond the policy.

Optional `ORBITIQ_EOP_VERIFICATION_FILE` is an absolute path to the operator's
selected receipt. Only a bounded 64 KiB file with matching package version,
EOP/leap hashes, `selected` status and aware acquisition/verification/selection
times is accepted. Otherwise these times remain unknown. Matching a receipt is
local operator evidence, **not** a cryptographic attestation or proof of worker
restart. Restrict write access; do not place it in frontend configuration.
See [controlled maintenance](eop-maintenance.md).

## Dashboard

Use the **Scientific-data readiness** navigation button. Four labelled sections
and overall status provide text indicators, UTC refresh/target times, factual
coverage/freshness details and actionable messages. Optional requested time,
manual refresh, API failure/retry and partial-section handling use the existing
same-origin `/api` proxy. There is no background polling, acquisition button or
public operator control. Editing the time clears old results and cancels pending
requests; leaving the page aborts the request. Fetches have a five-second timeout.

Desktop/tablet use a two-column grid above 800 px, mobile a single column. Native
labelled inputs/buttons, visible focus, semantic regions/status/error messages,
and a return-to-explorer action support keyboard navigation. Partial unreliable
sections become explicitly unknown without inventing facts for them.
