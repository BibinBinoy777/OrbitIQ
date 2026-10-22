# Swarm-A retrospective comparison protocol — version 1

Predeclared on **22 October 2026**, before any genuine Swarm-A residuals.
Status: **PREDECLARED BUT NOT YET EXECUTABLE for scientific evaluation**.
Phase 11.3.1 is **PARTIAL**, scientific evaluation **BLOCKED**. ESA technical
clarification is pending under user-supplied support reference `RITM0144536`.
This protocol does not select a genuine GP record or reference epoch.

## Objective and separate claims

The proposed question is: at qualified reference epochs inside the approved
interval, how does the Cartesian position calculated with SGP4/WGS72 from one
eligible historical Swarm-A GP record differ from the matching ESA kinematic
spacecraft-center-of-mass position, after justified time and frame alignment?

| Level | What success would establish | What it would not establish |
| --- | --- | --- |
| Element validation | Supported schema, finite fields, target and static model compatibility | Physical orbit accuracy or an eligible scientific input |
| Propagation correctness | Agreement with trusted numerical SGP4 reference cases | Accuracy for this spacecraft and historical fit |
| Time consistency | A supported common physical epoch and documented conversion | Reference quality or frame alignment |
| Frame compatibility | A justified common origin, axes, scale and realization treatment | Error-free position estimates |
| Reference quality | Suitable KIN samples under documented criteria | Absolute orbital truth |
| Residual | Reference minus calculated position for the qualified pair | A uniquely attributable propagation error |
| Statistics | Descriptive summaries for the selected samples | Independent accuracy, confidence or physical-event claims |
| Historical availability | Availability before a cutoff, if separately evidenced | Availability inferred from the orbital epoch |
| Independence | Only the dependencies actually established by lineage evidence | Independence inferred from different provider names |

The initial study is **retrospective**. GP historical availability and complete
fitting lineage are unknown. An external processed reference also has uncertainty
and potentially shared upstream dependencies. No absolute-truth, maneuver,
anomaly, collision or operational-safety conclusion is supported.

## Fixed identity, source and configuration

Target: Swarm-A / NORAD **39452**, designator **2013-067B**, SP3 **L47**.
Use the existing, explicit [17-column CSV contract](phase-11.3.1-historical-csv-intake.md),
not a repaired JSON file. Pin the complete original CSV SHA-256
`2b5712d5c2fe3fd6f8106633cb84780d6562eb455f49922fbbbbe9d09a26f1c4`,
source index, original epoch/field strings, parsed values, static-check results,
`ELEMENT_SET_NO` and `REV_AT_EPOCH`. Preserve the three rows and set values 35–37;
their sequence is not a publication clock or a globally unique identifier.

Record source attribution/authentication limits, actual acquisition/receipt time
where known, unavailable creation time, and any separately evidenced historical
availability. Unknown values remain null. CelesTrak's reported lack of retained
creation timestamps does not prove availability in 2014. See the
[provider reconciliation](phase-11.3.1-provider-response-reconciliation.md).

Reference: `SW_OPER_SP3AKIN_2__20131231T235944_20140101T235944_0201.sp3`,
product `SP3AKIN_2_`, file version `0201`, `L2PS-DUT/44.88`, creator
`SPC_DUT` / `44.88`. Pin KIN/VAL archives, members, hashes, quality evidence and
resource versions from the [pairing report](phase-11.3.1-scientific-pairing-report.md).
No separate processing-baseline identifier is inferred.

Preserve SGP4/WGS72, nominal UTC-calendar propagation, geocentric TEME km/km/s,
the existing exact datetime contract and inclusive ±7-day source-epoch bound.
Pin Astropy, PyERFA, sgp4, leap/EOP hashes, policies and calculation software.
The bound is a necessary software constraint, not a prediction-accuracy guarantee.

## Interval, reference epochs and exclusions

Provisional requested closed UTC interval:
**[2013-12-31T23:59:44Z, 2014-01-01T23:59:44Z]**, from XML validity metadata.
It is an intended scope, not an assertion that inconsistent SP3 fields are valid.
Producer-supported time interpretation must establish the interval and individual
epochs before this scope is frozen for an actual run. Amend/version the protocol
before evaluation if authoritative evidence requires a different interval;
never move it after viewing residuals to improve results.

Retain every original reference index and timestamp string. In principle, only
epochs inside that interval, for the exact target, with qualified time, acceptable
KIN quality and qualified frame treatment could enter the comparison. The earlier
5,118 conversions are conditional calendar diagnostics, not eligible scientific
epochs. Currently **zero epochs are scientifically accepted**.

Maintain the current 1,806 submicrosecond and 723 GPS second-60 exclusions.
No rounding, rollover, interpolation, grid snapping, extrapolation or nearest-time
matching. A later approved time policy requires independent tests and a versioned
protocol change; it does not silently modify original timestamps. Retain all
7,647 source indices, including missing/unsupported/quality-rejected entries.
No regular sampling cadence or complete daily coverage is inferred from count.

Before calculation, freeze an indexed acceptance mask with reason codes for
every exclusion, including target mismatch, invalid/ambiguous source, unsupported
time/precision, inconsistent header, outside interval, duplicate epoch, missing
position, failed EOP coverage, unqualified frame and unaccepted quality. Duplicate
or competing reference records at one epoch require review; do not pick a value
by source order. Unknown quality remains unaccepted. Do not treat absent extended
P flags, small EP sigmas or XML quality `000` as acceptance.

## Deterministic GP policy — not applied to genuine inputs

After every scientific gate passes, use a **single fixed initial GP record** for
the complete frozen epoch set. Do not switch to a newer record at each reference
epoch. The anchor is the frozen interval start, not a residual-dependent epoch or
the first surviving quality sample. Require the GP element epoch to be no later
than that anchor, and within ±7 days of **every** accepted reference epoch.
No backward-propagation study is included in version 1.

Filter only by documented identity, original-source integrity, static checks,
time/frame/quality prerequisites and these temporal constraints. Rank remaining
records by decreasing element epoch. The first unique record would be the
proposed initial condition for separate review. Duplicate source identities or
competing same-epoch records block the plan; source index, set number, revolution,
filename and smallest residual are not tie-breakers. No silent fallback to an
older record after ambiguity. No candidates means BLOCKED, not a substituted
current GP record, another satellite or changed interval.

Historical availability is assessed separately: unknown availability requires
retrospective-only interpretation and `forecast_eligible=false`. Even a known
retrieval clock does not supply the fit's observation window. Any future
historical-forecast claim needs independently supported availability before its
declared cutoff and a separately reviewed protocol.

The following executable **synthetic specification model** tests the ordering
rule. It is documentation, has no operational caller, accepts only already-checked
metadata for hypothetical examples and never selects a source or enables a run.
Its gate booleans are test inputs, not a scientific approval API. The actual
qualification tool continues to return BLOCKED. It must not be applied to the
genuine three-row intake in this task.

<!-- protocol-model -->
```python
from datetime import timedelta

REQUIRED_GATES = (
    "input_provenance",
    "record_selection_basis",
    "reference_time",
    "time_conversion",
    "frame_alignment",
    "kin_epochs",
    "reference_quality",
    "protocol",
    "uncertainty_policy",
    "lineage_limits",
)


def planned_order(records, start, end, epochs, gates):
    result = {
        "status": "BLOCKED",
        "candidate_order": [],
        "selected_source_index": None,
        "comparison_ready": False,
    }
    if any(gates.get(name) is not True for name in REQUIRED_GATES):
        return result
    times = [start, end, *epochs]
    if (
        not epochs
        or len(epochs) != len(set(epochs))
        or any(t.tzinfo is None or t.utcoffset() != timedelta(0) for t in times)
        or start > end
        or any(not start <= t <= end for t in epochs)
    ):
        return result
    eligible = []
    for record in records:
        t = record["epoch"]
        if t.tzinfo is None or t.utcoffset() != timedelta(0):
            return result
        if (
            record["catalog_id"] == 39452
            and record["designator"] == "2013-067B"
            and record["static_valid"] is True
            and t <= start
            and all(abs(e - t) <= timedelta(days=7) for e in epochs)
        ):
            eligible.append(record)
    if (
        not eligible
        or len({r["epoch"] for r in eligible}) != len(eligible)
        or len({r["id"] for r in eligible}) != len(eligible)
    ):
        return result
    result["status"] = "PLAN_ONLY"
    result["candidate_order"] = [
        r["id"] for r in sorted(eligible, key=lambda r: r["epoch"], reverse=True)
    ]
    return result
```

This model omits source parsing, cryptographic provenance, reference qualification
and execution intentionally; those remain existing/future separately verified
stages. It does not replace their validation or generalize their input schemas.

## Residual and statistics, only after authorization

At exactly the same qualified physical epoch, origin, realization and axes:
`d(t) = r_reference(t) - r_SGP4_aligned(t)`, Cartesian XYZ in **km**.
Convert units explicitly and once; retain original units. Propagate once per
epoch from the fixed GP record, then use the approved alignment. The output frame
must identify the actual realization or documented precision-scoped treatment,
not simply say “ITRS”. Preserve GP epoch, reference epoch, retrieval and calculation
clocks separately. No geodetic latitude/height or WGS84 surface projection enters
this Cartesian residual. WGS72 gravity constants are not a datum transform.

Potential primary outputs are signed XYZ differences and their Euclidean norm.
The product has no V/EV records: no measured velocity errors, reference-derived
RAC basis or clock-as-velocity interpretation. No extra orbital/event metrics.
Calculation failure remains an indexed failure with no zero substitute; an
incomplete frozen run is not reported as successful, and is not reranked.

Report requested/accepted/excluded/failed counts, reasons, exact selected source
and reference indices/hashes, temporal extrema/gaps and sample spacing. For
`N=0` all metrics are unavailable; for `N=1` show that single discrepancy only.
For `N>=2`, optional equal-weight descriptive component bias, MAE and RMSE,
and norm mean/RMS/maximum/median may be reported with explicit formulas:

`bias_j = sum(d_ij)/N`, `MAE_j = sum(abs(d_ij))/N`,
`RMSE_j = sqrt(sum(d_ij**2)/N)`,
`norm_RMS = sqrt(sum(||d_i||**2)/N)`.

These are summaries over accepted irregular samples, not time-weighted full-day
statistics or independent errors. Record sample correlation as unknown. No
confidence intervals, significance, normality/IID assumptions, weighted scores,
outlier deletion, fitted trend or inferred future error. EP formal uncertainty,
reference systematics and GP uncertainty remain distinct. No numerical accuracy
target or pass threshold is adopted: required precision and defensible contributor
bounds remain unresolved in the [frame investigation](phase-11.3.1-frame-alignment-investigation.md).

## Release gate and evidence required

All ten model gates require reviewed evidence, not just a boolean or a passing
test. Freeze an evaluation configuration only after: exact accepted GP provenance
and static validation; justified initial-record rule; producer-supported reference
time and tested conversion; justified frame treatment; KIN-specific accepted epoch
mask and quality assessment; this versioned protocol; precision/uncertainty policy;
and disclosed actual-pair availability/lineage/independence limits.

Then independently review all source/member/resource/selection hashes, versions,
units, sign conventions, interval, exclusions and proposed interpretation, and
obtain separate authorization for genuine evaluation. CSV success, proximity,
synthetic tests, generic ITRS, an assumed identity transform, or a general VAL
label cannot close those gates. Current selected source is null, reference mask
empty, operational adapter inactive and genuine prediction/residual counts zero.

## References and verification

Reviewed **22 October 2026**: the existing source/intake/reconciliation and
qualification tools; current engine, coordinates, EOP implementation and reference
tests; ESA L2 specification revision 3.0 §5.9.1; SP3-d field definitions; IGS
IGb08 chronology; IERS terrestrial-frame conventions; installed Astropy 7.2.3.
Exact authoritative URLs, review/acquisition distinctions and independent
mathematical controls are in the [frame investigation](phase-11.3.1-frame-alignment-investigation.md).
Protocol-control tests are in `backend/tests/test_swarm_comparison_protocol.py`.
Actual outcomes are recorded in [verification evidence](phase-11.3.1-protocol-verification.json).
