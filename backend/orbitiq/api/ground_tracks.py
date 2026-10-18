"""Separate explicit terrestrial endpoints; the original TEME route is unchanged."""

from pathlib import Path as FilePath
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from orbitiq.api.orbits import Catalog, RequestedTime, Snapshot, call, database_path
from orbitiq.api.scientific_schemas import EarthFixedPosition, GroundTrack
from orbitiq.services import ground_tracks

router = APIRouter()


@router.get("/snapshots/{snapshot_id}/earth-fixed", response_model=EarthFixedPosition)
def earth_fixed(
    snapshot_id: Snapshot,
    at: RequestedTime,
    path: Annotated[FilePath, Depends(database_path)],
    frame: Literal["ITRS"] = "ITRS",
):
    return call(ground_tracks.terrestrial_position, path, snapshot_id, at)


@router.get("/satellites/{catalog_id}/ground-track", response_model=GroundTrack)
def ground_track(
    catalog_id: Catalog,
    snapshot_id: Annotated[int, Query(ge=1, le=9223372036854775807)],
    start: RequestedTime,
    end: RequestedTime,
    path: Annotated[FilePath, Depends(database_path)],
    step_seconds: Annotated[int, Query(ge=10, le=3600)] = 60,
    frame: Literal["ITRS"] = "ITRS",
):
    return call(
        ground_tracks.track, path, catalog_id, snapshot_id, start, end, step_seconds
    )
