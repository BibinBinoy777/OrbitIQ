"""Offline metadata/epoch assessment of the retained Swarm-A KIN/VAL/GP pair.

No propagation, frame transformation, source normalization or residual entrypoint.
The report contains private source-derived diagnostics; keep it out of Git.
"""

import argparse
import os
import runpy
import stat
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from orbitiq import replay
from orbitiq.replay_json import decoded

SCRIPTS = Path(__file__).resolve().parent
SOURCE = runpy.run_path(str(SCRIPTS / "inspect_swarm_reference.py"))
CSV = runpy.run_path(str(SCRIPTS / "inspect_historical_csv.py"))
QUALIFY = runpy.run_path(str(SCRIPTS / "qualify_swarm_inputs.py"))
BOUND_US = 7 * 86400 * 1000000


def offset_us(at, epoch):
    """Signed exact datetime offset, not float total_seconds or orbital age error."""
    delta = at - epoch
    return (delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds


def redundant_header_time(raw):
    """Exact redundant GPS header diagnostics; no rounding or source repair."""
    lines = raw.decode("ascii").splitlines()
    fields = lines[1].split()
    SOURCE["require"](len(fields) == 6, "Demonstrated GPS header fields required")
    elapsed, _ = SOURCE["epoch"](lines[22].split()[1:])
    week_elapsed = int(fields[1]) * 604800 + SOURCE["decimal"](fields[2])
    mjd_elapsed = (int(fields[4]) - 44244 + SOURCE["decimal"](fields[5])) * 86400
    return {
        "gps_week_and_seconds_match_first_epoch": week_elapsed == elapsed,
        "week_seconds_minus_first_epoch_seconds": str(week_elapsed - elapsed),
        "mjd_minus_first_epoch_seconds": str(mjd_elapsed - elapsed),
        "mjd_fraction_used_for_conversion": False,
        "status": "PASS" if week_elapsed == mjd_elapsed == elapsed else "PARTIAL",
        "scope": "redundant_header_consistency_not_a_tolerance_or_clock_accuracy",
    }


def quality_audit(raw):
    """Additional diagnostics AFTER the existing bounded specimen inspection.

    SP3-d pp.16-17: XYZ km; EP XYZ sigmas mm; clock sigma ps; correlations
    scaled by 10^7. Formal fields are not independently measured orbit errors.
    """
    SOURCE["inspect_sp3"](raw)
    lines = raw.decode("ascii").splitlines()
    rows, sigma_columns = [], [[], [], []]
    clock_sigmas = []
    for index, offset in enumerate(range(22, len(lines) - 1, 3)):
        _, position, ep = lines[offset : offset + 3]
        SOURCE["require"](len(ep) == 80, "Demonstrated fixed-width EP required")
        # Compare fixed-width extraction to the existing token inspection. This
        # avoids shifting uncertainty fields if the demonstrated layout changes.
        sigma = [int(ep[a:b]) for a, b in ((4, 8), (9, 13), (14, 18), (19, 26))]
        correlation = [int(ep[a : a + 8]) for a in (27, 36, 45, 54, 63, 72)]
        SOURCE["require"](
            sigma + correlation == [int(t) for t in ep.split()[1:]],
            "EP fixed-width and token views disagree",
        )
        zero_axes = [
            axis
            for axis, a, b in (("x", 4, 18), ("y", 18, 32), ("z", 32, 46))
            if SOURCE["decimal"](position[a:b].strip()) == 0
        ]
        reasons = []
        if zero_axes:
            reasons.append("zero_component_requires_missing_position_review")
        if any(value <= 0 or value == 9999 for value in sigma[:3]):
            reasons.append("axis_sigma_zero_or_overflow_requires_review")
        if any(abs(value) >= 10000000 for value in correlation):
            reasons.append("correlation_outside_sp3_d_range")
        rows.append(
            {
                "source_index": index,
                "zero_position_components": zero_axes,
                "axis_sigmas_mm": sigma[:3],
                "clock_sigma_ps": sigma[3],
                "correlation_integers_scaled_by_10000000": correlation,
                "extended_p_quality_fields_present": len(position.rstrip()) > 60,
                "format_review_reasons": reasons,
                "quality_accepted": False,
            }
        )
        for column, value in zip(sigma_columns, sigma[:3], strict=True):
            column.append(value)
        clock_sigmas.append(sigma[3])
    return {
        "status": "PARTIAL",
        "source_records": len(rows),
        "header_accuracy_exponent": int(lines[7][9:12]),
        "header_zero_accuracy_means_unknown": True,
        "axis_sigma_ranges_mm": [
            {"minimum": min(values), "maximum": max(values)} for values in sigma_columns
        ],
        "clock_sigma_range_ps": {
            "minimum": min(clock_sigmas),
            "maximum": max(clock_sigmas),
        },
        "rows_with_format_review_reasons": sum(
            bool(row["format_review_reasons"]) for row in rows
        ),
        "rows_with_zero_position_component": sum(
            bool(row["zero_position_components"]) for row in rows
        ),
        "rows_with_extended_p_quality_fields": sum(
            row["extended_p_quality_fields_present"] for row in rows
        ),
        "rows": rows,
        "accepted_quality_indices": [],
        "covariance_or_physical_accuracy_inferred": False,
        "nominal_product_uncertainty_not_epoch_error_bound": True,
        "reason": "formal_uncertainties_and_matching_val_are_not_epoch_acceptance",
    }


def timing_audit(raw, candidates):
    """Convert only supported times; test EOP coverage at EVERY converted epoch.

    Timing offsets are assessed for all candidates, without choosing a nearest
    record, reference interval or quality threshold.
    """
    rows, exclusions = [], Counter()
    evaluated_at = datetime.now(UTC)
    with QUALIFY["orientation"]() as (data, mode):
        for index, line in enumerate(
            line for line in raw.decode("ascii").splitlines() if line.startswith("*  ")
        ):
            row = {
                "source_index": index,
                "source_gps_epoch": line.strip(),
                "utc": None,
                "exclusion": None,
                "eop_coverage": None,
            }
            rows.append(row)
            try:
                elapsed = QUALIFY["gps_value"](line.split()[1:], "GPS")
                row["utc"] = QUALIFY["to_utc"](elapsed, data)
            except QUALIFY["QualificationError"] as error:
                row["exclusion"] = error.code
                exclusions[error.code] += 1
                continue
            # Resource preflight only. No spacecraft coordinate is transformed.
            try:
                eop = QUALIFY["parameters"](
                    data,
                    QUALIFY["Time"](row["utc"], scale="utc"),
                    mode,
                    now=evaluated_at,
                )
                row["eop_coverage"] = {
                    "status": "PASS",
                    "quality": eop["source_quality"],
                    "auto_download": eop["auto_download"],
                }
            except QUALIFY["TransformationError"] as error:
                row["eop_coverage"] = {"status": "BLOCKED", "reason": error.code}
        resource_metadata = data.metadata
    converted = [row for row in rows if row["utc"] is not None]
    candidate_results = []
    for item in candidates:
        epoch = datetime.fromisoformat(item["orbital_epoch_utc"])
        offsets = [
            offset_us(datetime.fromisoformat(row["utc"]), epoch) for row in converted
        ]
        candidate_results.append(
            {
                "source_index": item["source_index"],
                "attachment_sha256": item["attachment_sha256"],
                "epoch_source_text": item["epoch_source_text"],
                "orbital_epoch_utc": item["orbital_epoch_utc"],
                "catalog_id": item["catalog_id"],
                "international_designator": item["international_designator"],
                "element_set_source_text": item["source_fields"]["ELEMENT_SET_NO"],
                "revolution_source_text": item["source_fields"]["REV_AT_EPOCH"],
                "first_reference_offset_microseconds": offsets[0] if offsets else None,
                "last_reference_offset_microseconds": offsets[-1] if offsets else None,
                "minimum_offset_microseconds": min(offsets) if offsets else None,
                "maximum_offset_microseconds": max(offsets) if offsets else None,
                "within_inclusive_seven_day_bound": sum(
                    abs(value) <= BOUND_US for value in offsets
                ),
                "reference_before_element_epoch": sum(value < 0 for value in offsets),
                "reference_at_element_epoch": offsets.count(0),
                "reference_after_element_epoch": sum(value > 0 for value in offsets),
                "element_not_later_than_first_ordinary_reference": bool(offsets)
                and offsets[0] >= 0,
                "available_at": None,
                "forecast_eligible": False,
                "selected": False,
                "temporal_pair_approved": False,
            }
        )
    return {
        "status": "PARTIAL" if converted else "BLOCKED",
        "evaluated_at_utc": evaluated_at.isoformat(),
        "source_epoch_count": len(rows),
        "converted_count": len(converted),
        "excluded_count": sum(exclusions.values()),
        "exclusion_reasons": dict(exclusions),
        "first_converted_utc": converted[0]["utc"] if converted else None,
        "last_converted_utc": converted[-1]["utc"] if converted else None,
        "eop_scope": "all_converted_epochs_and_existing_plus_minus_half_second_support",
        "eop_passed": sum(row["eop_coverage"]["status"] == "PASS" for row in converted),
        "eop_blocked": sum(
            row["eop_coverage"]["status"] == "BLOCKED" for row in converted
        ),
        "resources": resource_metadata,
        "rows": rows,
        "candidate_offsets": candidate_results,
        "offset_unit": "integer microseconds",
        "source_rounding_or_second_60_rollover": False,
        "reference_epoch_quality_approved": False,
    }


def assess(kinematic, validation, csv_raw, kin_sha, val_sha, csv_sha, provenance=None):
    inspected = SOURCE["inspect"](kinematic, validation, kin_sha, val_sha)
    SOURCE["require"](replay.digest(csv_raw) == csv_sha, "CSV hash mismatch")
    csv = CSV["inspect_attachment"](csv_raw, provenance)
    SOURCE["require"](
        not csv["document_errors"]
        and not csv["counts"]["excluded"]
        and csv["counts"]["candidate"] == 3,
        "Three validated target records required; no valid-prefix acceptance",
    )
    _, raw = SOURCE["unpack"](kinematic, kin_sha, "KIN")
    time = timing_audit(raw, csv["records"])
    return {
        "kind": "orbitiq_swarm_scientific_pairing_assessment",
        "schema_version": 1,
        "status": "BLOCKED",
        "phase_status": "PARTIAL",
        "assessment_tool_sha256": replay.digest(Path(__file__).read_bytes()),
        "reference_source": {
            key: inspected[key]
            for key in (
                "tool_sha256",
                "kinematic",
                "validation",
                "sp3",
                "catalog_mapping",
            )
        },
        "csv_inspection": csv,
        "time": time,
        "redundant_header_time": redundant_header_time(raw),
        "quality": quality_audit(raw),
        "frame": QUALIFY["frame_qualification"](inspected["sp3"]["frame_declaration"]),
        "qualification_gates": csv["qualification_gates"],
        "pairing_decision": {
            "status": "BLOCKED",
            "selected_source_index": None,
            "accepted_reference_indices": [],
            "approved_evaluation_configuration": None,
            "timing_candidate_indices": [
                item["source_index"] for item in time["candidate_offsets"]
            ],
            "method": "all_records_against_all_ordinary_times_no_nearest_selection",
            "future_comparison_label": "retrospective_only_unless_availability_proven",
            "prerequisites": [
                "authenticated_source_and_actual_pair_provenance_assessment",
                "predeclared_initial_record_and_reference_epoch_selection",
                "source_time_and_format_discrepancy_disposition",
                "precision_scoped_igb08_alignment_and_independent_verification",
                "kinematic_epoch_quality_acceptance_and_uncertainty_limits",
                "fitting_lineage_and_independence_limitations",
                "reproducible_operational_input_configuration_and_separate_authorization",
            ],
        },
        "comparison_ready": False,
        "adapter_operational": False,
        "prediction_evaluations": 0,
        "coordinate_transformations": 0,
        "residuals": None,
        "normalized_observations": [],
        "independence": "NOT_ESTABLISHED",
        "prediction_uncertainty": "not_quantified",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("kinematic", "validation", "gp-csv"):
        parser.add_argument("--" + name, required=True, type=Path)
        parser.add_argument("--" + name + "-sha256", required=True)
    parser.add_argument("--csv-metadata", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        output = args.output
        if not output.is_absolute() or output != output.resolve():
            raise ValueError("Explicit output without symlinks required")
        read = CSV["INTAKE"]["read_input"]
        provenance = (
            decoded(read(args.csv_metadata, 16384)) if args.csv_metadata else None
        )
        result = assess(
            read(args.kinematic, SOURCE["MAX_ZIP"]),
            read(args.validation, SOURCE["MAX_ZIP"]),
            read(args.gp_csv, CSV["INTAKE"]["MAX_BYTES"]),
            args.kinematic_sha256,
            args.validation_sha256,
            args.gp_csv_sha256,
            provenance,
        )
        with replay.directory(output.parent) as fd:
            info = os.fstat(fd)
            if stat.S_IMODE(info.st_mode) != 0o700 or info.st_uid != os.getuid():
                raise ValueError("Owned private output directory mode 0700 required")
            replay.write_file(fd, output.name, replay.encoded(result))
            os.fsync(fd)
        print(
            '{"assessment_completed":true,"status":"BLOCKED","comparison_ready":false}'
        )
        return 0
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        IndexError,
        RuntimeError,
        replay.BundleError,
    ):
        print(
            '{"assessment_completed":false,"status":"BLOCKED","comparison_ready":false}'
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
