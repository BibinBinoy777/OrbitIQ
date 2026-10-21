"""Synthetic source-format edge cases; none are acquired satellite observations.

The private authentic ESA product is inspected separately by the operator command.
Ordinary tests do not fetch data or require redistribution of provider products.
"""

import io
import json
import runpy
import stat
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import pytest

TOOL = runpy.run_path(
    str(Path(__file__).resolve().parents[2] / "scripts/inspect_swarm_reference.py")
)
inspect = TOOL["inspect"]
digest = TOOL["replay"].digest


def synthetic_sp3():
    lines = [
        "#dP2014  1  1  0  2 20.00000000       2 U+u   IGb08 KIN TUD",
        "## 1773 259220.00000000              0 56658 0.0016203703708",
        "+    1   L47" + "  0" * 16,
        *["+        " + "  0" * 17 for _ in range(4)],
        *["++       " + "  0" * 17 for _ in range(5)],
        "%c L  cc GPS ccc",
        "%c cc cc ccc",
        "%f  0.0000000 0.0000000",
        "%f  0.0000000 0.0000000",
        "%i 0 0 0",
        "%i 0 0 0",
        *["/* SYNTHETIC FORMAT TEST ONLY" for _ in range(4)],
    ]
    for second in ("20.00000000", "30.00000000"):
        lines += [
            "*  2014 01 01 00 02 " + second,
            f"PL47{6500:14.6f}{-1200:14.6f}{-1800:14.6f}{0.0001:14.6f}",
            "EP    20  30  40  50 0 0 0 0 0 0",
        ]
    return ("\n".join([*lines, "EOF"]) + "\n").encode()


def package(family="KIN", data=None, mutate_header=None, members=None):
    """Entirely artificial header/archive, using only the reviewed format layout."""
    suffix = ".sp3" if family == "KIN" else ".pdf"
    if data is None:
        data = synthetic_sp3() if family == "KIN" else b"%PDF-1.5\nSYNTHETIC\n%%EOF\n"
    stem = f"SW_OPER_SP3A{family}_2__20131231T235944_20140101T235944_0201"
    tree = ET.Element("Earth_Explorer_Header")
    fields = {
        "Fixed_Header/Mission": "Swarm",
        "Fixed_Header/File_Name": stem,
        "Fixed_Header/File_Type": f"SP3A{family}_2_",
        "Fixed_Header/File_Version": "0201",
        "Fixed_Header/Validity_Period/Validity_Start": "UTC=2013-12-31T23:59:44",
        "Fixed_Header/Validity_Period/Validity_Stop": "UTC=2014-01-01T23:59:44",
        "Fixed_Header/Source/Creation_Date": "UTC=2022-05-17T12:08:43",
        "Fixed_Header/Source/Creator_Version": "44.88",
        "Variable_Header/MPH/Product": stem,
        "Variable_Header/MPH/Software_Version": "L2PS-DUT/44.88",
        "Variable_Header/MPH/Proc_Time": "UTC=2022-05-17T12:08:43.000000",
        "Variable_Header/MPH/Product_Format": "ASCII" if family == "KIN" else "PDF",
        "Variable_Header/MPH/Tot_Size": str(len(data)),
        "Variable_Header/MPH/CRC": str(TOOL["posix_cksum"](data)),
        "Variable_Header/MPH/Product_Err": "0",
        "Variable_Header/SPH/SPH_Descriptor": f"SP3A{family}_2_",
        "Variable_Header/SPH/Original_Filename": stem + suffix,
        "Variable_Header/SPH/Sensing_Time_Interval/Sensing_Start": (
            "UTC=2013-12-31T23:59:44.000000"
        ),
        "Variable_Header/SPH/Sensing_Time_Interval/Sensing_Stop": (
            "UTC=2014-01-01T23:59:44.000000"
        ),
        "Variable_Header/SPH/Product_Confidence_Data/Quality_Indicator": "000",
    }
    for path, value in fields.items():
        node = tree
        for part in path.split("/"):
            existing = node.find(part)
            node = ET.SubElement(node, part) if existing is None else existing
        node.text = value
    inputs = ET.SubElement(
        tree.find("Variable_Header/SPH"), "List_of_Input_File_Names", count="4"
    )
    for prefix in ("MODA_SC_1B_", "STRAATT_1B_", "SC_ADYN_1B_", "GPSA_RO_1B_"):
        ET.SubElement(inputs, "File_Name").text = "SW_OPER_" + prefix + "SYNTHETIC"
    if mutate_header:
        mutate_header(tree)
    entries = [(stem + ".HDR", ET.tostring(tree)), (stem + suffix, data)]
    if members:
        entries = members(entries)
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in entries:
            archive.writestr(name, raw)
    return stream.getvalue()


def run(kin=None, val=None):
    kin = kin if kin is not None else package()
    val = val if val is not None else package("VAL")
    return inspect(kin, val, digest(kin), digest(val))


@pytest.mark.parametrize("raw,expected", [(b"", 4294967295), (b"123456789", 930766865)])
def test_posix_cksum_independent_literal_cases(raw, expected):
    assert TOOL["posix_cksum"](raw) == expected


def test_supported_inspection_preserves_semantics_and_never_claims_benchmark():
    result = run()
    assert result["sp3"]["epoch_count"] == 2
    assert result["sp3"]["exact_gps_calendar_interval_histogram_seconds"] == {"1E+1": 1}
    assert result["sp3"]["frame_declaration"] == "IGb08"
    assert result["sp3"]["time_system"] == "GPS"
    assert result["comparison_ready"] is False
    assert result["residuals"] is None and result["normalized_observations"] == []
    assert result["independence"] == "uncertain"
    assert result["prediction_uncertainty"] == "not_quantified"
    assert not result["kinematic"]["quality_codes_interpreted_as_acceptance"]
    assert json.loads(TOOL["replay"].encoded(result)) == result


def test_nanosecond_and_second_60_encodings_are_diagnostics_not_rounded_utc():
    raw = synthetic_sp3().replace(b"30.00000000", b"60.00000000")
    raw = raw.replace(b"20.00000000", b"20.00000001")
    result = run(package(data=raw))
    assert result["sp3"]["epoch_and_field_diagnostics"] == {
        "submicrosecond": 1,
        "seconds_field_60": 1,
    }
    assert result["sp3"]["first_epoch_raw"].endswith("20.00000001")
    assert result["sp3"]["time_diagnostic_is_utc_conversion"] is False


@pytest.mark.parametrize(
    "old,new",
    [
        (b"#dP", b"#cP"),
        (b"#dP", b"#dV"),
        (b"IGb08", b"ITRS "),
        (b"cc GPS", b"cc UTC"),
        (b"L47", b"L48"),
        (b"PL47", b"PL48"),
        (b"6500.000000", b"        NaN"),
        (b"6500.000000", b"16500000.00"),
        (b"30.00000000", b"20.00000000"),
        (b"30.00000000", b"61.00000000"),
        (b"EP    20", b"EP    -1"),
        (b"0 0 0 0 0 0", b"10000001 0 0 0 0 0"),
        (b"EOF", b""),
        (b"       2 U+u", b"       3 U+u"),
    ],
)
def test_incompatible_or_corrupt_state_record_is_rejected(old, new):
    raw = synthetic_sp3()
    assert old in raw
    with pytest.raises(ValueError):
        run(package(data=raw.replace(old, new)))


@pytest.mark.parametrize(
    "path,value",
    [
        ("Fixed_Header/Mission", "Other"),
        ("Fixed_Header/File_Type", "SP3BKIN_2_"),
        ("Fixed_Header/File_Version", "9999"),
        ("Fixed_Header/Validity_Period/Validity_Start", "2014-01-01T00:00:00"),
        ("Fixed_Header/Source/Creation_Date", "UTC=2010-01-01T00:00:00"),
        ("Variable_Header/MPH/Software_Version", "UNKNOWN"),
        ("Variable_Header/MPH/CRC", "123"),
        ("Variable_Header/MPH/Tot_Size", "1"),
        ("Variable_Header/SPH/Original_Filename", "other.sp3"),
        (
            "Variable_Header/SPH/List_of_Input_File_Names/File_Name",
            "SW_OPER_GPSB_RO_1B_OTHER",
        ),
        ("Variable_Header/SPH/Product_Confidence_Data/Quality_Indicator", ""),
    ],
)
def test_missing_or_contradictory_product_metadata_rejected(path, value):
    def change(tree):
        tree.find(path).text = value

    with pytest.raises(ValueError):
        run(package(mutate_header=change))


def test_unsupported_quality_flags_are_retained_without_automatic_acceptance():
    def flag(tree):
        tree.find("Variable_Header/MPH/Product_Err").text = "9"

    result = run(package(mutate_header=flag))
    assert result["kinematic"]["product_error_code"] == "9"
    assert result["comparison_ready"] is False


def test_matching_quality_product_and_full_input_lineage_required():
    def change(tree):
        tree.find(
            "Variable_Header/SPH/List_of_Input_File_Names/File_Name"
        ).text += "OTHER"

    with pytest.raises(ValueError, match="Unmatched quality"):
        run(val=package("VAL", mutate_header=change))


@pytest.mark.parametrize(
    "mutate",
    [
        lambda pairs: [("../" + n, b) for n, b in pairs],
        lambda pairs: [(n.replace("0201", "9999"), b) for n, b in pairs],
        lambda pairs: pairs[:1],
        lambda pairs: [pairs[0], pairs[0]],
        lambda pairs: [
            (n, b'<!DOCTYPE x [<!ENTITY a "unsafe">]>' + b)
            if n.endswith(".HDR")
            else (n, b)
            for n, b in pairs
        ],
    ],
)
def test_unsafe_or_unsupported_archive_members_rejected(mutate):
    with pytest.raises(ValueError):
        run(package(members=mutate))


def test_symlink_archive_member_rejected():
    info = zipfile.ZipInfo("source.HDR")
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as z:
        z.writestr(info, "outside")
        z.writestr("other.sp3", "not a product")
    with pytest.raises(ValueError):
        run(data.getvalue())


def test_checksum_anchor_detects_changed_or_truncated_archive():
    kin, val = package(), package("VAL")
    with pytest.raises(ValueError, match="checksum"):
        inspect(kin + b"changed", val, digest(kin), digest(val))
    with pytest.raises(zipfile.BadZipFile):
        run(kin[:20])


def test_excessive_uncompressed_data_is_refused_before_read():
    with pytest.raises(ValueError, match="Unsafe"):
        run(package(data=b"0" * (TOOL["MAX_MEMBER"] + 1)))


def test_cli_exclusive_output_input_integrity_and_deterministic_json(tmp_path, capsys):
    kin, val = package(), package("VAL")
    kp, vp = tmp_path / "kin.zip", tmp_path / "val.zip"
    kp.write_bytes(kin)
    vp.write_bytes(val)
    output = tmp_path / "inspection.json"
    args = [
        "--kinematic",
        str(kp),
        "--validation",
        str(vp),
        "--kinematic-sha256",
        digest(kin),
        "--validation-sha256",
        digest(val),
        "--output",
        str(output),
    ]
    assert TOOL["main"](args) == 0
    original = output.read_bytes()
    assert TOOL["main"](args) == 1
    assert (
        output.read_bytes() == original
        and kp.read_bytes() == kin
        and vp.read_bytes() == val
    )
    assert json.loads(original) == run(kin, val)
    assert not output.stat().st_mode & 0o077
    assert "inspection_refused" in capsys.readouterr().out


def test_cli_refuses_symlink_input_and_leaves_no_output(tmp_path):
    real = tmp_path / "real.zip"
    real.write_bytes(package())
    link = tmp_path / "link.zip"
    link.symlink_to(real)
    output = tmp_path / "result.json"
    args = [
        "--kinematic",
        str(link),
        "--validation",
        str(real),
        "--kinematic-sha256",
        digest(real.read_bytes()),
        "--validation-sha256",
        digest(real.read_bytes()),
        "--output",
        str(output),
    ]
    assert TOOL["main"](args) == 1
    assert not output.exists()
