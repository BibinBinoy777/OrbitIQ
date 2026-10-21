"""Synthetic metadata/timing cases; no actual Swarm coordinates or GP fixtures."""

import json
import runpy
import stat
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from orbitiq import replay
from orbitiq.orbits import coordinates, engine
from orbitiq.orbits.earth_orientation import TransformationError
from orbitiq.orbits.elements import Elements
from orbitiq.services import analysis
from sgp4 import omm

ROOT = Path(__file__).resolve().parents[2]
TOOL = runpy.run_path(str(ROOT / "scripts/assess_swarm_pairing.py"))
SOURCE = runpy.run_path(
    str(Path(__file__).with_name("test_phase113_swarm_inspection.py"))
)
CSV = runpy.run_path(str(Path(__file__).with_name("test_historical_csv_intake.py")))


def sp3(*, sigma=(20, 30, 40, 50), correlation=(0, 0, 0, 0, 0, 0)):
    # SP3-d fixed column layout, deliberately artificial values.
    ep = "EP  " + " ".join(f"{value:4d}" for value in sigma[:3])
    ep += f" {sigma[3]:7d} " + " ".join(f"{value:8d}" for value in correlation)
    assert len(ep) == 80
    return b"\n".join(
        ep.encode() if line.startswith(b"EP") else line
        for line in SOURCE["synthetic_sp3"]().split(b"\n")
    )


def candidates():
    return TOOL["CSV"]["inspect_attachment"](CSV["encoded"]())["records"]


@pytest.mark.parametrize(
    "microseconds", [0, 1, -1, 604800000000, -604800000000, 604800000001, -604800000001]
)
def test_offsets_are_exact_signed_integer_microseconds(microseconds):
    epoch = datetime(2014, 1, 1, 5, 30, 45, 123456, tzinfo=UTC)
    assert (
        TOOL["offset_us"](epoch + timedelta(microseconds=microseconds), epoch)
        == microseconds
    )


def test_all_candidates_audited_without_nearest_selection_or_availability_inference():
    result = TOOL["timing_audit"](sp3(), candidates())
    assert result["source_epoch_count"] == result["converted_count"] == 2
    assert result["eop_passed"] == 2 and result["eop_blocked"] == 0
    assert result["first_converted_utc"] == "2014-01-01T00:02:04.000000Z"
    entries = result["candidate_offsets"]
    # Synthetic GP epochs are Dec31, Jan1 and Jan2 UTC midnight. Independent
    # literal arithmetic expectations use the documented Jan2014 GPS-UTC=16 s.
    assert [entry["first_reference_offset_microseconds"] for entry in entries] == [
        86524000000,
        124000000,
        -86276000000,
    ]
    assert [entry["reference_before_element_epoch"] for entry in entries] == [0, 0, 2]
    assert all(entry["within_inclusive_seven_day_bound"] == 2 for entry in entries)
    assert all(
        entry["available_at"] is None
        and not entry["selected"]
        and not entry["temporal_pair_approved"]
        for entry in entries
    )


def test_redundant_header_discrepancy_retained_without_using_mjd_to_adjust_epochs():
    result = TOOL["redundant_header_time"](sp3())
    # Independent decimal arithmetic: 0.0016203703708 * 86400 =
    # 140.00000003712, while the calendar tag is exactly 140 s into its day.
    from decimal import Decimal

    # Week 1773, second 259220 is Wednesday 00:00:20; the first calendar
    # record is Wednesday 00:02:20. Preserve the 120-second contradiction.
    assert not result["gps_week_and_seconds_match_first_epoch"]
    assert Decimal(result["week_seconds_minus_first_epoch_seconds"]) == -120
    assert Decimal(result["mjd_minus_first_epoch_seconds"]) == Decimal("0.00000003712")
    assert result["status"] == "PARTIAL"
    assert not result["mjd_fraction_used_for_conversion"]


def test_consistent_week_header_is_distinguished_from_fraction_discrepancy():
    synthetic = sp3().replace(b"259220.00000000", b"259340.00000000")
    result = TOOL["redundant_header_time"](synthetic)
    assert result["gps_week_and_seconds_match_first_epoch"]
    assert result["status"] == "PARTIAL"  # MJD fraction remains discrepant.


def test_wrong_gps_week_is_detected_as_a_header_discrepancy():
    result = TOOL["redundant_header_time"](sp3().replace(b"## 1773", b"## 1774"))
    assert not result["gps_week_and_seconds_match_first_epoch"]
    assert result["status"] == "PARTIAL"


def test_every_supported_epoch_gets_eop_preflight_and_failure_is_retained(monkeypatch):
    calls, original = [], TOOL["QUALIFY"]["parameters"]

    def check(data, at, mode, **kwargs):
        calls.append(at.isot)
        if len(calls) == 2:
            raise TransformationError("eop_unavailable", "Synthetic failure")
        return original(data, at, mode, **kwargs)

    monkeypatch.setitem(TOOL["QUALIFY"], "parameters", check)
    result = TOOL["timing_audit"](sp3(), candidates())
    assert len(calls) == 2
    assert result["eop_passed"] == result["eop_blocked"] == 1
    assert result["rows"][1]["eop_coverage"] == {
        "status": "BLOCKED",
        "reason": "eop_unavailable",
    }
    assert result["reference_epoch_quality_approved"] is False


@pytest.mark.parametrize(
    "replacement,reason",
    [
        (b"20.00000001", "source_precision_exceeds_microsecond_contract"),
        (b"60.00000000", "source_second_60_requires_provider_clarification"),
    ],
)
def test_excluded_source_epochs_keep_indices_without_rounding(replacement, reason):
    result = TOOL["timing_audit"](
        sp3().replace(b"30.00000000", replacement), candidates()
    )
    assert result["converted_count"] == result["excluded_count"] == 1
    assert result["rows"][1]["source_index"] == 1
    assert result["rows"][1]["exclusion"] == reason
    assert result["rows"][1]["utc"] is None
    assert result["source_rounding_or_second_60_rollover"] is False


def test_quality_fields_units_and_header_accuracy_are_separate_from_acceptance():
    result = TOOL["quality_audit"](sp3())
    assert result["header_accuracy_exponent"] == 0
    assert result["header_zero_accuracy_means_unknown"]
    assert result["axis_sigma_ranges_mm"] == [
        {"minimum": n, "maximum": n} for n in (20, 30, 40)
    ]
    assert result["clock_sigma_range_ps"] == {"minimum": 50, "maximum": 50}
    assert result["rows_with_extended_p_quality_fields"] == 0
    assert result["rows_with_format_review_reasons"] == 0
    assert result["accepted_quality_indices"] == []
    assert result["covariance_or_physical_accuracy_inferred"] is False
    assert all(not row["quality_accepted"] for row in result["rows"])


@pytest.mark.parametrize(
    "sigma,correlation,reason",
    [
        (
            (0, 30, 40, 50),
            (0, 0, 0, 0, 0, 0),
            "axis_sigma_zero_or_overflow_requires_review",
        ),
        (
            (9999, 30, 40, 50),
            (0, 0, 0, 0, 0, 0),
            "axis_sigma_zero_or_overflow_requires_review",
        ),
        (
            (20, 30, 40, 50),
            (10000000, 0, 0, 0, 0, 0),
            "correlation_outside_sp3_d_range",
        ),
    ],
)
def test_uncertainty_sentinels_and_correlation_boundaries_are_not_accepted(
    sigma, correlation, reason
):
    result = TOOL["quality_audit"](sp3(sigma=sigma, correlation=correlation))
    assert result["rows_with_format_review_reasons"] == 2
    assert all(reason in row["format_review_reasons"] for row in result["rows"])


def test_single_zero_position_component_is_flagged_without_changing_source():
    original = sp3()
    changed = original.replace(f"{6500:14.6f}".encode(), f"{0:14.6f}".encode())
    result = TOOL["quality_audit"](changed)
    assert result["rows_with_zero_position_component"] == 2
    assert result["rows"][0]["zero_position_components"] == ["x"]
    assert original == sp3() and not result["accepted_quality_indices"]


def test_unsupported_ep_layout_is_refused():
    with pytest.raises(ValueError, match="fixed-width"):
        TOOL["quality_audit"](SOURCE["synthetic_sp3"]())


def test_whole_assessment_cannot_evaluate_or_promote_source(
    monkeypatch, forbid_swarm_residuals
):
    def forbidden(*args, **kwargs):
        raise AssertionError("No orbital scientific evaluation during qualification")

    for obj, name in (
        (Elements, "satellite"),
        (omm, "initialize"),
        (engine, "propagate"),
        (engine, "propagate_satellite"),
        (coordinates, "earth_fixed"),
        (analysis, "position"),
        (replay, "write_file"),
    ):
        monkeypatch.setattr(obj, name, forbidden)
    kin, val, csv = (
        SOURCE["package"](data=sp3()),
        SOURCE["package"]("VAL"),
        CSV["encoded"](),
    )
    result = TOOL["assess"](
        kin, val, csv, replay.digest(kin), replay.digest(val), replay.digest(csv)
    )
    assert result["status"] == "BLOCKED" and result["phase_status"] == "PARTIAL"
    assert result["pairing_decision"]["selected_source_index"] is None
    assert not result["pairing_decision"]["accepted_reference_indices"]
    assert result["prediction_evaluations"] == result["coordinate_transformations"] == 0
    assert result["residuals"] is None and not result["comparison_ready"]
    assert result["frame"]["status"] == "BLOCKED"
    assert len(result["qualification_gates"]) == 10
    assert result["independence"] == "NOT_ESTABLISHED"


def test_cli_hashes_and_private_exclusive_output(tmp_path):
    tmp_path.chmod(0o700)
    kin, val, csv = (
        SOURCE["package"](data=sp3()),
        SOURCE["package"]("VAL"),
        CSV["encoded"](),
    )
    args = []
    for name, body in (("kinematic", kin), ("validation", val), ("gp-csv", csv)):
        path = tmp_path / name
        path.write_bytes(body)
        args += ["--" + name, str(path), "--" + name + "-sha256", replay.digest(body)]
    output = tmp_path / "report.json"
    args += ["--output", str(output)]
    assert TOOL["main"](args) == 0
    before = output.read_bytes()
    assert stat.S_IMODE(output.stat().st_mode) == 0o600
    assert json.loads(before)["status"] == "BLOCKED"
    assert TOOL["main"](args) == 1 and output.read_bytes() == before
    args[3] = "0" * 64
    assert TOOL["main"](args) == 1


def test_residual_guard_remains_active_without_optional_application_feature(
    forbid_swarm_residuals,
):
    from orbitiq import observation_validation

    with pytest.raises(AssertionError, match="residual evaluation forbidden"):
        observation_validation.residual(None, None)
