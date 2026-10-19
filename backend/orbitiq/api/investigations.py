"""Bounded public stored-data browsing and two-source investigation."""

from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response

from orbitiq.api.orbits import RequestedTime, call, database_path
from orbitiq.orbits.elements import MAX_CATALOG_ID
from orbitiq.services import investigations

router = APIRouter()
Identifier = Annotated[int, Query(ge=1, le=9223372036854775807)]
OptionalID = Annotated[int | None, Query(ge=1, le=9223372036854775807)]


@router.get("/snapshots")
@router.get("/discovery/satellites")
def snapshots(
    response: Response,
    path: Annotated[Path, Depends(database_path)],
    q: Annotated[str, Query(max_length=64)] = "",
    match: Literal["exact", "partial"] = "partial",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    before_id: OptionalID = None,
    anchor_id: OptionalID = None,
    catalog_id: Annotated[int | None, Query(ge=1, le=MAX_CATALOG_ID)] = None,
    snapshot_id: OptionalID = None,
    context_snapshot_id: OptionalID = None,
    selected_only: bool = False,
):
    response.headers["Cache-Control"] = "no-store"
    return call(
        lambda: investigations.listing(
            path,
            query=q,
            match=match,
            limit=limit,
            before_id=before_id,
            anchor_id=anchor_id,
            catalog_id=catalog_id,
            snapshot_id=snapshot_id,
            context_snapshot_id=context_snapshot_id,
            selected_only=selected_only,
        )
    )


@router.get("/comparisons")
def comparison(
    response: Response,
    path: Annotated[Path, Depends(database_path)],
    first_id: Identifier,
    second_id: Identifier,
    at: RequestedTime | None = None,
    frame: Literal["TEME", "ITRS"] = "TEME",
    category: Literal["all", "shared", "added", "removed", "incompatible"] = "all",
):
    response.headers["Cache-Control"] = "no-store"
    return call(investigations.compare, path, first_id, second_id, at, frame, category)
