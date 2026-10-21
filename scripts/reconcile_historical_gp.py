"""Offline replacement comparison, never source repair for scientific ingestion.

Only after a replacement is supplied can a pinned, previously recorded syntax
assessment be replayed IN MEMORY to inspect the original's comparison view.
That view is never returned as GP input, saved, propagated or accepted. A matched
replacement still requires independent provenance and scientific qualification.
"""

import json
import re
import runpy
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from orbitiq import replay
from orbitiq.replay_json import decoded

INTAKE = runpy.run_path(str(Path(__file__).with_name("inspect_historical_gp.py")))
LEADING_DECIMAL = re.compile(r"-?\.\d+(?:[eE][+-]?\d+)?")


def checked(raw, expected, bound):
    if (
        not isinstance(raw, bytes)
        or not 0 < len(raw) <= bound
        or not isinstance(expected, str)
        or not INTAKE["HASH"].fullmatch(expected)
        or replay.digest(raw) != expected
    ):
        raise ValueError("unverified_or_over_budget_comparison_bytes")


def exact_records(raw):
    # Reuse strict JSON's existing duplicate-key, finite-number and work budgets
    # BEFORE obtaining Decimal numbers for exact semantic comparison.
    decoded(raw)
    value = json.loads(raw, parse_float=Decimal)
    records = [value] if isinstance(value, dict) else value
    if not isinstance(records, list) or not 1 <= len(records) <= INTAKE["MAX_RECORDS"]:
        raise ValueError("unsupported_record_structure")
    return records


def comparison_view(original, assessment):
    """Replay only nine anchored insertions from an existing diagnostic ledger.

    This is comparison-only, not a new repair detector or an ingestion fallback.
    The trusted caller must independently review the assessment. Hash anchoring
    and Decimal equality cannot authenticate the producer or replace that review.
    """
    if (
        not isinstance(assessment, dict)
        or assessment.get("kind") != "orbitiq_historical_attachment_format_diagnostic"
        or assessment.get("original_sha256") != replay.digest(original)
        or assessment.get("original_bytes") != len(original)
        or assessment.get("original_strict_json_valid") is not False
        or not isinstance(assessment.get("edits"), list)
        or len(assessment["edits"]) != 9
        or any(not isinstance(edit, dict) for edit in assessment["edits"])
    ):
        raise ValueError("incompatible_recorded_assessment")
    text = original.decode("ascii")
    masked = list(text)
    offset, decoder = 0, json.JSONDecoder()
    while offset < len(text):
        if text[offset] == '"':
            _, end = decoder.raw_decode(text, offset)
            masked[offset:end] = " " * (end - offset)
            offset = end
        else:
            offset += 1
    edits, previous = assessment["edits"], -1
    for edit in edits:
        start, end = (
            edit["start_byte_in_original"],
            edit["stop_byte_exclusive_in_original"],
        )
        if (
            type(start) is not int
            or type(end) is not int
            or not previous <= start < end
        ):
            raise ValueError("invalid_edit_offsets")
        before = text[start:end]
        after = "-0" + before[1:] if before.startswith("-.") else "0" + before
        left, right = text[:start].rstrip(), text[end:].lstrip()
        if (
            not LEADING_DECIMAL.fullmatch(before)
            or "".join(masked[start:end]) != before
            or not left
            or left[-1] not in ":[,"
            or not right
            or right[0] not in ",}]"
            or edit["original_token"] != before
            or edit["probe_token"] != after
            or Decimal(before) != Decimal(after)
        ):
            raise ValueError("unapproved_or_non_numeric_edit")
        previous = end
    probe = text
    for edit in reversed(edits):
        probe = (
            probe[: edit["start_byte_in_original"]]
            + edit["probe_token"]
            + probe[edit["stop_byte_exclusive_in_original"] :]
        )
    raw = probe.encode("ascii")
    if replay.digest(raw) != assessment.get("probe_sha256"):
        raise ValueError("recorded_comparison_view_hash_mismatch")
    return raw


def identity(record):
    return (
        record["NORAD_CAT_ID"],
        record["OBJECT_ID"],
        INTAKE["exact_epoch"](record["EPOCH"]).isoformat(),
    )


def numeric(value):
    return type(value) in {int, Decimal}


def representation(value):
    if isinstance(value, Decimal):
        t = value.as_tuple()
        return ("decimal", t.sign, t.digits, t.exponent)
    return (type(value).__name__, value)


def flat_source_tokens(raw):
    """Lexemes of an already pinned/checked flat original, for CSV comparison only.

    This does not accept input for ingestion. The nine-edit ledger and strict
    comparison view must have passed before this function is called.
    """
    text, decoder = raw.decode("ascii"), json.JSONDecoder()
    records, record, offset = [], None, 0
    number = re.compile(r"-?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
    while offset < len(text):
        char = text[offset]
        if char == "{":
            if record is not None:
                raise ValueError("nested_original_requires_separate_review")
            record = {}
        elif char == "}":
            if record is None:
                raise ValueError("invalid_flat_record")
            records.append(record)
            record = None
        elif char == '"':
            value, stop = decoder.raw_decode(text, offset)
            cursor = stop
            while cursor < len(text) and text[cursor].isspace():
                cursor += 1
            if cursor < len(text) and text[cursor] == ":":
                cursor += 1
                while cursor < len(text) and text[cursor].isspace():
                    cursor += 1
                if record is None:
                    raise ValueError("flat_record_required")
                if text[cursor] == '"':
                    record[value], stop = decoder.raw_decode(text, cursor)
                elif match := number.match(text, cursor):
                    record[value] = match[0]
                    stop = match.end()
                else:
                    raise ValueError("flat_scalar_gp_fields_required")
            offset = stop
            continue
        offset += 1
    return records


def reconcile(
    original_raw=None,
    assessment_raw=None,
    replacement_raw=None,
    *,
    original_sha256=None,
    assessment_sha256=None,
    replacement_sha256=None,
    replacement_format="json",
    original_provenance=None,
    replacement_provenance=None,
):
    result = {
        "kind": "orbitiq_historical_gp_reconciliation",
        "schema_version": 1,
        "status": "BLOCKED",
        "reasons": [],
        "original_count": None,
        "replacement_count": None,
        "matched_records": [],
        "added_records": [],
        "removed_records": [],
        "ambiguous_identities": [],
        "field_differences": [],
        "representation_differences": [],
        "adapter_numeric_type_differences": [],
        "semantic_match": False,
        "comparison_ready": False,
        "source_accepted": False,
        "adapter_operational": False,
        "prediction_evaluations": 0,
        "residuals": None,
        "normalized_observations": [],
        "historical_availability": None,
        "forecast_eligible": False,
        "qualification_gates": INTAKE["gates"](),
        "independent_assessment_review": "not_established_by_this_tool",
        "scope": "comparison diagnostics only; never science approval or GP import",
        "replacement_format": replacement_format,
        "source_token_differences": [],
        "field_comparisons": [],
    }
    if replacement_raw is None:
        result["reasons"] = ["corrected_provider_export_not_supplied"]
        return result  # No original decoding, ledger replay or real-data validation.
    try:
        checked(replacement_raw, replacement_sha256, INTAKE["MAX_BYTES"])
        result["replacement_sha256"] = replacement_sha256
        if replacement_format == "csv":
            csv_tool = runpy.run_path(
                str(Path(__file__).with_name("inspect_historical_csv.py"))
            )
            inspected = csv_tool["inspect_attachment"](
                replacement_raw, replacement_provenance
            )
            result["qualification_gates"] = inspected["qualification_gates"]
        elif replacement_format == "json":
            inspected = INTAKE["inspect_attachment"](
                replacement_raw, replacement_provenance
            )
        else:
            raise ValueError("unsupported_explicit_replacement_format")
        result["replacement_inspection"] = inspected
        if inspected["document_errors"]:
            raise ValueError("replacement_explicit_format_refused")
        result["replacement_count"] = inspected["counts"]["enumerated"]
        if inspected["counts"]["excluded"]:
            raise ValueError("replacement_contains_invalid_or_duplicate_records")
        checked(original_raw, original_sha256, INTAKE["MAX_BYTES"])
        checked(assessment_raw, assessment_sha256, 65536)
        assessment = decoded(assessment_raw)
        view = comparison_view(original_raw, assessment)
        original_inspection = INTAKE["inspect_attachment"](view, original_provenance)
        result["original_inspection"] = original_inspection
        if (
            original_inspection["document_errors"]
            or original_inspection["counts"]["excluded"]
        ):
            raise ValueError("original_comparison_view_not_model_compatible_or_unique")
        before = exact_records(view)
        if replacement_format == "csv":
            after = [
                csv_tool["exact_record"](row["source_fields"])
                for row in inspected["records"]
            ]
            original_tokens = flat_source_tokens(original_raw)
            if len(original_tokens) != len(before):
                raise ValueError("original_source_token_count_mismatch")
            result["provenance_comparison"] = {
                "original": original_inspection["provenance"],
                "csv": inspected["provenance"],
                "authentication_established_by_value_match": False,
                "original_format": "malformed_JSON",
                "csv_format": "CSV_not_corrected_JSON",
                "assessment_edit_count": len(assessment["edits"]),
                "asserted_metadata_differences": [
                    field
                    for field in sorted(INTAKE["METADATA_FIELDS"])
                    if original_inspection["provenance"]["asserted"][field]
                    != inspected["provenance"]["asserted"][field]
                ],
            }
        else:
            after = exact_records(replacement_raw)
        result.update(
            original_sha256=original_sha256,
            assessment_sha256=assessment_sha256,
            comparison_view_sha256=replay.digest(view),
            original_count=len(before),
        )
        grouped = []
        for records in (before, after):
            groups = defaultdict(list)
            for index, record in enumerate(records):
                groups[identity(record)].append(index)
            grouped.append(groups)
        old, new = grouped
        for key in sorted(old.keys() | new.keys()):
            oi, ni = old.get(key, []), new.get(key, [])
            item = {
                "identity": list(key),
                "original_indices": oi,
                "replacement_indices": ni,
            }
            if len(oi) > 1 or len(ni) > 1:
                result["ambiguous_identities"].append(item)
            elif not oi:
                result["added_records"].append(item)
            elif not ni:
                result["removed_records"].append(item)
            else:
                result["matched_records"].append(item)
                left, right = before[oi[0]], after[ni[0]]
                for field in sorted(left.keys() | right.keys()):
                    entry = {**item, "field": field}
                    if replacement_format == "csv":
                        old_token = original_tokens[oi[0]].get(field)
                        new_token = inspected["records"][ni[0]]["source_fields"].get(
                            field
                        )
                        result["field_comparisons"].append(
                            {
                                **entry,
                                "original_source_text": old_token,
                                "csv_source_text": new_token,
                                "value_equal": field in left
                                and field in right
                                and left[field] == right[field],
                            }
                        )
                        if old_token != new_token:
                            result["source_token_differences"].append(
                                {
                                    **entry,
                                    "original_source_text": old_token,
                                    "csv_source_text": new_token,
                                    "exponent_case_only": isinstance(old_token, str)
                                    and isinstance(new_token, str)
                                    and old_token.lower() == new_token.lower()
                                    and numeric(left.get(field))
                                    and numeric(right.get(field)),
                                }
                            )
                    if field not in left or field not in right:
                        entry["reason"] = (
                            "field_added" if field not in left else "field_removed"
                        )
                        result["field_differences"].append(entry)
                    elif isinstance(left[field], (dict, list)) or isinstance(
                        right[field], (dict, list)
                    ):
                        result["field_differences"].append(
                            {**entry, "reason": "nested_field_requires_separate_review"}
                        )
                    elif numeric(left[field]) and numeric(right[field]):
                        if Decimal(left[field]) != Decimal(right[field]):
                            result["field_differences"].append(
                                {**entry, "reason": "numeric_value_changed"}
                            )
                        elif (
                            representation(Decimal(old_token))
                            != representation(Decimal(new_token))
                            if replacement_format == "csv"
                            else representation(left[field])
                            != representation(right[field])
                        ):
                            result["representation_differences"].append(
                                {
                                    **entry,
                                    "reason": (
                                        "numeric_representation_or_precision_changed"
                                    ),
                                }
                            )
                        if replacement_format == "csv" and type(
                            left[field]
                        ) is not type(right[field]):
                            result["adapter_numeric_type_differences"].append(
                                {
                                    **entry,
                                    "original_comparison_type": type(
                                        left[field]
                                    ).__name__,
                                    "csv_exact_comparison_type": type(
                                        right[field]
                                    ).__name__,
                                    "reason": (
                                        "explicit_csv_schema_typing_not_source_text_change"
                                    ),
                                }
                            )
                    elif (
                        type(left[field]) is not type(right[field])
                        or left[field] != right[field]
                    ):
                        result["field_differences"].append(
                            {**entry, "reason": "field_value_or_type_changed"}
                        )
        if any(
            result[k]
            for k in (
                "added_records",
                "removed_records",
                "ambiguous_identities",
                "field_differences",
            )
        ):
            result["reasons"] = [
                "unexplained_record_or_field_discrepancy_acceptance_stopped"
            ]
        else:
            result["semantic_match"] = True
            result["status"] = "PARTIAL"
            result["reasons"] = [
                "content_comparison_only_provenance_and_science_unqualified"
            ]
        if result["representation_differences"]:
            result["reasons"].append(
                "numeric_representation_or_precision_requires_review"
            )
        result["source_order_preserved"] = (
            len(before) == len(after)
            and len(result["matched_records"]) == len(before)
            and all(
                item["original_indices"] == item["replacement_indices"]
                for item in result["matched_records"]
            )
        )
    except (
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        UnicodeError,
        replay.BundleError,
    ):
        result["reasons"] = ["strict_input_or_pinned_comparison_assessment_refused"]
    return result
