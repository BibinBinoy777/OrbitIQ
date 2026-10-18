"""CelesTrak GP JSON (OMM fields) validation, without claiming orbit accuracy."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sgp4 import omm
from sgp4.api import WGS72, Satrec

ELEMENT_UNITS = {
    "EPOCH": "ISO8601 UTC",
    "REV_AT_EPOCH": "rev",
    "MEAN_MOTION": "rev/day",
    "ECCENTRICITY": "dimensionless",
    "INCLINATION": "deg",
    "RA_OF_ASC_NODE": "deg",
    "ARG_OF_PERICENTER": "deg",
    "MEAN_ANOMALY": "deg",
    "BSTAR": "1/Earth-radii",
    "MEAN_MOTION_DOT": "rev/day^2",
    "MEAN_MOTION_DDOT": "rev/day^3",
}
MAX_CATALOG_ID = 339999  # python-sgp4 2.27 Alpha-5 initialization limit.


class Elements(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra="ignore")

    name: str = Field(alias="OBJECT_NAME", min_length=1, max_length=128)
    object_id: str = Field(alias="OBJECT_ID", max_length=32)
    catalog_id: int = Field(alias="NORAD_CAT_ID", strict=True, ge=1, le=MAX_CATALOG_ID)
    epoch: datetime = Field(alias="EPOCH")
    mean_motion: float = Field(alias="MEAN_MOTION", strict=True, gt=0, le=100)
    eccentricity: float = Field(alias="ECCENTRICITY", strict=True, ge=0, lt=1)
    inclination: float = Field(alias="INCLINATION", strict=True, ge=0, le=180)
    raan: float = Field(alias="RA_OF_ASC_NODE", strict=True, ge=0, lt=360)
    argument: float = Field(alias="ARG_OF_PERICENTER", strict=True, ge=0, lt=360)
    anomaly: float = Field(alias="MEAN_ANOMALY", strict=True, ge=0, lt=360)
    bstar: float = Field(alias="BSTAR", strict=True)
    ndot: float = Field(alias="MEAN_MOTION_DOT", strict=True)
    nddot: float = Field(alias="MEAN_MOTION_DDOT", strict=True)
    classification: Literal["U"] = Field(alias="CLASSIFICATION_TYPE")
    element_set: int = Field(alias="ELEMENT_SET_NO", strict=True, ge=0)
    revolution: int = Field(alias="REV_AT_EPOCH", strict=True, ge=0)
    ephemeris_type: Literal[0] = Field(alias="EPHEMERIS_TYPE")
    # CelesTrak GP JSON omits these invariant fields; its format defines defaults.
    center: Literal["EARTH"] = Field(default="EARTH", alias="CENTER_NAME")
    frame: Literal["TEME"] = Field(default="TEME", alias="REF_FRAME")
    time_system: Literal["UTC"] = Field(default="UTC", alias="TIME_SYSTEM")
    theory: Literal["SGP4"] = Field(default="SGP4", alias="MEAN_ELEMENT_THEORY")

    @model_validator(mode="before")
    @classmethod
    def source_types(cls, value):
        if not isinstance(value, dict):
            raise ValueError("Expected an OMM object")
        if not isinstance(value.get("EPOCH"), str):
            raise ValueError("EPOCH must be an ISO timestamp string")
        if any(isinstance(item, bool) for item in value.values()):
            raise ValueError("Boolean values are not valid OMM fields")
        return value

    @field_validator("epoch")
    @classmethod
    def utc_epoch(cls, value: datetime) -> datetime:
        # CelesTrak's timezone-free EPOCH explicitly means UTC, not local time.
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        if value.utcoffset().total_seconds() != 0:
            raise ValueError("OMM epoch must use UTC")
        if not 1957 <= value.year <= 2099:
            raise ValueError("Epoch outside supported range 1957..2099")
        return value.astimezone(UTC)

    def satellite(self) -> Satrec:
        fields = self.model_dump(by_alias=True)
        fields["EPOCH"] = self.epoch.replace(tzinfo=None).isoformat(
            timespec="microseconds"
        )
        satellite = Satrec()
        omm.initialize(satellite, fields, gravconst=WGS72)
        return satellite
