# Operator monitoring and alert delivery

The monitor is an explicitly invoked CLI, not a new service or enabled scheduler.
It reuses `/api/health`, `/api/ready`, `/api/readiness`, optional existing structured
request logs and private backup/recovery receipts. The API does not send alerts.
An approved receiver, credentials, evaluation schedule, signal owner and escalation
policy remain unconfigured production prerequisites.

```sh
export PYTHONPATH=backend
uv run --locked python -m orbitiq.maintenance.monitor \
  --base-url https://your-approved-domain \
  --state-file /protected/monitor/state.json \
  --backup-manifest /protected/state/latest-backup.json \
  --request-log /protected/logs/api-requests.jsonl
```

This observes and prints a bounded result; it sends nothing by default. Status 200
on informational readiness does not mean all components are healthy. Findings
identify API/dependency failures and nonhealthy existing database, data-age,
ingestion, EOP/leap states. The latest successful acquisition timestamp remains
distinct from orbital-element freshness; successful collection is not accuracy.
Predicted EOP can be a deliberate policy-labelled degraded state, not an outage;
the owner must choose severity/escalation appropriately. No readiness restriction
is bypassed to make the monitor green.

Backup receipts must report a successful, recent (48h) external round-trip and
approved independence, with a valid checksum, to avoid an unknown recovery finding.
A failed job receipt is unavailable; a missing, stale, local-only or invalid receipt
is unknown. Receipt reading is not a fresh independent audit of remote storage.
The export CLI can atomically update this operator-owned receipt on success/failure.
Keep old job manifests separately; do not replace them with a fabricated success.

Optional request-log evaluation reads at most the trailing 256 KiB, considers the
last five minutes of existing `http_request` records, and flags five or more
429/500/502/503/504 statuses or requests over two seconds. It forwards no raw logs,
queries or request identifiers. This bounded signal is not a complete metrics store,
CPU/disk/memory monitor or guarantee of detecting every incident. Configure the
selected host/platform monitor for disk space, OOM/restarts, certificate expiry,
ingress failures and other signals not visible in these application records.

## Opt-in delivery

Store an approved HTTPS webhook URL in an absolute private file. Credentials must
not be in command-line URL queries, usernames/passwords or fragments. An optional
private token file supplies a Bearer authorization header; it is not placed in the
payload or logs. Files must be bounded and private. Use a private operator-owned
directory (0700) for state and configuration, and files 0600/0400.

```sh
uv run --locked python -m orbitiq.maintenance.monitor \
  --base-url https://your-approved-domain \
  --state-file /protected/monitor/state.json \
  --backup-manifest /protected/state/latest-backup.json \
  --webhook-url-file /protected/config/approved-webhook \
  --token-file /protected/keys/alert-token \
  --deliver --test-alert
```

Run the test only after the owner approves that real destination. Confirm receipt
and escalation with its owner; no real destination was configured or contacted
during Phase 8.1. A success HTTP response confirms only that endpoint's acceptance,
not paging, human receipt or the entire operational monitoring system. A normal
incident uses `orbitiq_readiness`; a test is explicitly `orbitiq_monitor_test` with
`test=true`. Local test mode automatically labels every notification as a test.

Payload schema 1 contains only: event/test flag, a bounded monitor ID, UTC time,
hash incident ID, active flag and known component/status pairs. There are no
database paths, source payloads, credentials, recipient URL, raw exception text,
arbitrary readiness messages or user notes. HTTP calls use finite timeouts and
bounded GET responses; redirects are refused, and webhook response bodies are not
consumed. HTTP transport is permitted only for loopback with `--allow-local-test`.

The private schema-1 state is locked and atomically/fsync persisted. Admission is
recorded **before** sending. Default global cooldown is 1800 seconds, configurable
from 300 to 86400. Failures consume the same cooldown; changed/flapping findings
cannot bypass it. Corrupt or unsupported state is refused without a silent reset.
During cooldown a new incident or recovery can be delayed; this is a deliberate
storm-control tradeoff, not guaranteed immediate paging. A persistent incident may
send a later reminder; recovery can send a subsequent clear state. Keep the state
on protected retained storage and do not delete it to force delivery. Multiple
hosts need separate ownership/monitor identities and receiver-side incident policy.

CLI exit 0 means the check completed, including findings or suppressed/no delivery;
it does not mean the system is healthy. Exit 2 records failed attempted delivery;
exit 1 indicates refused configuration/state or another safe check failure. A
scheduler must inspect JSON **and** exit status. No scheduler or automatic retry
loop was enabled; the owner must set a nonoverlapping interval, failure handling,
retention, alert severity and on-call escalation without creating retry storms.

## Actual Phase 8.1 evidence and remaining setup

The controlled loopback receiver accepted labelled test payloads from actual
archive readiness, exercised a deliberate HTTP-503 receiver failure, and verified
repeat/failure suppression. An unavailable loopback API plus a real wrong-password
backup failure receipt produced the expected findings. These were local controlled
tests, not a real production alert destination or a fabricated satellite event.

Before launch select the receiver/provider, approve credentials, test real signal
delivery and human escalation, provide persistent private state/log forwarding,
schedule checks and backups, verify outage/recovery scenarios and monitor the
monitor itself. Production alert delivery and operational ownership remain
**BLOCKED** until those actions have actual evidence.
