"""Bounded replay bundle contract; checksums are not provider authentication."""

from typing import Annotated, Literal

from pydantic import Field, JsonValue

from orbitiq.reporting import Contract, ReportTime

SHA256 = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
UUID_TEXT = Annotated[
    str,
    Field(pattern=(r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$")),
]
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_TOTAL_BYTES = 24 * 1024 * 1024
MAX_JSON_DEPTH = 32
MAX_JSON_NODES = 200000
MAX_COLLECTION_ITEMS = 4096
MAX_STRING_LENGTH = 16384
TOLERANCES = {
    "position_km": 1e-8,
    "velocity_km_s": 1e-10,
    "geodetic_angle_deg": 1e-9,
    "altitude_km": 1e-8,
    "relative": 0,
    "other_numeric": 0,
}


class BundleError(ValueError):
    """Only static safe messages and fixed member/field labels reach diagnostics."""

    def __init__(self, message, code="bundle_invalid", *, member=None, field=None):
        super().__init__(message)
        self.code, self.member, self.field = code, member, field


class FileIdentity(Contract):
    sha256: SHA256
    bytes: Annotated[int, Field(strict=True, ge=1, le=MAX_FILE_BYTES)]


class ReplaySettings(Contract):
    eop_policy: Literal["measured_only", "measured_or_predicted"]
    fresh_hours: Annotated[float, Field(strict=True, gt=0)]
    stale_hours: Annotated[float, Field(strict=True, gt=0, le=168)]
    max_samples: Annotated[int, Field(strict=True, ge=1, le=1000)]
    max_duration_seconds: Annotated[int, Field(strict=True, ge=10, le=86400)]


class BundleManifest(Contract):
    schema_version: Annotated[int, Field(strict=True, ge=1, le=1)]
    kind: Literal["orbitiq_replay_bundle"]
    capture_id: UUID_TEXT
    report_id: UUID_TEXT
    captured_at: ReportTime
    policy_evaluated_at: ReportTime
    source_count: Annotated[int, Field(strict=True, ge=1, le=2)]
    eop_required: Annotated[bool, Field(strict=True)]
    environment: dict[str, JsonValue]
    source_revision: dict[str, JsonValue]
    settings: ReplaySettings
    tolerances: dict[str, float]
    files: dict[str, FileIdentity]
