# Historical GP attachment intake

This offline operator workflow prepares for the original Swarm-A attachment.
**No genuine historical GP attachment has arrived.** The user supplied a request
confirmation for catalog 39452, dates 2013-12-30 through 2014-01-02, requested
2026-10-21T06:10:16Z. That confirms the request, not data delivery, authenticity,
historical availability or scientific qualification. Personal details and the
private message are intentionally omitted here. The earlier prepared-request
document and assessment reports remain unchanged as records of their execution.

The new `scripts/inspect_historical_gp.py` does not replace ordinary CelesTrak
ingestion or the earlier ESA qualification tool. Its output is a **private intake
diagnostic**, never an observation package, accepted orbital input or accuracy
report. It cannot be loaded as an operational Swarm adapter.

## Preserve the attachment first

Use an owned, access-controlled filesystem and an explicit private directory.
The repository's existing `data/` exclusion covers the suggested location. Confirm
that exclusion before copying anything. If such storage is unavailable, stop and
arrange private storage; do not put the attachment or correspondence in Git.

From the project root, create a NEW directory once, without `-p` or changing an
existing directory's permissions:

```bash
umask 077
mkdir -m 700 /workspace/OrbitIQ/data/historical-gp-intake
git check-ignore /workspace/OrbitIQ/data/historical-gp-intake/probe
```

`git check-ignore` must identify the ignored path. Preserve the returned original
file unchanged in private storage. Do not paste an email body into a GP file,
hand-edit arrays, invent missing fields or use today's current elements instead.
The source attachment must be a bounded regular file, not a ZIP or symlink.

Optionally create a private metadata JSON file. Supported fields are `provider`,
`acquired_at`, `received_at`, `original_filename`, `format`, and `notes` only.
All default to null and remain operator assertions. For example, it is valid to
begin with just `{"provider":"CelesTrak","format":"GP JSON"}` if independently
supported; omit unknown times. Do not copy that example as authenticated evidence.
Timestamp values require an explicit timezone and at most six fractional digits.
Acquisition cannot be after receipt. `stored_at_utc` is generated separately and
is **never substituted for actual acquisition/receipt or historical publication**.
Include non-sensitive acquisition method or reuse information in private notes;
exclude credentials, tokens, private email bodies and personal contact details.

After the actual attachment arrives, substitute real absolute paths:

```bash
PYTHONPATH=backend uv run --locked python scripts/inspect_historical_gp.py \
  --attachment /absolute/private/original-provider-attachment.json \
  --archive-root /workspace/OrbitIQ/data/historical-gp-intake \
  --metadata /absolute/private/acquisition-metadata.json
```

Omit `--metadata` when none is known. Optional `--expected-sha256` checks an
independently recorded whole-file SHA-256. A self-computed checksum detects byte
changes against its anchor; it does not authenticate the provider.

The root must already exist, be owned by the executing user, and have mode 0700.
Absolute paths with symlink components are refused. File reads are bounded and
reject nonregular files; archive/member writes are exclusive. Existing archives
and sources are never replaced, deleted or chmodded. Each invocation creates a
new random 32-hex directory, mode 0700, containing mode-0600 files:

1. `attachment.original`: exact original bytes, with no JSON normalization.
2. `receipt.json`: whole-file hash, size, input basename, actual storage clock,
   supplied original filename/format/provider/times/notes and explicit unknowns.
3. `inspection.json`: candidate/exclusion diagnostics and blocked gates.
4. `manifest.json`: hashes and sizes of those three members, written **last** as
   the marker that capture and diagnostics completed.

Original bytes and receipt are fsynced before parsing. A failed write or unexpected
inspection error leaves an incomplete private capture for review; do not reuse
it. A manifest can also describe a successfully completed diagnostic of **invalid
JSON**. Manifest presence therefore does not mean that scientific input is valid.
An I/O failure cannot guarantee preservation of a complete copy; retain the
original attachment separately. Hashes and permissions are local integrity and
access controls, not immutable storage or independent backups.

Exit 0 means the capture/diagnostic completed. Read `document_errors`, counts and
every record's reasons before interpreting the result. Its scientific status is
always BLOCKED. Exit 1 means intake was refused or incomplete. Standard output
contains a sanitized hash/count/status summary, not filenames, provenance notes,
record values or private paths. Inspect private reports locally, without pasting
them wholesale into public reports or GitHub.

## Bounded record inspection

The supported attachment forms are one GP JSON object or an array of 1–512
records, in original order. These are explicitly supported intake shapes, not a
claim about the missing attachment's actual structure. Do not unwrap another
envelope automatically. Unknown JSON objects fail required GP fields; non-object
array entries are individually excluded. Top-level scalar values are unsupported.

Budgets are 2 MiB per attachment, 64 KiB per parsed/reserialized record and 16 KiB
for supplied metadata. The reused `replay_json.decoded` adds its existing limits:
32 levels of nesting, 200,000 nodes, 4,096 items per collection and 16,384 characters
per string. JSON syntax/encoding errors, duplicate keys, nonfinite constants and
overflowing float literals refuse the **entire document**, with no partial JSON
salvage. Mixed records in otherwise valid JSON each retain their index and their
individual model/identity/epoch failures. Arrays over 512 are refused, never
truncated. Larger genuine returns require a reviewed limit/selection change;
never split/edit the original and call those bytes the provider attachment.

Every enumerated record retains `source_index` (zero-based, including index 0 for
a single object) and whole-attachment SHA-256. Optional record hashes have the
exact scope **SHA-256 of UTF-8 `json.dumps(parsed_record, sort_keys=True, indent=2,
allow_nan=False)` with default `ensure_ascii=True`, followed by one LF**. These
use the existing `replay.encoded` function. They hash decoded and reserialized
values, with Python's JSON numeric semantics, **not original record substrings**.
Whitespace/key order can differ in the original while those hashes agree. Other
semantically similar representations are not guaranteed to agree. The complete
original attachment remains the byte-level evidence.

All copies with the same parsed-record hash are excluded as duplicates, retaining
all duplicate source indices. Different records sharing an epoch are retained if
otherwise compatible, with an explicit review warning. Neither order nor a nearest
epoch automatically chooses an input. No record is silently dropped.

## Candidate diagnostics and scientific boundary

The workflow reuses `Elements.model_validate`, including its required OMM fields,
finite numerical ranges, SGP4/UTC/TEME/Earth conventions and CelesTrak-defined
omitted invariant defaults. It adds target 39452/designator 2013-067B and exact
UTC epoch text checks. Original epoch text is retained. Nonzero digits beyond
microseconds, leap-second text, unsupported timezone offsets and invalid calendars
are excluded without rounding. Extra trailing zero digits are exactly representable
and do not drop nonzero precision. UTC without a suffix has the existing
CelesTrak GP meaning; this is not a generic timezone-free OMM convention.

The ordinary `parse_response` function accepts exactly one record in an array
and calls propagation for dynamic validation. **This intake tool does not call it
or `Elements.satellite()`**. A model-compatible candidate is not yet dynamically
validated by that parser. No satellite state is constructed during intake.

Diagnostics use an explicit operator scope [2013-12-30T00:00:00Z,
2014-01-03T00:00:00Z), including the whole requested stop calendar date. The
provider's inclusive/exclusive date semantics remain unknown. Out-of-scope records
are retained as exclusions, without declaring provider error. The existing ±7-day
source-epoch bound is checked against the ordinary convertible reference span
2014-01-01T00:02:04Z through 23:57:54Z. Reports show the bounded intersection and
whether both endpoints fit; this is **not actual epoch pairing, quality selection
or evidence of forecast accuracy**. The ±7-day value is the unchanged application
safety bound, not a new numerical tolerance or physical accuracy guarantee.

`CREATION_DATE`, when a string, is retained as an unverified source claim, not an
availability timestamp. Unknown publication/archive times stay unknown. Receipt
now does not prove availability in 2014. Future permitted comparisons remain
retrospective unless a separately reviewed evidence path establishes availability;
this version offers no forecast promotion or approval switch.

Nine gates cover source identity, input structure/numbers, historical selection,
time conversion, frame, lineage/independence, reference quality,
prediction/retrieval configuration and residual authorization. They use existing
PARTIAL/BLOCKED conventions. File presence and successful model checks cannot pass
any scientific gate. Intake cannot issue observations, propagate, temporally pair,
transform coordinates, calculate residuals, quantify uncertainty or produce an
accuracy report. No changes were made to established Phase 11 analysis or synthetic
mathematical tests.

The time gate explicitly refers to the previous and freshly confirmed bounded
audit: **7,647 inspected, 5,118 converted, 1,806 submicrosecond and 723 second-60
excluded (2,529 total)**. These baseline counts are not a new time conversion
performed by intake. The actual qualifier still reports GPS scale, resource hashes,
UTC bounds and endpoint EOP checks; full-source time approval remains incomplete.
SGP4 TEME → Astropy ITRS → ESA **IGb08** still lacks approved realization treatment,
parameters/epoch assumptions and uncertainty budget. No identity approximation,
station correction or Helmert transform was added. Reference quality selection,
source-format discrepancies and lineage/independence also remain unresolved.

## Next review when genuine data arrives

Check private capture completeness, original hash/bytes, provider provenance,
actual receipt, catalog/designator, parser failures, every duplicate/exclusion and
unknown availability field. A candidate list is not permission to evaluate it.
Document a deterministic record/reference-epoch selection rule before examining
errors; preserve original indices and attachment/member hashes. Resolve reference
time anomalies, quality acceptance and IGb08 treatment with authoritative evidence
and independent tests. Then review actual pairing, dynamic validation, resource
configuration and fitting-lineage limits. Only a separately justified scientific
workflow can authorize residual calculation; none is enabled here.
