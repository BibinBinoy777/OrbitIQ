"""Synthetic CSV intake/reconciliation tests, never genuine Swarm observations."""

import csv
import io
import json
import re
import runpy
import stat
from pathlib import Path

import pytest
from orbitiq import replay
from orbitiq.ingestion import celestrak
from orbitiq.orbits import engine
from orbitiq.orbits.elements import Elements
from orbitiq.services import analysis

ROOT = Path(__file__).resolve().parents[2]
CSV = runpy.run_path(str(ROOT / "scripts/inspect_historical_csv.py"))
RECON = runpy.run_path(str(ROOT / "scripts/reconcile_historical_gp.py"))
QUALIFY = runpy.run_path(str(ROOT / "scripts/qualify_swarm_inputs.py"))
FACTORY = runpy.run_path(str(Path(__file__).with_name("test_historical_gp_intake.py")))
SP3 = runpy.run_path(str(Path(__file__).with_name("test_phase113_swarm_inspection.py")))


def records():
    return [
        {
            name: str(value)
            for name, value in FACTORY["synthetic"](
                EPOCH=epoch,
                ECCENTRICITY=0.000123,
                BSTAR=0.001234,
                MEAN_MOTION_DOT=0.012345,
            ).items()
            if name in CSV["FIELDS"]
        }
        for epoch in (
            "2013-12-31T00:00:00",
            "2014-01-01T00:00:00",
            "2014-01-02T00:00:00",
        )
    ]


def encoded(rows=None, header=None, quoting=csv.QUOTE_MINIMAL):
    header = CSV["FIELDS"] if header is None else header
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, quoting=quoting)
    writer.writerow(header)
    for row in records() if rows is None else rows:
        writer.writerow([row.get(name, "") for name in header])
    return stream.getvalue().encode()


def inspect(rows=None):
    return CSV["inspect_attachment"](encoded(rows))


def test_verified_schema_three_records_source_strings_and_conventions():
    raw = encoded()
    result = CSV["inspect_attachment"](raw)
    assert result["header"] == list(CSV["FIELDS"])
    assert result["counts"] == {"enumerated": 3, "candidate": 3, "excluded": 0}
    assert result["attachment_sha256"] == replay.digest(raw)
    assert result["attachment_bytes"] == len(raw)
    assert result["status"] == "PARTIAL" and result["source_format"] == "CSV"
    for index, row in enumerate(result["records"]):
        assert row["source_index"] == index and row["physical_line_end"] == index + 2
        assert row["source_fields"] == records()[index]
        assert (
            row["element_model_compatible"] and not row["dynamic_parser_check_executed"]
        )
        assert row["attachment_sha256"] == replay.digest(raw)
    assert result["model_conventions_not_csv_columns"]["REF_FRAME"] == "TEME"
    assert len(result["qualification_gates"]) == 10
    assert result["qualification_gates"]["record_structure"]["status"] == "PASS"
    assert (
        result["qualification_gates"]["numbers_and_element_model"]["status"] == "PASS"
    )
    assert result["selected_source_index"] is None and not result["source_accepted"]


@pytest.mark.parametrize("token", [".000123", ".123e-3", ".123E-3", "0.00012300"])
def test_fractional_exponent_text_preserved_without_tolerance(token):
    rows = records()
    rows[0]["ECCENTRICITY"] = token
    row = inspect(rows)["records"][0]
    assert row["status"] == "CANDIDATE"
    assert row["source_fields"]["ECCENTRICITY"] == token


@pytest.mark.parametrize(
    "field,token",
    [
        ("BSTAR", "NaN"),
        ("BSTAR", "Infinity"),
        ("BSTAR", "-Inf"),
        ("BSTAR", "1e999"),
        ("BSTAR", "1e-999"),
        ("BSTAR", "bad"),
        ("BSTAR", "1e"),
        ("BSTAR", "1e999999999999999999999999999"),
        ("MEAN_MOTION", "0"),
        ("MEAN_MOTION", "101"),
        ("ECCENTRICITY", "1.0"),
        ("INCLINATION", "181"),
        ("RA_OF_ASC_NODE", "360"),
        ("MEAN_ANOMALY", "-1"),
        ("NORAD_CAT_ID", "39452.0"),
        ("NORAD_CAT_ID", "25544"),
        ("OBJECT_ID", "2013-067A"),
        ("EPHEMERIS_TYPE", "1"),
        ("CLASSIFICATION_TYPE", "S"),
        ("ELEMENT_SET_NO", "-1"),
        ("MEAN_MOTION_DOT", " 0.01"),
        ("OBJECT_NAME", ""),
        ("EPOCH", ""),
        ("EPOCH", "invalid"),
        ("EPOCH", "2014-02-30T00:00:00"),
        ("EPOCH", "2014-01-01T00:00:60"),
        ("EPOCH", "2014-01-01T00:00:00.1234567"),
        ("EPOCH", "2014-01-01T00:00:00+01:00"),
        ("EPOCH", "2014-01-04T00:00:00"),
    ],
)
def test_bad_row_excluded_without_discarding_other_rows(field, token):
    rows = records()
    rows[1][field] = token
    result = inspect(rows)
    assert result["counts"] == {"enumerated": 3, "candidate": 2, "excluded": 1}
    assert result["records"][1]["source_fields"][field] == token
    assert result["records"][1]["reasons"]
    assert [r["source_index"] for r in result["records"]] == [0, 1, 2]


@pytest.mark.parametrize(
    "kind", ["missing", "extra", "duplicate", "wrong", "delimiter"]
)
def test_invalid_headers_fail_closed(kind):
    header = list(CSV["FIELDS"])
    if kind == "missing":
        header.pop()
    elif kind == "extra":
        header.append("UNREVIEWED")
    elif kind == "duplicate":
        header[-1] = header[0]
    elif kind == "wrong":
        header[-1] = "NDDOT"
    raw = encoded(header=header)
    if kind == "delimiter":
        raw = raw.replace(b",", b";")
    result = CSV["inspect_attachment"](raw)
    assert result["document_errors"] and result["records"] == []
    assert result["comparison_ready"] is False


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"\xff",
        b'"unterminated',
        b'bad"quote,a\n',
        b'"closed"oops,a\n',
        b"a,\x00b\n",
    ],
)
def test_empty_invalid_encoding_and_malformed_csv(raw):
    result = CSV["inspect_attachment"](raw)
    assert result["document_errors"] and not result["comparison_ready"]


def test_header_only_and_blank_row_are_not_silently_ignored():
    assert CSV["inspect_attachment"](encoded([]))["document_errors"]
    result = CSV["inspect_attachment"](encoded() + b"\r\n")
    assert result["counts"]["enumerated"] == 4 and result["counts"]["excluded"] == 1
    assert result["records"][3]["source_field_count"] == 0


@pytest.mark.parametrize("extra", [b"extra", b",extra,extra"])
def test_inconsistent_row_width_retains_index_and_diagnostic(extra):
    result = CSV["inspect_attachment"](encoded() + extra + b"\r\n")
    row = result["records"][3]
    assert row["source_index"] == 3 and row["status"] == "EXCLUDED"
    assert row["reasons"] and row["source_cell_preview"]


def test_quoted_multiline_and_bom_and_reordered_headers():
    rows = records()
    rows[0]["OBJECT_NAME"] = 'SYNTHETIC, "quoted"\nFORMAT ONLY'
    raw = b"\xef\xbb\xbf" + encoded(rows, list(reversed(CSV["FIELDS"])), csv.QUOTE_ALL)
    result = CSV["inspect_attachment"](raw)
    assert result["counts"]["candidate"] == 3
    assert (
        result["records"][0]["source_fields"]["OBJECT_NAME"] == rows[0]["OBJECT_NAME"]
    )
    assert result["records"][0]["physical_line_end"] == 3


def test_byte_cell_and_record_budgets_are_explicit(monkeypatch):
    with pytest.raises(ValueError, match="byte_budget"):
        CSV["inspect_attachment"](b"x" * (2 * 1024 * 1024 + 1))
    rows = records()
    rows[0]["OBJECT_NAME"] = "x" * 4097
    assert inspect(rows)["records"][0]["reasons"]
    monkeypatch.setitem(CSV["INTAKE"], "MAX_RECORDS", 2)
    result = inspect()
    assert result["document_errors"]
    assert "unenumerated" in result["document_errors"][0]
    assert result["counts"]["candidate"] == 0


def test_duplicates_use_exact_decimal_values_not_binary_float_hashes():
    rows = records()
    rows.append(dict(rows[0], BSTAR=".00123400"))
    result = inspect(rows)
    assert result["counts"] == {"enumerated": 4, "candidate": 2, "excluded": 2}
    assert result["records"][0]["duplicate_source_indices"] == [0, 3]
    rows[3]["BSTAR"] = ".0012340000000000000000000001"
    result = inspect(rows)
    assert "ambiguous_same_epoch_identity" in result["records"][0]["reasons"]
    assert "duplicate_exact_record" not in result["records"][0]["reasons"]


def test_missing_provenance_stays_unknown_and_receipt_does_not_prove_availability():
    result = CSV["inspect_attachment"](
        encoded(),
        {
            "provider": "SYNTHETIC ASSERTION",
            "format": "CSV",
            "received_at": "2026-10-21T00:00:00Z",
            "original_filename": "synthetic.csv",
        },
    )
    provenance = result["provenance"]
    assert provenance["historically_available_at"] is None
    assert provenance["source_authenticated"] is False
    assert "acquired_at" in provenance["missing"]
    assert (
        result["qualification_gates"]["provenance_and_independence"]["status"]
        == "BLOCKED"
    )


@pytest.mark.parametrize("field", CSV["FIELDS"])
def test_every_source_column_is_required(field):
    result = CSV["inspect_attachment"](
        encoded(header=[name for name in CSV["FIELDS"] if name != field])
    )
    assert result["document_errors"] and result["counts"]["candidate"] == 0


def test_csv_qualification_cli_preserves_output_and_stays_format_explicit(tmp_path):
    kin, val, raw = SP3["package"](), SP3["package"]("VAL"), encoded()
    kp, vp, cp, out = [tmp_path / name for name in ("kin", "val", "csv", "result")]
    for path, body in ((kp, kin), (vp, val), (cp, raw)):
        path.write_bytes(body)
    args = [
        "--kinematic",
        str(kp),
        "--validation",
        str(vp),
        "--kinematic-sha256",
        replay.digest(kin),
        "--validation-sha256",
        replay.digest(val),
        "--gp-csv",
        str(cp),
        "--csv-sha256",
        replay.digest(raw),
        "--output",
        str(out),
    ]
    assert QUALIFY["main"](args) == 0
    before = out.read_bytes()
    result = json.loads(before)
    assert result["historical_input"]["source_format"] == "CSV"
    assert result["comparison_ready"] is False and result["prediction_evaluations"] == 0
    assert stat.S_IMODE(out.stat().st_mode) == 0o600
    assert QUALIFY["main"](args) == 1 and out.read_bytes() == before
    assert (
        QUALIFY["main"](
            args + ["--gp-json", str(cp), "--gp-sha256", replay.digest(raw)]
        )
        == 1
    )
    assert cp.read_bytes() == raw and kp.read_bytes() == kin and vp.read_bytes() == val


def test_capture_is_private_exclusive_original_preserving_and_json_stays_strict(
    tmp_path,
):
    root = tmp_path / "archive"
    root.mkdir(mode=0o700)
    source = tmp_path / "synthetic.csv"
    raw = encoded()
    source.write_bytes(raw)
    args = [
        "--attachment",
        str(source),
        "--archive-root",
        str(root),
        "--expected-sha256",
        replay.digest(raw),
    ]
    assert CSV["main"](args) == CSV["main"](args) == 0
    leaves = list(root.iterdir())
    assert len(leaves) == 2 and source.read_bytes() == raw
    for leaf in leaves:
        assert stat.S_IMODE(leaf.stat().st_mode) == 0o700
        assert (leaf / "attachment.original").read_bytes() == raw
        manifest = json.loads((leaf / "manifest.json").read_bytes())
        for name, entry in manifest["files"].items():
            file = leaf / name
            assert stat.S_IMODE(file.stat().st_mode) == 0o600
            assert entry == {
                "sha256": replay.digest(file.read_bytes()),
                "bytes": file.stat().st_size,
            }
        assert (
            json.loads((leaf / "inspection.json").read_bytes())["source_format"]
            == "CSV"
        )
    args[-1] = "0" * 64
    assert CSV["main"](args) == 1 and len(list(root.iterdir())) == 2
    assert CSV["INTAKE"]["inspect_attachment"](raw)["document_errors"]
    assert CSV["INTAKE"]["inspect_attachment"](b'[{"BSTAR":.123}]')["document_errors"]


def specimen():
    # Nine leading-decimal tokens in a deliberately malformed synthetic original.
    rows = records()
    typed = [CSV["typed_fields"](row)[0] for row in rows]
    for row in typed:
        # JSON may encode a schema floating field as an integer token. The CSV
        # adapter's Decimal type must not be called a source precision change.
        row["MEAN_MOTION_DDOT"] = 0
    for row in rows:
        row["MEAN_MOTION_DDOT"] = "0"
    valid = json.dumps(typed, separators=(",", ":")).encode()
    original = re.sub(
        rb'("(?:ECCENTRICITY|BSTAR|MEAN_MOTION_DOT)":)0\.', rb"\1.", valid
    )
    edits = []
    for match in re.finditer(rb":(\.\d+)(?=,)", original):
        start, stop = match.span(1)
        edits.append(
            {
                "start_byte_in_original": start,
                "stop_byte_exclusive_in_original": stop,
                "original_token": match[1].decode(),
                "probe_token": "0" + match[1].decode(),
            }
        )
    assert len(edits) == 9
    ledger = {
        "kind": "orbitiq_historical_attachment_format_diagnostic",
        "original_sha256": replay.digest(original),
        "original_bytes": len(original),
        "original_strict_json_valid": False,
        "edits": edits,
        "probe_sha256": replay.digest(valid),
    }
    return original, replay.encoded(ledger), rows


def reconcile(original, assessment, raw):
    return RECON["reconcile"](
        original,
        assessment,
        raw,
        original_sha256=replay.digest(original),
        assessment_sha256=replay.digest(assessment),
        replacement_sha256=replay.digest(raw),
        replacement_format="csv",
    )


def test_all_51_fields_reconcile_with_source_indices_text_and_ledger_lineage():
    original, ledger, rows = specimen()
    result = reconcile(original, ledger, encoded(rows))
    assert result["semantic_match"] and result["status"] == "PARTIAL"
    assert result["original_count"] == result["replacement_count"] == 3
    assert result["source_order_preserved"]
    assert len(result["field_comparisons"]) == 51
    assert all(item["value_equal"] for item in result["field_comparisons"])
    assert result["assessment_sha256"] == replay.digest(ledger)
    assert result["original_sha256"] == replay.digest(original)
    assert result["provenance_comparison"]["assessment_edit_count"] == 9
    assert result["provenance_comparison"]["csv_format"] == "CSV_not_corrected_JSON"
    assert not result["source_accepted"] and not result["comparison_ready"]
    assert len(result["adapter_numeric_type_differences"]) == 3
    assert not result["representation_differences"]


def test_exponent_case_only_is_recorded_as_lexical_not_numeric_change():
    original, ledger, rows = specimen()
    # A separate pinned synthetic assessment whose valid/original tokens use e.
    old = json.loads(ledger)
    view = RECON["comparison_view"](original, old)
    before = view.replace(b'"BSTAR":0.001234', b'"BSTAR":1.234e-3')
    # Keep exactly nine assessment edits: use ECC, DOT and BSTAR leading decimals.
    before = before.replace(b'"BSTAR":1.234e-3', b'"BSTAR":0.1234e-2')
    original = re.sub(
        rb'("(?:ECCENTRICITY|BSTAR|MEAN_MOTION_DOT)":)0\.', rb"\1.", before
    )
    edits = []
    for match in re.finditer(rb":(\.[0-9]+(?:e-2)?)(?=,)", original):
        start, stop = match.span(1)
        edits.append(
            {
                "start_byte_in_original": start,
                "stop_byte_exclusive_in_original": stop,
                "original_token": match[1].decode(),
                "probe_token": "0" + match[1].decode(),
            }
        )
    old.update(
        original_sha256=replay.digest(original),
        original_bytes=len(original),
        edits=edits,
        probe_sha256=replay.digest(before),
    )
    for row in rows:
        row["BSTAR"] = ".1234E-2"
    result = reconcile(original, replay.encoded(old), encoded(rows))
    assert result["semantic_match"]
    assert (
        sum(item["exponent_case_only"] for item in result["source_token_differences"])
        == 3
    )


@pytest.mark.parametrize(
    "kind", ["hidden_numeric", "precision", "reorder", "drop", "duplicate"]
)
def test_reconciliation_preserves_discrepancies_and_precision(kind):
    original, ledger, rows = specimen()
    if kind == "hidden_numeric":
        rows[0]["BSTAR"] = ".0012340000000000000000000001"
    elif kind == "precision":
        rows[0]["BSTAR"] = ".00123400"
    elif kind == "reorder":
        rows.reverse()
    elif kind == "drop":
        rows.pop()
    elif kind == "duplicate":
        rows.append(dict(rows[0]))
    result = reconcile(original, ledger, encoded(rows))
    if kind in {"precision", "reorder"}:
        assert result["semantic_match"]
        assert (
            result["representation_differences"]
            if kind == "precision"
            else not result["source_order_preserved"]
        )
    else:
        assert not result["semantic_match"] and result["status"] == "BLOCKED"
    assert not result["source_accepted"]


def test_csv_qualification_never_initializes_propagates_writes_or_calculates_residual(
    monkeypatch,
    forbid_swarm_residuals,
):
    def forbidden(*args, **kwargs):
        raise AssertionError("CSV diagnostics cannot perform scientific evaluation")

    for obj, name in (
        (Elements, "satellite"),
        (engine, "propagate_satellite"),
        (analysis, "position"),
        (analysis, "position_from_snapshot"),
        (celestrak, "parse_response"),
        (replay, "write_file"),
    ):
        monkeypatch.setattr(obj, name, forbidden)
    monkeypatch.setitem(
        QUALIFY["qualify"].__globals__, "historical_candidate", forbidden
    )
    original, ledger, rows = specimen()
    raw = encoded(rows)
    assert reconcile(original, ledger, raw)["semantic_match"]
    kin, val = SP3["package"](), SP3["package"]("VAL")
    result = QUALIFY["qualify"](
        kin,
        val,
        replay.digest(kin),
        replay.digest(val),
        csv_raw=raw,
        csv_sha256=replay.digest(raw),
    )
    assert result["historical_input"]["counts"]["candidate"] == 3
    assert len(result["qualification_gates"]) == 10
    assert result["qualification_gates"]["coordinate_frame"]["status"] == "BLOCKED"
    assert result["comparison_ready"] is False and result["residuals"] is None
    assert result["prediction_evaluations"] == 0 and not result["adapter_operational"]
    assert all(
        not item["pairing_approved"]
        for item in result["historical_input"][
            "actual_reference_epoch_bound_diagnostics"
        ]
    )


@pytest.mark.parametrize("kind", ["hash", "unpaired", "both"])
def test_qualification_refuses_ambiguous_or_unverified_source(kind):
    kin, val, raw = SP3["package"](), SP3["package"]("VAL"), encoded()
    kwargs = {"csv_raw": raw, "csv_sha256": replay.digest(raw)}
    if kind == "hash":
        kwargs["csv_sha256"] = "0" * 64
    elif kind == "unpaired":
        kwargs["csv_sha256"] = None
    else:
        kwargs["gp_raw"] = b"{}"
    with pytest.raises(QUALIFY["QualificationError"]):
        QUALIFY["qualify"](kin, val, replay.digest(kin), replay.digest(val), **kwargs)
