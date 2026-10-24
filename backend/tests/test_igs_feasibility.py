"""E8 offline controls; invented coordinates, no real IGS/GP files or network."""

import gzip
import hashlib
import json
import runpy
import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from orbitiq.orbits import engine

ROOT = Path(__file__).parents[2]
PATH = ROOT / "scripts/inspect_igs_reference.py"
M = runpy.run_path(str(PATH))
# Functions share the runpy globals; monkeypatch that actual module namespace.
GLOBALS = M["qualify"].__globals__
FIXTURES = Path(__file__).parent / "fixtures/igs"
NAME = "IGS0OPSFIN_20240010000_01D_15M_ORB.SP3.gz"
STAMP = "2023-12-31T23:59:42.000000+00:00"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def source(mutate=None):
    lines = (FIXTURES / "synthetic-final.sp3").read_text().splitlines()
    if mutate:
        mutate(lines)
    text = ("\n".join(lines) + "\n").encode()
    return gzip.compress(text, mtime=0)


def inspect(raw=None):
    raw = source() if raw is None else raw
    return M["inspect_sp3"](raw, sha(raw), NAME)


def gp(at=STAMP):
    record = json.loads(
        (Path(__file__).parent / "fixtures/vallado-leo.json").read_text()
    )[0]["omm"]
    record.update(
        OBJECT_NAME="E8 SYNTHETIC GP ONLY",
        OBJECT_ID="2014-008A",
        NORAD_CAT_ID=39533,
        EPOCH=at,
        MEAN_MOTION=2.005,
    )
    return [record]


def selected(records=None):
    raw = json.dumps(gp() if records is None else records).encode()
    return M["gp_record"](raw, sha(raw), 39533)


def mapping(raw=None, prn="G30", at=datetime(2024, 1, 1)):
    raw = (FIXTURES / "synthetic-metadata.snx").read_bytes() if raw is None else raw
    return M["nominal_identity"](raw, sha(raw), prn, at)


def test_realistic_layout_is_explicitly_synthetic_and_never_exports_coordinates():
    raw = source()
    before = bytes(raw)
    p = inspect(raw)
    assert raw == before and p["source_sha256"] == sha(raw)
    assert p["expanded_sha256"] == sha(gzip.decompress(raw))
    assert p["epoch_count"] == 2 and p["satellite_ids"] == ["G10", "G30"]
    assert p["position_counts"] == {"G10": 2, "G30": 2}
    assert p["frame_declaration"] == "IGS20" and p["position_unit"] == "km"
    assert p["time_system"] == "GPS" and p["velocity_records"] == 0
    assert p["complete_15_minute_daily_grid"] is False
    assert p["quality_counts"]["G30"]["x_sigma_exponent_0"] == 2
    assert "zero is 1 mm" in p["axis_sigma_rule"]
    assert p["scientifically_accepted_count"] == 0
    assert not any(
        k in json.dumps(p) for k in ("position_km", "residual_km", "velocity_km_s")
    )
    assert b"SYNTHETIC" in gzip.decompress(raw)


def replace(lines, index, start, stop, text):
    lines[index] = lines[index][:start] + text + lines[index][stop:]


@pytest.mark.parametrize(
    "mutation,code",
    [
        (lambda lines: replace(lines, 12, 9, 12, "UTC"), "unsupported_time_system"),
        (lambda lines: replace(lines, 12, 9, 12, "   "), "unsupported_time_system"),
        (
            lambda lines: replace(lines, 0, 46, 51, "IGb20"),
            "unsupported_frame_declaration",
        ),
        (
            lambda lines: replace(lines, 0, 46, 51, "ITRS "),
            "unsupported_frame_declaration",
        ),
        (
            lambda lines: replace(lines, 0, 46, 51, "     "),
            "unsupported_frame_declaration",
        ),
        (
            lambda lines: replace(lines, 0, 40, 45, "METRE"),
            "unsupported_data_units_profile",
        ),
        (lambda lines: replace(lines, 0, 1, 3, "cV"), "unsupported_sp3_profile"),
        (lambda lines: replace(lines, 0, 1, 3, "dP"), "unsupported_sp3_profile"),
        (
            lambda lines: replace(lines, 1, 8, 23, " 86401.00000000"),
            "gps_week_conflict",
        ),
        (lambda lines: replace(lines, 1, 39, 44, "60311"), "mjd_conflict"),
        (
            lambda lines: replace(lines, 1, 24, 38, "    60.0000000"),
            "unsupported_sampling_interval",
        ),
        (
            lambda lines: lines.__setitem__(25, lines[22]),
            "duplicate_ambiguous_or_irregular_epoch",
        ),
        (lambda lines: lines.pop(23), "unsupported_state_record"),
        (
            lambda lines: replace(lines, 23, 1, 4, "G30"),
            "duplicate_or_unknown_state_identity",
        ),
        (lambda lines: replace(lines, 23, 4, 18, "           NaN"), "invalid_number"),
        (lambda lines: replace(lines, 23, 79, 80, "X"), "unknown_quality_flag"),
        (lambda lines: lines.pop(), "missing_eof"),
        (
            lambda lines: replace(lines, 0, 32, 39, "      3"),
            "declared_epoch_count_mismatch",
        ),
        (
            lambda lines: lines.__setitem__(
                18, "/* SYNTHETIC WITHOUT FINAL DECLARATION"
            ),
            "missing_final_combination_declaration",
        ),
    ],
)
def test_malformed_ambiguous_or_unsupported_product_is_refused(mutation, code):
    with pytest.raises((M["Refusal"], ValueError), match=code):
        inspect(source(mutation))


@pytest.mark.parametrize(
    "name",
    [
        "IGS0OPSULT_20240010000_02D_15M_ORB.SP3.gz",
        "IGS0OPSRAP_20240010000_01D_15M_ORB.SP3.gz",
        "unknown.sp3.gz",
    ],
)
def test_no_rapid_or_predicted_product_substitution(name):
    raw = source()
    with pytest.raises(M["Refusal"], match="not_supported_combined_final_product"):
        M["inspect_sp3"](raw, sha(raw), name)


def test_hash_compression_and_size_integrity(monkeypatch):
    raw = source()
    with pytest.raises(M["Refusal"], match="source_hash_mismatch"):
        M["inspect_sp3"](raw, "0" * 64, NAME)
    for invalid in (b"<html>login</html>", raw[:-8]):
        with pytest.raises(M["Refusal"], match="not_gzip_ascii_sp3"):
            inspect(invalid)
    monkeypatch.setitem(M["inspect_sp3"].__globals__, "MAX_TEXT", 64)
    with pytest.raises(M["Refusal"], match="expanded_source_size"):
        inspect(raw)


def test_predicted_maneuver_missing_position_and_unknown_sigma_are_explicit():
    def damage(lines):
        replace(lines, 24, 4, 46, "      0.000000" * 3)
        replace(lines, 24, 61, 63, "  ")
        replace(lines, 24, 78, 80, "MP")

    p = inspect(source(damage))
    assert p["epochs"][0]["exclusions"]["G30"] == [
        "missing_position",
        "maneuver_flag",
        "predicted_position",
        "unknown_x_sigma",
    ]
    assert p["position_counts"]["G30"] == 2  # Retain the record; no hidden deletion.
    assert p["scientifically_accepted_count"] == 0


def test_static_gp_validation_and_existing_deep_space_initialization_only(monkeypatch):
    monkeypatch.setattr(
        engine, "propagate", lambda *a: pytest.fail("Propagation prohibited")
    )
    monkeypatch.setattr(
        engine, "propagate_satellite", lambda *a: pytest.fail("Propagation prohibited")
    )
    elements, info = selected()
    assert elements.epoch.isoformat(timespec="microseconds") == STAMP
    assert (
        info["initialization_method"] == "d" and info["propagation_executed"] is False
    )
    assert info["canonical_record_sha256"] == sha(
        json.dumps(
            gp()[0], sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r[0].update(EPHEMERIS_TYPE=2),
        lambda r: r[0].update(REF_FRAME="ITRS"),
        lambda r: r[0].update(TIME_SYSTEM="GPS"),
        lambda r: r[0].update(EPOCH="2024-01-01T00:00:00.00000001"),
        lambda r: r[0].pop("EPOCH"),
        lambda r: r[0].update(MEAN_MOTION=True),
    ],
)
def test_incompatible_gp_record_is_never_repaired(mutation):
    r = gp()
    mutation(r)
    with pytest.raises(M["Refusal"], match="unsupported_gp_record"):
        selected(r)


@pytest.mark.parametrize(
    "records", [[], gp() + gp(), [{"NORAD_CAT_ID": 99999}], {"error": "missing data"}]
)
def test_missing_or_competing_gp_never_falls_back(records):
    with pytest.raises(M["Refusal"]):
        selected(records)


def test_duplicate_gp_json_field_is_refused():
    raw = b'[{"NORAD_CAT_ID":39533,"NORAD_CAT_ID":39533}]'
    with pytest.raises(M["Refusal"], match="invalid_gp_json"):
        M["gp_record"](raw, sha(raw), 39533)


def test_time_dependent_prn_mapping_and_no_alias_guessing():
    m = mapping()
    assert (m["svn"], m["catalog_id"], m["cospar_id"]) == ("G064", 39533, "2014-008A")
    assert "nominal civil-calendar" in m["scope"]
    raw = (FIXTURES / "synthetic-metadata.snx").read_bytes()
    duplicate = raw.replace(
        b"-SATELLITE/PRN", b" G073 2015:304:00000 0000:000:00000 G30\n-SATELLITE/PRN"
    )
    for value in (duplicate, raw.replace(b"+SATELLITE/PRN", b"+SATELLITE/OTHER")):
        with pytest.raises(M["Refusal"]):
            mapping(value)
    with pytest.raises(M["Refusal"], match="missing_or_ambiguous_prn_mapping"):
        mapping(at=datetime(2010, 1, 1))


def test_half_open_mapping_interval_does_not_select_both_assignments():
    raw = (
        (FIXTURES / "synthetic-metadata.snx")
        .read_bytes()
        .replace(
            b"G064 2014:052:00000 0000:000:00000 G30",
            b"G064 2014:052:00000 2024:001:00000 G30\n"
            b" G073 2024:001:00000 0000:000:00000 G30",
        )
    )
    assert mapping(raw)["svn"] == "G073"


def test_common_times_are_deterministic_exact_and_never_enable_science():
    e, g = selected()
    p = inspect()
    first = M["qualify"](p, e, g, mapping())
    second = M["qualify"](p, e, g, mapping())
    assert first == second
    assert first["frozen_anchor_utc"] == "2023-12-31T23:59:42.000000Z"
    assert [r["utc_diagnostic"] for r in first["utc_diagnostics"]] == [
        "2023-12-31T23:59:42.000000Z",
        "2024-01-01T00:14:42.000000Z",
    ]
    assert first["time_and_source_eligible_indices"] == [1, 2]
    assert first["decision"] == "BLOCKED — ADDITIONAL EVIDENCE REQUIRED"
    assert (
        first["scientifically_accepted_count"] == 0
        and not first["residuals_calculated"]
    )
    assert "reviewed_frame_alignment" in first["blocking_requirements"]
    assert "complete_daily_coverage" in first["blocking_requirements"]


def test_existing_inclusive_seven_day_guard_and_fixed_first_epoch_anchor():
    p = inspect()
    e, g = selected(
        (
            lambda r: (
                r[0].update(
                    EPOCH=(
                        datetime.fromisoformat(STAMP) - timedelta(days=7)
                    ).isoformat()
                ),
                r,
            )[1]
        )(gp())
    )
    q = M["qualify"](p, e, g, mapping())
    assert q["time_and_source_eligible_indices"] == [1]
    assert q["utc_diagnostics"][1]["exclusions"] == ["outside_existing_7_day_guard"]
    p["epochs"][0]["exclusions"]["G30"] = ["predicted_position"]
    later = gp((datetime.fromisoformat(STAMP) + timedelta(minutes=5)).isoformat())
    e, g = selected(later)
    q = M["qualify"](p, e, g, mapping())
    assert q["time_and_source_eligible_indices"] == []
    assert q["frozen_anchor_utc"] == "2023-12-31T23:59:42.000000Z"
    assert all(
        "gp_after_reference_anchor" in r["exclusions"] for r in q["utc_diagnostics"]
    )


def test_wrong_identity_and_missing_resources_never_fall_back(monkeypatch):
    e, g = selected()
    p = inspect()
    m = mapping()
    m["catalog_id"] = 41019
    with pytest.raises(M["Refusal"], match="gp_reference_identity_mismatch"):
        M["qualify"](p, e, g, m)

    @contextmanager
    def missing():
        raise ValueError("PRIVATE RESOURCE CONTENT MUST NOT LEAK")
        yield

    monkeypatch.setitem(GLOBALS, "orientation", missing)
    with pytest.raises(M["Refusal"], match="time_or_eop_resources_unavailable"):
        M["qualify"](p, e, g, mapping())


@pytest.mark.parametrize(
    "parts",
    [
        ["2024", "1", "1", "0", "0", "60.00000000"],
        ["2024", "1", "1", "0", "0", "0.00000001"],
    ],
)
def test_unrepresentable_or_invalid_gps_epochs_are_not_rounded(parts):
    with pytest.raises(M["TIME"]["QualificationError"]):
        M["TIME"]["gps_value"](parts, "GPS")


def test_bounded_files_symlinks_and_no_overwrite_cli(tmp_path):
    product = tmp_path / "synthetic.gz"
    product.write_bytes(source())
    rawgp = tmp_path / "synthetic.json"
    rawgp.write_text(json.dumps(gp()))
    metadata = tmp_path / "synthetic.snx"
    metadata.write_bytes((FIXTURES / "synthetic-metadata.snx").read_bytes())
    link = tmp_path / "link"
    link.symlink_to(product)
    with pytest.raises(M["Refusal"], match="regular_input_file_required"):
        M["bounded_file"](link, 4096)
    output = tmp_path / "out.json"
    cmd = [
        sys.executable,
        str(PATH),
        "--product",
        str(product),
        "--product-name",
        NAME,
        "--gp",
        str(rawgp),
        "--metadata",
        str(metadata),
        "--prn",
        "G30",
        "--catalog-id",
        "39533",
        "--output",
        str(output),
    ]
    for label, path in (("product", product), ("gp", rawgp), ("metadata", metadata)):
        cmd += ["--" + label + "-sha256", sha(path.read_bytes())]
    run = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert run.returncode == 0, run.stderr
    before = output.read_bytes()
    assert json.loads(before)["scientifically_accepted_count"] == 0
    again = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert again.returncode == 1 and output.read_bytes() == before
    assert "No fallback or comparison" in again.stderr
    assert str(tmp_path) not in again.stderr


def test_mapping_metadata_requires_valid_header_identifiers_and_nominal_calendar():
    raw = (FIXTURES / "synthetic-metadata.snx").read_bytes()
    invalid = [
        raw.replace(b"%=SNX", b"OTHER"),
        raw.replace(b"G064", b"X064"),
        raw.replace(b"39533", b"false"),
        raw.replace(b"2014-008A", b"2014-?08A"),
    ]
    for damaged in invalid:
        with pytest.raises(M["Refusal"]):
            mapping(damaged)
    with pytest.raises(M["Refusal"], match="nominal_mapping_calendar_required"):
        mapping(at=datetime.fromisoformat(STAMP))
