"""Opt-in local captured evidence; GET only, no ingestion/upload or replay endpoint."""

import os
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter
from fastapi import Path as RoutePath

from orbitiq.api.errors import OrbitalAPIError
from orbitiq.replay_contract import BundleError
from orbitiq.services.observation_validation import archive_listing, read_package

router = APIRouter()


def root():
    value = os.environ.get("ORBITIQ_VALIDATION_ARCHIVE")
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute() or path.is_symlink() or not path.is_dir():
        raise ValueError("Unavailable explicit validation archive")
    return path


def safe(function):
    try:
        return function()
    except (OSError, ValueError, KeyError, TypeError, BundleError):
        raise OrbitalAPIError(
            503,
            "validation_evidence_unavailable",
            (
                "Configured validation evidence is unavailable, incomplete or"
                " incompatible; ask the local operator to verify it."
            ),
        ) from None


@router.get("/observation-validations")
def validations():
    return safe(lambda: archive_listing(root()))


@router.get("/observation-validations/{run_id}")
def validation(run_id: Annotated[str, RoutePath(pattern=r"^[a-f0-9]{32}$")]):
    def load():
        path = root()
        if path is None:
            raise OrbitalAPIError(
                404,
                "validation_not_configured",
                "No observation validation evidence archive is configured",
            )
        return read_package(path / run_id)[0]

    return safe(load)
