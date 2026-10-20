"""Minimal dependency probe; scientific readiness is a separate public contract."""

import sqlite3

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from orbitiq.database import configured_path
from orbitiq.storage import browsing_connection

router = APIRouter()


@router.get("/ready")
def ready():
    try:
        with browsing_connection(configured_path()) as db:
            versions = db.execute(
                "SELECT version FROM schema_version LIMIT 2"
            ).fetchall()
            if [tuple(row) for row in versions] != [(3,)]:
                raise ValueError
            db.execute("SELECT id FROM snapshots LIMIT 1").fetchall()
            db.execute("SELECT id FROM ingestion_attempts LIMIT 1").fetchall()
            db.execute("SELECT snapshot_id FROM snapshot_insertions LIMIT 1").fetchall()
            db.execute("SELECT id FROM collection_gate LIMIT 1").fetchall()
        return JSONResponse({"status": "ready"}, headers={"Cache-Control": "no-store"})
    except (OSError, ValueError, sqlite3.Error, RuntimeError):
        return JSONResponse(
            {"status": "unavailable"},
            status_code=503,
            headers={"Cache-Control": "no-store"},
        )
