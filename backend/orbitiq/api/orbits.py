"""Read-only routes; orchestration and calculations live outside the API layer."""

from pathlib import Path as FilePath
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path, Query
from pydantic import AwareDatetime, BeforeValidator

from orbitiq.api.errors import OrbitalAPIError
from orbitiq.api.scientific_schemas import ScientificPosition, SnapshotList
from orbitiq.database import configured_path
from orbitiq.orbits.elements import MAX_CATALOG_ID
from orbitiq.services import analysis

router = APIRouter()
Catalog = Annotated[int, Path(ge=1, le=MAX_CATALOG_ID)]
Snapshot = Annotated[int, Path(ge=1, le=9223372036854775807)]


def iso_time(value):
    if isinstance(value, str) and value.replace(".", "", 1).lstrip("+-").isdigit():
        raise ValueError("Expected ISO8601 datetime with timezone")
    return value


RequestedTime = Annotated[AwareDatetime, BeforeValidator(iso_time)]


def database_path():
    try:
        return configured_path()
    except ValueError:
        raise OrbitalAPIError(
            503, "storage_unconfigured", "Orbital storage is not configured"
        ) from None


def call(function, *args):
    try:
        return function(*args)
    except analysis.AnalysisError as error:
        raise OrbitalAPIError(error.status, error.code, error.message) from None


@router.get("/satellites/{catalog_id}/snapshots", response_model=SnapshotList)
def snapshots(
    catalog_id: Catalog,
    path: Annotated[FilePath, Depends(database_path)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    before_id: Annotated[int | None, Query(ge=1, le=9223372036854775807)] = None,
):
    return call(analysis.snapshot_history, path, catalog_id, limit, before_id)


@router.get("/snapshots/{snapshot_id}")
def snapshot(snapshot_id: Snapshot, path: Annotated[FilePath, Depends(database_path)]):
    return call(analysis.snapshot_detail, path, snapshot_id)


@router.get("/snapshots/{snapshot_id}/position", response_model=ScientificPosition)
def position(
    snapshot_id: Snapshot,
    at: RequestedTime,
    path: Annotated[FilePath, Depends(database_path)],
    frame: Annotated[
        Literal["TEME"],
        Query(description="Only TEME is supported; no frame conversion"),
    ] = "TEME",
):
    return call(analysis.position, path, snapshot_id, at)
