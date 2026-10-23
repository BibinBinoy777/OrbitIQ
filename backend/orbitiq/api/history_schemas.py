"""Document the stable history envelope, without response serialization/filtering.

Dynamic scientific evidence stays opaque here; the service owns those rules.
The frontend separately validates source references and window relationships.
"""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

SafeId = Annotated[int, Field(ge=1, le=9007199254740991)]
CatalogId = Annotated[int, Field(ge=1, le=339999)]
PageSize = Annotated[int, Field(ge=1, le=20)]
Count = Annotated[int, Field(ge=0)]


class Envelope(BaseModel):
    model_config = ConfigDict(strict=True, extra="allow")


class HistoryWindow(Envelope):
    catalog_id: CatalogId
    limit: PageSize
    before_id: SafeId | None
    anchor_id: SafeId | None


class HistoryPagination(Envelope):
    anchor_id: SafeId | None
    has_more: bool
    next_before_id: SafeId | None
    page_size: PageSize
    total_count: Count | None
    total_count_status: Literal["exact_within_anchor", "unknown_exceeds_bounded_count"]


class HistoryCoverage(Envelope):
    inspected_count: Annotated[int, Field(ge=0, le=20)]
    validated_record_count: Annotated[int, Field(ge=0, le=20)]
    complete_anchored_history: bool
    oldest_verifiable_retrieval: str | None
    newest_verifiable_retrieval: str | None
    retrieval_span_seconds: Annotated[float, Field(ge=0, allow_inf_nan=False)] | None
    chronology: str
    summary: str
    trend_statistic: None
    interpolation: Literal[False]
    extrapolation: Literal[False]


class HistoricalAnalysisEnvelope(Envelope):
    """Bounded version-1 envelope; nested evidence is defined by the history rules."""

    kind: Literal["orbitiq_historical_analysis"]
    schema_version: Literal[1]
    rule_set_version: Literal[1]
    report_id: Annotated[str, Field(pattern=r"^history-report-sha256:[a-f0-9]{64}$")]
    generated_at: str
    catalog_id: CatalogId
    request: HistoryWindow
    pagination: HistoryPagination
    coverage: HistoryCoverage
    sources: Annotated[list[dict[str, Any]], Field(max_length=20)]
    points: Annotated[list[dict[str, Any]], Field(max_length=20)]
    intervals: Annotated[list[dict[str, Any]], Field(max_length=19)]
    comparisons: Annotated[list[dict[str, Any]], Field(max_length=19)]
    findings: Annotated[list[dict[str, Any]], Field(max_length=200)]
    methodology: dict[str, Any]
    limitations: list[str]
