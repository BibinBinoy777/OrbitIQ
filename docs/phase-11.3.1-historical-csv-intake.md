# Phase 11.3.1 — historical GP CSV intake

**22 October 2026 format decision:** the user-reported CelesTrak response confirms
CSV as supported and preferred. The existing validated CSV adapter is the format
path for this investigation; a corrected JSON export is no longer a prerequisite.
The original JSON remains invalid and unchanged; no provider fix is claimed.
This format decision does not authorize operational ingestion or scientific
evaluation. See the [provider response reconciliation](phase-11.3.1-provider-response-reconciliation.md)
for availability, identifier and independence limits. The recorded implementation
and execution evidence below remains the 21 October checkpoint.

The 21 October 2026 checkpoint supports the actual privately preserved
`sat000039452.csv` as a separate **CSV** source. It contains three Swarm-A records,
17 columns per record, comma delimiters, CRLF endings and no quoted fields in the
received file. There are no missing source cells or additional provider metadata
columns. This is not corrected JSON, an operational importer, or a scientific
accuracy evaluation. Phase 11.3.1 remains **PARTIAL**.

The user attributes this export to the CelesTrak fulfillment. Email headers and
independent sender authentication were not supplied. Actual receipt/acquisition
times and historical publication/availability remain unknown. Local storage and
qualification clocks are recorded separately and do not substitute for them.
Original attachments, correspondence and source-derived diagnostics remain in
Git-ignored private storage. Do not paste private reports wholesale into GitHub.

## Verified source mapping

Column names are mapped by name; the received order is retained in the `header`
list, with original cell strings keyed by column name. A reordered header with
exactly the same 17 unique
names is supported. Unknown, missing or duplicate columns refuse the document;
there is no guessed mapping, delimiter sniffing or alternative-provider envelope.

| Source header | Existing `Elements` attribute | Input interpretation / units |
| --- | --- | --- |
| `OBJECT_NAME` | `name` | Text, bounded by the existing model |
| `OBJECT_ID` | `object_id` | Text; target `2013-067B` |
| `EPOCH` | `epoch` | Exact ISO calendar; UTC by CelesTrak GP convention |
| `MEAN_MOTION` | `mean_motion` | Finite number, rev/day |
| `ECCENTRICITY` | `eccentricity` | Finite number, dimensionless |
| `INCLINATION` | `inclination` | Finite number, degrees |
| `RA_OF_ASC_NODE` | `raan` | Finite number, degrees |
| `ARG_OF_PERICENTER` | `argument` | Finite number, degrees |
| `MEAN_ANOMALY` | `anomaly` | Finite number, degrees |
| `EPHEMERIS_TYPE` | `ephemeris_type` | Unsigned integer; supported value 0 |
| `CLASSIFICATION_TYPE` | `classification` | Text; supported value U |
| `NORAD_CAT_ID` | `catalog_id` | Unsigned integer; target 39452 |
| `ELEMENT_SET_NO` | `element_set` | Nonnegative integer |
| `REV_AT_EPOCH` | `revolution` | Nonnegative integer, revolutions |
| `BSTAR` | `bstar` | Finite number, inverse Earth radii |
| `MEAN_MOTION_DOT` | `ndot` | Finite number, source GP rev/day² convention |
| `MEAN_MOTION_DDOT` | `nddot` | Finite number, source GP rev/day³ convention |

The existing model supplies CelesTrak's omitted EARTH / TEME / UTC / SGP4
conventions. These four defaults are explicitly labelled as **model conventions,
not CSV columns or independently supplied source metadata**. No orbital values are
filled in. This intake does not call `Elements.satellite()` or the normal
one-record ingestion parser, which performs dynamic validation at epoch.

## Parsing and exclusion rules

`scripts/inspect_historical_csv.py` is an operator-only adapter beside the existing
GP inspector. It uses Python's CSV parser with explicit comma/quote rules, UTF-8
(optional BOM), and a quote-structure check that rejects stray/unclosed quotes.
Quoted commas, escaped quotes and quoted newlines are supported. No source bytes
are rewritten. The existing strict JSON decoder and its tests remain unchanged.

Limits are 2 MiB per attachment, 512 source rows and 4,096 characters per cell;
Python's CSV reader may also refuse an oversized field before the cell check.
The existing 64 KiB typed-record budget applies before model validation. Blank
rows, wrong widths and invalid cells are retained as indexed exclusions. An
invalid document or exhausted row budget refuses use of the whole document;
any enumerated prefix is diagnostic only, with unenumerated rows explicitly
reported on budget exhaustion. Raw originals remain the complete evidence even
when malformed-cell previews must be bounded. Nothing is silently salvaged.

All cells are required. Empty values, surrounding whitespace and unsupported
numeric placeholders are not replaced. Numeric columns accept leading decimal
points and `e`/`E`, including `.0003955`; integer columns require ASCII digits.
Decimal parsing checks the source value before conversion to the existing model's
binary floating type. Nonfinite/overflow and nonzero-to-zero underflow are
excluded. The adapter introduces no decimal quantization, matching tolerance or
rounding rule. Ordinary binary floating representation is used only for static
model validation; exact reconciliation uses Decimal values from original cell
strings, including digits that model floats cannot distinguish.

Every enumerated row retains its zero-based index, physical ending line, source
field count, original decoded field strings, attachment hash and validation
reasons. The complete CSV preserves quoting, byte-level spelling and line endings.
Typed-record hashes inherited from JSON inspection identify a reserialized model
input view, **not original row bytes or exact semantic duplicate identity**.
CSV duplicate detection instead compares exact Decimal/text fields: all copies
are excluded. All same-target/same-exact-epoch candidates with competing records
are also excluded for review, rather than selecting the first or closest record.

Epoch checks reuse the existing exact calendar validator. Nonzero precision
beyond microseconds, invalid/leap-second calendars and non-UTC offsets are
excluded, never rounded. Extra trailing zero fraction digits are exactly
representable. The explicit request interval is 2013-12-30 inclusive to
2014-01-03 exclusive UTC; provider date-boundary semantics remain unknown.
The unchanged ±7-day bound is a software safety diagnostic, not an accuracy claim.
No record/reference pair is approved by source order or nearest epoch.

## Private workflow

Run from the repository root after the documented locked installation. Use
absolute input/output paths without symlinks. Keep the original upload separately;
the tool appends an exclusive new mode-0700 capture with mode-0600 files and a
manifest written last. Existing captures are never replaced. An incomplete
capture remains for review after failure. Hashes and permissions provide local
integrity/access controls, not off-machine backup or immutable storage.

```sh
# Create a NEW private capture root, or use an existing owned mode-0700 root.
mkdir -m 700 /absolute/private/csv-captures
PYTHONPATH=backend uv run --locked python scripts/inspect_historical_csv.py \
  --attachment /absolute/private/sat000039452.csv \
  --archive-root /absolute/private/csv-captures \
  --expected-sha256 2b5712d5c2fe3fd6f8106633cb84780d6562eb455f49922fbbbbe9d09a26f1c4 \
  --metadata /absolute/private/csv-metadata.json
```

`--metadata` is optional. Its JSON object uses only the existing `provider`,
`original_filename`, `format`, `received_at`, `acquired_at`, `notes` keys. Unknown
values are omitted or null; do not invent a receipt time. Provider statements
remain operator-supplied assertions even when populated. The capture writes
original bytes and receipt claims before validation, followed by `inspection.json`
and `manifest.json`; the shared capture tool and CSV adapter each record their
own hashes. Exit 0 means diagnostic/capture completion, including completed
inspection of invalid input. Inspect errors/counts/reasons privately. Exit 1
means refusal or incomplete capture. Neither exit code authorizes evaluation.

Explicit reconciliation reuses `scripts/reconcile_historical_gp.py`'s existing
Python interface. Supply all three independent hash anchors and the CSV format;
never serialize CSV into a fake replacement provider JSON file:

```python
from pathlib import Path
import runpy
from orbitiq import replay

# Set these absolute private paths and independently reviewed expected hashes.
original_path = Path("/absolute/private/original-json/attachment.original")
assessment_path = Path("/absolute/private/format-diagnostic.json")
csv_path = Path("/absolute/private/original-csv/attachment.original")
output_path = Path("/absolute/private/NEW-reconciliation.json")
tool = runpy.run_path("scripts/reconcile_historical_gp.py")
reader = tool["INTAKE"]["read_input"]
report = tool["reconcile"](
    reader(original_path, 2 * 1024 * 1024),
    reader(assessment_path, 65536),
    reader(csv_path, 2 * 1024 * 1024),
    original_sha256="c55dc4cbb2331a162014833a1a354e6f62ff4572d5238954b8108f69cae3053c",
    assessment_sha256="620e9545fd4820709a3ecfff101e3705f4a70fbde2ae91de6f48dd5e7c0c8575",
    replacement_sha256="2b5712d5c2fe3fd6f8106633cb84780d6562eb455f49922fbbbbe9d09a26f1c4",
    replacement_format="csv",
    # Optionally supply reviewed original_provenance/replacement_provenance
    # using the same metadata keys. Omitted metadata stays explicitly unknown.
)
with replay.directory(output_path.parent) as fd:
    replay.write_file(fd, output_path.name, replay.encoded(report))
```

Run that operator example with `PYTHONPATH=backend uv run --locked python`.
It requires an existing private output directory and an unused output filename.
Reconciliation only replays the previous hash-pinned nine-token syntax ledger
**in memory for comparison**. Each insertion is checked outside strings, at its
original offsets, for equal Decimal value, and against the recorded probe hash.
No repaired GP payload is saved, returned as operational input or propagated.
The original's strict JSON status remains invalid.

The qualifier now accepts an explicitly separate CSV path:

```sh
PYTHONPATH=backend uv run --locked python scripts/qualify_swarm_inputs.py \
  --kinematic /absolute/private/SW_OPER_SP3AKIN_2__20131231T235944_20140101T235944_0201.ZIP \
  --validation /absolute/private/SW_OPER_SP3AVAL_2__20131231T235944_20140101T235944_0201.ZIP \
  --kinematic-sha256 a62164ca7940d415d63a81518a974422d7868b285abc2509423bac96bd9048b3 \
  --validation-sha256 e258ea6afb9bc998e406c5d2f7a26369d716d958da7d2961eb273b645adfeca2 \
  --gp-csv /absolute/private/sat000039452.csv \
  --csv-sha256 2b5712d5c2fe3fd6f8106633cb84780d6562eb455f49922fbbbbe9d09a26f1c4 \
  --csv-metadata /absolute/private/csv-metadata.json \
  --output /absolute/private/NEW-qualification.json
```

CSV/hash arguments are paired; JSON and CSV inputs are mutually exclusive.
`--csv-metadata` is optional and requires CSV input. Qualification output is
exclusive mode 0600, never an overwrite. CSV uses static inspection and bypasses
the older single-JSON-record dynamic diagnostic. Exit 0 means the audit ran;
scientific status remains BLOCKED. Existing JSON behavior is retained.

## Actual reconciliation and scientific boundary

The private audit found **three candidates, zero exclusions, 51 equal values**
(39 numeric and 12 text). Original indices and order match. Six original/CSV
numeric token differences are solely exponent-letter case. No source precision
changes or unexplained differences were found. Three JSON-integer-to-CSV-Decimal
comparison-type differences for `MEAN_MOTION_DDOT` are labelled separately from
source text/precision changes. No tolerance was used. Missing metadata and
asserted metadata differences are retained; content equality authenticates
neither source nor historical availability.

Ten independent gates cover identity, structure, numerical/model checks,
historical selection, temporal pairing, time, frame, quality, provenance and
independence, and operational evaluation. Only structure and static model checks
PASS. Labels agree but authentication is incomplete. All three candidate epochs
fit the ±7-day constraint across the freshly audited ordinary ESA interval;
that interval is not an approved quality/temporal selection.

The fresh ESA audit retains **5,118 converted / 2,529 excluded** timestamps
(1,806 submicrosecond and 723 second-60 encodings), without rounding. Full-source
time qualification, format/interval documentation discrepancies, IGb08 alignment,
per-epoch reference quality, historical selection/availability and actual-pair
fitting lineage/independence remain unresolved. No identity/Helmert approximation,
quality threshold or operational adapter is introduced. Predictions remain zero,
residuals null and normalized observations empty for genuine Swarm-A evidence.
See the [completion report](phase-11.3.1-csv-intake-report.md) for executed checks.
