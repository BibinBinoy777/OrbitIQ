# E4 candidate and diagnostic artifact retention

Policy date: **23 October 2026 (IST)**. This policy covers the existing private
GitHub Actions repository. It does not authorize production deployment, private
data export, a registry push, a GitHub release object, or a new storage account.
See the [closure assessment](engineering-e4-final-closure.md) for actual results.

## Artifact classes

| Artifact                              | Requested retention                     | Classification and purpose                                                                                      | Reproducibility                                                |
| ------------------------------------- | --------------------------------------- | --------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| `backend-verification`                | 90 days                                 | Internal engineering evidence: JUnit, four numerical reference results, fixture installation/recovery summaries | A rerun produces new evidence, not the original test execution |
| `frontend-verification`               | 90 days                                 | Internal engineering evidence: JUnit                                                                            | A rerun produces new evidence                                  |
| `python-advisories`, `npm-advisories` | 90 days                                 | Internal engineering evidence: advisory lookup at this run                                                      | Advisory databases change; do not substitute a later lookup    |
| `frontend-dist`                       | 90 days                                 | Non-sensitive application package, private repository access                                                    | Rebuilding requires new verification                           |
| `release-evidence`                    | 90 days                                 | Compact sealed capture, proxy results, browser/E2 summaries, seven PDFs and paired JSON                         | Hashes and exact commit identify this execution                |
| `retained-candidate`                  | 90 days, explicit manual selection only | Tested API/web image bytes, complete compact evidence and frontend package                                      | Retain these bytes; a rebuild cannot inherit their approval    |
| `fresh-checkout-recovery`             | 7 days                                  | Installation and recovery diagnostics; synthetic fixtures only, no databases                                    | Debugging rerun is possible, with different timing/logs        |
| `browser-pdf-regressions`             | 7 days                                  | Full browser screenshots, trace ZIPs, logs and expected-failure diagnostics                                     | Contains only synthetic application activity                   |
| `release-verification`                | 7 days                                  | Compatibility copy of root release JSON; the full verifiable copy is in `release-evidence`                      | Not the sole long-lived release record                         |

Every artifact upload has explicit `retention-days`. Seven days bounds the larger
routine diagnostic footprint; 90 days provides a longer investigation/review
window for compact evidence and deliberately selected candidate bytes. These are
engineering policies, not an approved production backup RPO/RTO or permanent
production-release retention schedule. No production release exists in this task.

Before this continuation, the authoritative artifact API showed the frontend
package expiring about 90 days after creation, while other E4 artifacts expired
about seven days later. Thus 90-day artifacts are demonstrably supported in this
repository. The repository-wide retention-settings request returns HTTP 403, so
the account maximum and raw Actions log/cache retention remain unverified. Raw job
logs are not the durable release record; bounded diagnostic artifacts and explicit
JUnit/reference/sealed evidence carry the documented retention instead.

After a run, inspect actual `created_at`, `expires_at`, `expired`, digest and size
for each artifact. The server's accepted metadata is authoritative; a workflow
request alone does not establish retention. No artifact is deleted to test expiry,
and no claim is made that a 90-day expiration has already occurred. Observed
90-day expirations are capped at workflow-creation time plus 90 days; later uploads
therefore have slightly less than 90 full days remaining. Use the read-back
`expires_at`, not an assumed upload-time anniversary. GitHub admins
can delete artifacts early; retention is not immutability or independent recovery.
A real production release will need an owner-approved long-term artifact policy,
access controls, capacity/budget and transfer evidence before these artifacts expire.

## Select and verify a candidate

Normal pushes and pull requests keep the three existing jobs and run all existing
checks. They retain compact evidence but **do not export image archives**. Select
a specific published engineering SHA through the existing manual workflow:

```sh
gh workflow run ci.yml --ref engineering-e4-final-closure -f retain_release_images=true
```

Confirm that the resulting run's `head_sha` is the intended commit. The manual run
must pass `backend`, `frontend` and `release-images`, including E1/E2/PDF and E3/E4
checks. Failed or partial evidence never authorizes candidate export. The image
archive/upload steps are optional on ordinary pushes, mandatory on this selected
manual path. The original mandatory checks and failure-diagnostic uploads remain.

The packer first rechecks the E4 seal, current clean committed source, frontend
contents and image identities. It uses `docker image save` on the exact two image
IDs, not a container filesystem: mounted databases and browser fixtures are never
included. It checks configuration digests, source labels and every uncompressed
layer digest against the tested IDs. It then retains:

- `images.tar.gz`: precisely the tested API/web image bytes.
- `evidence/`: the sealed record and every file required by `verify-files`, including
  the PDF/paired-JSON bytes; full screenshots/traces remain shorter-lived diagnostics.
- `frontend/`: the exact frontend artifact, for independent retained verification.
- `candidate.json`: source/image identities and every retained file's SHA256.

Archive verification refuses changed/missing/extra files, unsafe names, links,
config/layer mismatches, incorrect source labels, oversized archives, fabricated
production approval and a wrong expected commit. It never extracts files, loads
images into Docker, starts containers or contacts an application endpoint. The
compressed transfer bound is 512 MiB and uncompressed member bound is 2 GiB; these
are processing limits, not a storage quota or approved cost allowance. A partial
output directory is not a successful candidate and is not uploaded by the normal
success-only candidate step. Existing output paths are refused.

Download to a new directory using repository-authorized access:

```sh
gh run download RUN_ID --name retained-candidate --dir /tmp/new-orbitiq-candidate
python3 scripts/verify_retained_candidate.py verify --directory /tmp/new-orbitiq-candidate --revision EXACT_COMMIT_SHA
```

Successful verification establishes byte/record integrity, not deployment approval,
image security certification or scientific qualification. Records are unsigned
trusted-CI evidence. Replacing both records and hashes, or compromising the builder,
remains outside this check. Before any future image loading/deployment, obtain
separate authorization and validate the target, current advisories, architecture,
protected configuration, storage and all remaining production gates.

## Access, privacy and failure evidence

The repository remains private. Existing repository/Actions access governs artifact
access; no public sharing, permission expansion, registry or new provider is added.
Transfers use the authenticated GitHub CLI/API over HTTPS. This task does not
independently certify GitHub's storage encryption or configure an encryption key.
The workflow changes no account billing settings. Image retention is manual to
avoid multiplying large archives on routine pushes; review existing Actions usage
and quota before repeated selections. No automatic artifact deletion is introduced.

CI uses only a clean checkout, approved public/synthetic test inputs and image
build allowlists. No original GP attachments, private ESA products, email messages,
credentials, `.env`, live SQLite archive or private validation bundle belongs in
any artifact. JUnit and reference outputs are explicit paths, not workspace uploads.
The packer copies only the seal's required files and the known frontend inventory.

The existing `if: always()` uploads still preserve bounded fixture/browser failure
diagnostics when tests fail. Expected-failure probes return nonzero and produce
trace/screenshot diagnostics within the ordinary run. Inspect those downloaded
files and ZIP integrity. This does not claim that a separate deliberately failing
GitHub job or future platform expiration was exercised unless the closure report
records that evidence. Failed/cancelled runs and partial artifacts are not releases.

CI software artifacts are not application-data backups. Gate B still requires an
explicitly approved independent destination and a demonstrated restoration from it.
Phase 11.3.1 remains **PARTIAL**, scientific evaluation **BLOCKED**; these artifacts
provide no genuine Swarm-A residuals or independent-accuracy qualification.
