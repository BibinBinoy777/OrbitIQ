"""Offline ingestion tests; no request in this module uses the network."""

import json
import sqlite3
import ssl
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
from orbitiq.database import initialize
from orbitiq.ingestion.celestrak import (
    BASE_URL,
    DownloadedDataset,
    IngestionError,
    configured_source,
    fetch_dataset,
    ingest,
    process_dataset,
)
from orbitiq.storage import get_snapshot, list_snapshots, verify_archive


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "isolated.sqlite3"
    initialize(path)
    return path


@pytest.fixture
def dataset():
    fixture = json.loads((Path(__file__).parent / "fixtures/vallado.json").read_text())
    return DownloadedDataset(
        json.dumps([fixture[0]["omm"]]).encode(),
        BASE_URL + "?CATNR=5&FORMAT=JSON",
        datetime(2026, 10, 18, tzinfo=UTC),
        200,
    )


def test_exact_duplicate_preserves_first_provenance(database, dataset):
    first = process_dataset(database, 5, dataset)
    before = get_snapshot(database, first)
    replay = replace(dataset, retrieved_at=dataset.retrieved_at + timedelta(hours=2))
    assert process_dataset(database, 5, replay) == first
    assert len(list_snapshots(database, 5)) == 1
    assert get_snapshot(database, first) == before
    assert before["retrieved_at"] == dataset.retrieved_at.isoformat()
    assert before["orbital_epoch"] != before["retrieved_at"]
    assert before["source_url"] == dataset.source_url


def test_concurrent_duplicate_processing_creates_one_snapshot(database, dataset):
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(
            pool.map(lambda _: process_dataset(database, 5, dataset), range(8))
        )
    assert len(set(results)) == 1
    assert len(list_snapshots(database, 5)) == 1
    assert verify_archive(database) == 1


def test_transaction_failure_rolls_back_insert_and_preserves_history(database, dataset):
    first = process_dataset(database, 5, dataset)
    before = get_snapshot(database, first)
    record = json.loads(dataset.raw)[0]
    record["ELEMENT_SET_NO"] += 1
    changed = replace(dataset, raw=json.dumps([record]).encode())
    with closing(sqlite3.connect(database)) as connection:
        connection.executescript("""
            CREATE TRIGGER injected_failure AFTER INSERT ON snapshots
            BEGIN SELECT RAISE(FAIL, 'injected write failure'); END;
        """)
    with pytest.raises(sqlite3.IntegrityError, match="injected write failure"):
        process_dataset(database, 5, changed)
    assert len(list_snapshots(database, 5)) == 1
    assert get_snapshot(database, first) == before
    assert verify_archive(database) == 1


@pytest.mark.parametrize("missing", ["EPOCH", "NORAD_CAT_ID", "MEAN_MOTION", "BSTAR"])
def test_missing_required_fields_rejected_without_writes(database, dataset, missing):
    record = json.loads(dataset.raw)[0]
    del record[missing]
    with pytest.raises(IngestionError):
        process_dataset(
            database, 5, replace(dataset, raw=json.dumps([record]).encode())
        )
    assert list_snapshots(database, 5) == []


@pytest.mark.parametrize("status", [403, 429, 500, 503, 206])
def test_http_failures_report_status_without_exposing_body(database, dataset, status):
    first = process_dataset(database, 5, dataset)
    before = get_snapshot(database, first)

    def response(request):
        return httpx.Response(
            status,
            content=b"token=DO_NOT_LOG_THIS",
            headers={"Set-Cookie": "session=DO_NOT_LOG_THIS"},
        )

    with pytest.raises(IngestionError) as caught:
        ingest(database, 5, transport=httpx.MockTransport(response))
    assert caught.value.category == "upstream_http"
    assert caught.value.status_code == status
    assert "DO_NOT_LOG_THIS" not in str(caught.value)
    assert len(list_snapshots(database, 5)) == 1
    assert get_snapshot(database, first) == before


@pytest.mark.parametrize(
    "failure,category",
    [
        (httpx.ProxyError("proxy credentials MUST_NOT_LOG"), "proxy"),
        (httpx.ConnectError("connection failed MUST_NOT_LOG"), "network"),
        (httpx.ConnectTimeout("connect timeout MUST_NOT_LOG"), "timeout"),
        (httpx.ReadTimeout("read timeout MUST_NOT_LOG"), "timeout"),
    ],
)
def test_transport_failure_classification(database, failure, category):
    def reject(request):
        raise failure

    with pytest.raises(IngestionError) as caught:
        ingest(database, 5, transport=httpx.MockTransport(reject))
    assert caught.value.category == category
    assert "MUST_NOT_LOG" not in str(caught.value)
    assert list_snapshots(database, 5) == []


def test_tls_failure_classification(database):
    def reject(request):
        raise httpx.ConnectError("TLS failed") from ssl.SSLCertVerificationError(
            "bad cert"
        )

    with pytest.raises(IngestionError) as caught:
        ingest(database, 5, transport=httpx.MockTransport(reject))
    assert caught.value.category == "tls"
    assert list_snapshots(database, 5) == []


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://celestrak.org/NORAD/elements/gp.php",
        "https://user:SECRET@celestrak.org/NORAD/elements/gp.php",
        "https://untrusted.example/NORAD/elements/gp.php",
        "https://celestrak.org/NORAD/elements/gp.php?CATNR=5",
        "https://celestrak.org/NORAD/elements/gp.php#fragment",
        "https://celestrak.org:8443/NORAD/elements/gp.php",
        "https://celestrak.org/not-the-gp-endpoint",
    ],
)
def test_invalid_source_configuration_is_rejected_before_request(monkeypatch, endpoint):
    monkeypatch.setenv("ORBITIQ_CELESTRAK_URL", endpoint)

    def unexpected(request):
        pytest.fail("Invalid configuration must never make a request")

    with pytest.raises(IngestionError) as caught:
        fetch_dataset(5, transport=httpx.MockTransport(unexpected))
    assert caught.value.category == "configuration"
    assert "SECRET" not in str(caught.value)


def test_configured_official_source_is_used(monkeypatch, dataset):
    monkeypatch.setenv("ORBITIQ_CELESTRAK_URL", BASE_URL.replace("://", "://www."))

    def response(request):
        assert request.url.host == "www.celestrak.org"
        assert dict(request.url.params) == {"CATNR": "5", "FORMAT": "JSON"}
        return httpx.Response(
            200,
            stream=httpx.ByteStream(dataset.raw),
            headers={"content-type": "application/json"},
        )

    downloaded = fetch_dataset(5, transport=httpx.MockTransport(response))
    assert downloaded.http_status == 200
    assert downloaded.raw == dataset.raw
    assert downloaded.retrieved_at.tzinfo is not None
    assert downloaded.source_url.startswith(configured_source())


@pytest.mark.parametrize("change", ["source", "timestamp", "status"])
def test_replay_requires_consistent_provenance(database, dataset, change):
    if change == "source":
        invalid = replace(
            dataset, source_url=dataset.source_url.replace("CATNR=5", "CATNR=6")
        )
    elif change == "timestamp":
        invalid = replace(
            dataset, retrieved_at=dataset.retrieved_at.replace(tzinfo=None)
        )
    else:
        invalid = replace(dataset, http_status=403)
    with pytest.raises(IngestionError):
        process_dataset(database, 5, invalid)
    assert list_snapshots(database, 5) == []


def test_verified_replay_makes_only_one_http_request(database, dataset):
    requests = []

    def response(request):
        requests.append(request)
        return httpx.Response(
            200,
            stream=httpx.ByteStream(dataset.raw),
            headers={"content-type": "application/json"},
        )

    snapshot_id = ingest(
        database, 5, transport=httpx.MockTransport(response), verify_replay=True
    )
    assert len(requests) == 1
    assert get_snapshot(database, snapshot_id)["raw_response"] == dataset.raw
    assert len(list_snapshots(database, 5)) == 1
