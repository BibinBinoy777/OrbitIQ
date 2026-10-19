"""Application composition. Startup never creates or modifies a database."""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, ResponseValidationError

from orbitiq.api.errors import (
    OrbitalAPIError,
    orbital_error_handler,
    request_error_handler,
    response_error_handler,
)
from orbitiq.api.ground_tracks import router as ground_tracks_router
from orbitiq.api.health import router as health_router
from orbitiq.api.investigations import router as investigations_router
from orbitiq.api.orbits import router as orbits_router
from orbitiq.api.readiness import router as readiness_router


def create_app() -> FastAPI:
    application = FastAPI(title="OrbitIQ", version="0.1.0")
    application.add_exception_handler(OrbitalAPIError, orbital_error_handler)
    application.add_exception_handler(RequestValidationError, request_error_handler)
    application.add_exception_handler(ResponseValidationError, response_error_handler)
    application.include_router(health_router, prefix="/api")
    application.include_router(investigations_router, prefix="/api")
    application.include_router(orbits_router, prefix="/api")
    application.include_router(ground_tracks_router, prefix="/api")
    application.include_router(readiness_router, prefix="/api")
    return application


app = create_app()
