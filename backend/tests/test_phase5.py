"""Isolated reference-derived fixtures; never inserted into application storage."""

import copy
import hashlib
import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from orbitiq.database import initialize
from orbitiq.main import create_app
from orbitiq.orbits.elements import Elements
from orbitiq.services import analysis, investigations
from orbitiq.storage import get_snapshot, save_snapshot


@pytest.fixture
def archive(tmp_path, monkeypatch):
    path = tmp_path / "phase5-test-only.sqlite3"
    initialize(path)
    monkeypatch.setenv("ORBITIQ_DATABASE_PATH", str(path))
    for key in ["ORBITIQ_EOP_POLICY", "ORBITIQ_FRESH_HOURS", "ORBITIQ_STALE_HOURS"]:
        monkeypatch.delenv(key, raising=False)
    record = json.loads(
        (Path(__file__).parent / "fixtures/vallado-leo.json").read_text()
    )[0]["omm"]
    record["OBJECT_NAME"] = "REFERENCE TEST ONLY"
    record["RA_OF_ASC_NODE"] = 359.0
    first = store(path, record, datetime(2026, 10, 17, tzinfo=UTC))
    later = copy.deepcopy(record)
    later["EPOCH"] = (
        Elements.model_validate(record).epoch + timedelta(hours=6)
    ).isoformat()
    later["RA_OF_ASC_NODE"] = 1.0
    second = store(path, later, datetime(2026, 10, 18, tzinfo=UTC))
    third = copy.deepcopy(record)
    third["NORAD_CAT_ID"] = 12345  # Same name/designator, different stable identity.
    third_id = store(path, third, datetime(2026, 10, 16, tzinfo=UTC))
    with TestClient(create_app()) as client:
        yield client, path, first, second, third_id, record


def store(path, record, retrieved):
    return save_snapshot(
        path,
        json.dumps([record]).encode(),
        record,
        Elements.model_validate(record),
        f"https://celestrak.org/NORAD/elements/gp.php?CATNR={record['NORAD_CAT_ID']}&FORMAT=JSON",
        retrieved,
    )


def corrupt(path, sid, field, value):
    # Deliberately damage ONLY an isolated fixture, never the ordinary database.
    with sqlite3.connect(path) as db:
        db.execute("DROP TRIGGER IF EXISTS snapshots_no_update")
        db.execute(f"UPDATE snapshots SET {field}=? WHERE id=?", (value, sid))


@pytest.mark.parametrize(
    "query,match,expected",
    [
        ("reference", "partial", 3),
        ("REFERENCE TEST ONLY", "exact", 3),
        ("625", "partial", 2),
        ("6251", "exact", 2),
        ("12345", "exact", 1),
        ("not stored", "partial", 0),
        ("%", "partial", 0),
        ("_", "partial", 0),
    ],
)
def test_name_catalog_and_literal_search(archive, query, match, expected):
    client, *_ = archive
    r = client.get("/api/discovery/satellites", params={"q": query, "match": match})
    assert r.status_code == 200 and len(r.json()["snapshots"]) == expected
    assert r.json()["total_count"] is None and r.headers["cache-control"] == "no-store"


def test_other_supported_identifier_search(archive):
    client, _, _, _, _, record = archive
    data = client.get(
        "/api/discovery/satellites", params={"q": record["OBJECT_ID"], "match": "exact"}
    ).json()
    assert len(data["snapshots"]) == 3


def test_context_membership_and_selected_only_scope(archive):
    c, _, a, b, other, _ = archive
    data = c.get("/api/discovery/satellites", params={"context_snapshot_id": a}).json()
    memberships = {s["id"]: s["membership"] for s in data["snapshots"]}
    assert memberships[a] == "selected_snapshot_record"
    assert memberships[b] == "historical_record_also_in_selected"
    assert memberships[other] == "historical_only"
    selected = c.get(
        "/api/discovery/satellites",
        params={"context_snapshot_id": a, "selected_only": True},
    ).json()
    assert [r["id"] for r in selected["snapshots"]] == [a]
    assert c.get("/api/snapshots", params={"selected_only": True}).status_code == 422
    assert (
        c.get(
            "/api/snapshots",
            params={
                "selected_only": True,
                "context_snapshot_id": a,
                "snapshot_id": other,
            },
        ).status_code
        == 422
    )
    assert (
        c.get("/api/snapshots", params={"context_snapshot_id": 999}).status_code == 404
    )


def test_snapshot_pages_counts_and_order_independent_of_retrieval(archive):
    c, _, a, b, last_inserted, _ = archive
    first = c.get("/api/snapshots", params={"limit": 1}).json()
    assert (
        first["total_count"] == 3
        and first["total_count_status"] == "exact_within_anchor"
    )
    assert first["snapshots"][0]["id"] == last_inserted
    assert first["global_latest_retrieval_known"] is False
    second = c.get(
        "/api/snapshots",
        params={
            "limit": 1,
            "anchor_id": first["anchor_id"],
            "before_id": first["next_before_id"],
        },
    ).json()
    third = c.get(
        "/api/snapshots",
        params={
            "limit": 1,
            "anchor_id": first["anchor_id"],
            "before_id": second["next_before_id"],
        },
    ).json()
    assert [second["snapshots"][0]["id"], third["snapshots"][0]["id"]] == [b, a]
    assert third["has_more"] is False and third["next_before_id"] is None
    assert first["order"] == "insertion_id_desc_not_retrieval_chronology"
    scoped = c.get("/api/snapshots", params={"catalog_id": 6251}).json()
    assert scoped["total_count"] == 2


def test_empty_archive_and_direct_old_snapshot(archive, tmp_path, monkeypatch):
    c, _, oldest, *_ = archive
    assert c.get(f"/api/snapshots/{oldest}").status_code == 200
    assert (
        c.get("/api/snapshots", params={"snapshot_id": oldest}).json()["snapshots"][0][
            "id"
        ]
        == oldest
    )
    empty = tmp_path / "empty.sqlite3"
    initialize(empty)
    monkeypatch.setenv("ORBITIQ_DATABASE_PATH", str(empty))
    data = c.get("/api/snapshots").json()
    assert data["snapshots"] == [] and data["total_count"] == 0 and not data["has_more"]


def bulk(path, number):
    with sqlite3.connect(path) as db:
        db.executemany(
            """INSERT INTO snapshots (catalog_id,object_name,orbital_epoch,
            retrieved_at,source_url,raw_response,response_sha256,raw_record,
            normalized_record,element_units,validation_status,validator_version,sgp4_version)
            SELECT catalog_id, object_name, orbital_epoch, retrieved_at, source_url,
            raw_response, response_sha256, raw_record, normalized_record, element_units,
            validation_status, validator_version, sgp4_version
            FROM snapshots WHERE id=1""",
            [()] * number,
        )


def test_history_beyond_100_and_bounded_unknown_count(archive):
    c, path, a, *_ = archive
    bulk(path, 1001)
    seen = []
    cursor = None
    anchor = None
    while True:
        params = {"limit": 100}
        if cursor is not None:
            params.update(before_id=cursor, anchor_id=anchor)
        data = c.get("/api/snapshots", params=params).json()
        assert data["scanned_count"] <= 250 and data["total_count"] is None
        seen += [s["id"] for s in data["snapshots"]]
        anchor = data["anchor_id"]
        cursor = data["next_before_id"]
        if not data["has_more"]:
            break
    assert len(seen) == 1004 and len(set(seen)) == 1004 and seen[-1] == a
    assert c.get(f"/api/snapshots/{a}").status_code == 200
    legacy = c.get("/api/satellites/6251/snapshots", params={"limit": 100}).json()
    assert (
        len(legacy["snapshots"]) == 100
        and legacy["has_more"]
        and legacy["next_before_id"]
    )


def test_empty_search_window_continues_without_skipping(archive):
    c, path, *_ = archive
    bulk(path, 260)
    page = c.get(
        "/api/discovery/satellites", params={"q": "12345", "match": "exact"}
    ).json()
    assert page["snapshots"] == [] and page["has_more"] and page["scanned_count"] == 250
    page2 = c.get(
        "/api/discovery/satellites",
        params={
            "q": "12345",
            "match": "exact",
            "before_id": page["next_before_id"],
            "anchor_id": page["anchor_id"],
        },
    ).json()
    assert [s["catalog_id"] for s in page2["snapshots"]] == [12345] and not page2[
        "has_more"
    ]


def test_high_water_anchor_excludes_new_insertions(archive):
    c, path, *_ = archive
    first = c.get("/api/snapshots", params={"limit": 1}).json()
    bulk(path, 1)
    second = c.get(
        "/api/snapshots",
        params={
            "limit": 1,
            "before_id": first["next_before_id"],
            "anchor_id": first["anchor_id"],
        },
    ).json()
    assert second["total_count"] == 3 and second["anchor_id"] == 3


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 101},
        {"before_id": 0},
        {"anchor_id": -1},
        {"q": "x" * 65},
        {"q": "bad\x00value"},
        {"match": "regex"},
        {"catalog_id": 340000},
        {"snapshot_id": "abc"},
        {"before_id": 4, "anchor_id": 3},
    ],
)
def test_invalid_browse_inputs(archive, params):
    c, *_ = archive
    r = c.get("/api/snapshots", params=params)
    assert r.status_code == 422 and "error" in r.json()


@pytest.mark.parametrize(
    "field,value",
    [
        ("retrieved_at", ""),
        ("orbital_epoch", "bad"),
        ("normalized_record", "{bad"),
        ("object_name", ""),
        ("source_url", "https://user:SECRET@example.test/private"),
    ],
)
def test_missing_historical_metadata_is_inspectable_and_safe(archive, field, value):
    c, path, a, b, *_ = archive
    corrupt(path, a, field, value)
    listing = c.get("/api/snapshots", params={"snapshot_id": a}).json()["snapshots"][0]
    assert listing["metadata_issues"] and listing["snapshot_created_at"] is None
    response = c.get("/api/comparisons", params={"first_id": a, "second_id": b})
    assert response.status_code == 200
    if field == "object_name":
        # A missing display name does not invalidate a source-validated NORAD ID.
        assert listing["object_name"] is None
        assert response.json()["counts"]["shared"] == 1
    else:
        assert response.json()["counts"]["incompatible"] == 1
        assert response.json()["element_differences"] == []
    assert "SECRET" not in response.text and str(path) not in response.text


def test_chronology_uses_retrieval_not_ids_and_discloses_equal_missing(archive):
    c, path, a, b, other, _ = archive
    data = c.get("/api/comparisons", params={"first_id": a, "second_id": other}).json()
    assert data["chronology"]["older_snapshot_id"] == other
    corrupt(path, b, "retrieved_at", get_snapshot(path, a)["retrieved_at"])
    assert (
        c.get("/api/comparisons", params={"first_id": a, "second_id": b}).json()[
            "chronology"
        ]["status"]
        == "ambiguous_equal_retrieval_times"
    )
    corrupt(path, b, "retrieved_at", "bad")
    assert (
        c.get("/api/comparisons", params={"first_id": a, "second_id": b}).json()[
            "chronology"
        ]["status"]
        == "unknown"
    )


def test_stable_matching_added_removed_filters_and_wrapped_angles(archive):
    c, _, a, b, other, _ = archive
    shared = c.get("/api/comparisons", params={"first_id": a, "second_id": b}).json()
    assert shared["counts"] == {
        "shared": 1,
        "added": 0,
        "removed": 0,
        "incompatible": 0,
    }
    raan = next(
        r for r in shared["element_differences"] if r["field"] == "RA_OF_ASC_NODE"
    )
    assert (
        raan["first_value"] == 359
        and raan["second_value"] == 1
        and raan["difference"] == 2
        and raan["unit"] == "deg"
    )
    reverse = c.get("/api/comparisons", params={"first_id": b, "second_id": a}).json()
    assert (
        next(
            r for r in reverse["element_differences"] if r["field"] == "RA_OF_ASC_NODE"
        )["difference"]
        == -2
    )
    different = c.get(
        "/api/comparisons",
        params={"first_id": a, "second_id": other, "category": "added"},
    ).json()
    assert (
        different["counts"]["shared"] == 0
        and different["counts"]["added"] == 1
        and different["counts"]["removed"] == 1
    )
    assert (
        len(different["records"]) == 1
        and different["records"][0]["catalog_id"] == 12345
    )
    assert "do not, by themselves, prove" in different["caution"]


@pytest.mark.parametrize(
    "change",
    [
        {"NORAD_CAT_ID": None},
        {"NORAD_CAT_ID": 12345},
        {"REF_FRAME": "ITRS"},
        {"MEAN_MOTION": None},
    ],
)
def test_invalid_identifiers_and_elements_are_incompatible(archive, change):
    c, path, a, b, *_ = archive
    item = get_snapshot(path, a)
    item["normalized_record"].update(change)
    corrupt(path, a, "normalized_record", json.dumps(item["normalized_record"]))
    data = c.get("/api/comparisons", params={"first_id": a, "second_id": b}).json()
    assert data["counts"]["incompatible"] == 1 and not data["element_differences"]


def test_incompatible_units_are_not_subtracted(archive):
    c, path, a, b, *_ = archive
    item = get_snapshot(path, a)
    item["element_units"]["INCLINATION"] = "rad"
    corrupt(path, a, "element_units", json.dumps(item["element_units"]))
    data = c.get("/api/comparisons", params={"first_id": a, "second_id": b}).json()
    assert data["element_comparison_status"] == "incompatible_or_no_shared_record"
    assert data["element_differences"] == []


@pytest.mark.parametrize("frame", ["TEME", "ITRS"])
def test_common_time_state_and_lineage(archive, frame):
    c, _, a, b, _, record = archive
    at = Elements.model_validate(record).epoch + timedelta(hours=3)
    response = c.get(
        "/api/comparisons",
        params={"first_id": a, "second_id": b, "at": at.isoformat(), "frame": frame},
    )
    assert response.status_code == 200
    data = response.json()
    state = data["state_comparison"]
    assert (
        state["status"] == "complete"
        and state["first"]["at"] == state["second"]["at"] == at.isoformat()
    )
    assert state["frame"] == frame and state["units"] == {
        "position": "km",
        "velocity": "km/s",
    }
    assert state["difference_position_km"] == pytest.approx(
        [
            y - x
            for x, y in zip(
                state["first"]["position_km"],
                state["second"]["position_km"],
                strict=True,
            )
        ]
    )
    for result, sid in [(state["first"], a), (state["second"], b)]:
        origin = result if frame == "TEME" else result["teme"]
        assert origin["snapshot_id"] == sid and origin["catalog_id"] == 6251
    assert state["separation_km"] > 0


@pytest.mark.parametrize(
    "mutation",
    [
        {"frame": "ITRS"},
        {"at": "2000-01-01T00:00:00Z"},
        {"units": {"position": "m", "velocity": "km/s"}},
        {"position_km": [float("nan"), 0, 0]},
        {"snapshot_id": 999},
    ],
)
def test_mismatched_states_cannot_be_subtracted(archive, monkeypatch, mutation):
    _, path, a, b, _, record = archive
    original = analysis.position_from_snapshot

    def wrong(item, elements, at):
        result = original(item, elements, at)
        return {**result, **mutation} if item["id"] == b else result

    monkeypatch.setattr(analysis, "position_from_snapshot", wrong)
    result = investigations.compare(path, a, b, Elements.model_validate(record).epoch)[
        "state_comparison"
    ]
    assert (
        result["status"] == "unavailable" and result["difference_position_km"] is None
    )


def test_epoch_policy_failure_retains_element_comparison(archive):
    c, _, a, b, _, record = archive
    at = Elements.model_validate(record).epoch + timedelta(days=7, hours=3)
    data = c.get(
        "/api/comparisons", params={"first_id": a, "second_id": b, "at": at.isoformat()}
    ).json()
    assert data["element_comparison_status"] == "complete"
    assert data["state_comparison"]["status"] == "unavailable"
    assert (
        data["state_comparison"]["first"] is None and data["state_comparison"]["second"]
    )
    assert data["state_comparison"]["errors"][0]["code"] == "epoch_window_exceeded"


def test_eop_failure_retains_elements_and_never_refreshes(archive, monkeypatch):
    from orbitiq.orbits.earth_orientation import TransformationError

    c, _, a, b, _, record = archive

    def fail(*args, **kwargs):
        raise TransformationError(
            "eop_out_of_range", "Requested time is outside local coverage"
        )

    monkeypatch.setattr(investigations, "earth_fixed", fail)
    data = c.get(
        "/api/comparisons",
        params={
            "first_id": a,
            "second_id": b,
            "at": Elements.model_validate(record).epoch.isoformat(),
            "frame": "ITRS",
        },
    ).json()
    assert (
        data["element_comparison_status"] == "complete"
        and data["state_comparison"]["status"] == "unavailable"
    )
    assert data["state_comparison"]["errors"][0]["code"] == "eop_out_of_range"


@pytest.mark.parametrize(
    "params",
    [
        {"first_id": 0, "second_id": 1},
        {"first_id": "bad", "second_id": 1},
        {"first_id": 1, "second_id": 2, "frame": "ECI"},
        {"first_id": 1, "second_id": 2, "category": "anomaly"},
        {"first_id": 1, "second_id": 2, "at": "2000-01-01T00:00:00"},
    ],
)
def test_invalid_comparison_request(archive, params):
    c, *_ = archive
    assert c.get("/api/comparisons", params=params).status_code == 422


def test_unknown_snapshot_and_self_comparison(archive):
    c, _, a, *_ = archive
    assert (
        c.get("/api/comparisons", params={"first_id": a, "second_id": 999}).status_code
        == 404
    )
    data = c.get("/api/comparisons", params={"first_id": a, "second_id": a}).json()
    assert data["is_self_comparison"] and all(
        r["difference"] == 0 for r in data["element_differences"]
    )


def test_query_shape_and_read_only_preservation(archive, monkeypatch):
    from orbitiq import storage
    from orbitiq.ingestion import celestrak
    from orbitiq.maintenance import eop

    c, path, a, b, _, record = archive
    statements = []
    connect = storage.connect

    def traced(*args, **kwargs):
        db = connect(*args, **kwargs)
        db.set_trace_callback(statements.append)
        return db

    def forbidden(*args, **kwargs):
        raise AssertionError("No ingestion, update or download")

    monkeypatch.setattr(storage, "connect", traced)
    monkeypatch.setattr(celestrak, "ingest", forbidden)
    monkeypatch.setattr(eop, "prepare", forbidden)
    monkeypatch.setattr("astropy.utils.iers.iers.download_file", forbidden)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    assert c.get("/api/snapshots", params={"q": "test"}).status_code == 200
    assert (
        c.get(
            "/api/comparisons",
            params={
                "first_id": a,
                "second_id": b,
                "at": Elements.model_validate(record).epoch.isoformat(),
                "frame": "ITRS",
            },
        ).status_code
        == 200
    )
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    browse_sql = [
        s
        for s in statements
        if "SELECT id FROM snapshots WHERE" in s or "substr(normalized_record" in s
    ]
    assert browse_sql and all("LIMIT" in s for s in browse_sql)
    assert not any(
        "COUNT(" in s.upper()
        or "ORDER BY RETRIEVED" in s.upper()
        or "INTEGRITY_CHECK" in s.upper()
        for s in statements
    )
    assert not any(
        s.lstrip().upper().startswith(("UPDATE", "INSERT", "DELETE", "CREATE"))
        for s in statements
    )
    assert (
        store(path, record, datetime.now(UTC)) == a
    )  # Existing deduplication preserved.


def test_actual_eop_coverage_policy_rejects_unsupported_epoch(archive):
    c, path, _, _, _, record = archive
    old = copy.deepcopy(record)
    old["EPOCH"] = "1970-01-01T00:00:00"
    left = store(path, old, datetime(2026, 10, 18, tzinfo=UTC))
    old["MEAN_ANOMALY"] = (old["MEAN_ANOMALY"] + 1) % 360
    right = store(path, old, datetime(2026, 10, 19, tzinfo=UTC))
    params = {
        "first_id": left,
        "second_id": right,
        "at": "1970-01-01T00:00:00Z",
        "frame": "ITRS",
    }
    data = c.get("/api/comparisons", params=params).json()
    assert data["element_comparison_status"] == "complete"
    assert data["state_comparison"]["status"] == "unavailable"
    assert data["state_comparison"]["errors"][0]["code"] == "eop_out_of_range"
    assert data["state_comparison"]["difference_position_km"] is None
    params["frame"] = "TEME"
    assert (
        c.get("/api/comparisons", params=params).json()["state_comparison"]["status"]
        == "complete"
    )


def test_actual_measured_only_policy_preserved_for_both_sources(archive, monkeypatch):
    from astropy.time import Time
    from orbitiq.orbits.earth_orientation import orientation

    c, path, _, _, _, record = archive
    with orientation() as (resources, _):
        at = Time(resources.metadata["predictive_mjd"] + 2, format="mjd", scale="utc")
    future = copy.deepcopy(record)
    future["EPOCH"] = at.to_datetime(timezone=UTC).isoformat()
    left = store(path, future, datetime.now(UTC))
    future["RA_OF_ASC_NODE"] = 2.0
    right = store(path, future, datetime.now(UTC))
    monkeypatch.setenv("ORBITIQ_EOP_POLICY", "measured_only")
    data = c.get(
        "/api/comparisons",
        params={
            "first_id": left,
            "second_id": right,
            "at": future["EPOCH"],
            "frame": "ITRS",
        },
    ).json()
    assert data["state_comparison"]["status"] == "unavailable"
    assert all(
        e["code"] == "eop_prediction_disallowed"
        for e in data["state_comparison"]["errors"]
    )


def test_multiple_raw_records_are_not_accepted_as_one_valid_identity(archive):
    c, path, a, b, _, record = archive
    duplicate = json.dumps([record, record]).encode()
    corrupt(path, a, "raw_response", duplicate)
    corrupt(path, a, "response_sha256", hashlib.sha256(duplicate).hexdigest())
    data = c.get("/api/comparisons", params={"first_id": a, "second_id": b}).json()
    assert data["counts"]["incompatible"] == 1 and not data["element_differences"]


def test_query_budget_failure_is_safe_and_does_not_change_liveness(
    archive, monkeypatch
):
    from orbitiq import storage

    c, path, *_ = archive
    bulk(path, 200)
    monotonic = storage.time.monotonic
    started = False

    def expired():
        nonlocal started
        if not started:
            started = True
            return monotonic()
        return monotonic() + 1

    from types import SimpleNamespace

    monkeypatch.setattr(storage, "time", SimpleNamespace(monotonic=expired))
    response = c.get("/api/snapshots")
    assert response.status_code == 503 and str(path) not in response.text
    assert c.get("/api/health").status_code == 200


def test_itrs_sources_must_use_consistent_scientific_resources(archive, monkeypatch):
    c, _, a, b, _, record = archive
    original = investigations.earth_fixed

    def different_resource(teme):
        result = original(teme)
        if teme["snapshot_id"] == b:
            result["earth_orientation"] = {
                **result["earth_orientation"],
                "sha256": "f" * 64,
            }
        return result

    monkeypatch.setattr(investigations, "earth_fixed", different_resource)
    data = c.get(
        "/api/comparisons",
        params={
            "first_id": a,
            "second_id": b,
            "at": Elements.model_validate(record).epoch.isoformat(),
            "frame": "ITRS",
        },
    ).json()
    assert data["state_comparison"]["status"] == "unavailable"
    assert data["state_comparison"]["difference_position_km"] is None
    assert data["state_comparison"]["errors"][0]["code"] == "incompatible_states"


def test_non_finite_element_subtraction_is_withheld(archive):
    c, path, _, _, _, record = archive
    extreme = copy.deepcopy(record)
    extreme["BSTAR"] = -1e308
    a = store(path, extreme, datetime.now(UTC))
    extreme["BSTAR"] = 1e308
    b = store(path, extreme, datetime.now(UTC))
    response = c.get("/api/comparisons", params={"first_id": a, "second_id": b})
    assert response.status_code == 200
    data = response.json()
    assert data["counts"]["shared"] == 1 and not data["element_differences"]
    assert data["element_comparison_status"] == "unavailable_numeric_range"


def test_existing_catalog_cursor_uses_indexed_range_not_offset_scan(
    archive, monkeypatch
):
    from orbitiq import storage

    c, path, *_ = archive
    bulk(path, 1001)
    statements = []
    plans = []
    original = storage.connect

    def traced(*args, **kwargs):
        db = original(*args, **kwargs)

        def trace(sql):
            if "FROM snapshots" in sql and "catalog_id = 6251" in sql:
                statements.append(sql)

        db.set_trace_callback(trace)
        plans.extend(
            row[3]
            for row in db.execute("""EXPLAIN QUERY PLAN
            SELECT id FROM snapshots WHERE catalog_id=6251 AND id<4
            ORDER BY id DESC LIMIT 101""")
        )
        return db

    monkeypatch.setattr(storage, "connect", traced)
    response = c.get(
        "/api/satellites/6251/snapshots", params={"before_id": 4, "limit": 100}
    )
    assert response.status_code == 200
    assert [s["id"] for s in response.json()["snapshots"]] == [2, 1]
    assert statements and all(
        "IS NULL" not in sql and "id < 4" in sql for sql in statements
    )
    assert any(
        "SEARCH" in plan and "snapshots_catalog_id" in plan and "<?" in plan
        for plan in plans
    )


def test_unsupported_legacy_catalog_metadata_remains_browsable(archive):
    c, path, a, b, *_ = archive
    corrupt(path, a, "catalog_id", 400000)
    corrupt(
        path,
        a,
        "source_url",
        "https://celestrak.org/NORAD/elements/gp.php?CATNR=400000&FORMAT=JSON",
    )
    response = c.get("/api/snapshots", params={"snapshot_id": a})
    assert response.status_code == 200
    metadata = response.json()["snapshots"][0]
    assert metadata["catalog_id"] is None and metadata["source_url"] is None
    assert metadata["identity_consistent"] is False and metadata["metadata_issues"]
    assert (
        c.get("/api/comparisons", params={"first_id": a, "second_id": b}).json()[
            "counts"
        ]["incompatible"]
        == 1
    )
