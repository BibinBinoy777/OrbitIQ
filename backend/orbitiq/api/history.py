"""Read-only bounded historical analysis; never ingests or creates replay packages."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from orbitiq.api.orbits import call, database_path
from orbitiq.orbits.elements import MAX_CATALOG_ID
from orbitiq.services.history import historical_analysis

router = APIRouter()
Cursor = Annotated[int | None, Query(ge=1, le=9007199254740991)]


@router.get("/historical-analysis")
def history(
    response: Response,
    path: Annotated[Path, Depends(database_path)],
    catalog_id: Annotated[int, Query(ge=1, le=MAX_CATALOG_ID)],
    limit: Annotated[int, Query(ge=1, le=20)] = 20,
    before_id: Cursor = None,
    anchor_id: Cursor = None,
):
    response.headers["Cache-Control"] = "no-store"
    return call(
        lambda: historical_analysis(
            path, catalog_id, limit=limit, before_id=before_id, anchor_id=anchor_id
        )
    )
