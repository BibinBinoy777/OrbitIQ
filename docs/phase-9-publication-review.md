# Phase 9 publication gate review

20 October 2026 UTC. **Pre-publication snapshot retained for audit.** At this
checkpoint the reviewed work was ready for authorized feature-branch publication;
no commit or push had been performed. The later authorization, publication and
exact-commit CI results are recorded in the [publication status](phase-9-publication-status.md).
The original allowlist/hash evidence applies to implementation commit
`9e57de16eb83a7b394d934641a29c7f97d458af8`; subsequent tracking updates are separate.

## Branch, scope and preservation

Local branch: `main`. Local HEAD and GitHub `main` both remain
`341812ae66409691e9cf07b15e50dba3ab894e26`.
The repository is private; `origin` points to `BibinBinoy777/OrbitIQ` over HTTPS.
The proposed local/remote branch `phase-9-investigation-reports` was absent at review.
Recheck these facts immediately before publication.

The initial review covered all **31** Phase 9 paths: 11 modified tracked files and
20 new files. The full 221-file implementation manifest matched its recorded hashes
at review start. No unrelated changes or deletions were found. The README correction
removes an obsolete claim that Phase 6 was unpublished; the published baseline
already includes it. No prior Phase 0–8 report was edited.

The diff adds the bounded report API/model/service, report capture/download/print
UI, integration into existing and saved/read-only contexts, targeted API/admission
and frontend tests, browser/PDF verification scripts, schema/example and guides.
Existing API admission and gateway rate limiting include the new route. JSON and
HTML use one capture. Browser-only titles/notes/IDs remain excluded. Scientific
calculation services, reference tolerances, storage/ingestion, migrations,
dependencies/lockfiles, ignore rules, container definitions and CI workflow are
unchanged. No database or private-key files are included. Review and credential
signature checks found no credentials in the proposed changes.

The normal archive retains its recorded byte hash and complete schema/table
fingerprints; historical records were not written or migrated. The schema matches
the backend model, the example validates against that model, and all four frontend
report fixtures equal their retained actual API captures.

## Finding resolved during review

Running the read-only-view test alone failed: its synchronous heading assertion
depended on an earlier test having loaded the lazy report module. The test now
uses `await screen.findByRole(...)`. Its no-save, no-share and no-storage-write
assertions remain. The isolated case now passes, and the full frontend suite,
lint/format/type checks and build were rerun after the correction. No application
behavior was changed or disabled; no tests were removed or marked skip/only/xfail.

After that correction, 220 of the original 221 manifest inputs remain identical;
the sole changed input is `frontend/src/SavedInvestigations.test.tsx`. The initial
implementation evidence is retained as historical evidence. This review adds two
tracking files and a link in the Phase 9 report, bringing the proposed publication
set to **33 files**. Their exact allowlist and final hashes are in
[publication evidence](phase-9-publication-evidence.json).

## Local verification

| Check | Review result |
| --- | --- |
| Backend full suite | 675 passed in the workspace and again in a new isolated locked Python environment |
| Frontend full suite | 307 passed after the test correction, in the workspace and isolated fresh-install copy |
| Isolated read-only-view case | 1 passed after correction; the other 8 cases were excluded by the test-name filter |
| Lint / formatting / type checking / production build | Ruff, ESLint, Prettier, TypeScript and Vite passed |
| Clean dependency installation | `uv sync --locked --no-managed-python` and `npm ci --strict-ssl=true` passed in separate temporary directories |
| Scientific audits | 40 SGP4, 6 terrestrial, 32 expanded comparisons, 28 independent geodetic cases and 28 round trips passed |
| CI migration/backup selection | 5 passed, 57 deselected; isolated test databases only |
| Retained PDFs | All 7 passed fresh content/page-counter checks, including every maximum-track row and exclusion of application UI/private-note marker |
| Retained browser evidence | Three-engine 14 report cases and 21 regression cases match the original records; not newly executed during this review |
| Retained release images | API/web/browser image IDs match the recorded implementation evidence; no new container build/run claimed here |

Existing warnings remain: Starlette/httpx TestClient deprecation, a transitive npm
deprecation and the Three.js chunk-size advisory. The 361-point detailed report is
72 pages at tested defaults. Native Firefox/WebKit PDF dialogs, physical printers,
independent observation-based accuracy and exact historical replay remain outside
the verified scope. These are documented limitations, not newly verified features.

## Existing CI review

`.github/workflows/ci.yml` is active and unchanged. Unfiltered `push` and
`pull_request` events are configured; a feature-branch push should start
**OrbitIQ checks**. Scheduling and success must be observed for the new SHA.

| Expected job | What it verifies |
| --- | --- |
| `backend` | Python 3.12, uv 0.12.23, locked dependencies with dev group, full pytest suite, four scientific audit scripts, isolated migration/backup tests, Ruff check/format |
| `frontend` | Node 24, `npm ci`, full Vitest suite, ESLint, Prettier, TypeScript/Vite build and `frontend-dist` artifact |
| `release-images` | Locked API/web image builds, nginx configuration and local loopback smoke checks against a separately initialized empty schema-3 fixture |

The tests use temporary databases and committed fixtures; CI needs no production
database, CelesTrak ingestion or provider secrets. The smoke runner supplies its own
explicit test configuration and refuses normal archive targets. Migrations execute
only in tests; there is no deployment migration or automatic archive initialization.
Workflow token permissions are `contents: read`; there is no registry publication,
production deployment, DNS change or secret reference in this workflow. Public
package/registry downloads still need to succeed on the remote runner. Clean local
installs provide evidence without proving remote availability.

Full Playwright report/regression flows and PDF checks are **not** run by this
workflow. Their matched local evidence is kept separate. No redundant workflow or
CI bypass was added. The three job names above are expected checks, not a verified
required-check configuration.

## Remote evidence and authorization boundary

Read-only GitHub queries reconfirmed all three checks succeeded for the **old**
baseline SHA in [run 39377033436](https://github.com/BibinBinoy777/OrbitIQ/actions/runs/39377033436).
That run provides no Phase 9 remote verification.

GitHub's `main` branch summary reports `protected: false`. Detailed protection
access returned HTTP 403, `Resource not accessible by integration`. The branch-rules
endpoint also returned HTTP 403 and an upgrade/public-repository message. Required
checks/rules cannot be certified from these responses. No protection, plan or
repository-visibility changes were made or proposed as part of publication.

| Milestone | Current evidence |
| --- | --- |
| Locally verified | PASS for the reviewed implementation plus test-only correction |
| Phase 9 committed / published | NOT STARTED; explicit authorization required |
| Phase 9 remote CI verified | NOT RUN; no published Phase 9 SHA exists |
| Production deployed | Not performed or established by this task |
| Production infrastructure verified | Not established; Phase 8 gates remain separate |

Phase 8 hosting/public HTTPS, independent off-machine recovery and real production
monitoring/alert delivery remain unverified. Local backup/recovery is not evidence
of host-loss recovery. The Phase 8 baseline publication/CI milestone is verified for
the SHA above; the newer Phase 9 publication/CI milestone remains pending. Branch
protection/required checks remain an open gate. OrbitIQ is not declared ready for
public launch.

## Exact proposed publication actions — authorization required

1. Recheck HEAD, remote branch state and the final content hashes/allowlist. Stop
   to investigate any new change, remote divergence or occupied branch name.
2. Create `phase-9-investigation-reports` from the reviewed local `main` baseline:
   `git switch -c phase-9-investigation-reports`.
3. Stage **only** the 33 paths in `publication_allowlist` in the linked evidence;
   review the staged diff and run `git diff --cached --check`.
4. Create one commit titled
   `Add Phase 9 investigation reports and evidence export`.
5. Publish that branch using
   `git push --set-upstream origin phase-9-investigation-reports`.
6. Record the actual local commit SHA and confirm the remote branch points to it.
   Locate the automatically triggered workflow using that exact SHA. Verify
   `backend`, `frontend` and `release-images` each completed successfully; missing,
   skipped, pending or failed checks are not success. Investigate Phase 9 failures
   and rerun affected checks after corrections, recording each resulting SHA.
   Recheck available protection evidence and report any continuing access limits.

This proposal authorizes no direct push to `main`, merge, force-push, workflow
dispatch, visibility/settings change, deployment, DNS action or production operation.
Those actions are outside the requested publication plan. No Git mutation from the
plan has been executed. Approval is needed because the user's publication gate
explicitly prohibits committing and pushing without authorization.
