"""Private offline OMM XML diagnostics, never propagation or scientific approval."""

import argparse
import io
import json
import runpy
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path

from orbitiq import replay
from orbitiq.orbits.elements import Elements
from pydantic import ValidationError
from sgp4 import omm

CSV = runpy.run_path(str(Path(__file__).with_name("inspect_historical_csv.py")))
INTAKE = CSV["INTAKE"]
Error = INTAKE["IntakeError"]
STRICT_POLICY = "strict-historical-omm-v1"
RETROSPECTIVE_POLICY = "historical-retrospective-admission-v1"
POLICY_PATH = (
    Path(__file__).resolve().parents[1] / "config" / (RETROSPECTIVE_POLICY + ".json")
)
# Version 1 is immutable. Extension needs a separately reviewed version.
POLICY_SHA256 = "617b281feaa8a8e53338d2bbe7ea8144fca96c4d201c245686b1ef3ac84002d4"
# These are reviewed intake targets for the same reference grid, not a general
# satellite alias resolver or authorization to execute either comparison.
TARGETS = {
    39533: {"prn": "G30", "svn": "G064", "cospar_id": "2014-008A"},
    35752: {"prn": "G05", "svn": "G050", "cospar_id": "2009-043A"},
}
REQUEST_START = datetime(2023, 12, 25, tzinfo=UTC)
REQUEST_STOP = datetime(2024, 1, 1, tzinfo=UTC)  # Exclusive calendar stop.
ELIGIBLE_START = datetime(2023, 12, 25, 23, 44, 42, tzinfo=UTC)
ELIGIBLE_STOP = datetime(2023, 12, 31, 23, 59, 42, tzinfo=UTC)
DECLARATIONS = {"CENTER_NAME", "REF_FRAME", "TIME_SYSTEM", "MEAN_ELEMENT_THEORY"}
GROUPS = {
    "metadata": {"OBJECT_NAME", "OBJECT_ID", *DECLARATIONS},
    "meanElements": {
        "EPOCH",
        "MEAN_MOTION",
        "ECCENTRICITY",
        "INCLINATION",
        "RA_OF_ASC_NODE",
        "ARG_OF_PERICENTER",
        "MEAN_ANOMALY",
    },
    "tleParameters": set(CSV["FIELDS"])
    - {
        "OBJECT_NAME",
        "OBJECT_ID",
        "EPOCH",
        "MEAN_MOTION",
        "ECCENTRICITY",
        "INCLINATION",
        "RA_OF_ASC_NODE",
        "ARG_OF_PERICENTER",
        "MEAN_ANOMALY",
    },
}
UNITS = {
    "MEAN_MOTION": {"rev/day"},
    "ECCENTRICITY": {"1"},
    "INCLINATION": {"deg"},
    "RA_OF_ASC_NODE": {"deg"},
    "ARG_OF_PERICENTER": {"deg"},
    "MEAN_ANOMALY": {"deg"},
    "BSTAR": {"1/ER"},
    "MEAN_MOTION_DOT": {"rev/day**2"},
    "MEAN_MOTION_DDOT": {"rev/day**3"},
}
SCHEMA_HINT = "{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation"


class BoundedTree(ET.TreeBuilder):
    """Refuse DTD/entities and excessive nesting before constructing the tree."""

    def __init__(self):
        super().__init__()
        self.depth = self.nodes = 0

    def doctype(self, name, pubid, system):
        raise Error("xml_doctype_forbidden")

    def start(self, tag, attrs):
        self.depth += 1
        self.nodes += 1
        if self.depth > 12 or self.nodes > 30000:
            raise Error("xml_structure_budget_exceeded")
        return super().start(tag, attrs)

    def end(self, tag):
        self.depth -= 1
        return super().end(tag)


def require(condition, reason):
    if not condition:
        raise Error(reason)


def children(node, allowed, required=(), attrs=()):
    require(set(node.attrib) <= set(attrs), "unsupported_xml_attributes")
    require(not (node.text or "").strip(), "unexpected_xml_text")
    tags = [child.tag for child in node]
    require(set(tags) <= set(allowed), "unexpected_xml_structure")
    require(set(required) <= set(tags), "missing_xml_structure")
    require(all(not (c.tail or "").strip() for c in node), "unexpected_xml_text")
    return tags


def fields(node, allowed):
    children(node, allowed | {"COMMENT"})
    values, units = {}, {}
    for child in node:
        require(not list(child), "nested_xml_field")
        require(set(child.attrib) <= {"units"}, "unsupported_xml_attributes")
        require(len(child.text or "") <= CSV["MAX_CELL"], "xml_field_budget")
        if child.tag == "COMMENT":
            continue
        require(child.tag not in values, "duplicate_xml_field")
        values[child.tag] = child.text or ""
        if "units" in child.attrib:
            units[child.tag] = child.attrib["units"]
    return values, units


def document(raw):
    root = ET.fromstring(raw, parser=ET.XMLParser(target=BoundedTree()))
    if root.tag == "ndm":
        children(root, {"omm"}, attrs={SCHEMA_HINT})
        messages = list(root)
    else:
        require(root.tag == "omm", "not_supported_omm_xml")
        messages = [root]
    require(
        1 <= len(messages) <= INTAKE["MAX_RECORDS"], "empty_or_oversized_omm_response"
    )
    headers, units = [], []
    for message in messages:
        tags = children(
            message, {"header", "body"}, {"body"}, {"id", "version", SCHEMA_HINT}
        )
        require(message.get("version") == "2.0", "unsupported_omm_version")
        require(message.get("id") == "CCSDS_OMM_VERS", "unsupported_omm_identifier")
        require(
            tags.count("header") <= 1 and tags.count("body") == 1,
            "duplicate_xml_structure",
        )
        header = message.find("header")
        claims, header_units = (
            fields(header, {"CREATION_DATE", "ORIGINATOR", "MESSAGE_ID"})
            if header is not None
            else ({}, {})
        )
        require(not header_units, "unsupported_header_units")
        body = message.find("body")
        tags = children(body, {"segment"}, {"segment"})
        for segment in body:
            tags = children(segment, {"metadata", "data"}, {"metadata", "data"})
            require(len(tags) == 2, "duplicate_xml_structure")
            data = segment.find("data")
            tags = children(
                data,
                {"meanElements", "tleParameters"},
                {"meanElements", "tleParameters"},
            )
            require(len(tags) == 2, "duplicate_xml_structure")
            record_units = {}
            for group, allowed in GROUPS.items():
                node = segment.find(group) if group == "metadata" else data.find(group)
                _, group_units = fields(node, allowed)
                record_units.update(group_units)
            headers.append(claims)
            units.append(record_units)
    require(len(headers) <= INTAKE["MAX_RECORDS"], "too_many_omm_records")
    # The locked library provides the OMM field extraction. The preflight above
    # prevents its permissive dictionary updates from concealing duplicate fields.
    records = list(omm.parse_xml(io.BytesIO(raw)))
    require(len(records) == len(headers), "omm_record_count_conflict")
    return records, headers, units


def inspect_record(source, header, units, index, norad_id=39533):
    source = {k: v for k, v in source.items() if k != "COMMENT"}
    typed, failures = CSV["typed_fields"](
        {k: v for k, v in source.items() if k in CSV["FIELDS"]}
    )
    typed.update({k: v for k, v in source.items() if k in DECLARATIONS})
    missing = sorted(
        (set(CSV["FIELDS"]) | DECLARATIONS) - {k for k, v in source.items() if v}
    )
    missing_header = sorted(
        {"CREATION_DATE", "ORIGINATOR"} - {k for k, v in header.items() if v}
    )
    errors = []
    if failures or missing or missing_header:
        errors.append("missing_or_invalid_required_fields")
    if any(value != value.strip() or not value for value in header.values()):
        errors.append("invalid_header_metadata")
    for field, unit in units.items():
        if unit not in UNITS.get(field, set()):
            errors.append("unsupported_explicit_units")
    epoch = creation = None
    for key, value in (
        ("EPOCH", source.get("EPOCH")),
        ("CREATION_DATE", header.get("CREATION_DATE")),
    ):
        try:
            at = INTAKE["exact_epoch"](value)
            if key == "EPOCH":
                epoch = at
            else:
                creation = at
        except (ValueError, OverflowError):
            errors.append("invalid_" + key.lower())
    try:
        Elements.model_validate(typed)  # Never initialize or propagate a satellite.
    except ValidationError as error:
        errors.append("invalid_gp_model_fields")
        failures += [
            {"field": str(e["loc"][0]) if e["loc"] else "__record__", "code": e["type"]}
            for e in error.errors(include_input=False, include_context=False)[:32]
        ]
    expected = TARGETS[norad_id]
    catalog_matches = typed.get("NORAD_CAT_ID") == norad_id
    cospar_matches = source.get("OBJECT_ID") == expected["cospar_id"]
    identity = catalog_matches and cospar_matches
    in_request = epoch is not None and REQUEST_START <= epoch < REQUEST_STOP
    temporal = epoch is not None and ELIGIBLE_START <= epoch <= ELIGIBLE_STOP
    exclusions = []
    if not identity:
        exclusions.append("wrong_or_missing_target_identity")
    if not in_request:
        exclusions.append("outside_requested_calendar_interval")
    if not temporal:
        exclusions.append("outside_protocol_gp_epoch_interval")
    return {
        "source_index": index,
        "parsed_fields_sha256": replay.digest(replay.encoded(source)),
        "catalog_id": typed.get("NORAD_CAT_ID"),
        "object_id": source.get("OBJECT_ID"),
        "object_name": source.get("OBJECT_NAME"),
        "identity_checks": {
            "norad_matches": catalog_matches,
            "cospar_matches": cospar_matches,
            "object_name_policy": "required_nonempty_label_not_a_display_name_match",
            "svn_check": "not_available_in_supported_omm_schema",
            "prn_check": "external_dated_mapping_not_inferred_from_object_name",
        },
        "epoch_source_text": source.get("EPOCH"),
        "epoch_utc": epoch.isoformat() if epoch else None,
        "creation_source_text": header.get("CREATION_DATE"),
        "header_metadata_claims": header,
        "creation_utc": creation.isoformat() if creation else None,
        "creation_meaning": "unverified_omm_header_claim_not_established_publication",
        "publication_time_utc": None,
        "historically_available_at": None,
        "missing_required_fields": missing,
        "missing_header_metadata": missing_header,
        "field_failures": failures,
        "validation_errors": sorted(set(errors)),
        "structure_and_fields_valid": not errors,
        "target_identity_matches": identity,
        "in_requested_interval": in_request,
        "protocol_temporal_eligible": temporal,
        "static_candidate": not errors and not exclusions,
        "exclusions": exclusions,
        "duplicate_source_indices": [],
    }


def _inspect_strict_attachment(
    raw, provenance=None, *, synthetic=False, norad_id=39533
):
    require(
        type(norad_id) is int and norad_id in TARGETS, "unsupported_target_norad_id"
    )
    require(
        isinstance(raw, bytes) and 0 < len(raw) <= INTAKE["MAX_BYTES"],
        "xml_attachment_byte_budget",
    )
    report = {
        "kind": "orbitiq_historical_omm_xml_inspection",
        "schema_version": 1,
        "evidence_class": "SYNTHETIC_TEST_ONLY"
        if synthetic
        else "UNVERIFIED_LOCAL_ATTACHMENT",
        "status": "BLOCKED",
        "scientific_status": "BLOCKED",
        "attachment_sha256": replay.digest(raw),
        "attachment_bytes": len(raw),
        "provenance": INTAKE["metadata"](provenance),
        "policy": {
            "target_norad_id": norad_id,
            "target_cospar_id": TARGETS[norad_id]["cospar_id"],
            "target_prn": TARGETS[norad_id]["prn"],
            "target_svn": TARGETS[norad_id]["svn"],
            "request_start_inclusive": REQUEST_START.isoformat(),
            "request_stop_exclusive": REQUEST_STOP.isoformat(),
            "eligible_epoch_start_inclusive": ELIGIBLE_START.isoformat(),
            "eligible_epoch_stop_inclusive": ELIGIBLE_STOP.isoformat(),
            "selection": "latest_unique_eligible_epoch_no_same_epoch_tiebreak",
        },
        "parsed_hash_scope": "parsed field text only; not XML bytes, headers or units",
        "xml_inspector_sha256": replay.digest(Path(__file__).read_bytes()),
        "document_errors": [],
        "records": [],
        "record_count": 0,
        "counts": {"enumerated": 0, "static_candidates": 0},
        "parsing_status": "BLOCKED",
        "time_coverage_utc": None,
        "catalog_ids": [],
        "duplicate_groups": [],
        "same_epoch_conflict_groups": [],
        "mixed_object_content": False,
        "document_identity_matches": False,
        "latest_unique_static_candidate_index": None,
        "selected_source_index": None,
        "selection_status": "BLOCKED",
        "scientifically_accepted_count": 0,
        "propagation_executed": False,
        "residuals_calculated": False,
        "comparison_ready": False,
        "remaining_gates": [
            "historical_input_provenance",
            "igs20_frame_alignment",
            "satellite_physical_reference_point",
            "reference_quality_and_uncertainty",
            "source_dependencies_and_independence",
            "protocol_review_and_explicit_approval",
        ],
    }
    try:
        records, headers, units = document(raw)
    except Error as error:
        report["document_errors"] = [str(error)]
        return report
    except (ET.ParseError, LookupError, ValueError):
        # Includes unknown/unsupported XML encodings, without parser snippets.
        report["document_errors"] = ["malformed_xml"]
        return report
    report["records"] = items = [
        inspect_record(r, h, u, i, norad_id)
        for i, (r, h, u) in enumerate(zip(records, headers, units, strict=True))
    ]
    report["record_count"] = len(items)
    report["counts"] = {
        "enumerated": len(items),
        "static_candidates": sum(r["static_candidate"] for r in items),
    }
    report["parsing_status"] = (
        "VERIFIED"
        if all(r["structure_and_fields_valid"] for r in items)
        else "PARTIALLY VERIFIED"
    )
    report["catalog_ids"] = sorted(
        {r["catalog_id"] for r in items if r["catalog_id"] is not None}
    )
    report["mixed_object_content"] = (
        len({(r["catalog_id"], r["object_id"]) for r in items}) > 1
    )
    report["document_identity_matches"] = all(
        r["target_identity_matches"] for r in items
    )
    epochs = [r["epoch_utc"] for r in items if r["epoch_utc"]]
    if epochs:
        report["time_coverage_utc"] = {"start": min(epochs), "stop": max(epochs)}
    counts = Counter(r["parsed_fields_sha256"] for r in items)
    for digest, count in counts.items():
        if count > 1:
            indices = [
                r["source_index"] for r in items if r["parsed_fields_sha256"] == digest
            ]
            report["duplicate_groups"].append(indices)
            for i in indices:
                items[i]["duplicate_source_indices"] = [j for j in indices if j != i]
    eligible = [r for r in items if r["static_candidate"]]
    for epoch in sorted({r["epoch_utc"] for r in items if r["epoch_utc"]}):
        same_epoch = [r for r in items if r["epoch_utc"] == epoch]
        if len({r["parsed_fields_sha256"] for r in same_epoch}) > 1:
            report["same_epoch_conflict_groups"].append(
                [r["source_index"] for r in same_epoch]
            )
    if eligible:
        latest = max(r["epoch_utc"] for r in eligible)
        tied = [r for r in eligible if r["epoch_utc"] == latest]
        if len(tied) == 1:
            report["latest_unique_static_candidate_index"] = tied[0]["source_index"]
        else:
            report["selection_status"] = "BLOCKED_same_epoch_ambiguity_no_fallback"
    return report


def _load_retrospective_policy():
    raw = POLICY_PATH.read_bytes()
    require(
        len(raw) <= 16384 and replay.digest(raw) == POLICY_SHA256,
        "policy_definition_integrity_failed",
    )
    policy = json.loads(raw)
    require(
        policy["id"] == RETROSPECTIVE_POLICY
        and policy["version"] == 1
        and policy["activation"]["status"] == "ACTIVE_EXPLICIT_SELECTION_ONLY",
        "policy_not_active",
    )
    return policy, replay.digest(raw)


def _acquisition_evidence_valid(evidence):
    root = Path(__file__).resolve().parents[1]
    name = Path(evidence["path"])
    path = root / name
    if name.is_absolute() or not path.resolve().is_relative_to(root):
        return False
    raw = path.read_bytes()
    return (
        len(raw) == evidence["bytes"]
        and replay.digest(raw) == evidence["sha256"]
        and evidence["source"] == "USER_REPORTED_CELESTRAK_REQUEST_AND_FULFILLMENT"
        and evidence["request_status"] == "SUBMITTED_USER_REPORTED"
        and evidence["fulfillment_status"] == "RECEIVED_USER_REPORTED"
    )


def _authorize_artifact(report, policy):
    matches = [
        a for a in policy["artifacts"] if a["sha256"] == report["attachment_sha256"]
    ]
    if len(matches) != 1:
        return None, ["input_hash_not_authorized"]
    artifact = matches[0]
    errors = []
    if artifact["bytes"] != report["attachment_bytes"]:
        errors.append("authorized_input_size_mismatch")
    if artifact["norad_id"] != report["policy"]["target_norad_id"]:
        errors.append("authorized_target_mismatch")
    if artifact["expected_record_count"] != report["record_count"]:
        errors.append("unexpected_record_count")
    if report["document_errors"]:
        errors.append("invalid_xml_document")
    if (
        not report["document_identity_matches"]
        or report["mixed_object_content"]
        or any(
            r["catalog_id"] != artifact["norad_id"]
            or r["object_id"] != artifact["cospar_id"]
            for r in report["records"]
        )
    ):
        errors.append("authorized_record_identity_mismatch")
    if not _acquisition_evidence_valid(artifact["acquisition_evidence"]):
        errors.append("acquisition_evidence_integrity_failed")
    return artifact, errors


def _reference_times(policy):
    ref = policy["reference"]
    first = INTAKE["exact_epoch"](ref["first_utc"])
    times = [
        first + timedelta(seconds=i * ref["cadence_seconds"])
        for i in range(ref["epoch_count"])
    ]
    require(
        len(times) == 96
        and ref["cadence_seconds"] == 900
        and ref["guard_seconds_inclusive"] == 604800
        and ref["forward_only"]
        and times[-1] == INTAKE["exact_epoch"](ref["last_utc"])
        and first == ELIGIBLE_STOP
        and times[-1] - timedelta(days=7) == ELIGIBLE_START,
        "reference_policy_mismatch",
    )
    return times


def _empty_header_exception(record):
    header = record["header_metadata_claims"]
    required = {"CREATION_DATE", "ORIGINATOR"}
    return (
        required <= header.keys()
        and all(header[k] == "" for k in required)
        and all(v and v == v.strip() for k, v in header.items() if k not in required)
        and record["missing_header_metadata"] == sorted(required)
        and not record["missing_required_fields"]
        and not record["field_failures"]
        and set(record["validation_errors"])
        == {
            "invalid_creation_date",
            "invalid_header_metadata",
            "missing_or_invalid_required_fields",
        }
    )


def _apply_admission_policy(report, policy_id):
    report["admission_policy_id"] = policy_id
    report["strict_policy_id"] = STRICT_POLICY
    result = report["retrospective_admission"] = {
        "policy_id": policy_id,
        "policy_version": 1,
        "status": "NOT_REQUESTED",
        "definition_sha256": None,
        "artifact_authorized": False,
        "refusal_reasons": [],
        "counts": {"admitted": 0, "held": 0, "rejected": 0},
        "scientific_status": "BLOCKED",
        "selected_source_index": None,
        "scientifically_qualified_count": 0,
        "comparison_authorized": False,
    }
    for record in report["records"]:
        record["strict_policy_outcome"] = (
            "STATIC_CANDIDATE"
            if record["static_candidate"]
            else "REJECTED_STATIC_CANDIDATE"
        )
        record["retrospective_admission"] = {
            "policy_id": policy_id,
            "policy_version": 1,
            "disposition": "NOT_APPLIED",
            "metadata_status": "NOT_ASSESSED_BY_V1",
            "reasons": [],
            "scientific_status": "BLOCKED",
        }
    if policy_id == STRICT_POLICY:
        return report
    try:
        policy, digest = _load_retrospective_policy()
        result["definition_sha256"] = digest
        artifact, errors = _authorize_artifact(report, policy)
        times = _reference_times(policy)
    except (OSError, ValueError, KeyError, TypeError):
        artifact, errors, times = None, ["policy_or_acquisition_evidence_invalid"], []
    result["status"] = "REFUSED" if errors else "APPLIED"
    result["refusal_reasons"] = errors
    result["artifact_authorized"] = not errors
    if not errors:
        result["source_evidence"] = artifact["acquisition_evidence"]
        result["activation"] = policy["activation"]
    conflicting = {i for group in report["same_epoch_conflict_groups"] for i in group}
    for r in report["records"]:
        row = r["retrospective_admission"]
        waived = _empty_header_exception(r)
        row["metadata_status"] = (
            "PARTIAL — PROVIDER-EXPORTED MESSAGE PROVENANCE UNAVAILABLE"
            if waived
            else "STRICT_HEADER_CHECKS_SATISFIED"
            if r["structure_and_fields_valid"]
            else "FAILED_REQUIRED_METADATA_OR_FIELDS"
        )
        row["provenance_status"] = "PARTIAL"
        reasons = list(errors)
        if not errors:
            try:
                epoch = INTAKE["exact_epoch"](r["epoch_source_text"])
            except (ValueError, OverflowError):
                epoch = None
            passed = [
                epoch is not None and abs(t - epoch) <= timedelta(days=7) for t in times
            ]
            forward = epoch is not None and epoch <= times[0]
            row.update(
                reference_epochs_checked=96,
                age_guard_pass_count=sum(passed),
                forward_only_pass=forward,
                age_guard_failed_indices=[
                    i for i, valid in enumerate(passed) if not valid
                ],
            )
            if not (r["structure_and_fields_valid"] or waived):
                reasons.append("other_strict_validation_failed")
            if not r["target_identity_matches"] or not r["in_requested_interval"]:
                reasons.append("identity_or_request_interval_failed")
            if not forward or not all(passed):
                reasons.append("original_full_window_temporal_rule_failed")
        if reasons:
            disposition, count = "REJECTED", "rejected"
        elif r["duplicate_source_indices"] or r["source_index"] in conflicting:
            disposition, count = "HOLD", "held"
            reasons = ["unresolved_duplicate_or_same_epoch_conflict"]
        else:
            disposition, count = (
                "ADMITTED_FOR_FURTHER_SCIENTIFIC_QUALIFICATION",
                "admitted",
            )
        row.update(disposition=disposition, reasons=reasons)
        result["counts"][count] += 1
    return report


def inspect_attachment(
    raw,
    provenance=None,
    *,
    synthetic=False,
    norad_id=39533,
    admission_policy=STRICT_POLICY,
):
    require(
        admission_policy in {STRICT_POLICY, RETROSPECTIVE_POLICY},
        "unsupported_admission_policy",
    )
    report = _inspect_strict_attachment(
        raw, provenance, synthetic=synthetic, norad_id=norad_id
    )
    return _apply_admission_policy(report, admission_policy)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attachment", required=True, type=Path)
    parser.add_argument("--archive-root", required=True, type=Path)
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--expected-sha256")
    parser.add_argument(
        "--admission-policy",
        choices=[STRICT_POLICY, RETROSPECTIVE_POLICY],
        default=STRICT_POLICY,
        help="Explicit admission only; never enables comparison",
    )
    parser.add_argument(
        "--norad-id",
        type=int,
        choices=sorted(TARGETS),
        default=39533,
        help="Reviewed intake target; default preserves G30. Never enables comparison.",
    )
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="Label test evidence only; never enables acceptance",
    )
    args = parser.parse_args(argv)
    try:
        provenance = (
            INTAKE["decoded"](INTAKE["read_input"](args.metadata, 16384))
            if args.metadata
            else None
        )
        _, report = INTAKE["capture"](
            args.attachment,
            args.archive_root,
            provenance,
            args.expected_sha256,
            inspector=lambda raw, supplied: inspect_attachment(
                raw,
                supplied,
                synthetic=args.synthetic,
                norad_id=args.norad_id,
                admission_policy=args.admission_policy,
            ),
        )
        print(
            replay.encoded(
                {
                    "evidence_class": report["evidence_class"],
                    "status": "BLOCKED",
                    "intake_completed": True,
                    "attachment_sha256": report["attachment_sha256"],
                    "attachment_bytes": report["attachment_bytes"],
                    "target_norad_id": report["policy"]["target_norad_id"],
                    "document_identity_matches": report["document_identity_matches"],
                    "mixed_object_content": report["mixed_object_content"],
                    "counts": report["counts"],
                    "parsing_status": report["parsing_status"],
                    "document_errors": report["document_errors"],
                    "admission_policy_id": report["admission_policy_id"],
                    "admission_policy_version": report["retrospective_admission"][
                        "policy_version"
                    ],
                    "policy_definition_sha256": report["retrospective_admission"][
                        "definition_sha256"
                    ],
                    "strict_policy_id": report["strict_policy_id"],
                    "admission_counts": report["retrospective_admission"]["counts"],
                    "retrospective_status": report["retrospective_admission"]["status"],
                    "policy_refusal_reasons": report["retrospective_admission"][
                        "refusal_reasons"
                    ],
                    "comparison_ready": False,
                }
            ).decode(),
            end="",
        )
        return (
            1
            if (
                report["document_errors"]
                or report["retrospective_admission"]["status"] == "REFUSED"
            )
            else 0
        )
    except (OSError, ValueError, UnicodeError, replay.BundleError, RuntimeError):
        print(
            replay.encoded(
                {
                    "evidence_class": (
                        "SYNTHETIC_TEST_ONLY"
                        if args.synthetic
                        else "UNVERIFIED_LOCAL_ATTACHMENT"
                    ),
                    "status": "intake_refused",
                    "admission_policy_id": args.admission_policy,
                    "admission_policy_version": 1,
                    "strict_policy_id": STRICT_POLICY,
                    "comparison_ready": False,
                }
            ).decode(),
            end="",
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
