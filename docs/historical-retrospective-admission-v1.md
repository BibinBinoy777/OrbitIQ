# historical-retrospective-admission-v1

Version **1**, activated by the user's explicit E8.7.6 authorization on
**2026-10-25**. Status: **ACTIVE FOR EXPLICIT SELECTION ONLY**. Purpose: admit
otherwise valid records from two exact original artifacts for **further scientific
qualification**, with **PARTIAL provenance**. This policy authorizes no scientific
comparison, record selection, transformation, propagation or residual calculation.

The immutable [machine definition](../config/historical-retrospective-admission-v1.json)
is SHA-256 `617b281feaa8a8e53338d2bbe7ea8144fca96c4d201c245686b1ef3ac84002d4`.
The [XML inspector](../scripts/inspect_historical_xml.py) checks that fingerprint
before applying the definition. The [E8.7.6 ledger](engineering-e8.7.6-retrospective-admission-evidence.json)
records execution against both artifacts, source/code/definition hashes and
private versioned activation/result captures.

## Exact scope and evidence

| Target                  | Original SHA-256                                                   | Bytes / records | Bound acquisition evidence |
| ----------------------- | ------------------------------------------------------------------ | --------------- | -------------------------- |
| G05 / 35752 / 2009-043A | `c398ecdc707013d0c9bf245b9eeb1894aef1f2a7bafd60f9a687ce797e0a0828` | 10072 / 10      | E8.7.2 intake ledger       |
| G30 / 39533 / 2014-008A | `34ccec7bd8fd4be88346e03787027a5ecc71a6d75db75668bd4c641fcd713da5` | 11057 / 11      | E8.7.5 intake ledger       |

The definition binds the identity, size, count and acquisition-ledger path/size/hash
for each file. Those immutable evidence snapshots record the user-reported
CelesTrak requests and fulfillments, actual local captures and verification limits.
They do not provide independent email authentication, exact email receipt time,
historical publication/availability or complete fitting lineage. The policy
preserves those limits in every applied report. Provider attribution is not
upgraded to authenticated merely by admission.

No other hash, satellite, provider or future export is authorized. There is no
CLI policy-file override, environment bypass or automatic allowlist extension.
Changing a byte changes the hash and refuses the exception. Missing/mismatched
acquisition evidence, wrong target/record identity, mixed content, malformed XML,
unexpected record count or size also refuses artifact authorization. Definition
failure fails closed; strict inspection remains available independently.

## Reason for the exception

The provider supplied these historical artifacts with `<CREATION_DATE/>` and
`<ORIGINATOR/>` present-empty. E8.7.3/E8.7.5 establish that the exact declared
schema accepts that representation, while the strict intake requires populated
values. CelesTrak's generic unavailable-field guidance does not specifically
explain these headers. This is an explicit **OrbitIQ risk-management decision**,
not a claim of complete OMM semantic compliance or recovered provenance.

Earlier strict-policy rejections and the earlier G05 proposal remain accurate,
unaltered historical records. This version applies to both authorized artifacts
under fresh execution; it does not silently extend the G05-only proposal to G30.
The original G30 and G05 comparison protocols are unchanged.

## Executed rules

1. Run the existing bounded, safe OMM parser and all strict checks first. Retain
   their outcomes and errors. Compute the original-byte SHA-256; require an exact
   allowlisted artifact, size, expected count, requested NORAD/COSPAR and bound
   acquisition-evidence integrity.
2. Retain existing required GP fields, finite numeric/model/declaration checks,
   identity requirements, explicit units validation and exact source epochs.
   The only exception is **both header fields present-empty**, with no nil
   attributes or other missing/invalid fields. Other blank optional header values,
   malformed populated timestamps, missing elements or numeric failures are not waived.
3. Preserve creation/originator source text unchanged. Classify the empty content
   as **PARTIAL — PROVIDER-EXPORTED MESSAGE PROVENANCE UNAVAILABLE**, never PASS.
   Creation, publication and historical-availability timestamps remain null.
   A record with legitimately valid populated headers would retain its strict
   validation result; the two approved original artifacts have empty headers.
4. Require the unchanged request calendar and exact UTC epoch precision. Evaluate
   the inclusive seven-day guard at **all 96 original reference instants**,
   UTC `2023-12-31T23:59:42Z` through `2024-01-01T23:44:42Z`, cadence 900 seconds.
   Forward-only uses the first original reference epoch. The resulting inclusive
   GP window stays `[2023-12-25T23:44:42Z, 2023-12-31T23:59:42Z]`. Time-grid
   construction is static timestamp arithmetic, not orbital interpolation.
5. Reject other validation or temporal failures. Otherwise put every record
   affected by an unresolved exact duplicate or same-epoch conflict on **HOLD**.
   Out-of-window members remain **REJECTED**, even if also in a conflict pair.
   Preserve both flags and all records. Do not merge, delete, use revolution/source
   order as a tie-break or fall back after an ambiguity.
6. Admit the remaining records as
   `ADMITTED_FOR_FURTHER_SCIENTIFIC_QUALIFICATION`, provenance PARTIAL.
   Do not choose a latest admitted record or evaluate expected/actual residuals.
   The original later single-record/latest-unique comparison-selection protocol
   remains a separate stage requiring its qualifications and authorization.

## Explicit use and result contract

Strict behavior remains the default, now explicitly labelled
`strict-historical-omm-v1`. That ID labels existing behavior; it does not rewrite
the historical reports or claim they previously carried this ID.

```sh
PYTHONPATH=backend uv run --locked python scripts/inspect_historical_xml.py \
  --attachment /absolute/private/path/original.xml \
  --archive-root /absolute/private/path/new-mode-0700-archive \
  --norad-id 35752 \
  --admission-policy historical-retrospective-admission-v1
```

Use `--norad-id 39533` for G30; omitting it retains the original 39533 default.
Only the two exact files above can be authorized. Existing absolute-path,
no-symlink, bounded-read, exclusive-capture and hash/manifest protections remain.
`--expected-sha256` optionally verifies original integrity before capture; it
cannot add a hash to the policy. Synthetic labeling also cannot authorize a hash.

Reports retain legacy strict `counts.static_candidates`, per-record
`static_candidate`, errors and selected-index fields. They additionally record:

- Explicit `admission_policy_id`, strict-policy ID, version, definition fingerprint
  and whether artifact authorization/APPLIED succeeded or REFUSED.
- Each record's `strict_policy_outcome` and separate `retrospective_admission`
  disposition, reasons, provenance/metadata status and all-epoch guard results.
- Retrospective admitted/held/rejected counts and the acquisition-evidence witness.

CLI summaries expose the IDs/version/fingerprint, policy refusals and admission
counts, without raw GP values. Exit 1 indicates document/intake/artifact-policy
refusal; exit 0 means processing completed, potentially with HOLD/REJECTED records.
Neither exit code is scientific authorization. Strict mode's prior exit behavior
is preserved. Every new capture is separate; old findings are never overwritten.

## Stages and limitations

Verification of original hash, XML/identity and static checks precedes policy
application. Admission then permits further qualification only. All reports keep
scientific status **BLOCKED**, qualified count **0**, selected source index
**null** and comparison authorization **false**. There is no approval switch.

Frame/datum and TEME/terrestrial/EOP compatibility, spacecraft physical point,
quality/uncertainty, historical creation/full fit lineage, source dependencies,
independence, G05 conflict explanation and final protocol review remain open.
Do not claim forecasting accuracy, independent validation, absolute truth,
collision/anomaly or operational safety. Missing data are not reconstructed.

Future extension requires new evidence, scope/risk review, explicit authorization,
a new policy version/fingerprint and tests. V1 must not be silently edited to
accept additional artifacts or loosen time/identity/ambiguity rules. Raw private
research data stay outside Git, build contexts and routine CI.
