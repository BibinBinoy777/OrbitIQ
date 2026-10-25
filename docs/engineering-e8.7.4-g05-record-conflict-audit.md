# E8.7.4 — G05 record conflict audit and provider clarification

Study `ORBITIQ-IGS-GPS-RETRO-001`. **Scientific study BLOCKED.** This is a direct
source-record audit and preparation of an **unsent** provider inquiry, not an
admission, record selection or scientific calculation.

The [evidence ledger](engineering-e8.7.4-record-conflict-evidence.json) contains
stable local identifiers, exact metadata differences, fragment hashes/source
offsets, equality findings, authoritative source identities and verification.
The [provider draft](engineering-e8.7.4-provider-clarification-draft.md) is addressed
to Dr. T. S. Kelso; it has not been sent. No email account was accessed.

## Original file and direct comparison method

The supplied `sat000035752.xml` and private E8.7.2 capture remain byte-identical:
**10072 bytes**, SHA-256
`c398ecdc707013d0c9bf245b9eeb1894aef1f2a7bafd60f9a687ce797e0a0828`.
The exact original bytes were read again; the audit does not rely on earlier
narrative assertions or a normalized/converted GP export. File modification
timestamp and hash remain unchanged. Actual email receipt time is still unknown.

The original contains ten OMM messages. The audit located each message's exact
byte span, extracted the four relevant original fragments without serialization,
and compared all **23 leaf fields** per message plus attributes, structure and
whitespace. Full raw field values, exact XML leaf lexemes, original offsets and
four original-byte fragments are retained in the ignored private area
`data/e8.7.4-record-conflict-audit/`, with a size/hash manifest.

Complete GP numerical values remain private. The public ledger/draft expose only
the requested identity/epoch/element-set/revolution metadata, hashes and comparison
verdicts. Local identifiers are original-file SHA-256 plus zero-based OMM index;
they are not producer-assigned archive identifiers or historical chronology.

## Exact differences

All four records identify **NORAD 35752**, **OBJECT_ID 2009-043A** and
**NAVSTAR 64 (USA 206)**. The retained dated IGS relationship is **G05 / SVN G050**;
the display name alone is not the identity criterion. `TIME_SYSTEM` is explicitly
UTC. Epoch strings below are unchanged, including all six fractional digits.

| Pair | Original record ordinal / zero-based index | EPOCH source text, UTC       | ELEMENT_SET_NO | REV_AT_EPOCH |
| ---- | ------------------------------------------ | ---------------------------- | -------------- | ------------ |
| A    | 1 / 0                                      | `2023-12-25T21:13:18.902784` | `999`          | `10520`      |
| A    | 2 / 1                                      | `2023-12-25T21:13:18.902784` | `999`          | `10522`      |
| B    | 4 / 3                                      | `2023-12-28T04:47:54.504096` | `999`          | `10524`      |
| B    | 5 / 4                                      | `2023-12-28T04:47:54.504096` | `999`          | `10527`      |

For **both** pairs, the only different field is **REV_AT_EPOCH**. No differing
attributes, other record metadata, numeric lexical representations, ordering or
whitespace were found. Every other original fragment byte is identical after
excluding that field's value for comparison only. This comparison operation was
in memory; no replacement/normalized XML was written over a source.

The exact source-text comparisons include all supplied GP values: MEAN_MOTION,
ECCENTRICITY, INCLINATION, RA_OF_ASC_NODE, ARG_OF_PERICENTER, MEAN_ANOMALY,
BSTAR, MEAN_MOTION_DOT and MEAN_MOTION_DDOT. They match within each pair.
The source identities, EPOCH, ELEMENT_SET_NO, EPHEMERIS_TYPE,
CLASSIFICATION_TYPE and Earth/TEME/UTC/SGP4 declarations also match, as do the
two empty header elements. The private audit preserves **all** source fields,
not just the differing value.

**Established directly:** these are distinct supplied record fragments with a
revolution-value difference; their other text is identical. Both members and
their original indices/hashes remain preserved. **Not established:** why the
producer/archive supplied both, whether they represent distinct archival element
sets, what generation/publication history they have, or whether a particular
member is preferable. Textual equality is not an executed demonstration of
model/physical equivalence. No propagation was used to compare them.

Current CCSDS prose labels REV_AT_EPOCH **Revolution Number**, not a revision
rank. ELEMENT_SET_NO `999` is shared and supplies no distinguishing identifier
here. Do not infer archive chronology, rollover, an export defect, a correction
or a preferred record from the numbers or source order. The cause remains
**UNRESOLVED**, requiring provider-linked evidence rather than assumption.

## Header semantics and authority boundaries

This audit reuses the hash-verified authoritative sources and actual schema
results from [E8.7.3](engineering-e8.7.3-omm-header-semantics.md). Their receipts
record actual 25 October 2026 retrievals; they were **not fetched again** in this
phase. The cached source bytes were reviewed, not merely their prior conclusions.

- **Raw representation:** all ten messages have exactly `<CREATION_DATE/>` and
  `<ORIGINATOR/>`. They are present-empty, without attributes, not absent,
  formal `xsi:nil`, literal `null` or populated values failing lexical validation.
- **Applicable schema:** the exact declared SANA unqualified NDM/XML **2.0.0**
  master and eleven dependencies fix OMM version **2.0**. Common schema lines
  203–210 require both elements; `epochType` at lines 683–688 permits empty
  content, and `xsd:string` imposes no nonempty content rule on ORIGINATOR.
  Neither declaration is nillable. E8.7.3 validated the unchanged complete file
  and all ten individual OMMs successfully. **Those results are reused, not a
  newly executed schema run in E8.7.4.**
- **Prose meanings:** current CCSDS **502.0-B-3** (April 2023, EC1 May 2023),
  section 4.2.2/Table 4-1, marks both mandatory and describes file creation in UTC
  and the creating agency/operator. This is OMM **3.0 prose**, not a replacement
  for the exact version-2 schema. Current **505.0-B-3** (May 2023, EC1 February
  2024, EC2 October 2024) identifies SANA distribution/versioned schema naming.
  Earlier attempts to acquire older 502.0-B-2 prose returned 404; full older-prose
  semantic conformance is not certified. No current schema was silently substituted.
- **Official CelesTrak page:** the retained current GP-format documentation,
  updated **2026 Jun 23**, describes some unavailable TLE fields as blank in KVN
  or “null” in XML, with OBJECT_NAME/OBJECT_ID examples. It does **not explicitly
  explain CREATION_DATE/ORIGINATOR emptiness in this historical export**. Its
  separate JSON/CSV omission guidance is not an XML header waiver. “Null” is not
  a documented instruction to rewrite these tags as `xsi:nil`.

Schema acceptance establishes neither a meaningful UTC creation value nor an
originator identity. Even populated message fields would not alone identify
observation times, element-fit times, complete producer lineage, archive insertion
or historical publication/availability. Message creation and file export are
separate from the generation of the underlying orbital element set.

The earlier user-reported CelesTrak clarification about unretained creation
timestamps is preserved in the [provider reconciliation](phase-11.3.1-provider-response-reconciliation.md).
It is not an independently authenticated G05-specific header explanation.
The draft acknowledges this limitation and asks only for evidence actually
retained; it does not ask the provider to invent unavailable timestamps.

## Prepared questions and evidence still required

The draft supplies the exact original filename/hash, request interval/submission,
NORAD/COSPAR, both epochs, all four revolution values, shared ELEMENT_SET_NO and
local indices. It states that no member has been merged or preferred. It asks:

1. Are the empty headers expected for historical GP XML exports of this kind?
2. What do they mean for creation history and provenance, including message
   originator versus underlying element producer?
3. Is any authoritative creation/originator/source archive record or other
   record-level provenance retained? If unavailable, confirmation of the
   limitation is sufficient; no estimated or reconstructed metadata is requested.
4. What explains these exact same-epoch REV_AT_EPOCH differences?
5. Are the members distinct historical sets/archive entries, and is an additional
   retained identifier or archive metadata available to distinguish them?

No provider clarification was received or inferred by preparing this draft.
Useful evidence would link the explanation and any archive IDs/source records
to these precise pairs and original hash. Reliable receipt/authenticated delivery
could strengthen file-level source evidence but would not by itself prove
record creation, fitting lineage or independence. No private research attachment
was uploaded or automatically attached to a message.

## Current decisions preserved

- The active strict XML inspector, tests and dependencies are unchanged. Its
  recorded active result remains **zero static candidates**, because both
  required header contents are missing. No populated values are reconstructed.
- E8.7.3's **six conditional recommendations, two same-epoch holds and two
  temporal rejections** remain historical results under a **PROPOSED, NOT
  ACTIVATED** policy. No recommendation is promoted into active admission.
- Both members of both pairs remain intact. No merge, discard, revolution-number
  tie-break, residual-based preference, fallback or record selection occurred.
- The original G30 protocol, G05 proposal, original XML/SP3, previous reports,
  private inputs and database remain unchanged. Frame/EOP, physical-point,
  quality/uncertainty, source-dependency, protocol-review and scientific
  authorization requirements remain separate and open.

## Actual verification and changed files

Direct raw-byte/field/attribute comparisons passed for four fragments and both
pairs; all 23 leaf fields and exact XML lexemes are recorded privately. Independent
evidence checks verified the quoted draft values, fragment/source hashes, byte
spans, no extra pair differences, authority/source locators, private manifests,
permissions and Git exclusion. Markdown/JSON formatting, local links, privacy
patterns, whitespace and the complete three-file diff were checked successfully.

No application code changed. XML regression tests and schema validation retain
their **previous E8.7.3 execution results** (83 synthetic XML tests and the exact
schema run); they were **not rerun** here. Full application/frontend/browser/PDF/
build/remote CI checks were not run. No earlier result is described as fresh.

New repository files are exactly this audit report, the provider draft and
`engineering-e8.7.4-record-conflict-evidence.json`. Complete GP fields and exact
original fragments stay in the ignored private audit directory with a preservation
manifest. Four existing worktree branches/HEADs, all prior repository files,
reference hashes and research inputs are preserved. The database was checked
read-only: schema **3**, two snapshots, SHA-256
`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
Nothing was staged, committed, published or deployed; no email was sent. Local
preservation is not demonstrated independent backup/recovery.

**Scientific study BLOCKED. No GP propagation, spacecraft transformation, orbital
interpolation/extrapolation, residual or new uncertainty calculation occurred.**
Swarm-A Phase 11.3.1 remains **PARTIAL**, scientific evaluation **BLOCKED**;
E4 production readiness remains **OPEN**.
