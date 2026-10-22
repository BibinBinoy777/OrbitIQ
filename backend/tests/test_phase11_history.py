"""Controlled isolated fixtures only; never count these as genuine archive history."""

import copy
import json
import sqlite3
from datetime import UTC, datetime, timedelta

import pytest
from orbitiq import replay
from orbitiq.database import initialize
from orbitiq.maintenance.recovery import fingerprint
from orbitiq.reporting import parse_definition
from orbitiq.services import analysis, history, investigations
from test_phase5 import corrupt, store

pytest_plugins = ["test_phase5"]
NOW = datetime(2026, 10, 20, tzinfo=UTC)


def run(archive, **options):
    return history.historical_analysis(archive[1], 6251, now=NOW, **options)


def rules(report, rule):
    return [f for f in report["findings"] if f["rule_id"] == "history." + rule]


def test_pair_reuses_comparison_and_preserves_sources(archive):
    client, path, a, b, *_ = archive
    before = fingerprint(path), path.read_bytes()
    report = run(archive)
    assert [p["metadata"]["id"] for p in report["points"]] == [a, b]
    assert report["coverage"]["validated_record_count"] == 2
    assert report["coverage"]["trend_statistic"] is None
    assert "only pairwise" in report["coverage"]["summary"]
    expected = investigations.compare(path, a, b)["element_differences"]
    assert report["comparisons"][0]["differences"] == [
        d for d in expected if d["field"] in history.FIELDS
    ]
    assert len(rules(report, "element_change")) == 3
    assert (fingerprint(path), path.read_bytes()) == before
    response = client.get("/api/historical-analysis", params={"catalog_id": 6251})
    assert (
        response.status_code == 200 and response.headers["cache-control"] == "no-store"
    )
    assert response.json()["kind"] == "orbitiq_historical_analysis"


def test_no_history_and_single_record(archive):
    none = history.historical_analysis(archive[1], 54321, now=NOW)
    one = history.historical_analysis(archive[1], 12345, now=NOW)
    for value, count in [(none, 0), (one, 1)]:
        assert value["coverage"]["validated_record_count"] == count
        assert len(value["points"]) == count and not value["comparisons"]
        assert value["coverage"]["complete_anchored_history"]
        assert rules(value, "coverage")[0]["category"] == "incomplete_data"
    assert "not yet possible" in one["coverage"]["summary"]
    assert none["coverage"]["oldest_verifiable_retrieval"] is None


def test_empty_database_is_not_silently_initialized(tmp_path):
    path = tmp_path / "absent.sqlite3"
    with pytest.raises(analysis.AnalysisError):
        history.historical_analysis(path, 6251)
    assert not path.exists()
    initialize(path)
    assert history.historical_analysis(path, 6251)["points"] == []


def test_pagination_full_archive_stable_anchor_not_first_page(archive):
    _, path, a, b, _, record = archive
    first = run(archive, limit=1)
    value = copy.deepcopy(record)
    value["MEAN_MOTION"] += 0.001
    added = store(path, value, datetime(2026, 10, 21, tzinfo=UTC))
    second = run(
        archive,
        limit=1,
        anchor_id=first["pagination"]["anchor_id"],
        before_id=first["pagination"]["next_before_id"],
    )
    assert [
        first["points"][0]["metadata"]["id"],
        second["points"][0]["metadata"]["id"],
    ] == [b, a]
    assert not second["pagination"]["has_more"]
    assert not second["coverage"]["complete_anchored_history"]
    assert rules(first, "partial_window") and rules(second, "partial_window")
    assert run(archive)["pagination"]["total_count"] == 3
    assert added not in [p["metadata"]["id"] for p in first["points"]]


def test_multiple_records_never_fit_or_invent_points(archive):
    _, path, a, b, _, record = archive
    for hours in [72, 144, 216]:
        r = copy.deepcopy(record)
        r["EPOCH"] = (
            datetime.fromisoformat(record["EPOCH"].replace("Z", "+00:00"))
            + timedelta(hours=hours)
        ).isoformat()
        store(path, r, NOW + timedelta(hours=hours))
    data = run(archive)
    assert len(data["points"]) == 5 and len(data["comparisons"]) == 4
    assert data["coverage"]["trend_statistic"] is None
    assert data["coverage"]["interpolation"] is False
    assert data["coverage"]["extrapolation"] is False
    assert "no reliable long-term" in data["coverage"]["summary"]
    assert {p["metadata"]["id"] for p in data["points"]} >= {a, b}


@pytest.mark.parametrize(
    "field,delta,unit",
    [
        ("INCLINATION", -0.25, "deg"),
        ("ECCENTRICITY", 0.001, "dimensionless"),
        ("MEAN_MOTION", 0.02, "rev/day"),
    ],
)
def test_scalar_differences_actual_values_not_wrapped_or_percentages(
    archive, field, delta, unit
):
    _, path, _, _, _, record = archive
    later = copy.deepcopy(record)
    later[field] += delta
    later["EPOCH"] = (
        datetime.fromisoformat(record["EPOCH"]).replace(tzinfo=UTC)
        + timedelta(hours=12)
    ).isoformat()
    sid = store(path, later, NOW)
    result = run(archive)
    change = next(
        d
        for p in result["comparisons"]
        if p["second"]["snapshot_id"] == sid
        for d in p["differences"]
        if d["field"] == field
    )
    assert change["difference"] == pytest.approx(delta)
    assert change["unit"] == unit and change["convention"] == "second_minus_first"
    assert change["difference"] == change["second_value"] - change["first_value"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("retrieved_at", "bad"),
        ("orbital_epoch", "bad"),
        ("response_sha256", "a" * 64),
        ("normalized_record", "{}"),
        ("element_units", "{}"),
        ("validation_status", "invalid"),
    ],
)
def test_invalid_missing_changed_sources_stay_visible_but_not_compared(
    archive, field, value
):
    corrupt(archive[1], archive[2], field, value)
    report = run(archive)
    assert len(report["points"]) == 2
    assert report["coverage"]["validated_record_count"] == 1
    assert rules(report, "validation") and rules(report, "comparison")
    assert report["comparisons"][0]["differences"] == []
    assert report["comparisons"][0]["evidence"]["definition"] is None


def test_ambiguous_equal_retrievals_have_no_direction(archive):
    _, path, a, b, *_ = archive
    corrupt(path, b, "retrieved_at", "2026-10-17T00:00:00+00:00")
    report = run(archive)
    assert report["coverage"]["chronology"] == "unknown_or_ambiguous_id_order_only"
    assert (
        report["comparisons"][0]["chronology_status"]
        == "ambiguous_equal_retrieval_times"
    )
    assert not report["comparisons"][0]["differences"]
    assert rules(report, "chronology")


def test_retrieval_and_epoch_reversal_explicit(archive):
    corrupt(archive[1], archive[3], "retrieved_at", "2026-10-16T00:00:00+00:00")
    report = run(archive)
    assert report["comparisons"][0]["chronology_status"] == "epoch_order_conflict"
    assert not report["comparisons"][0]["differences"]


@pytest.mark.parametrize("hours,expected", [(72, False), (72.000001, True)])
def test_interval_boundary_does_not_claim_outage(archive, hours, expected):
    corrupt(
        archive[1],
        archive[3],
        "retrieved_at",
        (datetime(2026, 10, 17, tzinfo=UTC) + timedelta(hours=hours)).isoformat(),
    )
    data = run(archive)
    assert bool(rules(data, "interval")) is expected
    if expected:
        f = rules(data, "interval")[0]
        assert f["inputs"]["operator"] == ">" and f["inputs"]["unit"] == "s"
        assert "not inferred" in f["explanation"]


def test_epoch_interval_and_capture_without_supported_common_time(archive):
    _, path, _, _, _, record = archive
    r = copy.deepcopy(record)
    r["EPOCH"] = (
        datetime.fromisoformat(record["EPOCH"]) + timedelta(days=10)
    ).isoformat()
    store(path, r, NOW)
    data = run(archive)
    assert rules(data, "epoch_interval")
    assert data["comparisons"][-1]["evidence"]["definition"]["at"] is None


@pytest.mark.parametrize(
    "hours,state",
    [
        (24, "fresh"),
        (24.000001, "aging"),
        (72, "aging"),
        (72.000001, "stale"),
        (-1, "future_epoch"),
    ],
)
def test_existing_freshness_boundaries_are_reused(archive, tmp_path, hours, state):
    path = tmp_path / "policy-only-fixture.sqlite3"
    initialize(path)
    epoch = datetime.fromisoformat(archive[5]["EPOCH"]).replace(tzinfo=UTC)
    store(path, archive[5], epoch - timedelta(hours=2))
    data = history.historical_analysis(path, 6251, now=epoch + timedelta(hours=hours))
    point = data["points"][0]
    assert point["freshness"]["state"] == state
    assert (
        point["freshness"]["retrieval_age_seconds"]
        != point["freshness"]["epoch_age_seconds"]
    )
    assert bool(rules(data, "freshness")) is (state != "fresh")


def test_determinism_rule_versions_hashes_no_claims(archive):
    first = run(archive)
    second = run(archive)
    assert first == second
    ids = set()
    for f in first["findings"]:
        assert f["schema_version"] == f["rule_version"] == 1
        assert f["severity"] is None and f["confidence"] is None
        assert f["finding_id"] not in ids
        ids.add(f["finding_id"])
        assert f["sources"] and all(s["response_sha256"] for s in f["sources"])
        assert f["reproduction_status"].startswith("deterministic_rule_evaluated")
        assert "No maneuver" in " ".join(f["limitations"])


def test_legacy_insertion_timestamp_not_inferred(archive):
    with sqlite3.connect(archive[1]) as db:
        db.execute("DROP TRIGGER insertions_no_delete")
        db.execute("DELETE FROM snapshot_insertions WHERE snapshot_id=?", (archive[2],))
    report = run(archive)
    assert rules(report, "metadata")
    assert report["points"][0]["metadata"]["snapshot_created_at"] is None


@pytest.mark.parametrize(
    "params",
    [
        {"catalog_id": 0},
        {"catalog_id": 340000},
        {"catalog_id": "ISS"},
        {"catalog_id": 6251, "limit": 21},
        {"catalog_id": 6251, "limit": 0},
        {"catalog_id": 6251, "before_id": -1},
        {"catalog_id": 6251, "anchor_id": 9007199254740992},
        {"catalog_id": 6251, "before_id": 5, "anchor_id": 2},
    ],
)
def test_api_rejects_invalid_or_oversized_queries(archive, params):
    assert archive[0].get("/api/historical-analysis", params=params).status_code == 422


def test_read_only_no_upstream_no_admin(archive, monkeypatch):
    import httpx

    def forbidden(*args, **kwargs):
        raise AssertionError("Unexpected external acquisition")

    monkeypatch.setattr(httpx.Client, "send", forbidden)
    before = fingerprint(archive[1]), archive[1].read_bytes()
    run(archive)
    assert (fingerprint(archive[1]), archive[1].read_bytes()) == before


def test_changed_archive_during_request_never_substitutes_source(archive, monkeypatch):
    original = analysis.load_snapshot
    calls = 0

    def changed(*args):
        nonlocal calls
        item, e = original(*args)
        calls += 1
        if calls > 2:
            item = {**item, "response_sha256": "f" * 64}
        return item, e

    monkeypatch.setattr(analysis, "load_snapshot", changed)
    with pytest.raises(analysis.AnalysisError, match="Exact source changed"):
        run(archive)


def test_underlying_evidence_replays_without_changing_findings_format(
    archive, tmp_path
):
    report = run(archive)
    pair = report["comparisons"][0]
    definition = pair["evidence"]["definition"]
    root = tmp_path / "historical-pair-evidence"
    capture = replay.capture(archive[1], parse_definition(json.dumps(definition)), root)
    result = replay.verify(root, capture["manifest_sha256"])
    assert result["status"] == "matched", result
    assert result["numerical_outcome"] == "exact_output_reproduction"
    stored = json.loads((root / "report.json").read_bytes())["calculation"]["data"]
    assert pair["differences"] == [
        d for d in stored["element_differences"] if d["field"] in history.FIELDS
    ]
    assert pair["evidence"]["manifest_sha256"] is None
    assert pair["evidence"]["status"] == "capture_recipe_available_not_captured"


def test_payload_deduplication_does_not_invent_history(archive):
    _, path, a, _, _, record = archive
    assert store(path, record, NOW) == a
    result = run(archive)
    assert result["coverage"]["validated_record_count"] == 2
    assert result["coverage"]["distinct_payload_count"] == 2


def test_twenty_point_limit_is_enforced_and_work_bounded(archive):
    _, path, _, _, _, record = archive
    for i in range(24):
        store(
            path,
            {**record, "OBJECT_NAME": f"ISOLATED PAGINATION FIXTURE {i}"},
            NOW + timedelta(hours=i),
        )
    result = run(archive)
    assert len(result["points"]) == 20
    assert len(result["comparisons"]) == 19
    assert len(result["findings"]) <= 200
    assert result["pagination"]["has_more"]
    assert not result["coverage"]["complete_anchored_history"]


def test_duplicate_payload_metadata_cannot_support_direction(archive):
    import copy

    sources = [
        investigations.source_for_comparison(archive[1], sid) for sid in archive[2:4]
    ]
    sources = copy.deepcopy(sources)
    sources[1][0]["response_sha256"] = sources[0][0]["response_sha256"]
    page = investigations.listing(archive[1], catalog_id=6251)
    result = history.analyze_sources(6251, sources, page, NOW, analysis.policy())
    assert result["comparisons"][0]["chronology_status"] == "duplicate_payload"
    assert not result["comparisons"][0]["differences"]
    assert rules(result, "chronology")[0]["inputs"]["duplicate_payload"] is True


def test_configured_policy_is_used_without_new_staleness_threshold(
    archive, monkeypatch
):
    monkeypatch.setenv("ORBITIQ_FRESH_HOURS", "12")
    monkeypatch.setenv("ORBITIQ_STALE_HOURS", "48")
    result = run(archive)
    assert result["methodology"]["freshness_policy"] == {
        "fresh_hours": 12,
        "stale_hours": 48,
    }
    assert all(p["freshness"]["stale_hours"] == 48 for p in result["points"])


def test_historical_endpoint_shares_calculation_admission():
    from orbitiq.api.boundary import EXPENSIVE

    assert EXPENSIVE.fullmatch("/api/historical-analysis")


def test_future_retrieval_does_not_establish_direction(archive):
    corrupt(
        archive[1], archive[3], "retrieved_at", (NOW + timedelta(days=1)).isoformat()
    )
    report = run(archive)
    pair = report["comparisons"][0]
    assert pair["chronology_status"] == "future_retrieval_timestamp"
    assert pair["differences"] == [] and pair["evidence"]["definition"] is None
    assert rules(report, "chronology")[0]["inputs"]["evaluated_at"] == NOW.isoformat()
