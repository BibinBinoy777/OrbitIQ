"""Bounded, read-only history interpretation using existing source/comparison rules."""

import hashlib
import json
from datetime import UTC, datetime

from orbitiq.orbits.elements import ELEMENT_UNITS
from orbitiq.orbits.freshness import classify, utc
from orbitiq.reporting import SourceReference
from orbitiq.services import analysis, investigations
from orbitiq.services.reports import package_version

VERSION = 1
MAX_POINTS = 20
FIELDS = ("INCLINATION", "ECCENTRICITY", "MEAN_MOTION")
CATEGORIES = {
    "informational": "Recorded facts or calculated differences; no physical severity.",
    "incomplete_data": (
        "Insufficient coverage or metadata; absence is not a negative finding."
    ),
    "stale_source_data": (
        "Element age exceeds the existing configured freshness policy."
    ),
    "comparison_unavailable": (
        "Compatible directional element comparison is not supported."
    ),
    "validation_failure": (
        "Stored source fails existing integrity/provenance validation."
    ),
}
LIMITATIONS = [
    "Published mean-element sets are source estimates, not direct observations.",
    "Element differences may reflect epochs, estimation or source updates, physical "
    "motion or data quality; these inputs cannot distinguish those explanations.",
    (
        "No maneuver, anomaly, collision-risk or operational-safety "
        "conclusion is supported."
    ),
    (
        "Two records support pairwise changes only. More samples alone "
        "do not establish "
        "a reliable long-term trend or prediction. No fit, "
        "interpolation or extrapolation is used."
    ),
    "Only the inspected insertion-ID window is analyzed. Chronology is retrieval "
    "time, not insertion ID; element epochs are separately checked for reversal.",
    (
        "Intervals between samples do not establish provider outages "
        "or expected collection cadence."
    ),
    "Checksums validate stored bytes, not independent provider authenticity.",
    (
        "Independent observation-based prediction validation is "
        "blocked; uncertainty is unquantified."
    ),
    (
        "Finding replay is not implemented by the Phase 10 format. "
        "A comparison capture "
        "recipe reproduces underlying calculations only; it is not an"
        " existing evidence package."
    ),
]
RULES = {
    "coverage": "Count provenance-validated records in the inspected window.",
    "partial_window": (
        "The bounded window does not contain the complete anchored satellite history."
    ),
    "metadata": (
        "Required public metadata issues or missing insertion timestamp are recorded."
    ),
    "validation": "Existing full source validation rejects this persisted record.",
    "freshness": (
        "Existing classify(epoch,retrieval,as_of,configured_policy) is not fresh."
    ),
    "chronology": (
        "Retrieval order is unknown/equal, epochs conflict, or payloads repeat."
    ),
    "interval": (
        "Retrieval interval exceeds configured stale_hours; a "
        "coverage flag, not an outage."
    ),
    "epoch_interval": (
        "Epoch separation exceeds configured stale_hours; no accuracy inference."
    ),
    "comparison": "Existing comparison service rejects compatible element subtraction.",
    "element_change": (
        "Existing element_differences: second minus first; inclination is not wrapped."
    ),
}


def encoded(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def reference(summary):
    return {
        "snapshot_id": summary["id"],
        **{
            k: summary[k]
            for k in ("catalog_id", "response_sha256", "retrieved_at", "orbital_epoch")
        },
    }


def capture_definition(first, second, directional):
    if not directional:
        return None
    # No orbital calculation or resource maintenance is performed here. The recipe
    # requests a bounded historical TEME calculation only when both epochs support it.
    a, b = (utc(s["orbital_epoch"]) for s in (first, second))
    at = b.isoformat() if abs((b - a).total_seconds()) <= 7 * 86400 else None
    return {
        "schema_version": 1,
        "mode": "comparison",
        "frame": "TEME",
        "at": at,
        "source": SourceReference.model_validate(reference(first)).model_dump(
            mode="json"
        ),
        "comparison_source": SourceReference.model_validate(
            reference(second)
        ).model_dump(mode="json"),
        "category": "all",
    }


def analyze_sources(catalog_id, sources, page, now, policy, *, before_id=None):
    "Pure rule evaluation after existing source validation; reproducible clock/policy."
    findings, comparisons, intervals = [], [], []
    summaries = [s[0] for s in sources]
    refs = [reference(s) for s in summaries]
    complete = before_id is None and not page["has_more"]
    valid = [
        s
        for s in sources
        if s[3] is None
        and s[0]["identity_consistent"]
        and s[0]["catalog_id"] == catalog_id
    ]

    def finding(
        rule,
        category,
        title,
        explanation,
        supporting,
        inputs,
        result=None,
        evidence=None,
    ):
        value = {
            "schema_version": VERSION,
            "rule_id": "history." + rule,
            "rule_version": VERSION,
            "category": category,
            "status": "recorded",
            "severity": None,
            "confidence": None,
            "title": title,
            "explanation": explanation,
            "catalog_id": catalog_id,
            "sources": [reference(s) for s in supporting],
            "inputs": inputs,
            "result": result,
            "evidence": evidence,
            "assumptions": [RULES[rule]],
            "limitations": LIMITATIONS[:],
            "reproduction_status": (
                "deterministic_rule_evaluated_not_independently_replayed"
            ),
        }
        value["finding_id"] = (
            "history-finding-sha256:" + hashlib.sha256(encoded(value)).hexdigest()
        )
        findings.append(value)

    n = len(valid)
    distinct = len({s[0]["response_sha256"] for s in valid})
    coverage_note = (
        "No suitable persisted records are available in this window."
        if n == 0
        else (
            "One suitable persisted record is available; historical "
            "comparison is not yet possible."
        )
        if n == 1
        else (
            "Two suitable persisted records are available; only pairwise "
            "changes are supported, not a long-term trend."
        )
        if n == 2
        else (
            f"{n} suitable persisted records are available. Changes describe "
            "these samples only; no reliable long-term trend or prediction "
            "is established."
        )
    )
    if distinct < n:
        coverage_note += (
            f" Only {distinct} distinct payload identities exist; repeated "
            "payloads cannot provide independent change evidence."
        )
    finding(
        "coverage",
        "incomplete_data" if n < 3 else "informational",
        "Historical coverage",
        coverage_note,
        summaries,
        {
            "validated_record_count": n,
            "distinct_payload_count": distinct,
            "inspected_count": len(sources),
            "scope": "inspected_window",
            "complete_anchored_history": complete,
        },
    )
    if not complete:
        finding(
            "partial_window",
            "incomplete_data",
            "Partial history window",
            (
                "Other insertion-ID windows remain outside this analysis. "
                "Counts, extrema and intervals apply only to inspected "
                "records."
            ),
            summaries,
            {
                "before_id": before_id,
                "anchor_id": page["anchor_id"],
                "has_more": page["has_more"],
                "limit": page["page_size"],
            },
        )

    points = []
    for summary, _item, elements, error in sources:
        usable = (
            error is None
            and summary["identity_consistent"]
            and summary["catalog_id"] == catalog_id
        )
        freshness = classify(
            summary["orbital_epoch"], summary["retrieved_at"], as_of=now, policy=policy
        )
        point = {
            "metadata": summary,
            "reference": reference(summary),
            "usable": usable,
            "validation_error": error,
            "elements": elements.model_dump(mode="json", by_alias=True)
            if usable
            else None,
            "element_units": ELEMENT_UNITS,
            "freshness": freshness,
        }
        points.append(point)
        issues = summary["metadata_issues"][:]
        if summary["snapshot_created_at"] is None:
            issues.append(
                (
                    "Insertion timestamp not recorded; it is not inferred from "
                    "retrieval or epoch."
                )
            )
        if issues:
            finding(
                "metadata",
                "incomplete_data",
                "Incomplete source metadata",
                " ".join(issues),
                [summary],
                {
                    "metadata_issues": issues,
                    "retrieved_at": summary["retrieved_at"],
                    "orbital_epoch": summary["orbital_epoch"],
                    "inserted_at": summary["snapshot_created_at"],
                },
            )
        if not usable:
            finding(
                "validation",
                "validation_failure",
                "Source validation unavailable",
                (
                    "This record cannot support orbital-element calculations. "
                    "Original metadata remain visible; missing or invalid values "
                    "are not zero."
                ),
                [summary],
                {
                    "error": error,
                    "identity_consistent": summary["identity_consistent"],
                    "requested_catalog_id": catalog_id,
                },
            )
        if freshness["state"] != "fresh":
            state = freshness["state"]
            finding(
                "freshness",
                "stale_source_data"
                if state == "stale"
                else "incomplete_data"
                if state in {"unknown", "future_epoch"}
                else "informational",
                f"Element freshness: {state}",
                (
                    f"Existing epoch-based policy classifies snapshot #{summary['id']} "
                    f"as {state}. Retrieval age is recorded separately and does "
                    "not quantify prediction accuracy."
                ),
                [summary],
                freshness,
            )

    all_times = [utc(s["retrieved_at"]) for s in summaries]
    ordered = all(t is not None for t in all_times) and len(set(all_times)) == len(
        all_times
    )
    ordered_sources = sorted(
        sources, key=lambda s: utc(s[0]["retrieved_at"]) if ordered else s[0]["id"]
    )
    for first, second in zip(ordered_sources, ordered_sources[1:], strict=False):
        if (
            utc(first[0]["retrieved_at"]) is not None
            and utc(second[0]["retrieved_at"]) is not None
            and utc(first[0]["retrieved_at"]) > utc(second[0]["retrieved_at"])
        ):
            first, second = second, first
        a, b = first[0], second[0]
        c = investigations.compare_sources([first, second], now=now)
        chronological = c["chronology"]["status"] == "ordered"
        epoch_a, epoch_b = utc(a["orbital_epoch"]), utc(b["orbital_epoch"])
        conflict = bool(chronological and epoch_a and epoch_b and epoch_b < epoch_a)
        duplicate = bool(
            a["response_sha256"] and a["response_sha256"] == b["response_sha256"]
        )
        future_retrieval = any(
            utc(s["retrieved_at"]) is not None and utc(s["retrieved_at"]) > now
            for s in (a, b)
        )
        directional = (
            not future_retrieval
            and chronological
            and not conflict
            and not duplicate
            and first in valid
            and second in valid
        )
        status = (
            "ordered"
            if directional
            else "future_retrieval_timestamp"
            if future_retrieval
            else "duplicate_payload"
            if duplicate
            else "epoch_order_conflict"
            if conflict
            else c["chronology"]["status"]
            if not chronological
            else "source_unusable"
        )
        pair_id = f"pair-{a['id']}-{b['id']}"
        if not directional:
            finding(
                "chronology",
                "comparison_unavailable",
                "Directional change unavailable",
                (
                    "Reliable compatible chronology is unavailable or element "
                    "epochs conflict, retrievals are future-dated, or payloads repeat. "
                    "No earlier-to-later "
                    "change is claimed."
                ),
                [a, b],
                {
                    "chronology": c["chronology"],
                    "epoch_order_conflict": conflict,
                    "duplicate_payload": duplicate,
                    "future_retrieval_timestamp": future_retrieval,
                    "evaluated_at": now.isoformat(),
                    "source_errors": c["source_errors"],
                },
            )
        interval = None
        if chronological:
            interval = (utc(b["retrieved_at"]) - utc(a["retrieved_at"])).total_seconds()
            # Under unknown global ordering, a pair may be returned B/A by ID.
            interval = abs(interval)
            intervals.append(
                {
                    "source_ids": [a["id"], b["id"]],
                    "seconds": interval,
                    "unit": "s",
                    "scope": "inspected_window_only",
                    "intermediate_samples": "not_inferred",
                }
            )
            if interval > policy.stale_hours * 3600:
                finding(
                    "interval",
                    "incomplete_data",
                    "Wide archived sampling interval",
                    (
                        f"The selected records are {interval} seconds apart. This "
                        f"exceeds the configured {policy.stale_hours}-hour coverage "
                        "flag. Uninspected history and provider availability "
                        "are not inferred."
                    ),
                    [a, b],
                    {
                        "retrieval_interval_seconds": interval,
                        "threshold_seconds": policy.stale_hours * 3600,
                        "operator": ">",
                        "unit": "s",
                    },
                )
        if (
            epoch_a
            and epoch_b
            and abs((epoch_b - epoch_a).total_seconds()) > policy.stale_hours * 3600
        ):
            finding(
                "epoch_interval",
                "informational",
                "Widely separated element epochs",
                (
                    "Epoch separation exceeds the configured stale-hours "
                    "duration. Subtraction compares distinct published solutions;"
                    " no physical event is identified."
                ),
                [a, b],
                {
                    "epoch_interval_seconds": abs((epoch_b - epoch_a).total_seconds()),
                    "threshold_seconds": policy.stale_hours * 3600,
                    "operator": ">",
                    "unit": "s",
                },
            )
        definition = capture_definition(a, b, directional)
        evidence = {
            "status": "capture_recipe_available_not_captured"
            if definition
            else "unavailable",
            "definition": definition,
            "manifest_sha256": None,
            "package_url": None,
            "scope": (
                "Underlying Phase 9 comparison report / Phase 10 calculation "
                "replay only; findings themselves are not replayed."
            ),
        }
        changes = (
            [d for d in c["element_differences"] if d["field"] in FIELDS]
            if directional and c["element_comparison_status"] == "complete"
            else []
        )
        pair = {
            "id": pair_id,
            "first": reference(a),
            "second": reference(b),
            "chronology_status": status,
            "status": "complete" if changes else "unavailable",
            "retrieval_interval_seconds": interval,
            "differences": changes,
            "evidence": evidence,
        }
        comparisons.append(pair)
        if not changes:
            finding(
                "comparison",
                "comparison_unavailable",
                "Element comparison unavailable",
                (
                    "The existing comparison service or chronology policy cannot "
                    "support this directional comparison; no missing value is "
                    "replaced with zero."
                ),
                [a, b],
                {
                    "element_comparison_status": c["element_comparison_status"],
                    "chronology_status": status,
                    "source_errors": c["source_errors"],
                },
                evidence=evidence,
            )
        for change in changes:
            finding(
                "element_change",
                "informational",
                f"{change['field']} recorded difference",
                (
                    f"{change['field']} differs by {change['difference']} "
                    f"{change['unit']} between snapshots #{a['id']} and #{b['id']}. "
                    f"Their element epochs are {a['orbital_epoch']} and "
                    f"{b['orbital_epoch']}. This is a difference between published "
                    "element sets; it does not independently establish a physical "
                    "orbital event."
                ),
                [a, b],
                {
                    "field": change["field"],
                    "first_value": change["first_value"],
                    "second_value": change["second_value"],
                    "unit": change["unit"],
                    "method": change["convention"],
                },
                {"comparison_id": pair_id, **change},
                evidence,
            )

    times = sorted(
        utc(s[0]["retrieved_at"])
        for s in valid
        if utc(s[0]["retrieved_at"]) is not None
    )
    result = {
        "kind": "orbitiq_historical_analysis",
        "schema_version": VERSION,
        "rule_set_version": VERSION,
        "generated_at": now.isoformat(),
        "catalog_id": catalog_id,
        "request": {
            "catalog_id": catalog_id,
            "limit": page["page_size"],
            "before_id": before_id,
            "anchor_id": page["anchor_id"],
        },
        "pagination": {
            k: page[k]
            for k in (
                "anchor_id",
                "has_more",
                "next_before_id",
                "page_size",
                "total_count",
                "total_count_status",
            )
        },
        "coverage": {
            "inspected_count": len(sources),
            "validated_record_count": n,
            "distinct_payload_count": distinct,
            "complete_anchored_history": complete,
            "extrema_scope": "verifiable_retrievals_in_inspected_window",
            "oldest_verifiable_retrieval": times[0].isoformat() if times else None,
            "newest_verifiable_retrieval": times[-1].isoformat() if times else None,
            "retrieval_span_seconds": (times[-1] - times[0]).total_seconds()
            if times
            else None,
            "chronology": "retrieval_ascending"
            if ordered
            else "unknown_or_ambiguous_id_order_only",
            "summary": coverage_note,
            "trend_statistic": None,
            "interpolation": False,
            "extrapolation": False,
        },
        "sources": refs,
        "points": sorted(
            points,
            key=lambda p: (
                utc(p["metadata"]["retrieved_at"]) if ordered else p["metadata"]["id"]
            ),
        ),
        "intervals": intervals,
        "comparisons": comparisons,
        "findings": findings,
        "methodology": {
            "software_versions": {
                n: package_version(n) for n in ("sgp4", "astropy", "pyerfa")
            },
            "fields": {f: ELEMENT_UNITS[f] for f in FIELDS},
            "difference": (
                "later retrieval minus earlier retrieval; inclination linear,"
                " not wrapped; no percentages"
            ),
            "freshness_policy": {
                "fresh_hours": policy.fresh_hours,
                "stale_hours": policy.stale_hours,
            },
            "observation_at": None,
            "calculation_at": None,
            "rules": RULES,
            "categories": CATEGORIES,
            "max_points": MAX_POINTS,
            "max_comparisons": MAX_POINTS - 1,
            "max_findings": 200,
        },
        "limitations": LIMITATIONS,
    }
    assert len(findings) <= 200
    result["report_id"] = (
        "history-report-sha256:" + hashlib.sha256(encoded(result)).hexdigest()
    )
    return result


def historical_analysis(
    path, catalog_id, *, limit=20, before_id=None, anchor_id=None, now=None
):
    if (
        type(catalog_id) is not int
        or not 1 <= catalog_id <= 339999
        or type(limit) is not int
        or not 1 <= limit <= MAX_POINTS
        or any(
            v is not None and (type(v) is not int or not 1 <= v <= 9007199254740991)
            for v in (before_id, anchor_id)
        )
    ):
        raise analysis.AnalysisError(
            422,
            "invalid_history_request",
            "Use a valid catalog, bounded page size and positive safe integer cursors",
        )
    now = utc(now) if now is not None else datetime.now(UTC)
    if now is None:
        raise analysis.AnalysisError(
            422, "invalid_time", "Evaluation time requires a timezone"
        )
    policy = analysis.policy()
    page = investigations.listing(
        path,
        catalog_id=catalog_id,
        limit=limit,
        before_id=before_id,
        anchor_id=anchor_id,
    )
    sources = []
    for summary in page["snapshots"]:
        summary["freshness_info"] = classify(
            summary["orbital_epoch"], summary["retrieved_at"], as_of=now, policy=policy
        )
        source = investigations.source_from_summary(path, summary)
        if source[1] and any(
            source[1].get(k) != summary[k]
            for k in (
                "id",
                "catalog_id",
                "response_sha256",
                "orbital_epoch",
                "retrieved_at",
            )
        ):
            raise analysis.AnalysisError(
                409,
                "history_source_changed",
                (
                    "Source metadata changed during analysis; retry with the same"
                    " exact references"
                ),
            )
        sources.append(source)
    result = analyze_sources(
        catalog_id, sources, page, now, policy, before_id=before_id
    )
    # Recheck exact references against a filesystem/database switch.
    for summary, item, _, error in sources:
        if error is None:
            current, _ = analysis.load_snapshot(path, summary["id"])
            if any(
                current[k] != item[k]
                for k in (
                    "response_sha256",
                    "catalog_id",
                    "orbital_epoch",
                    "retrieved_at",
                )
            ):
                raise analysis.AnalysisError(
                    409,
                    "history_source_changed",
                    "Exact source changed during analysis; no replacement was used",
                )
    return result
