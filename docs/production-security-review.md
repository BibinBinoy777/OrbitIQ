# Phase 8 production security review

Scope: the existing public read-only scientific explorer, local saves and parameter
links, operator-only collection/maintenance, and the proposed single-host container
boundary. This focused review and package advisory lookup are not a penetration
test, full dependency supply-chain assurance or public-hosting certification.

## Findings and implemented controls

| Surface | Finding / control | Verification |
| --- | --- | --- |
| Public data writes | No account/admin/ingestion HTTP service exists. Production rejects mutation methods before handlers. Existing read-route tests continue to reject writes. | Isolated POST/PUT/PATCH/DELETE tests; live gateway POST refusal; archive hashes unchanged |
| Expensive GETs | Existing input limits did not bound aggregate public traffic. Gateway now limits rates/connections; one API worker admits four simultaneous calculation paths, with 503/Retry-After. | Async admission/recovery test; real gateway burst returns 429/Retry-After; one-host scope only |
| Request size | Existing per-field validation retained; production adds URI/header bounds and rejects request bodies on read routes. Gateway adds body/header/timeouts. | 414/431/413 unit cases and actual gateway 414/413; oversized field 422 |
| Configuration | Development tolerated unavailable storage until a read. Production now requires explicit hosts, absolute path, EOP policy and valid sampling/freshness configuration; existing schema-3 archive is validated read-only at startup. | Missing path refuses without creating it; safe configuration errors; real non-root startup and isolated CI fixture smoke |
| Host/CORS | Development proxy is not a production ingress. Production validates Host; deployment uses a single origin and no permissive CORS middleware. Forwarded headers are not trusted by Uvicorn. | Unknown API Host 400; foreign Origin receives no Access-Control-Allow-Origin |
| Browser XSS/framing | React renders titles/notes as text; no arbitrary executable URL deserialization. Added production CSP with self-only scripts/styles/connect and no framing/base/object capability, nosniff, frame DENY and referrer protection. | Real saved/share browser workflows have no CSP violations; unit text/URL validation; headers on error/rate responses |
| URL sharing | Version 1, 2048-character URL, strict mode keys, time/frame/source bounds and hash/epoch/retrieval identity checks remain intact. No local title/notes/token/payload in links; no server save claimed. | 68 model/storage tests within 275 frontend tests; actual genuine-source reconstruction/missing-source browser checks |
| Error privacy | Existing safe scientific/validation errors retained. Unexpected pre-response exceptions now return a generic envelope. Production docs/OpenAPI UI disabled. | Fault test excludes path/query/header/exception canaries; API error cases expose no internal archive path |
| Log privacy | Default raw URL access logs were unsuitable for public query privacy. Request logging now uses generated IDs, UTC, route templates, status/latency/size only; edge excludes addresses/queries/headers. | App log capture and real gateway private-canary requests; matching request ID in logs; raw access logs disabled |
| Database privileges | API reads already use SQLite read-only connections. Container adds read-only data/root mounts, non-root UID 10001, dropped capabilities, no published API port and internal-only network. | Actual container UID/read-open refusal; restart/replacement preserve genuine source identities and hashes |
| Ingestion/admin | Collector, migration, backup and EOP selection remain explicit operator CLI actions. No upstream request occurs during API browsing. | Existing cooldown/deduplication/failed-transaction/EOP suites; no ingestion run or archive ledger change during this phase |
| Build context/secrets | No credential is required for public reading; runtime cloud identity absent. Docker allowlist excludes data, backup, Git, environment files and private keys. Optional build CA secret is transient, not copied. | Image/context inspection, tracked-file scan and unchanged dependency locks; no normal dataset included in image |

## Rate and identity boundaries

The Nginx defaults are a conservative candidate, not a promise of capacity. A
trusted upstream ingress must enforce perimeter limits, TLS, DDoS protection and
correct source addressing. Without an explicitly reviewed trusted-proxy CIDR list,
all clients behind a load balancer can share one rate bucket. Arbitrary forwarded
headers must never select a client identity or bypass limits. Distributed attackers
and multiple workers/instances are not controlled by the app's per-worker counter.
Proxy timeouts limit connection waiting; they do not cancel CPU work at a hard deadline.
The existing seven-day propagation window, 361-point default sampling ceiling,
bounded pagination/work budgets and fixed read-only source validation remain necessary.

No authentication was found or added. Public archive browsing can remain anonymous;
operator operations need host/filesystem access control, not an exposed HTTP route.
Browser saves are plaintext, browser/origin local, not private server documents.
Do not put secrets in notes. Share parameters are public to anyone with the link
and archive access, with no revocation/expiry. Protect identity/cloud saves under a
separate managed-authentication milestone before making ownership or sync promises.
The gateway currently strips Authorization/Cookie headers; authenticated features
must deliberately redesign that contract and its tests.

## Dependency and CI evidence

At the recorded Phase 8 run, `npm audit --json` returned zero advisory matches for
the locked dependency tree, and pip-audit 2.9.0 found no known vulnerability matches
among 29 installed Python project packages. Both lookups exited 0; they are dated
advisory-service results, not proof of absence of vulnerabilities. No application
dependency/lockfile change was needed. The audit tool was isolated under `/tmp`.
No comprehensive OS/base-image vulnerability scan or artifact-signature verification
is claimed. Pin image digests, review publisher provenance and scan current final
images again before a release; maintain a security update policy.

GitHub Actions for published Phase 7 SHA `ec1f9f832e5f2a488169d43083d83e24e1eac25e`
completed successfully. The new local workflow explicitly adds expanded/geodetic
audits and image build/startup verification. It has not run remotely for Phase 8.
The branch-protection API returned HTTP 403 “Resource not accessible by integration”;
the rulesets API returned HTTP 403 with a plan/visibility restriction. Protection
settings cannot be inferred. A repository administrator must inspect Settings →
Branches/Rules and confirm required checks and review rules before release.

## Remaining launch gates

Configure and test real HTTPS/renewal/HSTS, DNS, firewall and trusted ingress;
provide a durable archive and encrypted off-machine backup/restore proof; assign
least-privilege operator access, log retention, alert recipients and incident
ownership; validate capacity/shared-NAT limits and recovery on the target host;
inspect exact Phase 8 CI and protection evidence once publication is separately
authorized. Browser checks do not establish physical-device GPU or screen-reader
compatibility. Scientific observation validation remains BLOCKED and uncertainty
unquantified; no accuracy, maneuver or collision guarantee should be advertised.

## Phase 8.1 additions (earlier Phase 8 evidence retained)

Optional TLS reuses the reviewed same-origin routes and headers. Only loopback
certificates/hostnames were verified; no public certificate, redirect, renewal or
trusted-ingress claim is made. Operator backups use established restic encryption,
protected external configuration and exact-point checksum/schema/payload/API checks.
Local encrypted repositories are explicitly labelled test-only. Restore failures
are not ignored. Retention is preview-only and neither archive nor repository
initialization/deletion is automated.

Monitoring is a separately invoked CLI using existing status endpoints and optional
bounded request logs/backup receipts. HTTPS is required except explicitly labelled
loopback tests. Webhook/token configuration is private, no redirects are followed,
and only bounded component/status/time/incident metadata are sent. Delivery is
explicitly opt-in, persisted before sending and suppressed during a cooldown even
when delivery fails. It does not run inside or crash the API. Corrupt/unsupported
state is preserved. A loopback receiver test does not verify a production receiver.
Do not enable delivery to a real destination without owner approval and secure
configuration. No external recipient or storage account was contacted in this phase.
