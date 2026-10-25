"""SYNTHETIC policy controls. No genuine GP bytes or observed states in fixtures."""

import copy
import hashlib
import json
import runpy
import socket
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from orbitiq.orbits import coordinates, engine
from orbitiq.orbits.elements import Elements

ROOT = Path(__file__).resolve().parents[2]
TOOL = runpy.run_path(str(ROOT / "scripts/inspect_historical_xml.py"))
BASE = runpy.run_path(str(ROOT / "backend/tests/test_historical_xml_intake.py"))
STRICT = TOOL["STRICT_POLICY"]
RETRO = TOOL["RETROSPECTIVE_POLICY"]
ADMITTED = "ADMITTED_FOR_FURTHER_SCIENTIFIC_QUALIFICATION"


@pytest.fixture(autouse=True)
def no_scientific_or_network_operations(monkeypatch):
    def forbidden(*a, **k):
        pytest.fail(
            "Synthetic intake must not initialize, propagate, transform or fetch"
        )

    monkeypatch.setattr(Elements, "satellite", forbidden)
    monkeypatch.setattr(engine, "propagate", forbidden)
    monkeypatch.setattr(engine, "propagate_satellite", forbidden)
    monkeypatch.setattr(coordinates, "earth_fixed", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def synthetic_raw(norad=39533, epochs=None, changes=None):
    records = []
    for i, epoch in enumerate(epochs or ["2023-12-31T23:59:42Z"]):
        row = BASE["synthetic"](
            NORAD_CAT_ID=norad,
            OBJECT_ID="2009-043A" if norad == 35752 else "2014-008A",
            EPOCH=epoch,
            REV_AT_EPOCH=100 + i,  # Invented counter, never historical evidence.
        )
        row.update(changes or {})
        records.append(row)
    root = ET.fromstring(BASE["source"](records))
    for header in root.findall(".//header"):
        header.find("CREATION_DATE").text = None
        header.find("ORIGINATOR").text = None
    return ET.tostring(root)


@pytest.fixture
def authorize_synthetic(monkeypatch):
    """Private test dependency injection; no CLI/config override exists in production.

    Synthetic bytes cannot have the real artifact hashes. Only the test's loader
    result is replaced, leaving the immutable production definition untouched.
    The acquisition witness remains the reviewed public ledger, not private data.
    """
    production, _ = TOOL["_load_retrospective_policy"]()

    def setup(raw, norad=39533, mutate=None):
        policy = copy.deepcopy(production)
        artifact = next(a for a in policy["artifacts"] if a["norad_id"] == norad)
        artifact["sha256"] = hashlib.sha256(raw).hexdigest()
        artifact["bytes"] = len(raw)
        artifact["expected_record_count"] = len(ET.fromstring(raw).findall("omm"))
        policy["artifacts"] = [artifact]
        if mutate:
            mutate(policy, artifact)
        digest = hashlib.sha256(json.dumps(policy, sort_keys=True).encode()).hexdigest()
        monkeypatch.setitem(
            TOOL["inspect_attachment"].__globals__,
            "_load_retrospective_policy",
            lambda: (copy.deepcopy(policy), digest),
        )
        return policy

    return setup


def inspect(raw, norad=39533, policy=RETRO):
    return TOOL["inspect_attachment"](
        raw, synthetic=True, norad_id=norad, admission_policy=policy
    )


def test_production_definition_has_only_two_authorized_artifacts_and_pinned_witnesses():
    policy, digest = TOOL["_load_retrospective_policy"]()
    assert digest == TOOL["POLICY_SHA256"]
    assert policy["id"] == RETRO and policy["version"] == 1
    assert {
        a["norad_id"]: (a["sha256"], a["bytes"], a["expected_record_count"])
        for a in policy["artifacts"]
    } == {
        35752: (
            "c398ecdc707013d0c9bf245b9eeb1894aef1f2a7bafd60f9a687ce797e0a0828",
            10072,
            10,
        ),
        39533: (
            "34ccec7bd8fd4be88346e03787027a5ecc71a6d75db75668bd4c641fcd713da5",
            11057,
            11,
        ),
    }
    assert all(
        TOOL["_acquisition_evidence_valid"](a["acquisition_evidence"])
        for a in policy["artifacts"]
    )


@pytest.mark.parametrize("norad", [35752, 39533])
def test_synthetic_authorization_explicitly_admits_with_partial_metadata_only(
    authorize_synthetic, norad
):
    raw = synthetic_raw(norad)
    authorize_synthetic(raw, norad)
    r = inspect(raw, norad)
    assert r["evidence_class"] == "SYNTHETIC_TEST_ONLY"
    assert r["admission_policy_id"] == RETRO and r["strict_policy_id"] == STRICT
    assert r["counts"]["static_candidates"] == 0
    row = r["records"][0]
    assert row["strict_policy_outcome"] == "REJECTED_STATIC_CANDIDATE"
    assert row["retrospective_admission"]["disposition"] == ADMITTED
    assert row["retrospective_admission"]["metadata_status"].startswith("PARTIAL")
    assert row["retrospective_admission"]["reference_epochs_checked"] == 96
    assert row["creation_utc"] is row["publication_time_utc"] is None
    assert r["retrospective_admission"]["counts"] == {
        "admitted": 1,
        "held": 0,
        "rejected": 0,
    }
    assert r["selected_source_index"] is None and not r["comparison_ready"]
    assert r["scientifically_accepted_count"] == 0
    assert not r["retrospective_admission"]["comparison_authorized"]


@pytest.mark.parametrize("norad", [35752, 39533])
def test_strict_default_retains_prior_behavior_and_unknown_hash_never_gets_exception(
    norad,
):
    raw = synthetic_raw(norad)
    strict = TOOL["inspect_attachment"](raw, synthetic=True, norad_id=norad)
    assert strict["admission_policy_id"] == STRICT
    assert strict["counts"]["static_candidates"] == 0
    assert strict["retrospective_admission"]["status"] == "NOT_REQUESTED"
    refused = inspect(raw, norad)
    assert refused["retrospective_admission"]["status"] == "REFUSED"
    assert refused["retrospective_admission"]["refusal_reasons"] == [
        "input_hash_not_authorized"
    ]
    assert refused["retrospective_admission"]["counts"]["admitted"] == 0


@pytest.mark.parametrize("case", ["target", "identity", "count", "size", "evidence"])
def test_synthetic_artifact_scope_checks_reject_mismatch(authorize_synthetic, case):
    raw = synthetic_raw()

    def mutate(policy, artifact):
        if case == "target":
            artifact["norad_id"] = 35752
        elif case == "identity":
            artifact["cospar_id"] = "2009-043A"
        elif case == "count":
            artifact["expected_record_count"] += 1
        elif case == "size":
            artifact["bytes"] += 1
        else:
            artifact["acquisition_evidence"]["sha256"] = "0" * 64

    authorize_synthetic(raw, mutate=mutate)
    r = inspect(raw)
    assert r["retrospective_admission"]["status"] == "REFUSED"
    assert r["retrospective_admission"]["refusal_reasons"]
    assert r["retrospective_admission"]["counts"]["admitted"] == 0


def test_synthetic_changed_bytes_and_bad_xml_are_refused(authorize_synthetic):
    raw = synthetic_raw()
    authorize_synthetic(raw)
    for bad in [raw + b" ", b"<ndm>", b"<html>LOGIN</html>"]:
        r = inspect(bad)
        assert r["retrospective_admission"]["status"] == "REFUSED"
        assert r["retrospective_admission"]["counts"]["admitted"] == 0


@pytest.mark.parametrize(
    "epoch,admitted",
    [
        ("2023-12-25T23:44:41.999999Z", False),
        ("2023-12-25T23:44:42Z", True),
        ("2023-12-31T23:59:42Z", True),
        ("2023-12-31T23:59:42.000001Z", False),
        ("2023-12-31T23:59:42.0000001Z", False),
    ],
)
def test_synthetic_full96_guard_boundaries_and_forward_only(
    authorize_synthetic, epoch, admitted
):
    raw = synthetic_raw(epochs=[epoch])
    authorize_synthetic(raw)
    r = inspect(raw)["records"][0]["retrospective_admission"]
    assert (r["disposition"] == ADMITTED) is admitted
    assert r["reference_epochs_checked"] == 96
    if admitted:
        assert r["age_guard_pass_count"] == 96


@pytest.mark.parametrize(
    "damage",
    [
        "missing_creation",
        "bad_creation",
        "extra_empty_header",
        "bad_numeric",
        "bad_frame",
        "nil",
    ],
)
def test_synthetic_header_exception_never_waives_other_rules(
    authorize_synthetic, damage
):
    root = ET.fromstring(synthetic_raw())
    if damage == "missing_creation":
        h = root.find(".//header")
        h.remove(h.find("CREATION_DATE"))
    elif damage == "bad_creation":
        root.find(".//CREATION_DATE").text = "yesterday"
    elif damage == "extra_empty_header":
        ET.SubElement(root.find(".//header"), "MESSAGE_ID")
    elif damage == "bad_numeric":
        root.find(".//MEAN_MOTION").text = "NaN"
    elif damage == "bad_frame":
        root.find(".//REF_FRAME").text = "ITRS"
    else:
        root.find(".//CREATION_DATE").set(
            "{http://www.w3.org/2001/XMLSchema-instance}nil", "true"
        )
    raw = ET.tostring(root)
    authorize_synthetic(raw)
    r = inspect(raw)
    assert r["retrospective_admission"]["counts"]["admitted"] == 0
    assert (
        r["retrospective_admission"]["status"] == "REFUSED"
        or r["records"][0]["retrospective_admission"]["disposition"] == "REJECTED"
    )


def test_synthetic_g05_conflicts_in_and_outside_window_are_not_conflated(
    authorize_synthetic,
):
    epochs = [
        "2023-12-25T21:00:00Z",
        "2023-12-25T21:00:00Z",
        "2023-12-27T00:00:00Z",
        "2023-12-28T00:00:00Z",
        "2023-12-28T00:00:00Z",
        "2023-12-29T00:00:00Z",
        "2023-12-29T12:00:00Z",
        "2023-12-30T00:00:00Z",
        "2023-12-31T00:00:00Z",
        "2023-12-31T12:00:00Z",
    ]
    raw = synthetic_raw(35752, epochs)
    authorize_synthetic(raw, 35752)
    r = inspect(raw, 35752)
    assert r["same_epoch_conflict_groups"] == [[0, 1], [3, 4]]
    assert r["retrospective_admission"]["counts"] == {
        "admitted": 6,
        "held": 2,
        "rejected": 2,
    }
    assert [
        x["source_index"]
        for x in r["records"]
        if x["retrospective_admission"]["disposition"] == "HOLD"
    ] == [3, 4]
    assert [
        r["records"][i]["retrospective_admission"]["disposition"] for i in [0, 1]
    ] == ["REJECTED"] * 2


def test_synthetic_g30_all_epoch_failures_remain_rejected(authorize_synthetic):
    epochs = ["2023-12-25T06:00:00Z", "2023-12-25T07:00:00Z"] + [
        f"2023-12-26T{i:02d}:00:00Z" for i in range(9)
    ]
    raw = synthetic_raw(epochs=epochs)
    authorize_synthetic(raw)
    r = inspect(raw)
    assert r["retrospective_admission"]["counts"] == {
        "admitted": 9,
        "held": 0,
        "rejected": 2,
    }
    assert all(
        x["retrospective_admission"]["age_guard_pass_count"] < 96
        for x in r["records"][:2]
    )
    assert r["selected_source_index"] is None


def test_synthetic_exact_duplicates_are_held_without_deduplication(authorize_synthetic):
    root = ET.fromstring(synthetic_raw())
    root.append(copy.deepcopy(root[0]))
    raw = ET.tostring(root)
    authorize_synthetic(raw)
    r = inspect(raw)
    assert r["duplicate_groups"] == [[0, 1]]
    assert r["record_count"] == 2
    assert r["retrospective_admission"]["counts"] == {
        "admitted": 0,
        "held": 2,
        "rejected": 0,
    }


def test_definition_tampering_fails_closed_and_cannot_affect_default_strict(
    tmp_path, monkeypatch
):
    path = tmp_path / "SYNTHETIC-tampered-policy.json"
    path.write_text("{}")
    monkeypatch.setitem(TOOL["inspect_attachment"].__globals__, "POLICY_PATH", path)
    r = inspect(synthetic_raw())
    assert r["retrospective_admission"]["status"] == "REFUSED"
    assert r["retrospective_admission"]["counts"]["admitted"] == 0
    assert (
        inspect(synthetic_raw(), policy=STRICT)["retrospective_admission"]["status"]
        == "NOT_REQUESTED"
    )


def test_synthetic_cli_explicit_policy_recording_repeatable_reports_and_no_mutation(
    authorize_synthetic, tmp_path, capsys
):
    raw = synthetic_raw(35752)
    authorize_synthetic(raw, 35752)
    p = tmp_path / "SYNTHETIC-g05.xml"
    p.write_bytes(raw)
    mtime = p.stat().st_mtime_ns
    archive = tmp_path / "private"
    archive.mkdir(mode=0o700)
    results = []
    for _ in range(2):
        assert (
            TOOL["main"](
                [
                    "--attachment",
                    str(p),
                    "--archive-root",
                    str(archive),
                    "--norad-id",
                    "35752",
                    "--admission-policy",
                    RETRO,
                    "--synthetic",
                ]
            )
            == 0
        )
        output = json.loads(capsys.readouterr().out)
        assert output["admission_policy_id"] == RETRO
        assert output["admission_counts"]["admitted"] == 1
    for capture in archive.iterdir():
        results.append(json.loads((capture / "inspection.json").read_text()))
        assert (capture / "attachment.original").read_bytes() == raw
    assert results[0] == results[1]
    assert p.read_bytes() == raw and p.stat().st_mtime_ns == mtime


@pytest.mark.parametrize("mixed", [False, True])
def test_synthetic_actual_record_identity_mismatch_refuses_whole_artifact(
    authorize_synthetic, mixed
):
    if mixed:
        root = ET.fromstring(synthetic_raw())
        other = ET.fromstring(synthetic_raw(35752))
        root.append(other[0])
        raw = ET.tostring(root)
    else:
        raw = synthetic_raw(changes={"NORAD_CAT_ID": 35752, "OBJECT_ID": "2009-043A"})
    authorize_synthetic(raw)  # Authorized synthetic bytes, still bound to NORAD39533.
    r = inspect(raw)
    assert r["retrospective_admission"]["status"] == "REFUSED"
    assert (
        "authorized_record_identity_mismatch"
        in r["retrospective_admission"]["refusal_reasons"]
    )
    assert r["retrospective_admission"]["counts"]["admitted"] == 0


def test_synthetic_unknown_hash_cli_refusal_is_explicit_and_still_preserves_bytes(
    tmp_path,
):
    p = tmp_path / "SYNTHETIC-unknown.xml"
    raw = synthetic_raw()
    p.write_bytes(raw)
    result = BASE["command"](tmp_path, p, "--admission-policy", RETRO)
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert (
        output["admission_policy_id"] == RETRO
        and output["admission_policy_version"] == 1
    )
    assert output["retrospective_status"] == "REFUSED"
    assert output["policy_refusal_reasons"] == ["input_hash_not_authorized"]
    assert output["admission_counts"]["admitted"] == 0
    assert p.read_bytes() == raw
    captures = list((tmp_path / "private").iterdir())
    assert (
        len(captures) == 1 and (captures[0] / "attachment.original").read_bytes() == raw
    )


def test_synthetic_reference_policy_mismatch_cannot_relax_guard(authorize_synthetic):
    raw = synthetic_raw()
    authorize_synthetic(raw, mutate=lambda p, a: p["reference"].update(epoch_count=1))
    r = inspect(raw)
    assert r["retrospective_admission"]["status"] == "REFUSED"
    assert r["retrospective_admission"]["counts"]["admitted"] == 0
