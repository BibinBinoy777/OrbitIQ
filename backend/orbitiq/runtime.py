"""Explicit production configuration; no database creation or resource downloads."""

import os
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass

from orbitiq.database import configured_path, connect_existing, validate


@dataclass(frozen=True)
class Settings:
    environment: str = "development"
    allowed_hosts: tuple[str, ...] = ()
    max_calculations: int = 4

    @property
    def production(self):
        return self.environment == "production"

    @classmethod
    def load(cls):
        environment = os.environ.get("ORBITIQ_ENVIRONMENT", "development")
        if environment not in {"development", "test", "production"}:
            raise ValueError(
                "ORBITIQ_ENVIRONMENT must be development, test or production"
            )
        hosts = os.environ.get("ORBITIQ_ALLOWED_HOSTS", "")
        allowed = tuple(h.strip().lower() for h in hosts.split(",") if h.strip())
        label = r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
        if (
            len(hosts) > 1024
            or len(allowed) > 20
            or any(not re.fullmatch(rf"{label}(?:\.{label})*", h) for h in allowed)
            or any(len(h) > 253 for h in allowed)
        ):
            raise ValueError(
                "ORBITIQ_ALLOWED_HOSTS requires bounded explicit DNS hosts"
            )
        if environment == "production":
            if not allowed:
                raise ValueError("ORBITIQ_ALLOWED_HOSTS is required in production")
            configured_path()  # Explicit absolute path only; never creates a file.
            if os.environ.get("ORBITIQ_EOP_POLICY") not in {
                "measured_only",
                "measured_or_predicted",
            }:
                raise ValueError("ORBITIQ_EOP_POLICY must be explicit in production")
            for name, low, high, default in [
                ("ORBITIQ_TRACK_MAX_SAMPLES", 1, 1000, 361),
                ("ORBITIQ_TRACK_MAX_DURATION_SECONDS", 10, 86400, 86400),
            ]:
                try:
                    value = int(os.environ.get(name, str(default)))
                    if not low <= value <= high:
                        raise ValueError
                except ValueError:
                    raise ValueError(
                        f"{name} is outside its supported limits"
                    ) from None
            # The service's established freshness policy validates its own bounds.
            from orbitiq.orbits.freshness import FreshnessPolicy

            try:
                FreshnessPolicy.configured()
            except ValueError:
                raise ValueError("Orbital freshness configuration is invalid") from None
        return cls(environment, allowed)


def check_production_database():
    try:
        with closing(connect_existing(configured_path())) as db:
            validate(db)
            if db.execute("SELECT version FROM schema_version").fetchall() != [(3,)]:
                raise ValueError
    except (ValueError, OSError, sqlite3.Error):
        raise RuntimeError(
            "Production database validation failed; provision or explicitly migrate "
            "an existing schema-3 archive before starting."
        ) from None
