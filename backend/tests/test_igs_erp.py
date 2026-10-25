"""SYNTHETIC ERP controls only; no acquired scientific evidence or spacecraft states."""

import gzip
import hashlib
import json
import runpy
from decimal import Decimal
from pathlib import Path

import pytest

M = runpy.run_path(str(Path(__file__).parents[2] / "scripts/inspect_igs_erp.py"))
INSPECT = M["inspect_erp"]
REFUSAL = M["Refusal"]
HEADER = (
    "version 2\nSYNTHETIC ERP ONLY - NOT SCIENTIFIC EVIDENCE\n"
    "MJD Xpole Ypole UT1-UTC LOD Xsig Ysig UTsig LODsig Nr Nf Nt "
    "Xrt Yrt Xrtsig Yrtsig dpsi deps\n"
    '10**-6" .1us .1us/d 10**-6" .1us .1us/d 10**-6"/d 10**-6"/d 10**-6\n'
)
ROW = "60000.50 101 -102 103 -104 1 2 0 3 0 0 0 -1 2 3 4 0 0"


def packed(text=None):
    return gzip.compress(
        (HEADER + ROW + "\n" if text is None else text).encode(), mtime=0
    )


def inspect(source):
    return INSPECT(source, hashlib.sha256(source).hexdigest())


def test_synthetic_profile_preserves_lexemes_and_has_no_qualification_switch():
    raw = packed(HEADER + ROW + "\n" + ROW.replace("60000.50", "60001.50") + "\n\n")
    saved = bytes(raw)
    result = inspect(raw)
    assert raw == saved and result["record_count"] == 2
    assert result["MJD_lexemes"] == ["60000.50", "60001.50"]
    assert result["cadence_days"] == ["1.00"]
    assert result["records"][0]["raw"]["Ypole"] == "-102"
    assert result["all_zero_columns"] == ["UTsig", "Nr", "Nf", "Nt", "dpsi", "deps"]
    assert result["unqualified_extension_columns"] == ["dpsi", "deps"]
    assert result["scientific_status"] == "BLOCKED"
    assert result["time_system"] == "NOT_EXPLICITLY_DECLARED"
    assert not result["active_EOP_policy_changed"]
    assert "SYNTHETIC" in result["solution_description"]


@pytest.mark.parametrize(
    "text,code",
    [
        ("<html>login</html>\n" * 5, "unsupported_version"),
        ((HEADER + ROW).replace("version 2", "version 1"), "unsupported_version"),
        (
            (HEADER + ROW).replace("SYNTHETIC ERP ONLY - NOT SCIENTIFIC EVIDENCE", ""),
            "missing_solution_description",
        ),
        (
            (HEADER + ROW).replace("dpsi deps", "XYCorr XUTCor"),
            "unsupported_column_profile",
        ),
        ((HEADER + ROW).replace(".1us ", "1us ", 1), "unsupported_unit_profile"),
        (HEADER, "line_count"),
        (HEADER + "\n", "empty_response"),
        (HEADER + ROW + "\n" + ROW, "duplicate_or_unordered_epoch"),
        (
            HEADER + ROW + "\n" + ROW.replace("60000.50", "59999.50"),
            "duplicate_or_unordered_epoch",
        ),
        (HEADER + ROW.replace("60000.50", "60000.500"), "invalid_mjd"),
        (HEADER + ROW.replace("101", "NaN"), "invalid_integer_or_unqualified_sentinel"),
        (HEADER + ROW.replace("101", "1e2"), "invalid_integer_or_unqualified_sentinel"),
        (HEADER + ROW.replace("101", "***"), "invalid_integer_or_unqualified_sentinel"),
        (HEADER + ROW.replace(" 1 2 0 ", " -1 2 0 "), "negative_error_or_count"),
        (HEADER + ROW.rsplit(" ", 1)[0], "column_count"),
        (HEADER + ROW + " 0", "column_count"),
        (HEADER + ROW + "\n\n" + ROW.replace("60000.50", "60001.50"), "embedded_blank"),
        (HEADER + ROW + " " * 600, "line_size"),
        (HEADER + ROW + "\n\N{SNOWMAN}", "not_gzip_ascii_erp"),
    ],
)
def test_synthetic_malformed_or_unsupported_profile_refused(text, code):
    with pytest.raises(REFUSAL, match=f"^{code}$"):
        inspect(packed(text))


@pytest.mark.parametrize(
    "raw,code",
    [
        (b"", "source_size"),
        (b"x" * (M["MAX_SOURCE"] + 1), "source_size"),
        (b"<html>login</html>", "not_gzip_ascii_erp"),
        (packed()[:-8], "not_gzip_ascii_erp"),
        (packed("x" * (M["MAX_TEXT"] + 1)), "expanded_size"),
    ],
)
def test_synthetic_compression_and_bounds(raw, code):
    with pytest.raises(REFUSAL, match=f"^{code}$"):
        inspect(raw)


@pytest.mark.parametrize(
    "expected,code",
    [
        ("0" * 64, "hash_mismatch"),
        ("bad", "expected_sha256_required"),
        (None, "expected_sha256_required"),
    ],
)
def test_hash_is_mandatory_and_exact(expected, code):
    with pytest.raises(REFUSAL, match=f"^{code}$"):
        INSPECT(packed(), expected)


def test_fractional_knots_exact_boundaries_and_no_silent_nearest_extrapolation():
    r = M["arithmetic_coverage"](
        list(map(Decimal, ["60000.5", "60001.5", "60002.5"])),
        list(
            map(
                Decimal,
                [
                    "60000.49999",
                    "60000.5",
                    "60000.75",
                    "60001.75",
                    "60002.5",
                    "60002.50001",
                ],
            )
        ),
    )
    assert r["outside_indices"] == [0, 5]
    assert r["brackets_0based"] == [None, [0, 0], [0, 1], [1, 2], [2, 2], None]
    assert (
        not r["interpolation_performed"]
        and not r["time_scale_compatibility_established"]
    )


@pytest.mark.parametrize(
    "knots,targets",
    [
        (["1"], ["1"]),
        (["1", "1"], ["1"]),
        (["2", "1"], ["1"]),
        (["1", "2"], []),
        (["1", "NaN"], ["1"]),
        (["1", "2"], ["Infinity"]),
    ],
)
def test_invalid_coverage_inputs_refused(knots, targets):
    with pytest.raises(REFUSAL):
        M["arithmetic_coverage"](list(map(Decimal, knots)), list(map(Decimal, targets)))


def test_installed_astropy_noon_knots_are_not_a_drop_in_source():
    # Synthetic EOP diagnostic only, not a spacecraft transformation or new
    # scientific uncertainty estimate. Pin the actual implementation audited.
    import astropy
    from astropy import units as u
    from astropy.time import Time
    from astropy.utils import iers

    assert astropy.__version__ == "7.2.3"
    table = iers.IERS_B()
    table["MJD"] = [60000.5, 60001.5, 60002.5] * u.d
    table["PM_x"] = [0, 1, 4] * u.arcsec
    table["PM_y"] = [0, 1, 4] * u.arcsec
    xp, _, status = table.pm_xy(
        Time([60000.75, 60001.75], format="mjd", scale="utc"), return_status=True
    )
    assert status[0] == iers.TIME_BEFORE_IERS_RANGE  # Though inside actual knots.
    assert xp[0].value == 0  # Endpoint hold, not correct fractional bracketing.
    assert status[1] == iers.FROM_IERS_B
    assert xp[1].value == pytest.approx(1.25)  # Uses earlier daily bracket.
    # Correct arithmetic bracket is [1,2]; we do not build/activate an adapter.
    assert M["arithmetic_coverage"](
        list(map(Decimal, ["60000.5", "60001.5", "60002.5"])), [Decimal("60001.75")]
    )["brackets_0based"] == [[1, 2]]


def test_cli_missing_and_valid_synthetic_file(tmp_path, capsys):
    p = tmp_path / "synthetic.erp.gz"
    assert M["main"]([str(p), "--sha256", "0" * 64]) == 1
    assert json.loads(capsys.readouterr().out)["refused"] == "file_unavailable"
    raw = packed()
    p.write_bytes(raw)
    before = p.read_bytes()
    assert M["main"]([str(p), "--sha256", hashlib.sha256(raw).hexdigest()]) == 0
    assert json.loads(capsys.readouterr().out)["scientific_status"] == "BLOCKED"
    assert p.read_bytes() == before
