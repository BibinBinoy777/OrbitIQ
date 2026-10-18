"""Scientific wire contracts. Existing field names and timestamp strings remain."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat


class FreshnessInfo(BaseModel):
    state: Literal["fresh", "aging", "stale", "unknown", "future_epoch"]
    evaluated_at: str = Field(description="Actual age-evaluation time, ISO8601 UTC")
    epoch_age_seconds: FiniteFloat | None
    retrieval_age_seconds: FiniteFloat | None
    fresh_hours: FiniteFloat
    stale_hours: FiniteFloat
    basis: Literal["orbital_epoch"]
    accuracy_guarantee: Literal[False]


class VectorUnits(BaseModel):
    position: Literal["km"]
    velocity: Literal["km/s"]
    epoch_offset: Literal["days"]


class Uncertainty(BaseModel):
    status: Literal["not_quantified"]
    covariance_available: Literal[False]
    observation_validated: Literal[False]


class ScientificPosition(BaseModel):
    model_config = ConfigDict(extra="allow", allow_inf_nan=False)
    snapshot_id: int
    catalog_id: int
    response_sha256: str
    source_url: str
    retrieved_at: str = Field(description="First source retrieval time, ISO8601 UTC")
    orbital_epoch: str = Field(description="Mean-element epoch, ISO8601 UTC")
    at: str = Field(description="Requested calculation time normalized to UTC")
    calculated_at: str = Field(description="Actual calculation execution time, UTC")
    position_km: tuple[FiniteFloat, FiniteFloat, FiniteFloat] = Field(
        description="TEME geocentric Cartesian x,y,z position, kilometres"
    )
    velocity_km_s: tuple[FiniteFloat, FiniteFloat, FiniteFloat] = Field(
        description="TEME Cartesian vx,vy,vz velocity, kilometres per second"
    )
    frame: Literal["TEME"]
    origin: Literal["Earth center"]
    time_system: Literal["UTC"]
    kind: Literal["calculated"]
    model: Literal["SGP4"]
    gravity_model: Literal["WGS72"]
    sgp4_version: str
    epoch_offset_days: FiniteFloat
    validation_status: str
    validation_scope: str
    snapshot_validation_status: str
    validator_version: str
    ingestion_sgp4_version: str
    snapshot_created_at: None = Field(
        default=None,
        description="Insertion time was not recorded separately; never inferred",
    )
    units: VectorUnits
    uncertainty: Uncertainty
    freshness_info: FreshnessInfo
    warnings: list[str]


class SnapshotSummary(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    catalog_id: int
    object_name: str
    orbital_epoch: str
    retrieved_at: str
    source_url: str
    response_sha256: str
    freshness_info: FreshnessInfo


class SnapshotList(BaseModel):
    snapshots: list[SnapshotSummary]


class EarthOrientation(BaseModel):
    model_config = ConfigDict(extra="allow", allow_inf_nan=False)
    source: str
    package_version: str
    sha256: str
    leap_seconds_sha256: str
    leap_seconds_expires: str
    policy: Literal["measured_only", "measured_or_predicted"]
    status: Literal["measured", "predicted"]
    ut1_minus_utc_seconds: FiniteFloat
    polar_motion_x_arcsec: FiniteFloat
    polar_motion_y_arcsec: FiniteFloat
    prediction_table_age_days: FiniteFloat
    auto_download: Literal[False]
    degraded_results_allowed: Literal[False]


class GeodeticPosition(BaseModel):
    latitude_deg: FiniteFloat = Field(ge=-90, le=90)
    longitude_deg: FiniteFloat = Field(ge=-180, lt=180)
    altitude_km: FiniteFloat
    height_reference: Literal["WGS84 ellipsoid"]


class TerrestrialUnits(BaseModel):
    position: Literal["km"]
    velocity: Literal["km/s"]
    angles: Literal["deg"]
    altitude: Literal["km"]


class EarthFixedPosition(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    teme: ScientificPosition
    at: str
    kind: Literal["calculated"]
    input_frame: Literal["TEME"]
    frame: Literal["ITRS"]
    origin: Literal["Earth center"]
    time_system: Literal["UTC"]
    position_km: tuple[FiniteFloat, FiniteFloat, FiniteFloat]
    velocity_km_s: tuple[FiniteFloat, FiniteFloat, FiniteFloat]
    units: TerrestrialUnits
    geodetic: GeodeticPosition
    transformation_status: Literal["measured_eop", "predicted_eop"]
    method: str
    astropy_version: str
    pyerfa_version: str
    earth_orientation: EarthOrientation
    warnings: list[str]


class GroundTrackPoint(EarthFixedPosition):
    sample_index: int = Field(ge=0, le=999)
    segment_id: int = Field(ge=0, le=999)


class GroundTrack(BaseModel):
    status: Literal["complete"]
    failure_policy: Literal["reject_entire_request"]
    catalog_id: int
    snapshot_id: int
    response_sha256: str
    orbital_epoch: str
    retrieved_at: str
    requested_start: str
    requested_end: str
    actual_start: str
    actual_end: str
    step_seconds: int
    sample_count: int = Field(ge=1, le=1000)
    limits: dict[str, int]
    input_frame: Literal["TEME"]
    frame: Literal["ITRS"]
    kind: Literal["calculated"]
    points: list[GroundTrackPoint] = Field(min_length=1, max_length=1000)
    warnings: list[str]
