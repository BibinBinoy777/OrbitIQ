"""Offline qualification of the demonstrated Swarm-A 0201 SP3-d/VAL ZIP pair.

This is an inspector, not an observation importer or a qualified GP benchmark
adapter. It preserves original time/frame semantics and emits no normalized
observations, predictions or residuals. Network and database access are unnecessary.
"""

import argparse
import io
import re
import stat
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from orbitiq import replay

MAX_ZIP = 4 * 1024 * 1024
MAX_MEMBER = 8 * 1024 * 1024
MAX_EPOCHS = 10000
STEM = re.compile(r"SW_OPER_SP3A(KIN|VAL)_2__\d{8}T\d{6}_\d{8}T\d{6}_0201")
HASH = re.compile(r"[a-f0-9]{64}")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def posix_cksum(raw):
    """POSIX cksum CRC including byte length, as used by the acquired headers.

    This differs from ZIP's CRC32, which ZipFile independently validates.
    """
    table = []
    for index in range(256):
        value = index << 24
        for _ in range(8):
            value = (value << 1) ^ (0x04C11DB7 if value & 0x80000000 else 0)
            value &= 0xFFFFFFFF
        table.append(value)
    crc = 0
    for byte in raw:
        crc = ((crc << 8) & 0xFFFFFFFF) ^ table[(crc >> 24) ^ byte]
    size = len(raw)
    while size:
        crc = ((crc << 8) & 0xFFFFFFFF) ^ table[(crc >> 24) ^ (size & 255)]
        size >>= 8
    return crc ^ 0xFFFFFFFF


def decimal(text):
    require(bool(re.fullmatch(r"[+-]?\d+(?:\.\d+)?", text)), "Invalid number")
    value = Decimal(text)
    require(value.is_finite(), "Nonfinite number")
    return value


def epoch(parts):
    """Exact source GPS-calendar diagnostic; never labels or converts it to UTC."""
    require(len(parts) == 6, "Incomplete epoch")
    require(all(re.fullmatch(r"\d{1,4}", p) for p in parts[:5]), "Invalid date")
    year, month, day, hour, minute = (int(p) for p in parts[:5])
    require(1957 <= year <= 2099, "Unsupported date")
    base = datetime(year, month, day, hour, minute)
    require(bool(re.fullmatch(r"\d{1,2}\.\d{8}", parts[5])), "Unsupported precision")
    second = decimal(parts[5])
    require(0 <= second <= 60, "Invalid seconds")
    elapsed = base - datetime(1980, 1, 6)
    diagnostic = Decimal(elapsed.days * 86400 + elapsed.seconds) + second
    return diagnostic, {
        "seconds_field_60": second == 60,
        "submicrosecond": second * 1000000 != (second * 1000000).to_integral_value(),
    }


def utc_header(text):
    require(
        bool(re.fullmatch(r"UTC=\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{6})?", text)),
        "Missing explicit header UTC",
    )
    return datetime.fromisoformat(text[4:])


def unpack(raw, expected_hash, family):
    require(isinstance(raw, bytes) and 0 < len(raw) <= MAX_ZIP, "ZIP exceeds bounds")
    require(bool(HASH.fullmatch(expected_hash)), "Expected SHA-256 required")
    require(replay.digest(raw) == expected_hash, "Source checksum mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        require(len(entries) == 2, "Expected header and one data member")
        names = [e.filename for e in entries]
        require(len(set(names)) == 2, "Duplicate member")
        for e in entries:
            require(
                0 < e.file_size <= MAX_MEMBER
                and e.compress_type in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
                and not e.flag_bits & 1
                and not stat.S_ISLNK(e.external_attr >> 16)
                and "/" not in e.filename
                and "\\" not in e.filename,
                "Unsafe or unsupported ZIP member",
            )
        header_name = next((n for n in names if n.endswith(".HDR")), "")
        require(bool(header_name), "Missing product header")
        stem = header_name[:-4]
        match = STEM.fullmatch(stem)
        require(
            match is not None and match[1] == family, "Unsupported product identity"
        )
        extension = ".sp3" if family == "KIN" else ".pdf"
        require(
            set(names) == {stem + ".HDR", stem + extension}, "Wrong product members"
        )
        header = archive.read(header_name)  # ZIP CRC checked; no filesystem extraction.
        require(len(header) <= 32768, "Header exceeds bounds")
        require(
            b"<!DOCTYPE" not in header.upper() and b"<!ENTITY" not in header.upper(),
            "XML declarations are unsupported",
        )
        tree = ET.fromstring(header)

        def field(path):
            value = tree.findtext(path)
            require(
                value is not None and bool(value.strip()), "Missing header metadata"
            )
            return value.strip()

        fixed, mph, sph = (
            "Fixed_Header/",
            "Variable_Header/MPH/",
            "Variable_Header/SPH/",
        )
        require(field(fixed + "Mission") == "Swarm", "Wrong mission")
        require(
            field(fixed + "File_Name") == field(mph + "Product") == stem,
            "Contradictory product identity",
        )
        require(
            field(fixed + "File_Type")
            == field(sph + "SPH_Descriptor")
            == "SP3A" + family + "_2_",
            "Wrong spacecraft or product type",
        )
        require(field(fixed + "File_Version") == "0201", "Unsupported product version")
        require(
            field(mph + "Software_Version") == "L2PS-DUT/44.88",
            "Unsupported processing baseline",
        )
        require(
            field(fixed + "Source/Creator_Version") == "44.88",
            "Contradictory processor version",
        )
        expected_format = "ASCII" if family == "KIN" else "PDF"
        require(field(mph + "Product_Format") == expected_format, "Wrong data format")
        start = field(fixed + "Validity_Period/Validity_Start")
        stop = field(fixed + "Validity_Period/Validity_Stop")
        require(utc_header(start) < utc_header(stop), "Invalid coverage")
        require(
            utc_header(start)
            == utc_header(field(sph + "Sensing_Time_Interval/Sensing_Start"))
            and utc_header(stop)
            == utc_header(field(sph + "Sensing_Time_Interval/Sensing_Stop")),
            "Contradictory coverage",
        )
        created = field(fixed + "Source/Creation_Date")
        require(
            utc_header(created) == utc_header(field(mph + "Proc_Time")),
            "Contradictory processing time",
        )
        require(
            utc_header(created) >= utc_header(stop), "Invalid processing chronology"
        )
        period = "_".join(
            utc_header(t).strftime("%Y%m%dT%H%M%S") for t in (start, stop)
        )
        require(
            stem == f"SW_OPER_SP3A{family}_2__{period}_0201",
            "File identity and coverage disagree",
        )
        data = archive.read(stem + extension)
        require(int(field(mph + "Tot_Size")) == len(data), "Header size mismatch")
        require(int(field(mph + "CRC")) == posix_cksum(data), "Header CRC mismatch")
        require(
            field(sph + "Original_Filename") == stem + extension, "Wrong source file"
        )
        inputs = tree.find(sph + "List_of_Input_File_Names")
        require(inputs is not None, "Missing input lineage")
        input_names = [e.text for e in inputs.findall("File_Name")]
        require(
            len(input_names) == 4
            and int(inputs.attrib["count"]) == 4
            and all(
                isinstance(n, str) and n.startswith("SW_OPER_") for n in input_names
            ),
            "Incomplete input lineage",
        )
        require(
            len(set(input_names)) == 4
            and all(
                sum(n.startswith("SW_OPER_" + prefix) for n in input_names) == 1
                for prefix in (
                    "MODA_SC_1B_",
                    "STRAATT_1B_",
                    "SC_ADYN_1B_",
                    "GPSA_RO_1B_",
                )
            ),
            "Wrong spacecraft input lineage",
        )
        metadata = {
            "product": stem,
            "product_family": "SP3A" + family + "_2_",
            "version": "0201",
            "mission": "Swarm",
            "spacecraft": "Swarm-A",
            "header_validity_start": start,
            "header_validity_stop": stop,
            "created_at": created,
            "software": field(mph + "Software_Version"),
            "input_files": input_names,
            "product_error_code": field(mph + "Product_Err"),
            "quality_indicator": field(
                sph + "Product_Confidence_Data/Quality_Indicator"
            ),
            "quality_codes_interpreted_as_acceptance": False,
            "zip_sha256": expected_hash,
            "zip_crc_checked": True,
            "header_checksum_method": "POSIX cksum",
            "header_checksum": int(field(mph + "CRC")),
            "members": {
                n: {"bytes": len(b), "sha256": replay.digest(b)}
                for n, b in [(header_name, header), (stem + extension, data)]
            },
        }
        return metadata, data


def inspect_sp3(raw):
    lines = raw.decode("ascii").splitlines()
    require(
        len(lines) <= 22 + MAX_EPOCHS * 3 + 1
        and all(len(line) <= 128 for line in lines),
        "SP3 exceeds record bounds",
    )
    require(len(lines) >= 26 and lines[-1].strip() == "EOF", "Truncated SP3")
    head = lines[0].split()
    require(
        len(head) == 11 and head[0].startswith("#dP"),
        "Only SP3-d position files supported",
    )
    require(head[8:] == ["IGb08", "KIN", "TUD"], "Unsupported frame or processing kind")
    declared = int(head[6])
    require(1 <= declared <= MAX_EPOCHS, "Invalid epoch count")
    header_epoch = epoch([head[0][3:], *head[1:6]])[0]
    require(lines[1].startswith("## "), "Missing interval header")
    interval = decimal(lines[1].split()[3])
    require(interval == 0, "Only demonstrated irregular-epoch product supported")
    require(lines[2].split()[:3] == ["+", "1", "L47"], "Wrong SP3 spacecraft")
    require(
        all(s.startswith("+ ") for s in lines[2:7])
        and all(s.startswith("++") for s in lines[7:12]),
        "Invalid satellite headers",
    )
    satellites = " ".join(s[9:] for s in lines[2:7]).split()
    require(satellites == ["L47"] + ["0"] * 84, "Multiple or unknown satellites")
    require(
        lines[12].split()[:4] == ["%c", "L", "cc", "GPS"], "Explicit GPS time required"
    )
    require(
        lines[13].startswith("%c")
        and all(s.startswith("%f") for s in lines[14:16])
        and all(s.startswith("%i") for s in lines[16:18])
        and all(s.startswith("/*") for s in lines[18:22]),
        "Unsupported header structure",
    )
    records = lines[22:-1]
    require(len(records) == declared * 3, "Missing or extra state records")
    issues, intervals = Counter(), Counter()
    previous, first, last = None, None, None
    for offset in range(0, len(records), 3):
        stamp, position, ep = records[offset : offset + 3]
        require(stamp.startswith("*  "), "Missing epoch")
        current, flags = epoch(stamp.split()[1:])
        if previous is not None:
            require(current > previous, "Duplicate or reversed epochs")
            intervals[str((current - previous).normalize())] += 1
        else:
            require(current == header_epoch, "Header epoch differs from first sample")
            first = stamp.strip()
        previous, last = current, stamp.strip()
        issues.update(k for k, present in flags.items() if present)
        require(
            position.startswith("PL47") and len(position.rstrip()) == 60,
            "Unsupported position fields or prediction flags",
        )
        values = [
            decimal(position[a:b].strip())
            for a, b in [(4, 18), (18, 32), (32, 46), (46, 60)]
        ]
        require(all(abs(v) <= 1000000 for v in values), "Out-of-range values")
        if all(v == 0 for v in values[:3]):
            issues["missing_position_sentinel"] += 1
        tokens = ep.split()
        require(
            len(tokens) == 11
            and tokens[0] == "EP"
            and all(re.fullmatch(r"-?\d+", t) for t in tokens[1:]),
            "Invalid EP record",
        )
        sigma = [int(t) for t in tokens[1:5]]
        correlations = [int(t) for t in tokens[5:]]
        require(
            all(0 <= v <= 9999 for v in sigma)
            and all(abs(v) <= 10000000 for v in correlations),
            "Invalid EP uncertainties",
        )
        if any(v == 0 for v in sigma[:3]):
            issues["unknown_reference_axis_sigma"] += 1
    return {
        "format": "SP3-d",
        "sp3_id": "L47",
        "frame_declaration": "IGb08",
        "time_system": "GPS",
        "position_unit": "km",
        "velocity_records": 0,
        "epoch_count": declared,
        "position_count": declared,
        "ep_record_count": declared,
        "first_epoch_raw": first,
        "last_epoch_raw": last,
        "nominal_interval_seconds": "0",
        "interval_interpretation": "irregular epochs",
        "format_conformance": (
            "Specimen layout inspected; zero nominal interval and time encodings "
            "do not certify general SP3 conformance or temporal alignment."
        ),
        "exact_gps_calendar_interval_histogram_seconds": dict(
            sorted(intervals.items())
        ),
        "epoch_and_field_diagnostics": dict(issues),
        "time_diagnostic_is_utc_conversion": False,
        "reference_uncertainty": (
            "EP fields retained in source; no joint covariance inferred"
        ),
    }


def inspect(kinematic, validation, kinematic_sha256, validation_sha256):
    kin, states = unpack(kinematic, kinematic_sha256, "KIN")
    val, pdf = unpack(validation, validation_sha256, "VAL")
    require(
        pdf.startswith(b"%PDF-") and b"%%EOF" in pdf[-32:], "Invalid validation PDF"
    )
    require(
        kin["header_validity_start"] == val["header_validity_start"]
        and kin["header_validity_stop"] == val["header_validity_stop"]
        and kin["input_files"] == val["input_files"],
        "Unmatched quality product",
    )
    return {
        "kind": "orbitiq_swarm_source_inspection",
        "schema_version": 1,
        "status": "inspected_benchmark_blocked",
        "tool_sha256": replay.digest(Path(__file__).read_bytes()),
        "kinematic": kin,
        "validation": val,
        "sp3": inspect_sp3(states),
        "catalog_mapping": {
            "spacecraft": "Swarm-A",
            "sp3_id": "L47",
            "norad_id": 39452,
            "source": "https://ilrs.gsfc.nasa.gov/missions/correspondence_table.html",
        },
        "quality_review": (
            "PDF acquired and linked; plots require operator scientific interpretation"
        ),
        "comparison_ready": False,
        "normalized_observations": [],
        "residuals": None,
        "independence": "uncertain",
        "prediction_uncertainty": "not_quantified",
        "blockers": [
            "No verified historical GP/TLE and availability cutoff supplied.",
            "IGb08 realization has no approved mapping to the current ITRS comparison.",
            "GPS precision and second-60 encodings need a reviewed alignment policy.",
            "Reference quality and shared processing lineage require assessment.",
        ],
        "scope": (
            "Source qualification only; no propagation, UTC rounding, import "
            "or scientific accuracy claim."
        ),
    }


def read(path):
    require(path.is_absolute(), "Use explicit absolute input paths")
    with replay.directory(path.parent) as fd:
        return replay.read_file(fd, path.name, MAX_ZIP)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kinematic", required=True, type=Path)
    parser.add_argument("--validation", required=True, type=Path)
    parser.add_argument("--kinematic-sha256", required=True)
    parser.add_argument("--validation-sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        require(args.output.is_absolute(), "Use explicit output path")
        result = inspect(
            read(args.kinematic),
            read(args.validation),
            args.kinematic_sha256,
            args.validation_sha256,
        )
        with args.output.open("x", encoding="utf-8") as file:
            file.write(replay.encoded(result).decode())
        args.output.chmod(0o600)
        print('{"status":"inspected_benchmark_blocked","comparison_ready":false}')
        return 0  # Successful inspection is explicitly not a successful benchmark.
    except (
        OSError,
        ValueError,
        KeyError,
        IndexError,
        ET.ParseError,
        zipfile.BadZipFile,
        RuntimeError,
        replay.BundleError,
    ):
        print('{"status":"inspection_refused","comparison_ready":false}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
