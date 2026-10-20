"""Version-1 report contract; browser definitions are inputs, never evidence."""

import json
import re
from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    JsonValue,
    TypeAdapter,
    field_validator,
    model_validator,
)

MAX_DEFINITION_BYTES = 2048
MAX_REPORT_BYTES = 8 * 1024 * 1024
Identifier = Annotated[int, Field(strict=True, ge=1, le=9007199254740991)]


def report_time(value):
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?(?:Z|[+-]\d\d:\d\d)",
        value,
    ):
        raise ValueError("Expected an explicit ISO timestamp")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except (ValueError, OverflowError):
        raise ValueError("Unrepresentable timestamp") from None


ReportTime = Annotated[datetime, BeforeValidator(report_time)]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class SourceReference(Contract):
    snapshot_id: Identifier
    catalog_id: Annotated[int, Field(strict=True, ge=1, le=339999)]
    orbital_epoch: ReportTime
    retrieved_at: ReportTime
    response_sha256: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class Definition(Contract):
    schema_version: Literal[1]
    source: SourceReference

    @field_validator("schema_version", mode="before")
    @classmethod
    def actual_integer(cls, value):
        if type(value) is not int:
            raise ValueError("Schema version must be an integer")
        return value


class SnapshotDefinition(Definition):
    mode: Literal["snapshot"]
    frame: Literal["TEME"]


class PositionDefinition(Definition):
    mode: Literal["position"]
    frame: Literal["TEME"]
    at: ReportTime


class TrackParameters(Contract):
    start: ReportTime
    duration_minutes: Annotated[int, Field(strict=True, ge=1, le=1440)]
    step_seconds: Annotated[int, Field(strict=True, ge=10, le=3600)]
    selected_index: Annotated[int, Field(strict=True, ge=0, le=360)]


class TrackDefinition(Definition):
    mode: Literal["ground-track"]
    frame: Literal["ITRS"]
    at: ReportTime
    track: TrackParameters

    @model_validator(mode="after")
    def bounded_sample(self):
        count = self.track.duration_minutes * 60 // self.track.step_seconds + 1
        try:
            selected = self.track.start + timedelta(
                seconds=self.track.selected_index * self.track.step_seconds
            )
            self.track.start + timedelta(minutes=self.track.duration_minutes)
        except OverflowError:
            raise ValueError("Track interval is not representable") from None
        if count > 361 or self.track.selected_index >= count or selected != self.at:
            raise ValueError("Invalid bounded track or selected sample")
        return self


class ComparisonDefinition(Definition):
    mode: Literal["comparison"]
    frame: Literal["TEME", "ITRS"]
    at: ReportTime | None
    comparison_source: SourceReference
    category: Literal["all", "shared", "added", "removed", "incompatible"]


ReportDefinition = Annotated[
    SnapshotDefinition | PositionDefinition | TrackDefinition | ComparisonDefinition,
    Field(discriminator="mode"),
]
DEFINITION_ADAPTER = TypeAdapter(ReportDefinition)


def parse_definition(text: str):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate report definition key")
            result[key] = value
        return result

    def constant(_):
        raise ValueError("Nonfinite report definition")

    if len(text.encode()) > MAX_DEFINITION_BYTES:
        raise ValueError("Definition exceeds its bound")
    return DEFINITION_ADAPTER.validate_python(
        json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    )


class ReportIssue(Contract):
    code: str
    message: str


class ReportCalculation(Contract):
    status: Literal["complete", "unavailable", "not_requested"]
    data: dict[str, JsonValue] | None
    errors: list[ReportIssue]


class ReportInvestigation(Contract):
    id: str
    id_kind: Literal["configuration_sha256"]
    title: str
    title_origin: Literal["generated_from_verified_sources"]
    definition: ReportDefinition
    saved_record_id: None = None
    saved_title: None = None
    description: None = None
    created_at: None = None
    saved_metadata_status: Literal["browser_only_excluded"] = "browser_only_excluded"


class PayloadHash(Contract):
    algorithm: Literal["SHA-256"]
    value: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
    scope: str
    integrity_status: Literal["verified_against_stored_bytes"]


class ReportSource(Contract):
    role: Literal["primary", "comparison"]
    reference: SourceReference
    source_type: Literal["celestrak_gp_omm_mean_elements"]
    provider: Literal["CelesTrak"]
    source_url: str
    object_name: str
    object_id: str
    source_frame: Literal["TEME"]
    epoch_time_system: Literal["UTC"]
    snapshot_created_at: str | None
    snapshot_creation_status: Literal["recorded", "unknown_legacy"]
    observation_at: None
    observation_time_status: Literal["not_applicable_mean_elements_not_observations"]
    publication_at: None
    publication_time_status: Literal["not_recorded"]
    payload_hash: PayloadHash
    provider_published_hash: None
    provider_hash_status: Literal["not_recorded"]
    source_authenticity: Literal["not_independently_verified"]
    validation_status: str
    validator_version: str
    ingestion_sgp4_version: str
    checks_performed_for_report: list[str]
    freshness_info: dict[str, JsonValue]
    elements: dict[str, JsonValue]
    element_units: dict[str, str]


class InvestigationReport(Contract):
    schema_version: Literal[1] = 1
    template_version: Literal[1] = 1
    kind: Literal["orbitiq_investigation_report"] = "orbitiq_investigation_report"
    report_id: str
    generated_at: str
    status: Literal["complete", "partial"]
    investigation: ReportInvestigation
    sources: list[ReportSource]
    calculation: ReportCalculation
    validation: dict[str, JsonValue]
    methodology: dict[str, JsonValue]
    limitations: list[str]
    warnings: list[str]
