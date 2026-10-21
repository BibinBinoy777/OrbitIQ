"""Literal time anchors and synthetic input gates, never satellite accuracy data.

GPS epoch/2000 anchors: Astropy TimeGPS documentation. Historical UTC anchors:
GPS/TAI definition and IERS leap rows (2012:35, 2015:36, 2017:37 seconds).
Expected strings below are fixed independently of the conversion under test.
"""

import json
import runpy
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest
from astropy.time import Time
from orbitiq.orbits.earth_orientation import TransformationError
from orbitiq.services import analysis

ROOT = Path(__file__).resolve().parents[2]
TOOL = runpy.run_path(str(ROOT / "scripts/qualify_swarm_inputs.py"))
# Reuse the existing explicitly synthetic specimen factory without changing it.
FIXTURE = runpy.run_path(
    str(Path(__file__).with_name("test_phase113_swarm_inspection.py"))
)
GLOBALS = TOOL["gps_to_utc"].__globals__


def parts(text):
    return text.split()


@pytest.mark.parametrize(
    "gps,utc",
    [
        ("1980 01 06 00 00 00.00000000", "1980-01-06T00:00:00.000000Z"),
        ("2000 01 01 00 00 13.00000000", "2000-01-01T00:00:00.000000Z"),
        ("2014 01 01 00 02 20.00000000", "2014-01-01T00:02:04.000000Z"),
        ("2014 01 01 00 00 10.00000000", "2013-12-31T23:59:54.000000Z"),
        ("2014 01 01 23 59 59.12345600", "2014-01-01T23:59:43.123456Z"),
        ("2014 01 01 00 02 20.00000100", "2014-01-01T00:02:04.000001Z"),
        ("2015 07 01 00 00 15.00000000", "2015-06-30T23:59:59.000000Z"),
        ("2015 07 01 00 00 17.00000000", "2015-07-01T00:00:00.000000Z"),
        ("2017 01 01 00 00 16.00000000", "2016-12-31T23:59:59.000000Z"),
        ("2017 01 01 00 00 18.00000000", "2017-01-01T00:00:00.000000Z"),
    ],
)
def test_literal_gps_utc_instants_and_microsecond_preservation(gps, utc):
    assert TOOL["gps_to_utc"](parts(gps)) == utc


@pytest.mark.parametrize(
    "gps,code",
    [
        (
            "2014 01 01 00 02 60.00000000",
            "source_second_60_requires_provider_clarification",
        ),
        (
            "2014 01 01 00 02 20.00000001",
            "source_precision_exceeds_microsecond_contract",
        ),
        (
            "2014 01 01 00 02 19.99999999",
            "source_precision_exceeds_microsecond_contract",
        ),
        (
            "2015 07 01 00 00 16.00000000",
            "utc_leap_second_not_supported_by_propagator_datetime",
        ),
        (
            "2017 01 01 00 00 17.00000000",
            "utc_leap_second_not_supported_by_propagator_datetime",
        ),
        ("1979 01 01 00 00 00.00000000", "before_supported_gps_epoch"),
    ],
)
def test_time_encodings_are_explicitly_excluded_without_rounding(gps, code):
    with pytest.raises(TOOL["QualificationError"], match=code):
        TOOL["gps_to_utc"](parts(gps))


@pytest.mark.parametrize("scale", [None, "UTC", "TAI", "unknown"])
def test_missing_or_unsupported_time_scale_rejected(scale):
    with pytest.raises(TOOL["QualificationError"], match="time_scale"):
        TOOL["gps_to_utc"](parts("2014 01 01 00 02 20.00000000"), scale)


@pytest.mark.parametrize(
    "gps",
    [
        "2014 01 01",
        "2014 13 01 00 00 00.00000000",
        "2014 02 30 00 00 00.00000000",
        "2014 01 01 25 00 00.00000000",
        "2014 01 01 00 00 NaN",
        "2014 01 01 00 00 61.00000000",
        "2014 01 01 00 00 20Z",
    ],
)
def test_malformed_calendar_is_not_normalized(gps):
    with pytest.raises(TOOL["QualificationError"], match="invalid_gps_calendar"):
        TOOL["gps_to_utc"](parts(gps))


def test_missing_explicit_resources_fail_even_if_library_leaps_are_cached(monkeypatch):
    @contextmanager
    def unavailable():
        raise TransformationError("eop_unavailable", "Missing explicit leap resource")
        yield  # pragma: no cover

    monkeypatch.setitem(GLOBALS, "orientation", unavailable)
    with pytest.raises(TOOL["QualificationError"], match="resources_unavailable"):
        TOOL["gps_to_utc"](parts("2014 01 01 00 02 20.00000000"))


def test_expired_leap_resource_blocks_conversion(monkeypatch):
    original = GLOBALS["orientation"]

    @contextmanager
    def expired():
        with original() as (_, mode):
            yield (
                SimpleNamespace(leaps=SimpleNamespace(expires=Time("2010-01-01"))),
                mode,
            )

    monkeypatch.setitem(GLOBALS, "orientation", expired)
    with pytest.raises(TOOL["QualificationError"], match="leap_resource_out_of_range"):
        TOOL["gps_to_utc"](parts("2014 01 01 00 02 20.00000000"))


def test_time_audit_accounts_for_exclusions_and_retains_resource_identity():
    raw = FIXTURE["synthetic_sp3"]().replace(b"30.00000000", b"60.00000000")
    result = TOOL["time_audit"](raw, "GPS")
    assert result["converted_count"] == 1 and result["excluded_count"] == 1
    assert result["first_converted_utc"] == "2014-01-01T00:02:04.000000Z"
    assert len(result["resources"]["leap_seconds_sha256"]) == 64
    assert result["eop_checks"]["results"][0]["parameters"]["auto_download"] is False
    assert result["source_rounding_or_second_60_rollover"] is False


def test_eop_failure_is_not_replaced_with_fallback(monkeypatch):
    def fail(*args, **kwargs):
        raise TransformationError("eop_out_of_range", "Unsupported resources")

    monkeypatch.setitem(GLOBALS, "parameters", fail)
    with pytest.raises(TransformationError, match="Unsupported"):
        TOOL["time_audit"](FIXTURE["synthetic_sp3"](), "GPS")


def test_eop_endpoint_ages_share_the_recorded_audit_clock():
    result = TOOL["time_audit"](FIXTURE["synthetic_sp3"](), "GPS")
    assert result["evaluated_at_utc"].endswith("+00:00")
    ages = [
        r["parameters"]["prediction_table_age_days"]
        for r in result["eop_checks"]["results"]
    ]
    assert len(ages) == 2 and ages[0] == ages[1]


def synthetic_gp():
    record = json.loads((ROOT / "backend/tests/fixtures/vallado-leo.json").read_text())[
        0
    ]["omm"]
    record.update(
        NORAD_CAT_ID=39452,
        OBJECT_NAME="SYNTHETIC FORMAT TEST ONLY",
        OBJECT_ID="2013-067B",
        EPOCH="2014-01-01T00:00:00",
    )
    return json.dumps([record]).encode()


def test_existing_gp_parser_never_authenticates_provenance_or_invents_cutoff():
    raw = synthetic_gp()
    result = TOOL["historical_candidate"](raw, TOOL["replay"].digest(raw))
    assert result["catalog_id"] == 39452
    assert result["status"] == "PARTIAL" and result["forecast_eligible"] is False
    assert result["available_at"] is None and result["source_authenticated"] is False


def test_missing_gp_is_explicitly_blocked():
    assert TOOL["historical_candidate"]()["status"] == "BLOCKED"


@pytest.mark.parametrize(
    "kind",
    [
        "empty",
        "truncated",
        "wrong_satellite",
        "missing_epoch",
        "TLE",
        "changed_hash",
        "too_large",
    ],
)
def test_historical_input_format_identity_and_integrity_rejections(kind):
    raw = synthetic_gp()
    anchor = TOOL["replay"].digest(raw)
    if kind == "empty":
        raw = b""
    elif kind == "truncated":
        raw = raw[:20]
    elif kind == "TLE":
        raw = b"1 39452U SYNTHETIC ONLY\n2 39452 NO REAL DATA\n"
    elif kind == "too_large":
        raw = b"0" * 65537
    elif kind in {"wrong_satellite", "missing_epoch"}:
        record = json.loads(raw)[0]
        if kind == "wrong_satellite":
            record["NORAD_CAT_ID"] = 25544
        else:
            del record["EPOCH"]
        raw = json.dumps([record]).encode()
    if kind != "changed_hash":
        anchor = TOOL["replay"].digest(raw)
    else:
        anchor = "0" * 64
    with pytest.raises(TOOL["QualificationError"]):
        TOOL["historical_candidate"](raw, anchor)


@pytest.mark.parametrize(
    "declared,expected",
    [
        ("IGb08", "BLOCKED"),
        ("ITRS", "REJECTED"),
        ("TEME", "REJECTED"),
        ("unknown", "REJECTED"),
    ],
)
def test_realization_must_not_be_approved_by_changing_a_label(declared, expected):
    result = TOOL["frame_qualification"](declared)
    assert result["status"] == expected
    assert result["existing_path"] == ["TEME", "ITRS"]
    assert result["identity_transform_assumed"] is False


@pytest.mark.parametrize("supply_gp", [False, True])
def test_unqualified_pair_never_reaches_propagation_or_residuals(
    monkeypatch, supply_gp, forbid_swarm_residuals
):
    def forbidden(*args, **kwargs):
        raise AssertionError("Scientific calculation forbidden")

    monkeypatch.setattr(analysis, "position", forbidden)
    monkeypatch.setattr(analysis, "position_from_snapshot", forbidden)
    kin, val = FIXTURE["package"](), FIXTURE["package"]("VAL")
    gp = synthetic_gp() if supply_gp else None
    result = TOOL["qualify"](
        kin,
        val,
        TOOL["replay"].digest(kin),
        TOOL["replay"].digest(val),
        gp,
        TOOL["replay"].digest(gp) if gp else None,
    )
    assert (
        result["comparison_ready"] is False and result["adapter_operational"] is False
    )
    assert result["residuals"] is None and result["prediction_evaluations"] == 0
    assert result["normalized_observations"] == []
    assert (
        result["mandatory_conditions"]["historical_input_authenticated_and_paired"]
        is False
    )


def test_cli_refuses_existing_output_and_preserves_sources(tmp_path):
    kin, val = FIXTURE["package"](), FIXTURE["package"]("VAL")
    kp, vp = tmp_path / "kin.zip", tmp_path / "val.zip"
    kp.write_bytes(kin)
    vp.write_bytes(val)
    output = tmp_path / "qualification.json"
    args = [
        "--kinematic",
        str(kp),
        "--validation",
        str(vp),
        "--kinematic-sha256",
        TOOL["replay"].digest(kin),
        "--validation-sha256",
        TOOL["replay"].digest(val),
        "--output",
        str(output),
    ]
    assert TOOL["main"](args) == 0
    before = output.read_bytes()
    assert TOOL["main"](args) == 1
    assert (
        output.read_bytes() == before
        and kp.read_bytes() == kin
        and vp.read_bytes() == val
    )
    assert not output.stat().st_mode & 0o077
