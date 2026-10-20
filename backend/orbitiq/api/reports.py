"""Bounded public read-only export; no server investigation ownership is implied."""

import json
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from pydantic import ValidationError

from orbitiq.api.errors import OrbitalAPIError
from orbitiq.api.orbits import call, database_path
from orbitiq.reporting import (
    MAX_DEFINITION_BYTES,
    MAX_REPORT_BYTES,
    InvestigationReport,
    parse_definition,
)
from orbitiq.services.reports import build_report

router = APIRouter()


@router.get("/investigation-reports", response_model=InvestigationReport)
def investigation_report(
    definition: Annotated[str, Query(min_length=1, max_length=MAX_DEFINITION_BYTES)],
    path: Annotated[Path, Depends(database_path)],
):
    try:
        value = parse_definition(definition)
    except (ValueError, ValidationError, RecursionError):
        raise OrbitalAPIError(
            422,
            "report_definition_invalid",
            "Invalid or unsupported investigation definition.",
        ) from None
    report = call(build_report, path, value)
    try:
        encoded = json.dumps(
            report.model_dump(mode="json"), allow_nan=False, ensure_ascii=True
        ).encode()
    except (ValueError, TypeError):
        raise OrbitalAPIError(
            500, "report_invalid", "Report values could not be validated."
        ) from None
    if len(encoded) > MAX_REPORT_BYTES:
        raise OrbitalAPIError(
            413, "report_too_large", "Report exceeds the supported export size."
        )
    return Response(
        encoded,
        media_type="application/json",
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": (
                f'attachment; filename="orbitiq-report-{report.report_id}.json"'
            ),
        },
    )
