"""Operator-only, one-object ingestion; no public endpoint triggers upstream fetches."""

import argparse
import json
import os
import sqlite3
import ssl
import time
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import httpx
from pydantic import ValidationError

from orbitiq.database import configured_path
from orbitiq.orbits.elements import MAX_CATALOG_ID, Elements
from orbitiq.orbits.engine import propagate_satellite
from orbitiq.storage import connect, save_snapshot

BASE_URL = "https://celestrak.org/NORAD/elements/gp.php"
MAX_BYTES = 64 * 1024


class IngestionError(ValueError):
    def __init__(
        self,
        message: str,
        *,
        category: str = "validation",
        status_code: int | None = None,
    ):
        super().__init__(message)
        self.category = category
        self.status_code = status_code


@dataclass(frozen=True)
class DownloadedDataset:
    raw: bytes
    source_url: str
    retrieved_at: datetime
    http_status: int


def validate_catalog_id(catalog_id: int) -> None:
    if type(catalog_id) is not int or not 1 <= catalog_id <= MAX_CATALOG_ID:
        raise IngestionError(f"Catalog ID must be in 1..{MAX_CATALOG_ID}")


def configured_source() -> str:
    value = os.environ.get("ORBITIQ_CELESTRAK_URL", BASE_URL)
    try:
        url = httpx.URL(value)
    except httpx.InvalidURL:
        raise IngestionError(
            "Invalid CelesTrak endpoint configuration", category="configuration"
        ) from None
    if (
        url.scheme != "https"
        or url.host not in {"celestrak.org", "www.celestrak.org"}
        or url.port not in (None, 443)
        or url.username
        or url.password
        or url.path != "/NORAD/elements/gp.php"
        or url.query
        or url.fragment
    ):
        raise IngestionError(
            "Endpoint must be an official HTTPS CelesTrak GP URL "
            "without credentials, query or fragment",
            category="configuration",
        )
    return str(url)


def has_tls_cause(error: Exception) -> bool:
    current = error
    while current is not None:
        if isinstance(current, ssl.SSLError):
            return True
        current = current.__cause__
    return False


def parse_response(raw: bytes, catalog_id: int) -> tuple[dict, Elements]:
    if len(raw) > MAX_BYTES:
        raise IngestionError("Upstream response exceeds 64 KiB")
    try:

        def unique_object(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("Duplicate JSON field")
                result[key] = value
            return result

        def invalid_constant(value):
            raise ValueError("Non-finite JSON value")

        payload = json.loads(
            raw, object_pairs_hook=unique_object, parse_constant=invalid_constant
        )
        if not isinstance(payload, list) or len(payload) != 1:
            raise ValueError("Expected exactly one GP record")
        record = payload[0]
        elements = Elements.model_validate(record)
        if elements.catalog_id != catalog_id:
            raise ValueError("Returned catalog ID does not match the request")
        propagate_satellite(elements.satellite(), elements.epoch)
        return record, elements
    except (
        ValueError,
        TypeError,
        UnicodeError,
        OverflowError,
        ValidationError,
        RecursionError,
    ) as error:
        raise IngestionError("Invalid or unsupported CelesTrak GP record") from error


def fetch_dataset(catalog_id: int, *, transport=None) -> DownloadedDataset:
    """Download once. Separately processing these exact bytes permits safe replay."""
    validate_catalog_id(catalog_id)
    source = configured_source()
    params = {"CATNR": str(catalog_id), "FORMAT": "JSON"}
    timeout = httpx.Timeout(15, connect=5)
    try:
        with httpx.Client(
            timeout=timeout, follow_redirects=False, transport=transport
        ) as client:
            started = time.monotonic()
            with client.stream(
                "GET",
                source,
                params=params,
                headers={"User-Agent": "OrbitIQ/0.1", "Accept-Encoding": "identity"},
            ) as response:
                response.raise_for_status()
                if response.status_code != 200:
                    raise IngestionError(
                        f"Expected HTTP 200, received {response.status_code}",
                        category="upstream_http",
                        status_code=response.status_code,
                    )
                content_type = response.headers.get("content-type", "").lower()
                if content_type.split(";", 1)[0].strip() != "application/json":
                    raise IngestionError("Expected an upstream JSON response")
                if response.headers.get("content-encoding", "identity") != "identity":
                    raise IngestionError("Compressed upstream response is unsupported")
                body = bytearray()
                for chunk in response.iter_raw():
                    if time.monotonic() - started > 20:
                        raise IngestionError(
                            "Upstream response exceeded total time budget",
                            category="timeout",
                        )
                    body.extend(chunk)
                    if len(body) > MAX_BYTES:
                        raise IngestionError("Upstream response exceeds 64 KiB")
                source_url = str(response.url)
        retrieved_at = datetime.now(UTC)
    except httpx.ProxyError as error:
        raise IngestionError(
            "Outbound proxy connection failed; no snapshot saved", category="proxy"
        ) from error
    except httpx.HTTPStatusError as error:
        status = error.response.status_code
        raise IngestionError(
            f"Upstream HTTPS response returned HTTP {status}; no snapshot saved",
            category="upstream_http",
            status_code=status,
        ) from error
    except httpx.TimeoutException as error:
        raise IngestionError(
            "CelesTrak request timed out; no snapshot saved", category="timeout"
        ) from error
    except httpx.HTTPError as error:
        category = "tls" if has_tls_cause(error) else "network"
        raise IngestionError(
            f"CelesTrak {category} request failed; no snapshot saved", category=category
        ) from error
    return DownloadedDataset(
        bytes(body), source_url, retrieved_at, response.status_code
    )


def process_dataset(path: Path, catalog_id: int, dataset: DownloadedDataset) -> int:
    """Validate and persist a downloaded dataset; exact replay is idempotent."""
    validate_catalog_id(catalog_id)
    if dataset.http_status != 200:
        raise IngestionError("Only a successful response can be processed")
    source = httpx.URL(dataset.source_url)
    # Provenance must identify the same supported endpoint and requested object.
    base = source.copy_with(query=None, fragment=None)
    if (
        base.scheme != "https"
        or base.host not in {"celestrak.org", "www.celestrak.org"}
        or base.port not in (None, 443)
        or base.username
        or base.password
        or base.path != "/NORAD/elements/gp.php"
        or source.fragment
        or sorted(source.params.multi_items())
        != sorted([("CATNR", str(catalog_id)), ("FORMAT", "JSON")])
    ):
        raise IngestionError("Dataset source provenance does not match the request")
    if dataset.retrieved_at.tzinfo is None or dataset.retrieved_at.utcoffset() is None:
        raise IngestionError("Retrieval timestamp must include a timezone")
    record, elements = parse_response(dataset.raw, catalog_id)
    return save_snapshot(
        path, dataset.raw, record, elements, dataset.source_url, dataset.retrieved_at
    )


def ingest(
    path: Path, catalog_id: int, *, transport=None, verify_replay: bool = False
) -> int:
    validate_catalog_id(catalog_id)
    with closing(connect(path)):
        pass
    dataset = fetch_dataset(catalog_id, transport=transport)
    snapshot_id = process_dataset(path, catalog_id, dataset)
    if verify_replay and process_dataset(path, catalog_id, dataset) != snapshot_id:
        raise IngestionError(
            "Dataset replay did not reuse its snapshot", category="storage"
        )
    return snapshot_id


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog_id", type=int)
    parser.add_argument(
        "--verify-replay",
        action="store_true",
        help="Process the same downloaded bytes twice, without refetching",
    )
    args = parser.parse_args()
    try:
        snapshot_id = ingest(
            configured_path(), args.catalog_id, verify_replay=args.verify_replay
        )
    except (ValueError, OSError, RuntimeError, sqlite3.Error) as error:
        category = f" [{error.category}]" if isinstance(error, IngestionError) else ""
        parser.exit(1, f"Ingestion failed{category}: {error}\n")
    print(
        f"Snapshot {snapshot_id} ready from CelesTrak "
        "(an exact duplicate reuses the original snapshot)"
        + (
            "; replay verified without another HTTP request"
            if args.verify_replay
            else ""
        )
    )


if __name__ == "__main__":
    main()
