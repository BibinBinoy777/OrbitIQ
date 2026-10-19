"""Read-only stored discovery and two-source investigation, not anomaly detection."""

import json
import math
import re
from datetime import UTC, datetime
from urllib.parse import parse_qs, urlsplit

from orbitiq.orbits.coordinates import earth_fixed, finite_vector
from orbitiq.orbits.earth_orientation import TransformationError
from orbitiq.orbits.elements import ELEMENT_UNITS, MAX_CATALOG_ID
from orbitiq.orbits.freshness import classify, utc
from orbitiq.services import analysis
from orbitiq.storage import BROWSE_SCAN, COUNT_BOUND, browse_snapshots

CAUTION = (
    "Differences between two orbital-data snapshots do not, by themselves, prove "
    "that a satellite performed a maneuver or experienced an anomaly. Further "
    "evidence and appropriate scientific analysis are required."
)
WRAPPED = {"RA_OF_ASC_NODE", "ARG_OF_PERICENTER", "MEAN_ANOMALY"}


def text(value, maximum):
    return value if isinstance(value, str) and 0 < len(value) <= maximum else None


def public_metadata(row, now, thresholds):
    issues = []
    try:
        raw = row.get("normalized_record")
        normalized = (
            json.loads(raw) if isinstance(raw, str) and len(raw) <= 8192 else {}
        )
        if not isinstance(normalized, dict):
            normalized = {}
    except (ValueError, TypeError):
        normalized = {}
    catalog = row.get("catalog_id")
    valid_catalog = type(catalog) is int and 1 <= catalog <= MAX_CATALOG_ID
    identity = (
        valid_catalog
        and type(normalized.get("NORAD_CAT_ID")) is int
        and (normalized["NORAD_CAT_ID"] == catalog)
    )
    if not identity:
        issues.append(
            "Catalog identity is missing or inconsistent; matching is unsafe."
        )
    name = text(row.get("object_name"), 128)
    object_id = text(normalized.get("OBJECT_ID"), 32)
    if not name or not name.strip():
        name = None
        issues.append("Satellite name is unavailable.")
    if not object_id:
        issues.append("International designator is unavailable.")
    epoch, retrieval = utc(row.get("orbital_epoch")), utc(row.get("retrieved_at"))
    if epoch is None:
        issues.append("Orbital epoch is unavailable or invalid.")
    if retrieval is None:
        issues.append(
            "Retrieval time is unavailable or invalid; chronology is unknown."
        )
    safe_source = None
    try:
        source = urlsplit(row.get("source_url") or "")
        if (
            valid_catalog
            and source.scheme == "https"
            and source.hostname in {"celestrak.org", "www.celestrak.org"}
            and not source.username
            and not source.password
            and source.port in (None, 443)
            and source.path == "/NORAD/elements/gp.php"
            and not source.fragment
            and parse_qs(source.query) == {"CATNR": [str(catalog)], "FORMAT": ["JSON"]}
        ):
            safe_source = row["source_url"]
    except (ValueError, TypeError):
        pass
    if safe_source is None:
        issues.append("Supported source provenance is unavailable.")
    checksum = row.get("response_sha256")
    if not isinstance(checksum, str) or not re.fullmatch(r"[a-f0-9]{64}", checksum):
        checksum = None
        issues.append("Source checksum is unavailable.")
    status = text(row.get("validation_status"), 128)
    if status != "structural_and_epoch_propagation_passed":
        issues.append("Expected ingestion validation status is unavailable.")
    if not text(row.get("validator_version"), 128) or not text(
        row.get("sgp4_version"), 32
    ):
        issues.append("Ingestion validator/model version is unavailable.")
    return {
        "id": row["id"],
        "catalog_id": catalog if valid_catalog else None,
        "object_name": name,
        "object_id": object_id,
        "identity_consistent": bool(identity),
        "orbital_epoch": epoch.isoformat() if epoch else None,
        "retrieved_at": retrieval.isoformat() if retrieval else None,
        "snapshot_created_at": None,
        "insertion_time_status": "not_recorded",
        "source_url": safe_source,
        "provider": "CelesTrak" if safe_source else None,
        "response_sha256": checksum,
        "validation_status": status,
        "validator_version": text(row.get("validator_version"), 128),
        "ingestion_sgp4_version": text(row.get("sgp4_version"), 32),
        "frame": text(normalized.get("REF_FRAME"), 16),
        "record_count": 1,
        "record_count_basis": "schema_2_single_satellite_snapshot",
        "metadata_issues": issues,
        "listing_validation": "metadata_only_not_full_provenance_verification",
        "freshness_info": classify(epoch, retrieval, as_of=now, policy=thresholds),
    }


def listing(path, **options):
    query = options.get("query", "").strip()
    if len(query) > 64 or any(ord(c) < 32 or ord(c) == 127 for c in query):
        raise analysis.AnalysisError(
            422, "invalid_search", "Search must be at most 64 printable characters"
        )
    if options.get("selected_only") and options.get("context_snapshot_id") is None:
        raise analysis.AnalysisError(
            422,
            "snapshot_context_required",
            "Choose a snapshot for selected-only search",
        )
    if (
        options.get("selected_only")
        and options.get("snapshot_id") is not None
        and options["snapshot_id"] != options.get("context_snapshot_id")
    ):
        raise analysis.AnalysisError(
            422, "invalid_scope", "Direct snapshot and selected-only scope disagree"
        )
    before, anchor = options.get("before_id"), options.get("anchor_id")
    if before is not None and anchor is not None and before > anchor:
        raise analysis.AnalysisError(
            422, "invalid_cursor", "Pagination cursor exceeds its history anchor"
        )
    data = analysis.storage_read(browse_snapshots, path, **{**options, "query": query})
    if data.get("context_missing"):
        raise analysis.AnalysisError(
            404, "snapshot_not_found", "Selected snapshot not found"
        )
    now, thresholds = datetime.now(UTC), analysis.policy()
    context = (
        public_metadata(data["context"], now, thresholds) if data["context"] else None
    )
    rows = data["rows"]
    records, scanned, cursor = [], 0, None
    more = len(rows) > BROWSE_SCAN
    for row in rows[:BROWSE_SCAN]:
        item = public_metadata(row, now, thresholds)
        candidates = [
            str(item["catalog_id"] or ""),
            item["object_name"] or "",
            item["object_id"] or "",
        ]
        matches = not query or any(
            query.casefold() == value.casefold()
            if data["match"] == "exact"
            else query.casefold() in value.casefold()
            for value in candidates
        )
        if matches and len(records) == data["limit"]:
            more = True
            break  # This lookahead match is intentionally not consumed.
        scanned += 1
        cursor = row["id"]
        if matches:
            item["membership"] = (
                "selected_snapshot_record"
                if context and item["id"] == context["id"]
                else "identifier_unreliable"
                if not item["identity_consistent"]
                else "historical_record_also_in_selected"
                if context
                and context["identity_consistent"]
                and item["catalog_id"] == context["catalog_id"]
                else "historical_only"
                if context and context["identity_consistent"]
                else "context_unknown"
                if context
                else "stored_record"
            )
            records.append(item)
    total = data["candidate_count"] if not query else None
    return {
        "snapshots": records,
        "evaluated_at": now.isoformat(),
        "order": "insertion_id_desc_not_retrieval_chronology",
        "anchor_id": data["anchor_id"],
        "has_more": more,
        "next_before_id": cursor if more else None,
        "page_size": data["limit"],
        "returned_count": len(records),
        "scanned_count": scanned,
        "scan_limit": BROWSE_SCAN,
        "total_count": total,
        "total_count_status": "not_computed_for_search"
        if query
        else "exact_within_anchor"
        if total is not None
        else "unknown_exceeds_bounded_count",
        "count_bound": COUNT_BOUND,
        "context_snapshot": context,
        "storage_model": "one_satellite_record_per_snapshot",
        "global_latest_retrieval_known": False,
        "warnings": [
            "ID ordering is insertion order, not element or retrieval chronology.",
            (
                "No match means not found in inspected stored records, not "
                "absent from orbit."
            ),
            "Search can return an empty scan window with more history to examine.",
            "Counts exclude records appended above the fixed history anchor.",
        ],
    }


def source_for_comparison(path, snapshot_id):
    page = listing(path, snapshot_id=snapshot_id)
    if not page["snapshots"]:
        raise analysis.AnalysisError(404, "snapshot_not_found", "Snapshot not found")
    summary = page["snapshots"][0]
    try:
        item, elements = analysis.load_snapshot(path, snapshot_id)
        return summary, item, elements, None
    except analysis.AnalysisError as error:
        if error.code != "snapshot_invalid":
            # Malformed stored JSON is rejected by the older strict detail reader.
            if error.code != "storage_unavailable":
                raise
        return (
            summary,
            None,
            None,
            {
                "code": "snapshot_invalid",
                "message": (
                    "Snapshot cannot pass scientific provenance validation; "
                    "metadata remain inspectable."
                ),
            },
        )


def chronology(first, second):
    a, b = utc(first["retrieved_at"]), utc(second["retrieved_at"])
    if a is None or b is None:
        return {
            "status": "unknown",
            "basis": "stored_retrieval_time",
            "older_snapshot_id": None,
            "newer_snapshot_id": None,
        }
    if a == b:
        return {
            "status": "ambiguous_equal_retrieval_times",
            "basis": "stored_retrieval_time",
            "older_snapshot_id": None,
            "newer_snapshot_id": None,
        }
    return {
        "status": "ordered",
        "basis": "stored_retrieval_time",
        "older_snapshot_id": first["id"] if a < b else second["id"],
        "newer_snapshot_id": second["id"] if a < b else first["id"],
    }


def element_differences(first, second):
    left, right = first.model_dump(by_alias=True), second.model_dump(by_alias=True)
    differences = [
        {
            "field": field,
            "unit": unit,
            "first_value": left[field],
            "second_value": right[field],
            "difference": (right[field] - left[field] + 180) % 360 - 180
            if field in WRAPPED
            else right[field] - left[field],
            "convention": "wrapped_second_minus_first_[-180,180)"
            if field in WRAPPED
            else "second_minus_first",
        }
        for field, unit in ELEMENT_UNITS.items()
        if field != "EPOCH"
    ]
    if not all(math.isfinite(row["difference"]) for row in differences):
        raise ValueError("Element subtraction exceeds finite numeric range")
    return differences


def common_state(sources, at, frame):
    results, errors = [], []
    for _, item, elements, invalid in sources:
        try:
            if invalid:
                raise analysis.AnalysisError(422, invalid["code"], invalid["message"])
            result = analysis.position_from_snapshot(item, elements, at)
            if frame == "ITRS":
                result = earth_fixed(result)
            results.append(result)
            errors.append(None)
        except (analysis.AnalysisError, TransformationError) as error:
            results.append(None)
            errors.append(
                {
                    "code": error.code,
                    "message": str(error)
                    if isinstance(error, TransformationError)
                    else error.message,
                }
            )
    state = {
        "status": "unavailable",
        "evaluation_at": at.isoformat(),
        "frame": frame,
        "units": {"position": "km", "velocity": "km/s"},
        "first": results[0],
        "second": results[1],
        "errors": errors,
        "difference_position_km": None,
        "difference_velocity_km_s": None,
        "separation_km": None,
        "relative_speed_km_s": None,
        "difference_convention": "second_minus_first",
    }
    if any(errors):
        return state
    try:
        for source, result in zip(sources, results, strict=True):
            origin = result if frame == "TEME" else result.get("teme", {})
            if (
                utc(result.get("at")) != at
                or result.get("frame") != frame
                or result.get("time_system") != "UTC"
                or result.get("kind") != "calculated"
                or result.get("origin") != "Earth center"
                or result.get("units", {}).get("position") != "km"
                or result.get("units", {}).get("velocity") != "km/s"
                or origin.get("snapshot_id") != source[0]["id"]
                or origin.get("catalog_id") != source[0]["catalog_id"]
                or origin.get("response_sha256") != source[0]["response_sha256"]
                or utc(origin.get("orbital_epoch")) != utc(source[0]["orbital_epoch"])
                or utc(origin.get("retrieved_at")) != utc(source[0]["retrieved_at"])
                or origin.get("frame") != "TEME"
                or origin.get("model") != "SGP4"
                or origin.get("gravity_model") != "WGS72"
            ):
                raise ValueError
            finite_vector(result.get("position_km"))
            finite_vector(result.get("velocity_km_s"))
        if frame == "ITRS":
            for result in results:
                eop = result.get("earth_orientation", {})
                if (
                    eop.get("auto_download") is not False
                    or eop.get("degraded_results_allowed") is not False
                ):
                    raise ValueError
            for key in ("sha256", "leap_seconds_sha256", "package_version", "policy"):
                if not results[0]["earth_orientation"].get(key) or (
                    results[0]["earth_orientation"][key]
                    != results[1]["earth_orientation"].get(key)
                ):
                    raise ValueError
        dp = [
            b - a
            for a, b in zip(
                results[0]["position_km"], results[1]["position_km"], strict=True
            )
        ]
        dv = [
            b - a
            for a, b in zip(
                results[0]["velocity_km_s"], results[1]["velocity_km_s"], strict=True
            )
        ]
        if not all(
            math.isfinite(x) for x in (*dp, *dv, math.hypot(*dp), math.hypot(*dv))
        ):
            raise ValueError
    except (ValueError, TypeError, KeyError, TransformationError):
        state.update(
            errors=[
                {
                    "code": "incompatible_states",
                    "message": (
                        "State identity, time, frame, units or numbers are "
                        "incompatible."
                    ),
                }
            ],
            first=None,
            second=None,
        )
        return state
    state.update(
        status="complete",
        difference_position_km=dp,
        difference_velocity_km_s=dv,
        separation_km=math.hypot(*dp),
        relative_speed_km_s=math.hypot(*dv),
    )
    return state


def compare(path, first_id, second_id, at=None, frame="TEME", category="all"):
    now = datetime.now(UTC)
    if at is not None:
        at = utc(at)
        if at is None:
            raise analysis.AnalysisError(
                422, "invalid_time", "Evaluation time must include a timezone"
            )
    sources = [
        source_for_comparison(path, first_id),
        source_for_comparison(path, second_id),
    ]
    a, b = sources[0][0], sources[1][0]
    invalid = any(s[3] for s in sources) or not all(
        s[0]["identity_consistent"] for s in sources
    )
    shared = not invalid and a["catalog_id"] == b["catalog_id"]
    records = (
        [
            {
                "category": "incompatible",
                "catalog_id": None,
                "first_snapshot_id": first_id,
                "second_snapshot_id": second_id,
            }
        ]
        if invalid
        else [
            {
                "category": "shared",
                "catalog_id": a["catalog_id"],
                "first_snapshot_id": first_id,
                "second_snapshot_id": second_id,
            }
        ]
        if shared
        else [
            {
                "category": "removed",
                "catalog_id": a["catalog_id"],
                "first_snapshot_id": first_id,
                "second_snapshot_id": None,
            },
            {
                "category": "added",
                "catalog_id": b["catalog_id"],
                "first_snapshot_id": None,
                "second_snapshot_id": second_id,
            },
        ]
    )
    counts = {
        c: sum(r["category"] == c for r in records)
        for c in ("shared", "added", "removed", "incompatible")
    }
    state = {"status": "not_requested", "evaluation_at": None, "frame": frame}
    if at is not None:
        state = (
            common_state(sources, at, frame)
            if shared
            else {
                "status": "unavailable",
                "evaluation_at": at.isoformat(),
                "frame": frame,
                "errors": [
                    {
                        "code": "no_compatible_match",
                        "message": (
                            "State subtraction requires the same validated NORAD "
                            "identity in both snapshots."
                        ),
                    }
                ],
            }
        )
    differences, element_status = [], "incompatible_or_no_shared_record"
    if shared:
        try:
            differences = element_differences(sources[0][2], sources[1][2])
            element_status = "complete"
        except (ValueError, ArithmeticError):
            element_status = "unavailable_numeric_range"
    return {
        "kind": "stored_snapshot_comparison",
        "evaluated_at": now.isoformat(),
        "first": a,
        "second": b,
        "is_self_comparison": first_id == second_id,
        "chronology": chronology(a, b),
        "counts": counts,
        "records": [
            r for r in records if category == "all" or r["category"] == category
        ],
        "filter": category,
        "matching_basis": "validated_NORAD_catalog_id_not_name",
        "element_differences": differences,
        "element_comparison_status": element_status,
        "source_errors": [s[3] for s in sources],
        "provenance_differences": [
            {
                "field": field,
                "first_value": a.get(field),
                "second_value": b.get(field),
                "status": "unknown"
                if a.get(field) is None or b.get(field) is None
                else "same"
                if a[field] == b[field]
                else "different",
            }
            for field in (
                "source_url",
                "response_sha256",
                "orbital_epoch",
                "retrieved_at",
                "validation_status",
                "validator_version",
                "ingestion_sgp4_version",
                "object_id",
            )
        ],
        "state_comparison": state,
        "assumptions": [
            "Each schema-2 snapshot stores exactly one satellite record.",
            (
                "Added means only in second; removed means only in first, "
                "regardless of retrieval chronology."
            ),
            (
                "Element differences may reflect epoch, fitting or source "
                "updates; they are not physical change measurements."
            ),
            (
                "State differences use second minus first at one common "
                "time; no covariance or uncertainty is quantified."
            ),
            (
                "SGP4 WGS72, geocentric TEME; optional Astropy ITRS retains"
                " strict local EOP/leap policies."
            ),
            (
                "A same-snapshot comparison is a self-check, not distinct "
                "historical evidence."
            ),
        ],
        "caution": CAUTION,
    }
