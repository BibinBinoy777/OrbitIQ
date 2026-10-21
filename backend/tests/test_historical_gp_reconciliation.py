"""Synthetic readiness tests. No provider attachment or real residual fixture."""

import copy
import json
import re
import runpy
from pathlib import Path

import pytest
from orbitiq import replay
from orbitiq.orbits import engine
from orbitiq.orbits.elements import Elements

ROOT = Path(__file__).resolve().parents[2]
TOOL = runpy.run_path(str(ROOT / "scripts/reconcile_historical_gp.py"))
GLOBALS = TOOL["reconcile"].__globals__
INTAKE = TOOL["INTAKE"]
FACTORY = runpy.run_path(str(Path(__file__).with_name("test_historical_gp_intake.py")))


def specimen():
    records = [
        FACTORY["synthetic"](
            EPOCH=epoch,
            ECCENTRICITY=0.000123,
            BSTAR=0.001234,
            MEAN_MOTION_DOT=0.012345,
        )
        for epoch in [
            "2013-12-31T00:00:00",
            "2014-01-01T00:00:00",
            "2014-01-02T00:00:00",
        ]
    ]
    valid = json.dumps(records, separators=(",", ":")).encode()
    # Deliberately malformed SYNTHETIC tokens; never repair the actual attachment.
    original = re.sub(
        rb'("(?:ECCENTRICITY|BSTAR|MEAN_MOTION_DOT)":)0\.', rb"\1.", valid
    )
    edits = []
    for match in re.finditer(rb":(\.\d+)(?=,)", original):
        start, stop = match.span(1)
        token = match[1].decode()
        edits.append(
            {
                "start_byte_in_original": start,
                "stop_byte_exclusive_in_original": stop,
                "original_token": token,
                "probe_token": "0" + token,
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
    return original, ledger, valid, records


def compare(original, ledger, replacement):
    assessment = replay.encoded(ledger)
    return TOOL["reconcile"](
        original,
        assessment,
        replacement,
        original_sha256=replay.digest(original),
        assessment_sha256=replay.digest(assessment),
        replacement_sha256=replay.digest(replacement),
    )


def test_absent_replacement_never_reads_or_replays_original(monkeypatch):
    def forbidden(*args):
        raise AssertionError("No real-data validation before replacement arrival")

    monkeypatch.setitem(GLOBALS, "checked", forbidden)
    monkeypatch.setitem(GLOBALS, "comparison_view", forbidden)
    result = TOOL["reconcile"](object(), object())
    assert result["reasons"] == ["corrected_provider_export_not_supplied"]
    assert result["original_count"] is None and result["residuals"] is None


def test_reordered_reformatted_replacement_retains_indices_without_approval():
    original, ledger, _, records = specimen()
    raw = json.dumps(list(reversed(records)), indent=3).encode()
    result = compare(original, ledger, raw)
    assert result["status"] == "PARTIAL" and result["semantic_match"]
    assert result["original_count"] == result["replacement_count"] == 3
    assert [
        (r["original_indices"], r["replacement_indices"])
        for r in result["matched_records"]
    ] == [([0], [2]), ([1], [1]), ([2], [0])]
    assert result["source_accepted"] is False and result["comparison_ready"] is False
    assert result["historical_availability"] is None
    assert result["replacement_inspection"]["provenance"]["missing"]


@pytest.mark.parametrize(
    "change",
    [
        "numeric",
        "field_added",
        "field_removed",
        "added_record",
        "removed_record",
        "identifier",
        "epoch",
    ],
)
def test_record_and_field_discrepancies_stop_acceptance(change):
    original, ledger, _, records = specimen()
    if change == "numeric":
        records[0]["BSTAR"] = 0.002345
    elif change == "field_added":
        records[0]["CREATION_DATE"] = "2014-01-01T00:00:00"
    elif change == "field_removed":
        del records[0]["CENTER_NAME"]
    elif change == "added_record":
        records.append({**records[0], "EPOCH": "2013-12-30T00:00:00"})
    elif change == "removed_record":
        records.pop()
    elif change == "identifier":
        records[0]["NORAD_CAT_ID"] = 25544
    elif change == "epoch":
        records[0]["EPOCH"] = "2013-12-31T01:00:00"
    result = compare(original, ledger, replay.encoded(records))
    assert result["status"] == "BLOCKED" and not result["semantic_match"]
    assert result["reasons"] and result["source_accepted"] is False


def test_decimal_difference_hidden_by_float_rounding_is_not_lost():
    original, ledger, raw, _ = specimen()
    replacement = raw.replace(
        b'"BSTAR":0.001234', b'"BSTAR":0.0012340000000000000000000001', 1
    )
    assert json.loads(raw)[0]["BSTAR"] == json.loads(replacement)[0]["BSTAR"]
    result = compare(original, ledger, replacement)
    assert result["status"] == "BLOCKED"
    assert result["field_differences"][0]["reason"] == "numeric_value_changed"


def test_equal_values_with_changed_precision_are_explicitly_reported():
    original, ledger, raw, _ = specimen()
    replacement = raw.replace(b'"BSTAR":0.001234', b'"BSTAR":0.00123400', 1)
    result = compare(original, ledger, replacement)
    assert result["semantic_match"] and result["status"] == "PARTIAL"
    assert result["representation_differences"][0]["field"] == "BSTAR"
    assert result["source_accepted"] is False


def test_unreviewed_nested_metadata_cannot_be_silently_compared_as_flat_gp():
    original, ledger, _, records = specimen()
    records[0]["EXTRA_METADATA"] = {"value": 1}
    result = compare(original, ledger, replay.encoded(records))
    assert result["status"] == "BLOCKED" and result["field_differences"]
    # Exercise the nested-field branch when both views contain nested metadata.
    simple = GLOBALS["comparison_view"]
    raw = replay.encoded(records)

    def same_nested_view(*args):
        return raw

    from unittest.mock import patch

    with patch.dict(GLOBALS, {"comparison_view": same_nested_view}):
        result = compare(original, ledger, raw)
    assert GLOBALS["comparison_view"] is simple
    assert result["status"] == "BLOCKED" and not result["semantic_match"]
    assert (
        result["field_differences"][0]["reason"]
        == "nested_field_requires_separate_review"
    )


@pytest.mark.parametrize(
    "kind",
    [
        "duplicate",
        "same_epoch_distinct",
        "mixed",
        "missing_epoch",
        "malformed",
        "nonfinite",
        "unsupported",
    ],
)
def test_duplicates_ambiguous_identity_and_invalid_records_cannot_match(kind):
    original, ledger, raw, records = specimen()
    if kind == "duplicate":
        records.append(copy.deepcopy(records[0]))
    elif kind == "same_epoch_distinct":
        records.append({**records[0], "BSTAR": 0.009876})
    elif kind == "mixed":
        records.append(None)
    elif kind == "missing_epoch":
        del records[1]["EPOCH"]
    elif kind == "malformed":
        raw = b"[.123]"
    elif kind == "nonfinite":
        raw = b"[NaN]"
    elif kind == "unsupported":
        raw = b"null"
    if kind not in {"malformed", "nonfinite", "unsupported"}:
        raw = replay.encoded(records)
    result = compare(original, ledger, raw)
    assert result["status"] == "BLOCKED" and not result["semantic_match"]
    if kind == "same_epoch_distinct":
        assert result["ambiguous_identities"]
    if kind == "mixed":
        assert result["replacement_inspection"]["counts"]["enumerated"] == 4
        assert result["replacement_inspection"]["records"][3]["source_index"] == 3


@pytest.mark.parametrize(
    "kind",
    [
        "count",
        "token",
        "offset",
        "overlap",
        "string",
        "value",
        "probe_hash",
        "original_hash",
    ],
)
def test_pinned_ledger_cannot_change_values_strings_or_unrelated_bytes(kind):
    original, ledger, raw, _ = specimen()
    edit = ledger["edits"][0]
    if kind == "count":
        ledger["edits"].pop()
    elif kind == "token":
        edit["original_token"] = ".9"
    elif kind == "offset":
        edit["start_byte_in_original"] += 1
    elif kind == "overlap":
        ledger["edits"][1] = copy.deepcopy(edit)
    elif kind == "string":
        start = original.index(b'"EPOCH"') + 1
        edit.update(
            start_byte_in_original=start, stop_byte_exclusive_in_original=start + 2
        )
    elif kind == "value":
        edit["probe_token"] = "0.9"
    elif kind == "probe_hash":
        ledger["probe_sha256"] = "0" * 64
    elif kind == "original_hash":
        ledger["original_sha256"] = "0" * 64
    result = compare(original, ledger, raw)
    assert result["status"] == "BLOCKED" and not result["semantic_match"]


def test_independent_hash_anchors_are_required():
    original, ledger, replacement, _ = specimen()
    assessment = replay.encoded(ledger)
    result = TOOL["reconcile"](
        original,
        assessment,
        replacement,
        original_sha256=replay.digest(original),
        assessment_sha256="0" * 64,
        replacement_sha256=replay.digest(replacement),
    )
    assert not result["semantic_match"]


@pytest.mark.parametrize(
    "assessment",
    [
        [],
        None,
        {"edits": None},
        {
            "kind": "orbitiq_historical_attachment_format_diagnostic",
            "edits": [None] * 9,
        },
    ],
)
def test_invalid_assessment_structure_returns_blocked_instead_of_crashing(assessment):
    original, _, replacement, _ = specimen()
    raw = replay.encoded(assessment)
    result = TOOL["reconcile"](
        original,
        raw,
        replacement,
        original_sha256=replay.digest(original),
        assessment_sha256=replay.digest(raw),
        replacement_sha256=replay.digest(replacement),
    )
    assert result["status"] == "BLOCKED" and not result["semantic_match"]


def test_synthetic_comparison_does_not_initialize_propagate_or_save_input(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No orbital evaluation or input writes")

    monkeypatch.setattr(Elements, "satellite", forbidden)
    monkeypatch.setattr(engine, "propagate_satellite", forbidden)
    monkeypatch.setattr(replay, "write_file", forbidden)
    original, ledger, raw, _ = specimen()
    result = compare(original, ledger, raw)
    assert result["semantic_match"] and result["prediction_evaluations"] == 0
    assert result["normalized_observations"] == [] and result["residuals"] is None
    assert result["adapter_operational"] is False


@pytest.mark.parametrize(
    "token", [b".123", b"-.123", b".123e-3", b"-.123E+2", b"1.", b"+0.123", b"01.23"]
)
def test_strict_intake_never_corrects_malformed_numeric_literals(token):
    raw = b'[{"MEAN_MOTION":' + token + b"}]"
    result = INTAKE["inspect_attachment"](raw)
    assert result["document_errors"] and result["records"] == []
    assert result["comparison_ready"] is False and result["residuals"] is None
