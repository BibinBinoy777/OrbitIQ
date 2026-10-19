"""Informational readiness; no maintenance operation is exposed over HTTP."""

from typing import Literal

from fastapi import APIRouter, Response
from pydantic import BaseModel, ConfigDict

from orbitiq.api.orbits import RequestedTime
from orbitiq.services.readiness import assess

router = APIRouter()
Status = Literal["healthy", "degraded", "unavailable", "unknown"]


class Component(BaseModel):
    model_config = ConfigDict(extra="allow", allow_inf_nan=False)
    status: Status
    code: str
    message: str


class Components(BaseModel):
    database: Component
    orbital_data: Component
    ingestion: Component
    eop: Component
    leap_seconds: Component


class Readiness(BaseModel):
    status: Status
    kind: Literal["calculated_readiness_assessment"]
    evaluated_at: str
    requested_at: str
    time_system: Literal["UTC"]
    components: Components
    scope: str
    automatic_updates: Literal[False]


@router.get("/readiness", response_model=Readiness)
def readiness(response: Response, at: RequestedTime | None = None):
    response.headers["Cache-Control"] = "no-store"
    return assess(at)
