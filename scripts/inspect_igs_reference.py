"""Offline, bounded E8 feasibility inspector, NOT a comparison or observation adapter.

Profile: IGS combined FIN, GPS-only SP3-c position product, 15-minute epochs.
Original bytes/hashes and nullable quality are retained; no coordinates are
exported, propagated, transformed or subtracted. No approval flag enables science.
"""

import argparse
import gzip
import hashlib
import io
import json
import re
import runpy
import zlib
from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from orbitiq.orbits.earth_orientation import orientation, parameters
from orbitiq.orbits.elements import Elements
from orbitiq.reporting import report_time

# Reuse the existing checked TimeGPS conversion, without any ESA input or access.
TIME = runpy.run_path(str(Path(__file__).with_name("qualify_swarm_inputs.py")))
MAX_SOURCE = 4 * 1024 * 1024
MAX_TEXT = 16 * 1024 * 1024
NAME = re.compile(r"IGS0OPSFIN_(\d{4})(\d{3})0000_01D_15M_ORB\.SP3\.gz")
GPS_ID = re.compile(r"G(?:0[1-9]|[12][0-9]|3[0-2])")


class Refusal(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise Refusal(code)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(raw, sha256, maximum):
    require(isinstance(raw, bytes) and 0 < len(raw) <= maximum, "source_size")
    require(bool(re.fullmatch(r"[a-f0-9]{64}", sha256)), "expected_sha256_required")
    require(digest(raw) == sha256, "source_hash_mismatch")


def number(text):
    require(bool(re.fullmatch(r"[+-]?\d+(?:\.\d+)?", text.strip())), "invalid_number")
    return Decimal(text.strip())


def calendar(parts):
    try:
        value, _ = TIME["SOURCE"]["epoch"](parts)
        return value
    except (ValueError, TypeError, OverflowError):
        raise Refusal("invalid_epoch") from None


def inspect_sp3(source, sha256, product_name):
    checked(source, sha256, MAX_SOURCE)
    match = NAME.fullmatch(product_name)
    require(match is not None, "not_supported_combined_final_product")
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(source)) as stream:
            raw = stream.read(MAX_TEXT + 1)
        require(len(raw) <= MAX_TEXT, "expanded_source_size")
        lines = raw.decode("ascii").splitlines()
    except (OSError, EOFError, UnicodeError, zlib.error):
        raise Refusal("not_gzip_ascii_sp3") from None
    require(
        24 <= len(lines) <= 100000 and all(len(s) <= 80 for s in lines), "record_bounds"
    )
    require(lines[-1] == "EOF", "missing_eof")
    header = lines[0]
    require(header.startswith("#cP") and len(header) == 60, "unsupported_sp3_profile")
    count = int(header[32:39])
    require(1 <= count <= 96, "epoch_count")
    first_parts = header[3:31].split()
    first = calendar(first_parts)
    require(header[40:45] == "ORBIT", "unsupported_data_units_profile")
    require(header[46:51] == "IGS20", "unsupported_frame_declaration")
    require(
        header[52:55] == "HLM" and header[56:60].strip() == "IGS",
        "unsupported_producer_profile",
    )
    day = datetime(int(match[1]), 1, 1) + timedelta(days=int(match[2]) - 1)
    require(day.year == int(match[1]) and int(match[2]) >= 1, "product_calendar")
    require(
        first_parts
        == [str(day.year), str(day.month), str(day.day), "0", "0", "0.00000000"],
        "filename_header_time_mismatch",
    )
    week = lines[1]
    require(week.startswith("## ") and len(week) == 60, "interval_header")
    require(number(week[24:38]) == 900, "unsupported_sampling_interval")
    require(int(week[3:7]) * 604800 + number(week[8:23]) == first, "gps_week_conflict")
    gps_mjd = (datetime(1980, 1, 6) - datetime(1858, 11, 17)).days
    require(
        (int(week[39:44]) - gps_mjd + number(week[45:60])) * 86400 == first,
        "mjd_conflict",
    )
    require(
        all(s.startswith("+ ") for s in lines[2:7])
        and all(s.startswith("++") for s in lines[7:12]),
        "satellite_headers",
    )
    declared = int(lines[2][3:6])
    tokens = [s[i : i + 3].strip() for s in lines[2:7] for i in range(9, 60, 3)]
    sats = tokens[:declared]
    require(
        1 <= declared <= 32
        and len(set(sats)) == declared
        and all(GPS_ID.fullmatch(s) for s in sats)
        and all(s == "0" for s in tokens[declared:]),
        "satellite_identity_header",
    )
    accuracy = [s[i : i + 3].strip() for s in lines[7:12] for i in range(9, 60, 3)]
    require(
        all(re.fullmatch(r"\d{1,2}", s) for s in accuracy), "invalid_header_accuracy"
    )
    require(
        lines[12].startswith("%c G") and lines[12][9:12] == "GPS",
        "unsupported_time_system",
    )
    require(
        lines[13].startswith("%c")
        and all(s.startswith("%f") for s in lines[14:16])
        and all(s.startswith("%i") for s in lines[16:18]),
        "auxiliary_headers",
    )
    base = number(lines[14][3:13])
    require(base == Decimal("1.25"), "unsupported_sigma_base")
    comments, index = [], 18
    while index < len(lines) and lines[index].startswith("/*"):
        comments.append(lines[index][3:])
        index += 1
    require(
        len(comments) >= 4
        and any(
            "FINAL ORBIT COMBINATION FROM WEIGHTED AVERAGE OF:" in s for s in comments
        ),
        "missing_final_combination_declaration",
    )
    epochs, positions, quality = [], Counter(), {sid: Counter() for sid in sats}
    while index < len(lines) - 1:
        stamp = lines[index]
        require(stamp.startswith("*  "), "missing_epoch_record")
        parts = stamp[3:].split()
        value = calendar(parts)
        require(
            value == first + 900 * len(epochs), "duplicate_ambiguous_or_irregular_epoch"
        )
        reasons = {}
        try:
            TIME["gps_value"](parts, "GPS")
        except TIME["QualificationError"] as error:
            reasons["time"] = error.code
        require(index + declared < len(lines) - 1, "missing_state_records")
        seen = set()
        for record in lines[index + 1 : index + 1 + declared]:
            require(
                record.startswith("P") and len(record) == 80, "unsupported_state_record"
            )
            sid = record[1:4]
            require(
                sid in sats and sid not in seen, "duplicate_or_unknown_state_identity"
            )
            seen.add(sid)
            positions[sid] += 1
            values = [
                number(record[a:b]) for a, b in ((4, 18), (18, 32), (32, 46), (46, 60))
            ]
            reject = []
            if all(v == 0 for v in values[:3]):
                reject.append("missing_position")
            for column, allowed in ((74, " E"), (75, " P"), (78, " M"), (79, " P")):
                require(record[column] in allowed, "unknown_quality_flag")
            if record[78] == "M":
                reject.append("maneuver_flag")
            if record[79] == "P":
                reject.append("predicted_position")
            if values[3] == Decimal("999999.999999"):
                quality[sid]["missing_clock_unused"] += 1
            for axis, (a, b) in zip("xyz", ((61, 63), (64, 66), (67, 69)), strict=True):
                text = record[a:b].strip()
                require(
                    not text or bool(re.fullmatch(r"\d{1,2}", text)),
                    "invalid_axis_sigma",
                )
                if not text:
                    reject.append("unknown_" + axis + "_sigma")
                else:
                    quality[sid][axis + "_sigma_exponent_" + text] += 1
            reasons[sid] = reject
            quality[sid].update(reject)
        require(seen == set(sats), "missing_state_identity")
        epochs.append(
            {"source_index": len(epochs) + 1, "gps_parts": parts, "exclusions": reasons}
        )
        index += 1 + declared
    require(len(epochs) == count, "declared_epoch_count_mismatch")
    return {
        "product_name": product_name,
        "source_sha256": digest(source),
        "source_bytes": len(source),
        "expanded_sha256": digest(raw),
        "expanded_bytes": len(raw),
        "profile": "SP3-c/GPS/P/FIN/15M",
        "frame_declaration": "IGS20",
        "time_system": "GPS",
        "position_unit": "km",
        "clock_unit": "microseconds; unused",
        "velocity_records": 0,
        "epoch_count": count,
        "sampling_seconds": 900,
        "complete_15_minute_daily_grid": count == 96,
        "nominal_product_period_seconds": 86400,
        "last_sample_offset_seconds": (count - 1) * 900,
        "satellite_ids": sats,
        "position_counts": dict(positions),
        "header_accuracy_exponents": {s: int(accuracy[i]) for i, s in enumerate(sats)},
        "header_sigma_rule": (
            "2**exponent mm; zero means unknown; not a full uncertainty budget"
        ),
        "axis_sigma_rule": "1.25**exponent mm; zero is 1 mm; blank means unknown",
        "quality_counts": {s: dict(q) for s, q in quality.items()},
        "epochs": epochs,
        "scientifically_accepted_count": 0,
        "comparison_implemented": False,
    }


def unique_json(raw):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            require(key not in value, "duplicate_gp_field")
            value[key] = item
        return value

    try:
        return json.loads(
            raw,
            object_pairs_hook=unique,
            parse_constant=lambda _: (_ for _ in ()).throw(Refusal("nonfinite_gp")),
        )
    except (ValueError, UnicodeError):
        raise Refusal("invalid_gp_json") from None


def gp_record(raw, sha256, catalog_id):
    checked(raw, sha256, 65536)
    data = unique_json(raw)
    require(isinstance(data, list) and 1 <= len(data) <= 64, "gp_dataset_bounds")
    matches = [
        (i, r)
        for i, r in enumerate(data)
        if isinstance(r, dict) and r.get("NORAD_CAT_ID") == catalog_id
    ]
    require(len(matches) == 1, "missing_or_ambiguous_gp_record")
    index, record = matches[0]
    try:
        epoch = record.get("EPOCH")
        require(isinstance(epoch, str), "missing_gp_epoch")
        explicit = epoch if re.search(r"Z$|[+-]\d\d:\d\d$", epoch) else epoch + "Z"
        exact = report_time(
            explicit
        )  # Reject submicrosecond truncation before Pydantic.
        elements = Elements.model_validate(record)
        require(elements.epoch == exact, "gp_epoch_conflict")
        # Initialization verifies the selected existing model path, not a position.
        method = elements.satellite().method
    except (ValueError, TypeError, OverflowError):
        raise Refusal("unsupported_gp_record") from None
    return elements, {
        "source_sha256": digest(raw),
        "source_bytes": len(raw),
        "source_index_zero_based": index,
        "canonical_record_sha256": digest(
            json.dumps(
                record, sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode()
        ),
        "catalog_id": elements.catalog_id,
        "cospar_id": elements.object_id,
        "epoch_utc": elements.epoch.isoformat(),
        "ephemeris_type": elements.ephemeris_type,
        "mean_element_theory": elements.theory,
        "initialization_method": method,
        "gravity_model": "existing WGS72",
        "propagation_executed": False,
        "fit_lineage": "not established",
        "historical_availability": "not established",
    }


def nominal_identity(raw, sha256, prn, nominal_day):
    """SINEX civil-calendar lookup only, NOT sub-second time-scale qualification."""
    checked(raw, sha256, 2 * 1024 * 1024)
    require(bool(GPS_ID.fullmatch(prn)), "invalid_prn")
    try:
        lines = raw.decode("ascii").splitlines()
    except UnicodeError:
        raise Refusal("non_ascii_metadata") from None

    require(lines and lines[0].startswith("%=SNX 2.02 "), "unsupported_metadata_header")
    require(
        isinstance(nominal_day, datetime) and nominal_day.tzinfo is None,
        "nominal_mapping_calendar_required",
    )

    def block(name):
        start = "+SATELLITE/" + name
        end = "-SATELLITE/" + name
        begins = [i for i, s in enumerate(lines) if s.rstrip() == start]
        ends = [i for i, s in enumerate(lines) if s.rstrip() == end]
        require(
            len(begins) == len(ends) == 1 and begins[0] < ends[0],
            "missing_or_ambiguous_metadata_block",
        )
        return [
            s.split()
            for s in lines[begins[0] + 1 : ends[0]]
            if s.startswith(" ") and s.strip()
        ]

    def date(value):
        if value == "0000:000:00000":
            return None
        require(
            bool(re.fullmatch(r"\d{4}:\d{3}:\d{5}", value)), "invalid_mapping_epoch"
        )
        y, d, s = map(int, value.split(":"))
        require(1 <= d <= 366 and 0 <= s < 86400, "invalid_mapping_epoch")
        at = datetime(y, 1, 1) + timedelta(days=d - 1, seconds=s)
        require(at.year == y, "invalid_mapping_epoch")
        return at

    matches = []
    for row in block("PRN"):
        require(len(row) >= 4, "malformed_prn_record")
        if row[3] != prn:
            continue
        begin, end = date(row[1]), date(row[2])
        require(
            begin is not None and (end is None or begin < end),
            "invalid_mapping_interval",
        )
        if begin <= nominal_day and (end is None or nominal_day < end):
            matches.append(row)
    require(len(matches) == 1, "missing_or_ambiguous_prn_mapping")
    mapping = matches[0]
    require(bool(re.fullmatch(r"G\d{3}", mapping[0])), "invalid_svn")
    ids = [r for r in block("IDENTIFIER") if r[0] == mapping[0]]
    require(
        len(ids) == 1 and len(ids[0]) >= 4, "missing_or_ambiguous_satellite_identifier"
    )
    require(bool(re.fullmatch(r"\d{4}-\d{3}[A-Z]{1,3}", ids[0][1])), "invalid_cospar")
    require(ids[0][2].isdigit() and 1 <= int(ids[0][2]) <= 339999, "invalid_catalog")
    return {
        "prn": prn,
        "svn": mapping[0],
        "cospar_id": ids[0][1],
        "catalog_id": int(ids[0][2]),
        "valid_from_raw": mapping[1],
        "valid_to_raw": mapping[2],
        "metadata_sha256": digest(raw),
        "scope": (
            "nominal civil-calendar identity only; "
            "metadata interval time scale requires review at boundaries"
        ),
    }


def qualify(product, elements, gp, identity):
    require(identity["prn"] in product["satellite_ids"], "reference_target_missing")
    require(
        identity["catalog_id"] == elements.catalog_id
        and identity["cospar_id"] == elements.object_id,
        "gp_reference_identity_mismatch",
    )
    rows = []
    exclusions = Counter()
    resource_quality = Counter()
    try:
        with orientation() as (resources, policy):
            # Freeze the first source epoch, never the first surviving quality sample.
            anchor = TIME["to_utc"](
                TIME["gps_value"](
                    product["epochs"][0]["gps_parts"], product["time_system"]
                ),
                resources,
            )
            for epoch in product["epochs"]:
                reasons = list(epoch["exclusions"][identity["prn"]])
                time_error = epoch["exclusions"].get("time")
                if time_error:
                    reasons.append(time_error)
                stamp = None
                if not time_error:
                    value = TIME["gps_value"](
                        epoch["gps_parts"], product["time_system"]
                    )
                    stamp = TIME["to_utc"](value, resources)
                    # Resource preflight only; no spacecraft coordinate transform.
                    status = parameters(
                        resources, TIME["Time"](stamp, scale="utc"), policy
                    )
                    resource_quality.update(
                        [status["ut1_source"], status["polar_motion_source"]]
                    )
                    at = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
                    if abs(at - elements.epoch) > timedelta(days=7):
                        reasons.append("outside_existing_7_day_guard")
                exclusions.update(reasons)
                rows.append(
                    {
                        "source_index": epoch["source_index"],
                        "utc_diagnostic": stamp,
                        "exclusions": reasons,
                    }
                )
            resource_info = resources.metadata
    except (ValueError, RuntimeError, OSError) as error:
        raise Refusal("time_or_eop_resources_unavailable") from error
    after = elements.epoch > datetime.fromisoformat(anchor.replace("Z", "+00:00"))
    if after:
        for r in rows:
            r["exclusions"].append("gp_after_reference_anchor")
        exclusions["gp_after_reference_anchor"] = len(rows)
    candidates = [r["source_index"] for r in rows if not r["exclusions"]]
    return {
        "study_id": "ORBITIQ-IGS-GPS-RETRO-001",
        "decision": "BLOCKED — ADDITIONAL EVIDENCE REQUIRED",
        "candidate_gp": gp,
        "nominal_identity": identity,
        "utc_diagnostics": rows,
        "time_and_source_eligible_indices": candidates,
        "exclusion_counts": dict(exclusions),
        "resources": resource_info,
        "policy": policy,
        "frozen_anchor_utc": anchor,
        "resource_quality_counts": dict(resource_quality),
        "blocking_requirements": [
            "reviewed_frame_alignment",
            "reference_point_and_quality_review",
            "uncertainty_and_claims_protocol_review",
            "explicit_user_approval_before_comparison",
        ]
        + ([] if candidates else ["compatible_historical_gp_input"])
        + (
            []
            if product["complete_15_minute_daily_grid"]
            else ["complete_daily_coverage"]
        ),
        "statistical_independence": "UNVERIFIED",
        "scientifically_accepted_count": 0,
        "propagation_executed": False,
        "residuals_calculated": False,
    }


def bounded_file(path, maximum):
    require(not path.is_symlink() and path.is_file(), "regular_input_file_required")
    require(0 < path.stat().st_size <= maximum, "source_size")
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    require(len(raw) <= maximum, "source_size")
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("product", "gp", "metadata"):
        parser.add_argument("--" + name, type=Path, required=True)
        parser.add_argument("--" + name + "-sha256", required=True)
    parser.add_argument("--product-name", required=True)
    parser.add_argument("--prn", required=True)
    parser.add_argument("--catalog-id", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        product = inspect_sp3(
            bounded_file(args.product, MAX_SOURCE),
            args.product_sha256,
            args.product_name,
        )
        elements, gp = gp_record(
            bounded_file(args.gp, 65536), args.gp_sha256, args.catalog_id
        )
        first = product["epochs"][0]["gps_parts"]
        identity = nominal_identity(
            bounded_file(args.metadata, 2 * 1024 * 1024),
            args.metadata_sha256,
            args.prn,
            datetime(*map(int, first[:3])),
        )
        report = qualify(product, elements, gp, identity)
        report["reference_product"] = {
            k: v for k, v in product.items() if k != "epochs"
        }
        with args.output.open("x") as stream:
            json.dump(report, stream, indent=2, allow_nan=False)
            stream.write("\n")
    except (ValueError, OSError, TypeError, OverflowError):
        parser.exit(
            1,
            "IGS feasibility inspection refused; verify input hashes, "
            "supported metadata "
            "and local time/EOP resources. No fallback or comparison occurred.\n",
        )
    print(
        "Inspection complete; scientific comparison BLOCKED. "
        "No propagation or residuals."
    )


if __name__ == "__main__":
    main()
