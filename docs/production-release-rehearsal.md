# Local release and recovery rehearsal

This procedure exercises existing local images against a **separate restored
archive**. It is not a staging or production deployment. No public listener,
provider request, ingestion, repository publication or remote workflow is needed.
Use the [infrastructure decisions](production-infrastructure-decisions.md) before
attempting any separately authorized target-host work.

Phase 8.2 exact commands, outputs, case results and local helper sources are in
[structured evidence](phase-8.2-integration-results.json). Commands below parameterize
that tested procedure. Keep receipts private; publish only redacted evidence.

## Prerequisites and isolated recovery

From the repository root, use its locked Python/Node environment and local Docker
socket. Preserve inherited network proxy/CA trust for any build/download; do not
disable TLS verification. Required prebuilt images are `orbitiq-api:<local-tag>`,
`orbitiq-web:<local-tag>` and, for browsers, the reviewed image built from
[`Dockerfile.browser`](../deploy/Dockerfile.browser). Record their actual IDs.
Rebuild only if relevant source/configuration/lock inputs differ from verified
image evidence. Never pull/build silently during the rehearsal.

```sh
export UV_CACHE_DIR=/tmp/orbitiq-uv-cache
export PYTHONPATH="$PWD/backend"
: "${ORBITIQ_DATABASE_PATH:?Select the existing authoritative archive explicitly}"
export ORBITIQ_REHEARSAL_DIRECTORY="$(mktemp -d /tmp/orbitiq-rehearsal-XXXXXXXX)"
chmod 700 "$ORBITIQ_REHEARSAL_DIRECTORY"
uv run --locked python -m orbitiq.maintenance.recovery \
  --directory "$ORBITIQ_REHEARSAL_DIRECTORY/recovery" --keep-restored
```

The recovery CLI uses SQLite online backup into new paths, full schema/table
fingerprints, payload verification and restored listing/detail/comparison API
checks. It refuses existing targets. Keep its `verification.json`. Record the
authoritative file checksum and `fingerprint()` before/after the entire exercise.
Schema-3 means no migration is needed. If testing the explicit migration CLI, use
another new copy and a new pre-migration backup path. Never migrate or initialize
the authoritative database during this rehearsal. Schema-1/2 upgrade and failure
rollback are covered by the existing backend suite.

Prepare a new read-only runtime copy for non-root API UID 10001:

```sh
install -d -m 0755 "$ORBITIQ_REHEARSAL_DIRECTORY/runtime-data"
uv run --locked python - <<'PY'
import os, shutil
from pathlib import Path
root = Path(os.environ['ORBITIQ_REHEARSAL_DIRECTORY'])
with (root/'recovery/restored.sqlite3').open('rb') as source:
    with (root/'runtime-data/orbitiq.sqlite3').open('xb') as target:
        shutil.copyfileobj(source, target)
(root/'runtime-data/orbitiq.sqlite3').chmod(0o444)
PY
```

Read permission is intentional only on this isolated directory inside a private
parent. Docker bind mounting makes that directory accessible inside the container.
Use deliberately managed UID/GID permissions for an actual durable host volume.

## Start, probe and replace the local containers

Choose an unused loopback port; a conflict is a failure to investigate, not a
reason to stop another process. Set the tag to an existing reviewed local image.

```sh
export ORBITIQ_RELEASE=phase81-local
export ORBITIQ_DATA_DIRECTORY="$ORBITIQ_REHEARSAL_DIRECTORY/runtime-data"
export ORBITIQ_ALLOWED_HOSTS=127.0.0.1,localhost
export ORBITIQ_EOP_POLICY=measured_or_predicted
export ORBITIQ_HTTP_BIND=127.0.0.1:18089
export ORBITIQ_REHEARSAL_PROJECT="orbitiq-rehearsal-$(python -c 'import uuid; print(uuid.uuid4().hex[:12])')"

orbitiq_local_compose() {
  env -u DOCKER_HOST -u DOCKER_CONTEXT -u DOCKER_TLS \
    -u DOCKER_TLS_VERIFY -u DOCKER_CERT_PATH \
    docker --host=unix:///var/run/docker.sock compose \
    -p "$ORBITIQ_REHEARSAL_PROJECT" -f deploy/compose.yaml "$@"
}

orbitiq_local_compose config --quiet
orbitiq_local_compose up -d --no-build --pull never --wait --wait-timeout 90
orbitiq_local_compose exec -T web nginx -t
curl --noproxy 127.0.0.1 --fail --max-time 10 http://127.0.0.1:18089/api/health
curl --noproxy 127.0.0.1 --fail --max-time 10 http://127.0.0.1:18089/api/ready
curl --noproxy 127.0.0.1 --fail --max-time 10 http://127.0.0.1:18089/api/readiness
```

The gateway now has an explicit loopback health check through `/api/ready`, so
Compose `--wait` checks both API and gateway. The probe disables proxying only for
its own loopback request. A health check does not itself restart an unhealthy
container; production orchestration/alert policy remains an owner decision.
Minimal readiness returns only ready/unavailable; informational readiness may be
degraded with HTTP 200. Inspect its component codes without weakening EOP policy.

Using IDs actually present in the restored archive, check discovery, both exact
snapshot details, an explicit common-time ITRS comparison and bounded ground track.
Do not insert fixtures or collect new data to satisfy a test. Verify production
Host rejection, absent cross-origin authorization and mutation refusal. Existing
backend production tests cover missing/relative storage, invalid hosts/EOP/bounds,
safe errors and missing-database 503 without creating a file.

```sh
orbitiq_local_compose ps -q api
orbitiq_local_compose restart api
orbitiq_local_compose up -d --no-build --pull never --wait --wait-timeout 90
orbitiq_local_compose up -d --no-build --pull never --force-recreate \
  --wait --wait-timeout 90 api
orbitiq_local_compose ps -q api
```

Check readiness and exact source identities again; replacement must have a new
container ID and unchanged archive content. Allow for a maintenance interruption.
Do not infer zero downtime, host-loss durability or disk reattachment from this.

For local rollback, retain earlier API/web images known to support schema 3, set
`ORBITIQ_RELEASE` to that recorded tag and rerun `up` with
`--no-build --pull never --force-recreate --wait`. Check the same source identities,
then restore the candidate tag and repeat. Do not downgrade the schema or replace
the archive. Phase 8.2 used retained `phase8-local` images and returned to
`phase81-local`; both are local working-tree images, not published releases.

## Local TLS and browser checks

For TLS rehearsal, create a **fresh private test CA and server key** outside Git,
with server SANs `DNS:localhost,IP:127.0.0.1`. Sign a short-lived server certificate
for server authentication. Put only the server certificate/key in an explicitly
traversable test mount directory; keep the CA key private. Check directory modes
after creation: a restrictive umask can turn a requested 0755 directory into 0700,
which Nginx UID 101 cannot traverse. Never relax an unrelated existing directory.

Set `ORBITIQ_TLS_DIRECTORY` to that new mount and
`ORBITIQ_HTTPS_BIND=127.0.0.1:18443`. Add `-f deploy/compose.tls.yaml` to the local
Compose function, validate, and recreate the owned gateway. With the test CA passed
explicitly using curl `--cacert`, verify `/api/ready`, TLS 1.2 and 1.3 and HTTPS-only
HSTS. Verify an untrusted CA and wrong hostname fail certificate validation.
Do not use `-k`, `--insecure` or ignore browser HTTPS errors. HTTP has no HSTS.
There is no public certificate, redirect or renewal evidence in this procedure.

Use the repository's browser runner in the pinned supported image, sharing only
the owned gateway's network namespace:

```sh
export ORBITIQ_REHEARSAL_WEB_CONTAINER="$(orbitiq_local_compose ps -q web)"
install -d -m 0700 "$ORBITIQ_REHEARSAL_DIRECTORY/browser-results"
docker --host=unix:///var/run/docker.sock run --rm \
  --network "container:$ORBITIQ_REHEARSAL_WEB_CONTAINER" \
  --mount "type=bind,src=$PWD/scripts/verify_browser_critical.py,dst=/tests/run.py,readonly" \
  --mount "type=bind,src=$ORBITIQ_REHEARSAL_DIRECTORY/browser-results,dst=/results" \
  orbitiq-browser:phase81 python /tests/run.py \
  --base-url http://127.0.0.1:8080 --engine firefox \
  --catalog 25544 --first 1 --second 2 --output /results/firefox.json
```

The example IDs describe the actual Phase 8.2 two-record ISS archive. Adapt only
to genuine records available in the selected archive. Repeat for `webkit` and
`chromium` with distinct receipts. These tests exercise discovery, source identity,
save/open/reload/share, a backend track sample, common-time comparison, readiness,
mobile/reduced-motion/keyboard reconstruction and missing-source refusal. No API
or canvas mocking occurs. Headless Linux/software graphics and a viewport are not
physical-device, GPU, actual Safari or screen-reader certification.

The separate existing runner
`python scripts/verify_release_containers.py --release phase81-local` creates an
explicit **empty isolated fixture** and cleans it up. Keep that smoke evidence
separate from genuine archive recovery and browser evidence.

## Backup, monitoring, failure and cleanup

Follow the [encrypted backup runbook](backup-restore-runbook.md). A new local
encrypted repository is permissible only as an explicitly labelled test: private
new config/password files, deliberate test-only `restic init`, export CLI
`--allow-local-test`, a new job directory and private receipt. Run
`restic check --read-data`; retention uses `forget --dry-run` only. Test a wrong
password in another job and require a failed receipt/nonzero exit with unchanged
source. Exact-point restore must preserve all snapshot/audit/schema fingerprints
and pass representative restored APIs. **All such local repositories remain on
the same machine and cannot close independent recovery.**

Follow the [monitoring runbook](monitoring-and-alerting.md). A controlled loopback
POST receiver and private URL file can test `--allow-local-test --test-alert`:
first observe without `--deliver`, then deliver once, confirm cooldown suppression,
return HTTP 503 in a distinct test state and confirm exit 2 plus failure cooldown.
Use an unavailable loopback API and actual failed-backup receipt to check outage
signals. Every received payload must have `test=true`, the known schema and no
secrets/raw logs. Capture receiver acceptance separately from any human receipt.
Never substitute this receiver for the intended production delivery mechanism.

Retain bounded structured request events privately for the monitor. Missing log
export and host resource sensors remain production dependencies. Test corrupted
state/redirect/refusal behavior using existing operations tests; do not delete
operator state to bypass cooldown. No monitor/collector/backup scheduler is enabled.

After every success or failure, remove only containers/networks created under the
unique local project and stop only receiver processes this rehearsal started:

```sh
orbitiq_local_compose down --timeout 5
```

Confirm owned containers/networks are absent and loopback ports close. Keep the
private receipt set under an approved retention policy, compare the authoritative
database byte SHA and full fingerprint, and check all earlier reports and existing
changes against the pre-run manifest. No normal database reset, initialization,
collection, EOP download or data switch is part of this exercise.

## Required regressions

Run at the repository root except npm/tsc in `frontend`, preserving command exit
statuses and recording pass/fail/skipped separately:

```sh
uv run --locked pytest -q
PYTHONPATH=backend uv run --locked python scripts/verify_scientific_references.py --output /tmp/sgp4-results.json
PYTHONPATH=backend uv run --locked python scripts/verify_earth_fixed_references.py --output /tmp/earth-fixed-results.json
PYTHONPATH=backend uv run --locked python scripts/verify_phase61_science.py --output /tmp/phase61-results.json
PYTHONPATH=backend uv run --locked python scripts/verify_phase611_geodesy.py --output /tmp/geodesy-results.json
uv run --locked ruff check .
uv run --locked ruff format --check .
```

Frontend: `npm test`, `npm run lint`, `npm run format:check`,
`npx --no-install tsc --noEmit`, `npm run build`. Full backend tests include
ingestion/deduplication/cooldown, migrations/transaction rollback, backup/restore,
production configuration and exact saved-source restoration. Do not count earlier
phase results as new runs. Retain scientific limitations and visible intended use.
