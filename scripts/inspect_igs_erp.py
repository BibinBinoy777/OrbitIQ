"""Offline structural inspector for the E8.7.9 ERP-v2 18-column profile.

Not a general ERP decoder, time-scale qualifier, EOP adapter or interpolator.
Output can contain private raw EOP tokens; redirect it only to private storage.
The official IGSMAIL-1943 defines the core fields, not the final dpsi/deps
extensions in this profile. No error fields are converted into uncertainties.
"""

import argparse
import gzip
import hashlib
import io
import json
import re
import zlib
from bisect import bisect_right
from decimal import Decimal
from pathlib import Path

MAX_SOURCE = 64 * 1024
MAX_TEXT = 256 * 1024
COLUMNS = (
    "MJD Xpole Ypole UT1-UTC LOD Xsig Ysig UTsig LODsig Nr Nf Nt "
    "Xrt Yrt Xrtsig Yrtsig dpsi deps"
).split()
UNIT_TOKENS = (
    '10**-6" .1us .1us/d 10**-6" .1us .1us/d 10**-6"/d 10**-6"/d 10**-6'
).split()


class Refusal(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise Refusal(code)


def inspect_erp(source: bytes, expected_sha256: str) -> dict:
    """Read hash-pinned gzip/ASCII bytes; retain lexemes without repair."""
    require(isinstance(source, bytes) and 0 < len(source) <= MAX_SOURCE, "source_size")
    require(
        isinstance(expected_sha256, str)
        and re.fullmatch(r"[a-f0-9]{64}", expected_sha256),
        "expected_sha256_required",
    )
    require(hashlib.sha256(source).hexdigest() == expected_sha256, "hash_mismatch")
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(source)) as stream:
            raw = stream.read(MAX_TEXT + 1)
        require(len(raw) <= MAX_TEXT, "expanded_size")
        text = raw.decode("ascii")
    except (OSError, EOFError, UnicodeError, zlib.error):
        raise Refusal("not_gzip_ascii_erp") from None
    lines = text.splitlines()
    require(5 <= len(lines) <= 4101, "line_count")
    require(all(len(line) <= 512 for line in lines), "line_size")
    require(lines[0] == "version 2", "unsupported_version")
    require(bool(lines[1].strip()), "missing_solution_description")
    require(lines[2].split() == COLUMNS, "unsupported_column_profile")
    require(lines[3].split() == UNIT_TOKENS, "unsupported_unit_profile")
    records = []
    mjds = []
    for line_number, line in enumerate(lines[4:], 5):
        # A single trailing blank is present in the observed profile. Ignore
        # trailing blanks only, never a blank embedded between records.
        if not line.strip():
            require(all(not s.strip() for s in lines[line_number:]), "embedded_blank")
            break
        fields = line.split()
        require(len(fields) == len(COLUMNS), "column_count")
        require(bool(re.fullmatch(r"\d{5}\.\d{2}", fields[0])), "invalid_mjd")
        require(
            all(re.fullmatch(r"[+-]?\d+", value) for value in fields[1:]),
            "invalid_integer_or_unqualified_sentinel",
        )
        mjd = Decimal(fields[0])
        require(not mjds or mjd > mjds[-1], "duplicate_or_unordered_epoch")
        for name in [
            "Xsig",
            "Ysig",
            "UTsig",
            "LODsig",
            "Nr",
            "Nf",
            "Nt",
            "Xrtsig",
            "Yrtsig",
        ]:
            require(int(fields[COLUMNS.index(name)]) >= 0, "negative_error_or_count")
        records.append(
            {"line": line_number, "raw": dict(zip(COLUMNS, fields, strict=True))}
        )
        mjds.append(mjd)
    require(bool(records), "empty_response")
    return {
        "source_bytes": len(source),
        "source_sha256": expected_sha256,
        "expanded_bytes": len(raw),
        "expanded_sha256": hashlib.sha256(raw).hexdigest(),
        "format": "version 2; narrow 18-column E8.7.9 profile",
        "solution_description": lines[1],
        "header_lines": lines[:4],
        "time_system": "NOT_EXPLICITLY_DECLARED",
        "MJD_lexemes": [r["raw"]["MJD"] for r in records],
        "record_count": len(records),
        "cadence_days": sorted(
            {str(b - a) for a, b in zip(mjds, mjds[1:], strict=False)}
        ),
        "all_zero_columns": [
            name
            for name in COLUMNS[1:]
            if all(int(r["raw"][name]) == 0 for r in records)
        ],
        "unqualified_extension_columns": ["dpsi", "deps"],
        "zero_field_semantics": (
            "UNKNOWN; not proof of zero uncertainty or no contributors"
        ),
        "records": records,
        "scientific_status": "BLOCKED",
        "active_EOP_policy_changed": False,
    }


def arithmetic_coverage(knots: list[Decimal], targets: list[Decimal]) -> dict:
    """Only bracket full fractional MJD; time-scale compatibility is external.

    Does not interpolate EOP or orbital values, apply rates or fill gaps.
    Returned coverage is conditional on independently established epoch semantics.
    """
    require(
        len(knots) >= 2
        and all(isinstance(x, Decimal) and x.is_finite() for x in [*knots, *targets]),
        "invalid_coverage_epochs",
    )
    require(bool(targets), "empty_targets")
    require(all(a < b for a, b in zip(knots, knots[1:], strict=False)), "invalid_knots")
    brackets = []
    outside = []
    for index, target in enumerate(targets):
        if target < knots[0] or target > knots[-1]:
            outside.append(index)
            brackets.append(None)
            continue
        right = bisect_right(knots, target)
        left = right - 1
        if knots[left] == target:
            brackets.append([left, left])
        else:
            brackets.append([left, right])
    return {
        "target_count": len(targets),
        "outside_indices": outside,
        "all_targets_bracketed": not outside,
        "brackets_0based": brackets,
        "time_scale_compatibility_established": False,
        "interpolation_performed": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args(argv)
    try:
        with args.path.open("rb") as stream:
            source = stream.read(MAX_SOURCE + 1)
        result = inspect_erp(source, args.sha256)
    except OSError:
        result = {"refused": "file_unavailable", "scientific_status": "BLOCKED"}
    except Refusal as exc:
        result = {"refused": str(exc), "scientific_status": "BLOCKED"}
    print(json.dumps(result, indent=2))
    return int("refused" in result)


if __name__ == "__main__":
    raise SystemExit(main())
