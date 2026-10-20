"""Application composition. Startup never creates or modifies a database."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from orbitiq.api.boundary import HTTPBoundary
from orbitiq.api.errors import (
    OrbitalAPIError,
    orbital_error_handler,
    request_error_handler,
    response_error_handler,
)
from orbitiq.api.ground_tracks import router as ground_tracks_router
from orbitiq.api.health import router as health_router
from orbitiq.api.investigations import router as investigations_router
from orbitiq.api.operational import router as operational_router
from orbitiq.api.orbits import router as orbits_router
from orbitiq.api.readiness import router as readiness_router
from orbitiq.api.reports import router as reports_router
from orbitiq.runtime import Settings, check_production_database


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.load()

    @asynccontextmanager
    async def lifespan(application):
        if settings.production:
            check_production_database()
        yield

    application = FastAPI(
        title="OrbitIQ",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None if settings.production else "/docs",
        redoc_url=None if settings.production else "/redoc",
        openapi_url=None if settings.production else "/openapi.json",
    )
    application.add_exception_handler(OrbitalAPIError, orbital_error_handler)
    application.add_exception_handler(RequestValidationError, request_error_handler)
    application.add_exception_handler(ResponseValidationError, response_error_handler)
    application.include_router(health_router, prefix="/api")
    application.include_router(operational_router, prefix="/api")
    application.include_router(investigations_router, prefix="/api")
    application.include_router(orbits_router, prefix="/api")
    application.include_router(ground_tracks_router, prefix="/api")
    application.include_router(readiness_router, prefix="/api")
    application.include_router(reports_router, prefix="/api")
    if settings.production:
        application.add_middleware(
            TrustedHostMiddleware, allowed_hosts=list(settings.allowed_hosts)
        )
    application.add_middleware(HTTPBoundary, settings=settings)
    return application


app = create_app()
