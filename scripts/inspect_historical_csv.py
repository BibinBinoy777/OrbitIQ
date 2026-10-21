"""Private, bounded Swarm-A CSV diagnostics, not operational GP ingestion.

The 17-column schema was checked against the preserved source. CSV cells remain
source text; a separately identified typed view is used only for static Elements
validation. No satellite initialization, propagation, DB or residual operation.
"""

import argparse
import csv
import io
import math
import re
import runpy
from collections import defaultdict
from decimal import Decimal, DecimalException
from pathlib import Path

from orbitiq import replay
from orbitiq.replay_json import decoded

INTAKE = runpy.run_path(str(Path(__file__).with_name("inspect_historical_gp.py")))
FIELDS = (
    "OBJECT_NAME",
    "OBJECT_ID",
    "EPOCH",
    "MEAN_MOTION",
    "ECCENTRICITY",
    "INCLINATION",
    "RA_OF_ASC_NODE",
    "ARG_OF_PERICENTER",
    "MEAN_ANOMALY",
    "EPHEMERIS_TYPE",
    "CLASSIFICATION_TYPE",
    "NORAD_CAT_ID",
    "ELEMENT_SET_NO",
    "REV_AT_EPOCH",
    "BSTAR",
    "MEAN_MOTION_DOT",
    "MEAN_MOTION_DDOT",
)
TEXT = {"OBJECT_NAME", "OBJECT_ID", "EPOCH", "CLASSIFICATION_TYPE"}
INTEGER = {"EPHEMERIS_TYPE", "NORAD_CAT_ID", "ELEMENT_SET_NO", "REV_AT_EPOCH"}
NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
MAX_CELL = 4096


def gates():
    return {
        "source_identity": {"status": "PARTIAL", "reason": "labels_not_authentication"},
        "record_structure": {"status": "BLOCKED", "reason": "not_yet_checked"},
        "numbers_and_element_model": {"status": "BLOCKED", "reason": "not_yet_checked"},
        "historical_record_selection": {
            "status": "BLOCKED",
            "reason": "no_approved_record_selection",
        },
        "temporal_pairing": {
            "status": "BLOCKED",
            "reason": "epoch_bound_is_not_approved_pairing",
        },
        "time_system": {
            "status": "PARTIAL",
            "reason": "5118_converted_reference_times_2529_excluded",
        },
        "coordinate_frame": {"status": "BLOCKED", "reason": "igb08_unqualified"},
        "reference_quality": {
            "status": "BLOCKED",
            "reason": "no_approved_epoch_quality_selection",
        },
        "provenance_and_independence": {
            "status": "BLOCKED",
            "reason": "authentication_availability_lineage_unknown",
        },
        "operational_evaluation": {
            "status": "BLOCKED",
            "reason": "no_operational_adapter_or_scientific_approval",
        },
    }


def quote_structure(text):
    """Reject stray quotes which Python's CSV reader permits in unquoted cells."""
    state = "start"
    for char in text:
        if char == "\x00":
            raise ValueError("csv_nul_not_supported")
        if state == "quoted":
            if char == '"':
                state = "closed"
        elif state == "closed":
            if char == '"':
                state = "quoted"
            elif char in ",\r\n":
                state = "start"
            else:
                raise ValueError("csv_characters_after_closing_quote")
        elif char == '"':
            if state != "start":
                raise ValueError("csv_quote_in_unquoted_cell")
            state = "quoted"
        elif char in ",\r\n":
            state = "start"
        else:
            state = "unquoted"
    if state == "quoted":
        raise ValueError("csv_unterminated_quote")


def typed_fields(fields):
    result = {}
    failures = []
    for name, text in fields.items():
        try:
            if not text or text != text.strip() or len(text) > MAX_CELL:
                raise ValueError("missing_whitespace_or_over_budget_cell")
            if name in TEXT:
                if name == "EPOCH":
                    INTAKE["exact_epoch"](text)
                result[name] = text
            elif name in INTEGER:
                if not re.fullmatch(r"[0-9]+", text):
                    raise ValueError("unsigned_integer_required")
                result[name] = int(text)
            else:
                if not NUMBER.fullmatch(text):
                    raise ValueError("unsupported_numeric_text")
                exact = Decimal(text)
                value = float(exact)
                if not exact.is_finite() or not math.isfinite(value):
                    raise ValueError("nonfinite_or_float_overflow")
                if exact != 0 and value == 0:
                    raise ValueError("float_underflow")
                result[name] = value
        except (ValueError, OverflowError, DecimalException) as error:
            failures.append({"field": name, "code": str(error)[:128]})
    return result, failures


def exact_record(fields):
    """Exact comparison values from validated source strings, never model floats."""
    return {
        name: text if name in TEXT else int(text) if name in INTEGER else Decimal(text)
        for name, text in fields.items()
    }


def inspect_attachment(raw, provenance=None):
    if not isinstance(raw, bytes) or len(raw) > INTAKE["MAX_BYTES"]:
        raise ValueError("attachment_byte_budget_exceeded")
    whole_hash = replay.digest(raw)
    report = {
        "kind": "orbitiq_historical_csv_intake",
        "schema_version": 1,
        "status": "BLOCKED",
        "source_format": "CSV",
        "format_detected": "CSV",
        "attachment_sha256": whole_hash,
        "attachment_bytes": len(raw),
        "adapter_sha256": replay.digest(Path(__file__).read_bytes()),
        "provenance": INTAKE["metadata"](provenance),
        "header": [],
        "records": [],
        "document_errors": [],
        "qualification_gates": gates(),
        "record_order_preserved": True,
        "automatic_record_selection": False,
        "selected_source_index": None,
        "source_accepted": False,
        "comparison_ready": False,
        "adapter_operational": False,
        "prediction_evaluations": 0,
        "residuals": None,
        "accuracy": None,
        "normalized_observations": [],
        "forecast_eligible": False,
        "comparison_mode_if_other_gates_later_pass": "retrospective_only",
        "source_metadata_not_inferred": [
            "received_at",
            "acquired_at",
            "historically_available_at",
            "authentication",
        ],
        "model_conventions_not_csv_columns": {
            "CENTER_NAME": "EARTH",
            "REF_FRAME": "TEME",
            "TIME_SYSTEM": "UTC",
            "MEAN_ELEMENT_THEORY": "SGP4",
        },
        "numeric_conversion": (
            "exact source strings retained; Decimal checks then binary float for "
            "existing Elements only; reconciliation uses Decimal, no tolerance"
        ),
    }
    records = report["records"]
    try:
        text = raw.decode("utf-8-sig")
        quote_structure(text)
        reader = csv.reader(io.StringIO(text, newline=""), dialect="excel", strict=True)
        header = next(reader, [])
        if len(header) != len(FIELDS) or len(set(header)) != len(header):
            raise ValueError("missing_extra_or_duplicate_csv_columns")
        if set(header) != set(FIELDS):
            raise ValueError("unsupported_csv_header")
        report["header"] = header
        for index, cells in enumerate(reader):
            if index >= INTAKE["MAX_RECORDS"]:
                raise ValueError("record_budget_exceeded_unenumerated_rows_remain")
            row = {
                "source_index": index,
                "physical_line_end": reader.line_num,
                "attachment_sha256": whole_hash,
                "status": "EXCLUDED",
                "reasons": [],
                "source_field_count": len(cells),
                "source_fields": None,
                "element_model_compatible": False,
                "dynamic_parser_check_executed": False,
                "available_at": None,
                "forecast_eligible": False,
            }
            records.append(row)
            if len(cells) != len(header) or any(len(c) > MAX_CELL for c in cells):
                row["reasons"] = ["unexpected_field_count_or_over_budget_cell"]
                row["source_cell_preview"] = [c[:MAX_CELL] for c in cells[:18]]
                row["preview_is_complete"] = len(cells) <= 18 and all(
                    len(c) <= MAX_CELL for c in cells
                )
                continue
            fields = dict(zip(header, cells, strict=True))
            row["source_fields"] = fields
            typed, failures = typed_fields(fields)
            if failures:
                row["reasons"] = ["invalid_csv_field_text"]
                row["field_failures"] = failures
                continue
            row.update(INTAKE["inspect_record"](typed, index, whole_hash))
        if not records:
            raise ValueError("empty_csv_record_collection")
    except (ValueError, UnicodeError, csv.Error) as error:
        report["document_errors"] = [
            str(error)[:128] if type(error) is ValueError else "invalid_encoding_or_csv"
        ]
        # Preserve enumerated rows as diagnostics, never use a valid prefix.
        for row in records:
            row["status"] = "EXCLUDED"
            row["reasons"].append("document_structure_refused")

    groups, identities = defaultdict(list), defaultdict(list)
    for row in records:
        if row["status"] == "CANDIDATE":
            exact = exact_record(row["source_fields"])
            groups[tuple(exact[name] for name in FIELDS)].append(row)
            identities[
                (exact["NORAD_CAT_ID"], exact["OBJECT_ID"], row["orbital_epoch_utc"])
            ].append(row)
    for group in groups.values():
        if len(group) > 1:
            for row in group:
                row["status"] = "EXCLUDED"
                row["reasons"].append("duplicate_exact_record")
                row["duplicate_source_indices"] = [r["source_index"] for r in group]
    for group in identities.values():
        if len(group) > 1:
            for row in group:
                row["status"] = "EXCLUDED"
                row["reasons"].append("ambiguous_same_epoch_identity")
    report["counts"] = {
        "enumerated": len(records),
        "candidate": sum(row["status"] == "CANDIDATE" for row in records),
        "excluded": sum(row["status"] == "EXCLUDED" for row in records),
    }
    structural = (
        bool(records)
        and not report["document_errors"]
        and all(
            row["source_fields"] is not None and all(row["source_fields"].values())
            for row in records
        )
    )
    compatible = structural and all(r["element_model_compatible"] for r in records)
    if not records or any(
        row.get("catalog_id") != 39452
        or row.get("international_designator") != "2013-067B"
        for row in records
    ):
        report["qualification_gates"]["source_identity"] = {
            "status": "BLOCKED",
            "reason": "missing_invalid_or_inconsistent_identity",
        }
    for key, passed in (
        ("record_structure", structural),
        ("numbers_and_element_model", compatible),
    ):
        report["qualification_gates"][key] = {
            "status": "PASS" if passed else "BLOCKED",
            "reason": "static_csv_checks_only" if passed else "csv_validation_refused",
        }
    if report["counts"]["candidate"] and not report["document_errors"]:
        report["status"] = "PARTIAL"
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attachment", required=True, type=Path)
    parser.add_argument("--archive-root", required=True, type=Path)
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--expected-sha256")
    args = parser.parse_args(argv)
    try:
        provenance = (
            decoded(INTAKE["read_input"](args.metadata, 16384))
            if args.metadata
            else None
        )
        _, report = INTAKE["capture"](
            args.attachment,
            args.archive_root,
            provenance,
            args.expected_sha256,
            inspector=inspect_attachment,
        )
        print(
            replay.encoded(
                {
                    "status": report["status"],
                    "intake_completed": True,
                    "source_format": "CSV",
                    "attachment_sha256": report["attachment_sha256"],
                    "counts": report["counts"],
                    "document_errors": report["document_errors"],
                    "comparison_ready": False,
                }
            ).decode(),
            end="",
        )
        return 0  # Diagnostic completion, never source or science approval.
    except (OSError, ValueError, UnicodeError, replay.BundleError, RuntimeError):
        print('{"status":"csv_intake_refused","comparison_ready":false}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
