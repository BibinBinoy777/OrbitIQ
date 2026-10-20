# Reproducible evidence replay (Phase 10)

This operator CLI captures a **new** investigation report and the data needed to
recalculate it locally. It is separate from the Phase 9 browser export. Existing
Phase 9 JSON files cannot supply resources/software identities that were never
recorded. Capture from their exact definition; do not label the new calculation as
the original historical execution.

Install from the checkout with `uv sync --locked`. No additional dependency,
migration, account or running API server is needed. Run commands from the repository
root. Capture requires an existing, explicitly configured database containing the
requested exact references. It does not ingest, initialize, migrate or write storage.
Definitions use the existing [schema-1 investigation contract](investigation-reports.md).
Extract one from an existing report if useful:

```sh
python -c 'import json; from pathlib import Path; r=json.loads(Path("report.json").read_text()); p=Path("definition.json"); f=p.open("x"); json.dump(r["investigation"]["definition"], f); f.close()'
export ORBITIQ_DATABASE_PATH=/absolute/path/to/existing/orbitiq.sqlite3
PYTHONPATH=backend uv run --locked python -m orbitiq.maintenance.replay capture \
  --definition definition.json --directory /absolute/path/to/new-replay-bundle
```

The destination's parent must exist. Capture exclusively creates the new directory
(mode 0700), files (0600), and writes `manifest.json` last. Existing directories,
files and symlink destinations are refused. An interrupted write may leave an
incomplete new directory: retain it for inspection or remove it explicitly; never
reuse it or treat the missing/incomplete manifest as a successful capture.

Retain the returned `manifest_sha256` separately in trusted storage. Verify using
that checksum, the matching trusted source checkout and installed software:

```sh
PYTHONPATH=backend uv run --locked python -m orbitiq.maintenance.replay verify \
  --directory /absolute/path/to/new-replay-bundle \
  --expected-manifest-sha256 YOUR_SEPARATELY_RETAINED_SHA256 \
  --result /absolute/path/to/new-verification-result.json
```

Verification needs no database variable, database file, API server, CelesTrak access,
or downloading of IERS data. `uv run` can still require package installation if the
environment is absent: provision the matching environment before offline use.
No software is installed from a bundle and no bundled code is executed. To audit
network/database attempts in a fresh already-provisioned Python process:

```sh
PYTHONPATH=backend .venv/bin/python scripts/verify_replay_offline.py \
  --directory /absolute/path/to/new-replay-bundle \
  --expected-manifest-sha256 YOUR_SEPARATELY_RETAINED_SHA256
```

This audit removes the database variable and rejects Python socket connection,
resolution/sendto and SQLite connection events before importing replay/science
modules. It reports attempted accesses; it is an application-level audit rather
than an operating-system sandbox. The tests run it in an isolated subprocess.

`--result` is optional. It must be a new absolute path outside the bundle;
existing files/symlinks are refused. Verification never updates the bundle or
ordinary database. Replay bundles are local artifacts: the conventional
`replay-bundles/` directory is ignored by Git. Choose private storage and backup
it independently if it must survive this task environment.

## Bundle contract and identity

The version-1 directory contains:

| File | Meaning |
| --- | --- |
| `manifest.json` | Capture/report IDs, UTC capture and historical policy-evaluation times, identities, settings, tolerances and per-file SHA-256/byte counts |
| `report.json` | Complete new Phase 9 report, including original calculation clocks, limitations and warnings |
| `source-N.json` | Whitelisted immutable snapshot metadata, raw/normalized element records, units and recorded validation provenance |
| `source-N.response.json` | Exact archived CelesTrak response body bytes; one or two sources as applicable |
| `uv.lock` | Exact dependency lock at capture; retained as evidence, never installed automatically |
| `iers-a.all`, `leap-seconds.dat` | Exact applicable EOP/leap resources for terrestrial calculations; absent for TEME/source-only calculations |

Verification rejects missing/unknown files, directory or file symlinks, nonregular
files, traversal filenames, malformed/duplicate-key/nonfinite JSON, incompatible
contracts and bad sizes/hashes. Limits: manifest 128 KiB, each file at most 8 MiB,
total payload at most 24 MiB, raw source 64 KiB, source metadata/leaps 128 KiB,
lock 2 MiB. No ZIP extraction, pickle, public upload endpoint or shell execution
from bundle data is involved. Raw source bytes are revalidated against normalized
elements, units, catalog/epoch/retrieval identities, source URL and report evidence.

Python patch version/implementation, sgp4, Astropy, pyerfa, NumPy,
astropy-iers-data versions, dependency lock hash and every backend Python source
hash must match. Git HEAD/dirty state and OS/machine are descriptive evidence;
backend hashes identify local code even when HEAD alone does not. No claim of
bit-identical library binaries is made. An unrelated backend edit also blocks
version-1 replay: use the matching trusted checkout/environment in a separate
workspace rather than weakening checks or running supplied code. Local captures
from unpublished code require preserving that exact trusted code separately.

Without a separately trusted manifest checksum, verification establishes only
self-consistency. Someone able to replace a whole bundle can replace all its
checksums. Even a pinned checksum is not a provider signature, trustworthy clock,
independent satellite observation, or scientific accuracy certificate.

## Numerical comparison and historical policy

Replay calls the existing backend SGP4/WGS72, Astropy TEME-to-ITRS/WGS84, bounded
sampling, element-difference and common-time state-comparison services. No new
orbital model or frontend calculation is introduced. Comparison covers source
identities, times, frames, units, model/version metadata, state vectors, geodetic
values, all requested track rows and common-time separation/relative speed.
Track sample count/index/time is checked against the definition. Track visual
segments, comparison browsing summaries/chronology and prose are retained under
the file hashes; they are not independently regenerated by numerical replay.

The result projection omits changing execution clocks, freshness presentation and
warnings. Original values remain in the captured report. EOP provenance, flags,
resource hashes and prediction age are compared using the explicit **captured
historical policy-evaluation time**, never the current wall clock. The saved
freshness thresholds and sampling limits are injected locally without changing
environment variables. Copied, verified EOP/leap bytes are loaded for the scoped
calculation; Astropy contexts and the previous ERFA leap table/expiry are restored
on exit, including failure. The normal API still uses its current clock/resources
and measured/predicted policy. Historical replay does not check current EOP
readiness or make an expired prediction usable for a current request.

Fixed absolute tolerances (relative tolerance zero):

| Quantity | Absolute tolerance |
| --- | --- |
| Position, ground position, separation | `1e-8 km` |
| Velocity, relative speed | `1e-10 km/s` |
| Geodetic latitude/longitude | `1e-9 deg` |
| Ellipsoidal altitude | `1e-8 km` |
| Other numbers, metadata, units and flags | Exact |

These are software replay tolerances, **not orbit prediction error bounds**.
Bundles cannot select looser tolerances. Differences are bounded to 20 entries
with a separate total count. A matched report remains calculated from mean
elements; independent observation-based validation is blocked and prediction
uncertainty is unquantified. No maneuver, collision or operational-safety claim
follows from replay.

| Status | Meaning | Exit |
| --- | --- | --- |
| `captured` | A new bundle was written; this is not a replay result | 0 |
| `matched` | Inputs/runtime matched and requested numerical projection agreed | 0 |
| `verified_source_only` | Snapshot evidence, or comparison without common-time states, verified; no orbital-state numerical pass claimed | 0 |
| `mismatch` | Validated inputs/runtime but numerical/provenance projection differed | 2 |
| `unavailable` | Original report calculation unavailable; no numerical pass | 3 |
| `blocked` | Required inputs/resources/runtime invalid, missing or incompatible | 3 |
| `error` | CLI input/configuration/destination failure | 1 |

An unavailable original calculation remains unavailable even if newer software
could calculate it; capture a new explicitly identified report instead. A verifier
failure does not silently substitute a newer snapshot, EOP package or zero vector.

## Phase 10.1 integrity and reliability hardening

The bundle format remains version 1. See the current
[scientific evidence integrity contract](replay-integrity-contract.md) for required
manifest/report fields, JSON depth/node/string budgets, pre-replay scientific
validation and the scoped network/database/process denial policy.

Use `python -m orbitiq.maintenance.replay validate` with the same directory/digest
arguments to obtain an explicit validation-only result; it executes no orbital
replay and exits zero for `status="validated"`. `verify` now includes that validation
result and separates `numerical_outcome="exact_output_reproduction"` from
`"tolerance_agreement"`, `"mismatch"` and `"unverifiable"`. The primary `matched`
status remains compatible; it must be interpreted with the numerical outcome.
Source-only and validation-only operations explicitly report no state replay.
Residual details include units, absolute/meaningful relative differences and
pass/fail. No existing numerical tolerance was changed.

The [Phase 10.1 report](phase-10.1-report.md) records current local evidence,
including the reused published golden reference. The original Phase 10 report and
evidence remain historical and unchanged. Matching-code requirements still apply
when replaying older bundles; new backend hashes are not silently substituted.
