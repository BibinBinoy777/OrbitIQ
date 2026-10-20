"""Capture authoritative source evidence and existing backend calculations once."""

import hashlib
import json
import os
from datetime import UTC, datetime, timedelta
from importlib.metadata import PackageNotFoundError, version
from uuid import uuid4

from orbitiq.orbits.elements import ELEMENT_UNITS
from orbitiq.orbits.freshness import classify, utc
from orbitiq.reporting import InvestigationReport, ReportInvestigation
from orbitiq.services import analysis, ground_tracks, investigations

LIMITATIONS = [
    "Calculated orbital positions are not direct satellite observations.",
    "Independent observation-based prediction validation remains blocked; "
    "orbital prediction uncertainty is unquantified.",
    "Published numerical reference agreement does not establish universal "
    "real-world prediction accuracy or certify this investigation.",
    "Differences between element sets or calculated states do not independently "
    "establish a maneuver, anomaly, collision risk or operational safety.",
    "A stored payload checksum verifies its bytes, not provider authenticity "
    "or scientific correctness; no independent provider signature is recorded.",
    "This is a current recomputation from exact archived references, not a "
    "preserved original calculation. Exact replay additionally needs the same "
    "software and EOP/leap resources; those binaries/resources are not embedded.",
    "Browser-only saved UUID, title, private notes and creation time are excluded. "
    "The configuration identifier is not a server-owned or browser-saved record ID.",
]


def same_reference(ref, item):
    return (
        item.get("id", item.get("snapshot_id")) == ref.snapshot_id
        and item.get("catalog_id") == ref.catalog_id
        and utc(item.get("orbital_epoch")) == ref.orbital_epoch
        and utc(item.get("retrieved_at")) == ref.retrieved_at
        and item.get("response_sha256") == ref.response_sha256
    )


def checked_source(path, ref):
    item, elements = analysis.load_snapshot(path, ref.snapshot_id)
    if not same_reference(ref, item):
        raise analysis.AnalysisError(
            409,
            "report_source_mismatch",
            "Exact source identity, epoch, retrieval or checksum does not match. "
            "No newer source was substituted.",
        )
    return item, elements


def source_evidence(ref, item, role, now, *, freshness_policy=None):
    return {
        "role": role,
        "reference": ref.model_dump(mode="json"),
        "source_type": "celestrak_gp_omm_mean_elements",
        "provider": "CelesTrak",
        "source_url": item["source_url"],
        "object_name": item["normalized_record"]["OBJECT_NAME"],
        "object_id": item["normalized_record"]["OBJECT_ID"],
        "source_frame": "TEME",
        "epoch_time_system": "UTC",
        "snapshot_created_at": item.get("snapshot_inserted_at"),
        "snapshot_creation_status": "recorded"
        if item.get("snapshot_inserted_at")
        else "unknown_legacy",
        "observation_at": None,
        "observation_time_status": "not_applicable_mean_elements_not_observations",
        "publication_at": None,
        "publication_time_status": "not_recorded",
        "payload_hash": {
            "algorithm": "SHA-256",
            "value": item["response_sha256"],
            "scope": "Exact stored uncompressed CelesTrak GP JSON HTTP response "
            "body bytes, not normalized fields, headers or provider signatures.",
            "integrity_status": "verified_against_stored_bytes",
        },
        "provider_published_hash": None,
        "provider_hash_status": "not_recorded",
        "source_authenticity": "not_independently_verified",
        "validation_status": item["validation_status"],
        "validator_version": item["validator_version"],
        "ingestion_sgp4_version": item["sgp4_version"],
        "checks_performed_for_report": [
            "stored_payload_sha256_matches_bytes",
            "single_raw_record_matches_response",
            "normalized_elements_and_units_match_validated_source",
            "catalog_epoch_retrieval_source_url_and_recorded_provenance_checked",
            "requested_exact_reference_matches_archive",
        ],
        "freshness_info": classify(
            item["orbital_epoch"],
            item["retrieved_at"],
            as_of=now,
            policy=freshness_policy or analysis.policy(),
        ),
        "elements": {k: item["normalized_record"][k] for k in ELEMENT_UNITS},
        "element_units": dict(ELEMENT_UNITS),
    }


def package_version(name):
    try:
        return version(name)
    except PackageNotFoundError:
        return None  # Never manufacture a version when provenance is missing.


def build_report(path, definition):
    now = datetime.now(UTC)
    references = [definition.source]
    if definition.mode == "comparison":
        references.append(definition.comparison_source)
    captured = [checked_source(path, ref) for ref in references]
    sources = [
        source_evidence(ref, item, "primary" if i == 0 else "comparison", now)
        for i, (ref, (item, _)) in enumerate(zip(references, captured, strict=True))
    ]
    calculation = {"status": "not_requested", "data": None, "errors": []}
    try:
        if definition.mode == "position":
            data = analysis.position_from_snapshot(*captured[0], definition.at)
            calculation.update(status="complete", data=data)
        elif definition.mode == "ground-track":
            t = definition.track
            data = ground_tracks.track(
                path,
                definition.source.catalog_id,
                definition.source.snapshot_id,
                t.start,
                t.start + timedelta(minutes=t.duration_minutes),
                t.step_seconds,
            )
            if utc(data["points"][t.selected_index]["at"]) != definition.at:
                raise analysis.AnalysisError(
                    409, "report_source_mismatch", "Selected sample does not match."
                )
            calculation.update(status="complete", data=data)
        elif definition.mode == "comparison":
            data = investigations.compare(
                path,
                definition.source.snapshot_id,
                definition.comparison_source.snapshot_id,
                definition.at,
                definition.frame,
                definition.category,
            )
            state = data["state_comparison"]
            unavailable = (
                state["status"] == "unavailable"
                or data["element_comparison_status"] == "unavailable_numeric_range"
            )
            calculation.update(
                status="unavailable"
                if unavailable
                else "complete"
                if definition.at
                else "not_requested",
                data=data,
                errors=[e for e in state.get("errors", []) if e],
            )
            if data["element_comparison_status"] == "unavailable_numeric_range":
                calculation["errors"].append(
                    {
                        "code": "element_numeric_range",
                        "message": "Element difference unavailable.",
                    }
                )
    except analysis.AnalysisError as error:
        if error.code == "report_source_mismatch":
            raise
        calculation.update(
            status="unavailable",
            data=None,
            errors=[{"code": error.code, "message": error.message}],
        )

    # Sources are immutable, but a different archive could be mounted mid-request.
    # Recheck both exact references and calculation lineage, never substitute data.
    for ref in references:
        checked_source(path, ref)

    def check_lineage(value):
        if isinstance(value, dict):
            if "snapshot_id" in value and "response_sha256" in value:
                if not any(same_reference(ref, value) for ref in references):
                    raise analysis.AnalysisError(
                        409,
                        "report_source_mismatch",
                        "Calculation source changed during export.",
                    )
            for child in value.values():
                check_lineage(child)
        elif isinstance(value, list):
            for child in value:
                check_lineage(child)

    check_lineage(calculation["data"])
    if definition.mode == "comparison" and calculation["data"] is not None:
        for ref, side in zip(references, ["first", "second"], strict=True):
            if not same_reference(ref, calculation["data"][side]):
                raise analysis.AnalysisError(
                    409,
                    "report_source_mismatch",
                    "Comparison source changed during export.",
                )

    warnings = []
    for s in sources:
        if s["freshness_info"]["state"] != "fresh":
            warnings.append(
                f"Snapshot #{s['reference']['snapshot_id']} element freshness is "
                f"{s['freshness_info']['state']}; retrieval is not prediction accuracy."
            )
        if s["snapshot_creation_status"] == "unknown_legacy":
            warnings.append("A legacy snapshot insertion timestamp is not recorded.")

    def collect_warnings(value):
        if isinstance(value, dict):
            warnings.extend(value.get("warnings", []))
            for child in value.values():
                collect_warnings(child)
        elif isinstance(value, list):
            for child in value:
                collect_warnings(child)

    collect_warnings(calculation["data"])
    serialized = definition.model_dump(mode="json")
    canonical = json.dumps(
        serialized, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    identity = "configuration-sha256:" + hashlib.sha256(canonical.encode()).hexdigest()
    policy = os.environ.get("ORBITIQ_EOP_POLICY", "measured_or_predicted")
    terrestrial = (
        definition.frame == "ITRS" and getattr(definition, "at", None) is not None
    )
    return InvestigationReport(
        report_id=str(uuid4()),
        generated_at=now.isoformat(),
        status="partial" if calculation["status"] == "unavailable" else "complete",
        investigation=ReportInvestigation(
            id=identity,
            id_kind="configuration_sha256",
            title=f"NORAD {definition.source.catalog_id} · {definition.mode} · "
            f"snapshot #{definition.source.snapshot_id}"
            + (
                f" / #{definition.comparison_source.snapshot_id}"
                if definition.mode == "comparison"
                else ""
            ),
            title_origin="generated_from_verified_sources",
            definition=definition,
        ),
        sources=sources,
        calculation=calculation,
        validation={
            "status": "validated_with_warnings",
            "scope": "Exact stored source integrity/provenance checks and available "
            "backend calculations; not observation-based accuracy "
            "or source authentication.",
            "independent_observation_validation": "blocked",
            "prediction_uncertainty": "unquantified",
            "missing_data": [
                "provider_publication_time",
                "provider_published_hash",
                "browser_saved_metadata",
            ],
            "report_generation_is_scientific_certification": False,
        },
        methodology={
            "representation": (
                "Current backend recomputation from exact immutable references."
            ),
            "application": "OrbitIQ",
            "application_version": "0.1.0",
            "software_versions": {
                n: package_version(n) for n in ["sgp4", "astropy", "pyerfa"]
            },
            "calculation_method": (
                "SGP4 / WGS72; Astropy TEME to ITRS / WGS84 where requested"
            ),
            "source_frame": "TEME",
            "time_system": "UTC",
            "units": {
                "position": "km",
                "velocity": "km/s",
                "angles": "deg",
                "altitude": "km",
            },
            "eop_applicability": "required" if terrestrial else "not_applicable",
            "configured_eop_policy": policy
            if terrestrial and policy in {"measured_only", "measured_or_predicted"}
            else None,
            "eop_configuration_status": "not_applicable"
            if not terrestrial
            else "configured"
            if policy in {"measured_only", "measured_or_predicted"}
            else "invalid_configuration",
            "resource_provenance": (
                "Per-result earth_orientation contains actual EOP/leap hashes, "
                "policy, flags and versions when a transformation succeeds."
            ),
            "configuration_id_hash_scope": (
                "Version-1 validated definition, times normalized to UTC, JSON "
                "sorted keys, compact separators, ensure_ascii=true, UTF-8; "
                "array order retained. Not a source or export-package "
                "integrity hash/signature."
            ),
            "print_scope": (
                "Overview, evidence, selected state/sample, all returned track "
                "ITRS/geodetic rows and comparison values. Full per-sample "
                "derivation metadata remain in the JSON package."
            ),
        },
        limitations=LIMITATIONS,
        warnings=list(dict.fromkeys(warnings)),
    )
