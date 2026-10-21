"""Private, offline Swarm-A GP intake diagnostics; never an orbital evaluation.

Preserve the original attachment before parsing. Candidate records are not
authenticated historical inputs. No propagation, database, network or residual
operation is part of this tool. The existing one-record ingestion is unchanged.
"""

import argparse
import os
import re
import stat
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from orbitiq import replay
from orbitiq.orbits.elements import Elements
from orbitiq.replay_json import decoded
from orbitiq.reporting import report_time
from pydantic import ValidationError

MAX_BYTES = 2 * 1024 * 1024
MAX_RECORDS = 512
MAX_RECORD_BYTES = 65536
HASH = re.compile(r"[a-f0-9]{64}")
EPOCH = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.(\d+))?(?:Z|\+00:00)?")
REQUEST_START = datetime(2013, 12, 30, tzinfo=UTC)
REQUEST_STOP = datetime(2014, 1, 3, tzinfo=UTC)
REFERENCE_START = datetime(2014, 1, 1, 0, 2, 4, tzinfo=UTC)
REFERENCE_STOP = datetime(2014, 1, 1, 23, 57, 54, tzinfo=UTC)
METADATA_FIELDS = {
    "provider",
    "acquired_at",
    "received_at",
    "original_filename",
    "format",
    "notes",
}


class IntakeError(ValueError):
    pass


def metadata(value=None):
    """Operator assertions remain assertions, not provider authentication."""
    if value is None:
        value = {}
    if not isinstance(value, dict) or set(value) - METADATA_FIELDS:
        raise IntakeError("unsupported_metadata_fields")
    result = {field: None for field in sorted(METADATA_FIELDS)}
    for key, item in value.items():
        if item is None:
            continue
        if not isinstance(item, str) or not 0 < len(item) <= 1024:
            raise IntakeError("invalid_metadata_value")
        if key in {"acquired_at", "received_at"}:
            result[key] = report_time(item).isoformat()
        else:
            if key == "original_filename" and (
                Path(item).name != item or item in {".", ".."} or "\\" in item
            ):
                raise IntakeError("original_filename_must_be_basename")
            result[key] = item
    if (
        result["acquired_at"]
        and result["received_at"]
        and report_time(result["acquired_at"]) > report_time(result["received_at"])
    ):
        raise IntakeError("acquisition_after_receipt_requires_review")
    return {
        "asserted": result,
        "missing": [key for key, item in result.items() if item is None],
        "evidence_status": "operator_supplied_unverified",
        "source_authenticated": False,
        "historically_available_at": None,
        "availability_inferred_from_epoch_or_receipt": False,
    }


def exact_epoch(value):
    if not isinstance(value, str) or not (match := EPOCH.fullmatch(value)):
        raise IntakeError("epoch_requires_supported_utc_iso_calendar")
    fraction = match[1] or ""
    if any(digit != "0" for digit in fraction[6:]):
        raise IntakeError("epoch_submicrosecond_precision_unsupported")
    # No nonzero fractional digit is dropped; original source text is retained.
    at = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not 1957 <= at.year <= 2099:
        raise IntakeError("epoch_outside_existing_model_year_range")
    if at.tzinfo is None:
        at = at.replace(tzinfo=UTC)  # CelesTrak GP's documented omitted UTC zone.
    return at


def inspect_record(record, index, whole_hash):
    result = {
        "source_index": index,
        "attachment_sha256": whole_hash,
        "status": "EXCLUDED",
        "reasons": [],
        "unresolved": [],
        "parsed_record_sha256": replay.digest(replay.encoded(record)),
        "epoch_source_text": None,
        "orbital_epoch_utc": None,
        "catalog_id": None,
        "international_designator": None,
        "element_model_compatible": False,
        "dynamic_parser_check_executed": False,
        "available_at": None,
        "forecast_eligible": False,
        "duplicate_source_indices": [],
    }
    reasons = result["reasons"]
    if not isinstance(record, dict):
        reasons.append("record_must_be_object")
        return result
    if len(replay.encoded(record)) > MAX_RECORD_BYTES:
        reasons.append("record_exceeds_single_record_parser_budget")
        return result
    for field, key, kind in (
        ("EPOCH", "epoch_source_text", str),
        ("NORAD_CAT_ID", "catalog_id", int),
        ("OBJECT_ID", "international_designator", str),
    ):
        item = record.get(field)
        if type(item) is kind and (not isinstance(item, str) or len(item) <= 128):
            result[key] = item
    try:
        at = exact_epoch(record.get("EPOCH"))
        result["orbital_epoch_utc"] = at.isoformat()
    except (ValueError, OverflowError) as error:
        reasons.append("missing_invalid_or_unsupported_exact_epoch")
        result["epoch_failure"] = (
            str(error) if isinstance(error, IntakeError) else "invalid_epoch_calendar"
        )
        at = None
    if record.get("NORAD_CAT_ID") != 39452:
        reasons.append("wrong_or_missing_target_catalog_id")
    if record.get("OBJECT_ID") != "2013-067B":
        reasons.append("wrong_or_missing_international_designator")
    result["missing_required_fields"] = [
        field.alias
        for field in Elements.model_fields.values()
        if field.is_required() and field.alias not in record
    ]
    try:
        Elements.model_validate(record)
        result["element_model_compatible"] = True
    except ValidationError as error:
        reasons.append("incomplete_or_invalid_gp_fields")
        # No raw input values or exception repr in diagnostics.
        result["field_failures"] = [
            {"field": str(e["loc"][0]) if e["loc"] else "__record__", "code": e["type"]}
            for e in error.errors(include_input=False, include_context=False)[:32]
        ]
    if at is not None:
        if not REQUEST_START <= at < REQUEST_STOP:
            reasons.append("epoch_outside_intended_request_calendar_scope")
        low = max(REFERENCE_START, at - timedelta(days=7))
        high = min(REFERENCE_STOP, at + timedelta(days=7))
        result["epoch_bound_intersection"] = (
            {"start": low.isoformat(), "stop": high.isoformat()}
            if low <= high
            else None
        )
        result["entire_reference_span_inside_seven_day_bound"] = all(
            abs((point - at).total_seconds()) <= 7 * 86400
            for point in (REFERENCE_START, REFERENCE_STOP)
        )
        if low > high:
            reasons.append("no_reference_span_inside_seven_day_bound")
    result["source_creation_date_claim"] = (
        record.get("CREATION_DATE")
        if isinstance(record.get("CREATION_DATE"), str)
        else None
    )
    result["unresolved"] = [
        "provider_authentication_and_record_provenance",
        "historical_availability_not_established_by_epoch_creation_claim_or_receipt",
        "prediction_fitting_lineage_unknown",
        "dynamic_initialization_not_executed_in_intake",
        "reference_time_frame_quality_and_pairing_not_qualified",
    ]
    result["status"] = "EXCLUDED" if reasons else "CANDIDATE"
    return result


def gates():
    # Deliberately no user-controllable gate promotion or evaluation entrypoint.
    return {
        "source_identity": {"status": "BLOCKED", "reason": "provenance_unverified"},
        "input_structure_and_numbers": {
            "status": "PARTIAL",
            "reason": "model_checks_only_not_authentication_or_dynamic_validation",
        },
        "historical_record_and_selection": {
            "status": "BLOCKED",
            "reason": "no_authenticated_input_or_approved_temporal_pair",
        },
        "time_conversion": {
            "status": "PARTIAL",
            "reason": "5118_ordinary_reference_times_only_2529_excluded",
        },
        "reference_frame": {"status": "BLOCKED", "reason": "igb08_unqualified"},
        "lineage_and_independence": {
            "status": "BLOCKED",
            "reason": "actual_pair_lineage_unassessed",
        },
        "reference_quality": {
            "status": "BLOCKED",
            "reason": "no_approved_epoch_quality_selection",
        },
        "prediction_and_retrieval_configuration": {
            "status": "PARTIAL",
            "reason": "intake_metadata_does_not_define_approved_evaluation",
        },
        "residual_computation": {
            "status": "BLOCKED",
            "reason": "required_scientific_gates_unresolved_no_authorization_path",
        },
    }


def inspect_attachment(raw, provenance=None):
    if not isinstance(raw, bytes) or len(raw) > MAX_BYTES:
        raise IntakeError("attachment_byte_budget_exceeded")
    whole_hash = replay.digest(raw)  # Before JSON decoding.
    result = {
        "kind": "orbitiq_historical_gp_intake",
        "schema_version": 1,
        "status": "BLOCKED",
        "attachment_sha256": whole_hash,
        "attachment_bytes": len(raw),
        "format_detected": None,
        "provenance": metadata(provenance),
        "records": [],
        "document_errors": [],
        "qualification_gates": gates(),
        "selection_policy": {
            "target": 39452,
            "international_designator": "2013-067B",
            "request_start_inclusive_utc": REQUEST_START.isoformat(),
            "request_stop_exclusive_utc": REQUEST_STOP.isoformat(),
            "provider_date_boundary_semantics": "unknown",
            "reference_span": [REFERENCE_START.isoformat(), REFERENCE_STOP.isoformat()],
            "reference_span_scope": "ordinary_convertible_bounds_not_approved_epochs",
            "max_epoch_offset_days": 7,
            "automatic_record_selection": False,
            "duplicate_policy": "exclude_all_equal_parsed_record_hashes",
            "same_epoch_different_records": "retain_candidates_with_review_warning",
        },
        "parsed_record_hash_scope": (
            "SHA256 of UTF-8 json.dumps(parsed record, sort_keys=True, indent=2, "
            "allow_nan=False, default ensure_ascii=True) plus LF; "
            "NOT original record bytes, semantic identity or provider authentication"
        ),
        "comparison_mode_if_other_gates_later_pass": "retrospective_only",
        "selected_source_index": None,
        "comparison_ready": False,
        "adapter_operational": False,
        "normalized_observations": [],
        "prediction_evaluations": 0,
        "residuals": None,
        "accuracy": None,
    }
    try:
        value = decoded(raw)
        result["format_detected"] = "JSON"
        if isinstance(value, dict):
            records, result["structure"] = [value], "single_object"
        elif isinstance(value, list):
            records, result["structure"] = value, "array"
        else:
            raise IntakeError("unsupported_top_level_structure")
        if not 1 <= len(records) <= MAX_RECORDS:
            raise IntakeError("empty_or_over_budget_record_array")
    except (ValueError, UnicodeError, RecursionError, replay.BundleError):
        result["document_errors"] = ["invalid_unsupported_or_over_budget_json"]
        result["qualification_gates"]["input_structure_and_numbers"] = {
            "status": "BLOCKED",
            "reason": "document_parse_refused_no_records_discarded_or_selected",
        }
        result["counts"] = {"enumerated": 0, "candidate": 0, "excluded": 0}
        return result
    result["records"] = [
        inspect_record(record, index, whole_hash)
        for index, record in enumerate(records)
    ]
    hashes = Counter(item["parsed_record_sha256"] for item in result["records"])
    epochs = Counter(item["orbital_epoch_utc"] for item in result["records"])
    for item in result["records"]:
        if hashes[item["parsed_record_sha256"]] > 1:
            item["status"] = "EXCLUDED"
            item["reasons"].append("duplicate_parsed_record")
            item["duplicate_source_indices"] = [
                other["source_index"]
                for other in result["records"]
                if other["parsed_record_sha256"] == item["parsed_record_sha256"]
            ]
        if item["orbital_epoch_utc"] and epochs[item["orbital_epoch_utc"]] > 1:
            item["unresolved"].append("multiple_records_share_epoch_review_required")
    result["counts"] = {
        "enumerated": len(records),
        "candidate": sum(item["status"] == "CANDIDATE" for item in result["records"]),
        "excluded": sum(item["status"] == "EXCLUDED" for item in result["records"]),
    }
    if not result["counts"]["candidate"]:
        result["qualification_gates"]["input_structure_and_numbers"] = {
            "status": "BLOCKED",
            "reason": "no_structurally_compatible_nonduplicate_target_candidate",
        }
    return result


def read_input(path, limit):
    if not path.is_absolute() or path != path.resolve():
        raise IntakeError("absolute_input_without_symlink_components_required")
    with replay.directory(path.parent) as fd:
        return replay.read_file(fd, path.name, limit)


def capture(path, archive_root, provenance=None, expected_sha256=None):
    """Append a new private capture. Manifest is the completion marker, written last.

    A failed write/inspection leaves the private incomplete capture for review;
    no existing path is deleted or reused. Storage timestamp is not receipt time.
    """
    asserted = metadata(provenance)
    if not archive_root.is_absolute() or archive_root != archive_root.resolve():
        raise IntakeError("explicit_private_archive_without_symlinks_required")
    raw = read_input(path, MAX_BYTES)
    whole_hash = replay.digest(raw)
    if expected_sha256 is not None and (
        not HASH.fullmatch(expected_sha256) or expected_sha256 != whole_hash
    ):
        raise IntakeError("attachment_hash_mismatch")
    receipt = {
        "attachment_sha256": whole_hash,
        "attachment_bytes": len(raw),
        "input_basename": path.name,
        "stored_at_utc": datetime.now(UTC).isoformat(),
        "provenance": asserted,
        "format_detected": None,
        "note": "receipt claims unverified; stored_at is not received_at",
    }
    with replay.directory(archive_root) as root_fd:
        info = os.fstat(root_fd)
        if stat.S_IMODE(info.st_mode) != 0o700 or info.st_uid != os.getuid():
            raise IntakeError("archive_must_be_owned_mode_0700")
        capture_id = uuid4().hex
        os.mkdir(capture_id, 0o700, dir_fd=root_fd)
        fd = os.open(
            capture_id, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=root_fd
        )
        try:
            replay.write_file(fd, "attachment.original", raw)
            replay.write_file(fd, "receipt.json", replay.encoded(receipt))
            # Source bytes and source claims are durably stored BEFORE parsing.
            os.fsync(fd)
            report = inspect_attachment(raw, provenance)
            report["tool_sha256"] = replay.digest(Path(__file__).read_bytes())
            replay.write_file(fd, "inspection.json", replay.encoded(report))
            files = {
                name: {"sha256": replay.digest(body), "bytes": len(body)}
                for name, body in (
                    ("attachment.original", raw),
                    ("receipt.json", replay.encoded(receipt)),
                    ("inspection.json", replay.encoded(report)),
                )
            }
            replay.write_file(
                fd,
                "manifest.json",
                replay.encoded(
                    {
                        "kind": "orbitiq_private_gp_intake",
                        "schema_version": 1,
                        "files": files,
                        "comparison_ready": False,
                    }
                ),
            )
            os.fsync(fd)
            os.fsync(root_fd)
        finally:
            os.close(fd)
    return archive_root / capture_id, report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attachment", required=True, type=Path)
    parser.add_argument("--archive-root", required=True, type=Path)
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--expected-sha256")
    args = parser.parse_args(argv)
    try:
        supplied = decoded(read_input(args.metadata, 16384)) if args.metadata else None
        _, report = capture(
            args.attachment, args.archive_root, supplied, args.expected_sha256
        )
        # No private filename, provider, notes, record values or source path in stdout.
        print(
            replay.encoded(
                {
                    "status": "BLOCKED",
                    "intake_completed": True,
                    "attachment_sha256": report["attachment_sha256"],
                    "counts": report["counts"],
                    "document_errors": report["document_errors"],
                    "comparison_ready": False,
                }
            ).decode(),
            end="",
        )
        return 0  # Capture/diagnostic success, never scientific approval.
    except (OSError, ValueError, UnicodeError, replay.BundleError, RuntimeError):
        print('{"status":"intake_refused","comparison_ready":false}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
