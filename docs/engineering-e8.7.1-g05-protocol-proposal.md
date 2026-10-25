# E8.7.1 — G05 pre-inspection protocol proposal v0.2

Study `ORBITIQ-IGS-GPS-RETRO-001`. **PROPOSED, NOT APPROVED OR EXECUTED.**
Scientific study **BLOCKED**. No requested historical XML has been inspected,
no real record selected and no comparison authorized. This document precedes
inspection of the requested G05 attachment.

This is a candidate-specific successor proposal to the preserved
[G30 protocol v0.1](engineering-e8-comparison-protocol.md), not an amendment
to that file. The [readiness ledger](engineering-e8.7.1-readiness-evidence.json)
pins its original hash, source files, exact interval, safeguards and open gates.
The [readiness report](engineering-e8.7.1-g05-readiness.md) describes implementation
and verification. G30's investigation remains intact.

## Target and justification

Proposed target: **G05 / SVN G050 / NORAD 35752 / COSPAR 2009-043A**, GPS-IIR-M.
The retained IGS satellite metadata identifies G050 at line 1027 and assigns
G05 from `2009:229:00000` to open `0000:000:00000` at line 1634. Earlier G05
assignments belonged to other satellites. The lookup is a nominal-calendar
identity check, not subsecond qualification of assignment boundaries.

[E8.7](engineering-e8.7-alternate-pair-discovery.md) placed G05 first by ascending
PRN among nine alternatives passing the metadata screen. This is administrative
acquisition order, **not superior demonstrated accuracy**. The change is proposed
because G30 delivery is missing and G05 has inspectable reference metadata.
No residual outcome informed this decision.

The only proposed changes from v0.1 are target identity and its corresponding
input/quality/reference-point review. The grid, time conversion, guard, single-GP
policy, ambiguity refusal, claims and authorization gates are retained. G05's
GPS-IIR-M physical-point evidence must be assessed separately from G30 GPS-IIF.

## Frozen reference and exact interval

Use only the already acquired `IGS0OPSFIN_20240010000_01D_15M_ORB.SP3.gz`.
Compressed: 102609 bytes, SHA-256
`26f16fa5f97cce851948fa88711aed47f60ee2e4ddfe36f0e98b1076e79fbe38`.
Expanded: 253250 bytes, SHA-256
`8a638375273ab74011aebd9ffcc480df02b5718440c8fb7c51c408ff220d231c`.
The source is the existing BKG mirror acquisition; this does not authenticate an
unacquired CDDIS copy. Product metadata: SP3-c positions, final, IGS20, GPS time,
position km. G05 has one P record at each of the original 96 epochs.

| Property                       | Predeclared value              | Evidence                                          |
| ------------------------------ | ------------------------------ | ------------------------------------------------- |
| First GPS-calendar epoch       | `2024-01-01T00:00:00.00000000` | Original SP3 header and first epoch               |
| Last GPS-calendar epoch        | `2024-01-01T23:45:00.00000000` | Original final epoch                              |
| First UTC epoch / fixed anchor | `2023-12-31T23:59:42.000000Z`  | Existing E8 exact conversion, preserved v0.1      |
| Last UTC epoch                 | `2024-01-01T23:44:42.000000Z`  | Existing E8 exact conversion, preserved v0.1      |
| Cadence / count                | 900 seconds / 96 epochs        | Header and all source tags; original indices 0–95 |
| Elapsed first-to-last span     | 85500 seconds                  | 95 intervals; no invented following endpoint      |

Reuse E8's split-second Astropy TimeGPS/TAI-to-UTC convention, explicit local
leap/EOP context and version/resource hashes from
[E8.3](engineering-e8.3-frame-eop-evidence.json). The observed 18-second offset
is resource-derived, not a hard-coded conversion. No fresh spacecraft calculation
or time-grid replacement was performed here. Revalidate pinned resources before
any later authorized calculation. IGST clock-reference comments do not change
position epochs or authorize subtracting satellite clock corrections.

## Guard, sampling and selection recovered from existing work

The unchanged engine `propagate` rejects `abs(at - GP_epoch) / 86400 > 7`.
That is an inclusive product safety guard, not an accuracy guarantee.
`inspect_igs_reference.qualify` checks each source epoch separately and fixes
the forward-only anchor at the **first original reference epoch**, even if that
sample has a quality exclusion. Its synthetic seven-day/fixed-anchor test verifies
this behavior. No propagation function was used to derive the present proposal.

For a single proposed GP epoch E and each frozen reference time t_i require:

```text
E <= t_0                         (forward only, including equality)
abs(t_i - E) <= 604800 seconds   (inclusive, separately for every i=0..95)
```

Thus `t_95 - 7 days <= E <= t_0`, yielding exactly:

**`[2023-12-25T23:44:42Z, 2023-12-31T23:59:42Z]`, inclusive.**

The date-only request is `[2023-12-25T00:00:00Z, 2024-01-01T00:00:00Z)`.
Those calendar bounds enclose the eligibility interval; they are not a replacement
for it. A returned record just outside the exact window remains excluded even if
it is inside the requested dates. No timestamp rounding or nearest-epoch repair.

Preserve all 96 original indices. No discretionary subset, clock-derived epoch
shift, interpolation, extrapolation, missing-record filling, GP switching or
selection based on residual size. Missing, invalid, repeated, reversed or
unsupported-precision source epochs are retained with explicit refusal/reasons.
The original v0.1 requires an eligible GP for the entire frozen grid; the E8
helper can expose _partial diagnostic indices_. Those diagnostics do not authorize
a reduced arc. Quality exclusions must be frozen before any future outcome,
retained with source indices and reviewed; they cannot relax the all-epoch guard
or move the anchor. An incomplete/failed gate stays BLOCKED rather than silently
dropping samples. No sampling-rule conflict was resolved by changing code.

Future intake/review order, not executed in this phase:

1. Preserve the complete original provider response byte-for-byte, receipt/source
   assertions and original-file hash; do not accept an edited export.
2. Inspect every returned record using the supported OMM profile, exact timestamps
   and required finite fields. Verify numeric NORAD 35752 first and COSPAR
   2009-043A as an independent consistency check. OBJECT_NAME is a required label,
   not an exact display-name match. Review dated PRN/SVN mapping externally;
   neither is inferred from a name. Mixed/wrong-object content requires review.
3. Separate element epoch, OMM message creation, provider publication and historical
   availability. Receipt or epoch alone establishes neither publication nor
   availability. Missing lineage is not silently invented. The approved claim
   remains retrospective product disagreement, not historical forecasting.
4. After identity, static-field and provenance qualification, rank eligible records
   by decreasing epoch. Propose the latest **unique** eligible record for review.
   Zero eligible records means BLOCKED. Repeated identical or competing records
   at the latest eligible epoch block selection, with no fallback. Source order,
   element-set/revolution number and residual size are not tie-breakers.
5. Freeze one original record/index, original and derived hashes, exact fields,
   provenance, source grids/resources and mask only after the prerequisites and
   independent protocol review. Explicit scientific authorization is still required.

The requested file may contain zero, one or multiple records. None is chosen
here. The inspector's `static_candidate` and `latest_unique_static_candidate_index`
are pre-provenance diagnostics, **not a scientifically selected/eligible input**.
They may coexist with whole-response identity/metadata issues requiring refusal
at review. `selected_source_index` stays null and comparison remains BLOCKED.

## Scientific qualification and claims

The proposed path remains existing WGS72 SGP4/TEME at nominal UTC, followed by
reviewed same-instant Astropy ITRS and IGS20/physical-point alignment. It is a
specification, not an executed or validated transformation. ITRS's class name
does not establish an IGS20 realization. EOP coverage does not settle product-era
ERP/subdaily conventions. No station Helmert or antenna offsets are applied.

G05 quality fields are assessed from G05's own records in the readiness report.
Do not inherit G30 statistic interpretations or uncertainty. Historical antenna/
attitude processing and the future GP fitted physical point remain unqualified.
No GP covariance, full cross-provider covariance or statistical independence is
established. A reviewed uncertainty/claims policy is required; absence of a
covariance does not authorize an invented one or an independent-accuracy claim.

Permitted future interpretation remains **retrospective disagreement between two
estimated orbit products**, with any exclusions and limitations stated. No
forecasting-accuracy, truth, anomaly, collision or operational-safety claim is
authorized. No numerical scientific threshold, normalized residual, covariance,
confidence interval or new uncertainty estimate is introduced. The v0.1 future
reference-minus-calculated sign remains specification only, not a computed result.

This proposal authorizes **no attachment inspection or scientific computation**.
The [13-row readiness matrix](engineering-e8.7.1-readiness-evidence.json) records
the next evidence for every partial/blocked qualification. Study **BLOCKED**;
Swarm-A Phase 11.3.1 **PARTIAL**, evaluation **BLOCKED**; E4 **OPEN**.
