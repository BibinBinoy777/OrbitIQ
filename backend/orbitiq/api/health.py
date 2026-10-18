from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class Health(BaseModel):
    status: Literal["ok"]
    service: Literal["OrbitIQ"]


@router.get("/health", response_model=Health)
def health() -> Health:
    """Liveness only; does not assert database or orbital-data readiness."""
    return Health(status="ok", service="OrbitIQ")
