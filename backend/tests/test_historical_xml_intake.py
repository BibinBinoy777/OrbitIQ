"""E8.1.1 SYNTHETIC readiness controls, never acquired historical GP evidence."""

import copy
import hashlib
import json
import os
import runpy
import socket
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from orbitiq.orbits import engine
from orbitiq.orbits.elements import Elements

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "scripts/inspect_historical_xml.py"
TOOL = runpy.run_path(str(PATH))


@pytest.fixture(autouse=True)
def offline_static_only(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("XML intake must not use network, initialization or propagation")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(Elements, "satellite", forbidden)
    monkeypatch.setattr(engine, "propagate", forbidden)


def synthetic(**changes):
    # Reuse the established OMM numeric fixture, with invented G30 test labels.
    fields = json.loads((ROOT / "backend/tests/fixtures/vallado-leo.json").read_text())[
        0
    ]["omm"]
    fields.update(
        OBJECT_NAME="SYNTHETIC XML FORMAT TEST ONLY",
        OBJECT_ID="2014-008A",
        NORAD_CAT_ID=39533,
        EPOCH="2023-12-31T23:59:42Z",
        CENTER_NAME="EARTH",
        REF_FRAME="TEME",
        TIME_SYSTEM="UTC",
        MEAN_ELEMENT_THEORY="SGP4",
    )
    fields.update(changes)
    return fields


def source(records=None):
    root = ET.Element("ndm")
    for fields in records if records is not None else [synthetic()]:
        message = ET.SubElement(root, "omm", id="CCSDS_OMM_VERS", version="2.0")
        header = ET.SubElement(message, "header")
        ET.SubElement(header, "COMMENT").text = "SYNTHETIC TEST ONLY; NOT ACQUIRED DATA"
        ET.SubElement(header, "CREATION_DATE").text = "2026-10-24T00:00:00Z"
        ET.SubElement(header, "ORIGINATOR").text = "SYNTHETIC TEST GENERATOR"
        segment = ET.SubElement(ET.SubElement(message, "body"), "segment")
        metadata = ET.SubElement(segment, "metadata")
        data = ET.SubElement(segment, "data")
        nodes = {"metadata": metadata}
        for name in ("meanElements", "tleParameters"):
            nodes[name] = ET.SubElement(data, name)
        for name, allowed in TOOL["GROUPS"].items():
            for field in sorted(allowed):
                if field in fields:
                    ET.SubElement(nodes[name], field).text = str(fields[field])
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def inspect(raw=None, provenance=None):
    return TOOL["inspect_attachment"](
        source() if raw is None else raw, provenance, synthetic=True
    )


def changed(path, *, text=None, delete=False, attribute=None):
    root = ET.fromstring(source())
    node = root.find(path)
    if delete:
        parent = next(p for p in root.iter() if node in list(p))
        parent.remove(node)
    elif attribute:
        node.set(*attribute)
    else:
        node.text = text
    return ET.tostring(root)


def test_synthetic_valid_omm_uses_existing_conventions_without_scientific_acceptance():
    raw = source()
    report = inspect(raw)
    record = report["records"][0]
    assert (
        raw == source()
        and report["attachment_sha256"] == hashlib.sha256(raw).hexdigest()
    )
    assert report["attachment_bytes"] == len(raw) and report["record_count"] == 1
    assert report["evidence_class"] == "SYNTHETIC_TEST_ONLY"
    assert report["parsing_status"] == "VERIFIED" and not report["document_errors"]
    assert report["catalog_ids"] == [39533] and record["object_id"] == "2014-008A"
    assert record["epoch_source_text"] == "2023-12-31T23:59:42Z"
    assert record["static_candidate"] and record["protocol_temporal_eligible"]
    assert record["creation_utc"].startswith("2026-")
    assert (
        record["historically_available_at"] is None
        and record["publication_time_utc"] is None
    )
    assert report["latest_unique_static_candidate_index"] == 0
    assert (
        report["selected_source_index"] is None
        and report["selection_status"] == "BLOCKED"
    )
    assert report["status"] == report["scientific_status"] == "BLOCKED"
    assert (
        not report["comparison_ready"] and report["scientifically_accepted_count"] == 0
    )
    assert not report["propagation_executed"] and not report["residuals_calculated"]


@pytest.mark.parametrize(
    "raw,reason",
    [
        (b"<ndm>", "malformed_xml"),
        (b"<html><body>PRIVATE LOGIN CONTENT</body></html>", "not_supported_omm_xml"),
        (b"<ndm/>", "empty_or_oversized_omm_response"),
        (b"<other/>", "not_supported_omm_xml"),
        (b'<!DOCTYPE ndm [<!ENTITY secret "PRIVATE">]><ndm/>', "xml_doctype_forbidden"),
        (
            b'<!DOCTYPE ndm SYSTEM "file:///private/file"><ndm/>',
            "xml_doctype_forbidden",
        ),
        (b'<ndm xmlns="urn:unsupported"/>', "not_supported_omm_xml"),
        (b"<ndm>" * 14 + b"</ndm>" * 14, "xml_structure_budget_exceeded"),
    ],
)
def test_unsupported_or_unsafe_documents_are_refused_without_echoing_content(
    raw, reason
):
    report = inspect(raw)
    assert report["document_errors"] == [reason]
    assert report["parsing_status"] == "BLOCKED" and not report["records"]
    assert "PRIVATE" not in json.dumps(report)


@pytest.mark.parametrize("raw", [b"", b" " * (TOOL["INTAKE"]["MAX_BYTES"] + 1)])
def test_attachment_budget(raw):
    with pytest.raises(ValueError, match="byte_budget"):
        inspect(raw)


@pytest.mark.parametrize(
    "field,value",
    [
        ("NORAD_CAT_ID", 41019),
        ("OBJECT_ID", "2015-062A"),
    ],
)
def test_wrong_target_is_parsed_but_not_a_candidate(field, value):
    record = inspect(source([synthetic(**{field: value})]))["records"][0]
    assert record["structure_and_fields_valid"]
    assert not record["target_identity_matches"] and not record["static_candidate"]


def test_mixed_objects_are_all_reported_without_satellite_substitution():
    report = inspect(
        source([synthetic(), synthetic(NORAD_CAT_ID=41019, OBJECT_ID="2015-062A")])
    )
    assert report["record_count"] == 2 and report["catalog_ids"] == [39533, 41019]
    assert report["counts"]["static_candidates"] == 1
    assert report["records"][1]["exclusions"] == ["wrong_or_missing_target_identity"]
    assert report["selected_source_index"] is None


@pytest.mark.parametrize(
    "path,field",
    [
        (".//metadata/TIME_SYSTEM", "TIME_SYSTEM"),
        (".//metadata/CENTER_NAME", "CENTER_NAME"),
        (".//meanElements/MEAN_MOTION", "MEAN_MOTION"),
        (".//tleParameters/BSTAR", "BSTAR"),
    ],
)
def test_missing_required_fields_do_not_inherit_json_defaults(path, field):
    record = inspect(changed(path, delete=True))["records"][0]
    assert field in record["missing_required_fields"]
    assert not record["structure_and_fields_valid"] and not record["static_candidate"]


@pytest.mark.parametrize("field", ["CREATION_DATE", "ORIGINATOR"])
def test_missing_header_metadata_is_explicit(field):
    record = inspect(changed(".//header/" + field, delete=True))["records"][0]
    assert field in record["missing_header_metadata"]
    assert not record["static_candidate"]


@pytest.mark.parametrize(
    "value",
    [
        "not-a-time",
        "2023-02-30T00:00:00Z",
        "2023-12-31T23:59:60Z",
        "2023-12-31T23:59:42.0000001Z",
        "2023-12-31T23:59:42+01:00",
    ],
)
def test_invalid_epochs_are_not_repaired(value):
    record = inspect(source([synthetic(EPOCH=value)]))["records"][0]
    assert record["epoch_source_text"] == value
    assert record["epoch_utc"] is None and not record["static_candidate"]
    assert "invalid_epoch" in record["validation_errors"]


def test_invalid_creation_time_is_separate_from_valid_epoch():
    record = inspect(changed(".//CREATION_DATE", text="yesterday"))["records"][0]
    assert record["epoch_utc"] and record["creation_utc"] is None
    assert "invalid_creation_date" in record["validation_errors"]


@pytest.mark.parametrize(
    "epoch,in_request,eligible",
    [
        ("2023-12-24T23:59:59Z", False, False),
        ("2023-12-25T23:44:41.999999Z", True, False),
        ("2023-12-25T23:44:42Z", True, True),
        ("2023-12-31T23:59:42Z", True, True),
        ("2023-12-31T23:59:42.000001Z", True, False),
        ("2024-01-01T00:00:00Z", False, False),
    ],
)
def test_request_scope_and_exact_protocol_bounds_remain_separate(
    epoch, in_request, eligible
):
    record = inspect(source([synthetic(EPOCH=epoch)]))["records"][0]
    assert record["in_requested_interval"] is in_request
    assert record["protocol_temporal_eligible"] is eligible


def test_duplicate_records_and_same_epoch_conflicts_block_without_fallback():
    records = [synthetic(EPOCH="2023-12-30T00:00:00Z"), synthetic(), synthetic()]
    report = inspect(source(records))
    assert report["duplicate_groups"] == [[1, 2]]
    assert report["records"][1]["duplicate_source_indices"] == [2]
    assert report["latest_unique_static_candidate_index"] is None
    assert "same_epoch_ambiguity_no_fallback" in report["selection_status"]
    records[2]["ELEMENT_SET_NO"] += 1
    report = inspect(source(records))
    assert not report["duplicate_groups"]
    assert report["latest_unique_static_candidate_index"] is None


def test_latest_unique_static_candidate_uses_epoch_not_source_order():
    report = inspect(
        source(
            [
                synthetic(EPOCH="2023-12-26T00:00:00Z"),
                synthetic(),
                synthetic(EPOCH="2023-12-30T00:00:00Z"),
            ]
        )
    )
    assert report["latest_unique_static_candidate_index"] == 1
    assert report["selected_source_index"] is None
    assert report["time_coverage_utc"]["start"].startswith("2023-12-26")


def test_duplicate_fields_unknown_groups_and_bad_units_are_refused():
    root = ET.fromstring(source())
    ET.SubElement(root.find(".//metadata"), "TIME_SYSTEM").text = "GPS"
    assert inspect(ET.tostring(root))["document_errors"] == ["duplicate_xml_field"]
    root = ET.fromstring(source())
    ET.SubElement(root.find(".//data"), "covarianceMatrix")
    assert inspect(ET.tostring(root))["document_errors"] == ["unexpected_xml_structure"]
    report = inspect(changed(".//MEAN_MOTION", attribute=("units", "rad/sec")))
    assert "unsupported_explicit_units" in report["records"][0]["validation_errors"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("MEAN_MOTION", "NaN"),
        ("BSTAR", "1e9999"),
        ("ECCENTRICITY", "2"),
        ("NORAD_CAT_ID", "39533.0"),
    ],
)
def test_numeric_and_existing_model_refusals(field, value):
    record = inspect(source([synthetic(**{field: value})]))["records"][0]
    assert record["field_failures"] and not record["static_candidate"]


def test_operator_receipt_is_never_fabricated_from_creation_epoch_or_file_time():
    assert inspect()["provenance"]["asserted"]["received_at"] is None
    report = inspect(provenance={"received_at": "2026-10-24T12:00:00+05:30"})
    assert (
        report["provenance"]["asserted"]["received_at"] == "2026-10-24T06:30:00+00:00"
    )
    assert not report["provenance"]["availability_inferred_from_epoch_or_receipt"]
    assert report["records"][0]["historically_available_at"] is None
    with pytest.raises(ValueError):
        inspect(provenance={"received_at": "2026-10-24"})


def command(tmp_path, attachment, *extra):
    archive = tmp_path / "private"
    archive.mkdir(mode=0o700, exist_ok=True)
    return subprocess.run(
        [
            sys.executable,
            str(PATH),
            "--attachment",
            str(attachment),
            "--archive-root",
            str(archive),
            "--synthetic",
            *extra,
        ],
        env={**os.environ, "PYTHONPATH": str(ROOT / "backend")},
        capture_output=True,
        text=True,
        timeout=20,
    )


def test_cli_missing_empty_symlink_and_hash_mismatch_are_safe(tmp_path):
    missing = tmp_path / "MISSING_PRIVATE_FILENAME.xml"
    for p in (missing, tmp_path / "empty.xml"):
        if p != missing:
            p.write_bytes(b"")
        result = command(tmp_path, p)
        assert result.returncode == 1 and "intake_refused" in result.stdout
        assert "PRIVATE_FILENAME" not in result.stdout + result.stderr
    original = tmp_path / "synthetic.xml"
    original.write_bytes(source())
    link = tmp_path / "link.xml"
    link.symlink_to(original)
    assert command(tmp_path, link).returncode == 1
    assert command(tmp_path, original, "--expected-sha256", "0" * 64).returncode == 1
    assert not list((tmp_path / "private").iterdir())


def test_cli_preserves_original_and_prior_private_capture(
    tmp_path,
):
    original = tmp_path / "synthetic.xml"
    raw = source()
    original.write_bytes(raw)
    before = original.stat().st_mtime_ns
    outputs = []
    for _ in range(2):
        result = command(tmp_path, original)
        assert result.returncode == 0, result.stderr
        summary = json.loads(result.stdout)
        assert (
            summary["evidence_class"] == "SYNTHETIC_TEST_ONLY"
            and not summary["comparison_ready"]
        )
        assert original.read_bytes() == raw and original.stat().st_mtime_ns == before
        captures = sorted((tmp_path / "private").iterdir())
        outputs = captures
    assert len(outputs) == 2
    for capture in outputs:
        assert capture.stat().st_mode & 0o777 == 0o700
        assert (capture / "attachment.original").read_bytes() == raw
        report = json.loads((capture / "inspection.json").read_text())
        assert report["evidence_class"] == "SYNTHETIC_TEST_ONLY"
        assert report["provenance"]["asserted"]["received_at"] is None
        assert report["selected_source_index"] is None
        assert (
            json.loads((capture / "receipt.json").read_text())["input_basename"]
            == "synthetic.xml"
        )
        for name, expected in json.loads((capture / "manifest.json").read_text())[
            "files"
        ].items():
            body = (capture / name).read_bytes()
            assert (
                len(body) == expected["bytes"]
                and hashlib.sha256(body).hexdigest() == expected["sha256"]
            )


def test_cli_malformed_attachment_is_preserved_but_refused(tmp_path):
    path = tmp_path / "malformed-synthetic.xml"
    path.write_bytes(b"<ndm>")
    result = command(tmp_path, path)
    assert result.returncode == 1
    assert json.loads(result.stdout)["document_errors"] == ["malformed_xml"]
    capture = next((tmp_path / "private").iterdir())
    assert (capture / "attachment.original").read_bytes() == b"<ndm>"


@pytest.mark.parametrize("encoding", ["unknown-private-encoding", "UTF-32"])
def test_unsupported_encoding_does_not_leak_parser_errors(encoding):
    raw = f'<?xml version="1.0" encoding="{encoding}"?><ndm/>'.encode()
    assert inspect(raw)["document_errors"] == ["malformed_xml"]


def test_single_omm_and_multiple_segments_use_the_locked_library_reader():
    root = ET.fromstring(source())
    message = root.find("omm")
    assert inspect(ET.tostring(message))["record_count"] == 1
    body = message.find("body")
    second = copy.deepcopy(body.find("segment"))
    second.find(".//EPOCH").text = "2023-12-30T00:00:00Z"
    body.append(second)
    report = inspect(ET.tostring(root))
    assert report["record_count"] == 2
    assert report["latest_unique_static_candidate_index"] == 0


@pytest.mark.parametrize(
    "field,unit",
    [
        ("MEAN_MOTION", "rev/day"),
        ("INCLINATION", "deg"),
        ("BSTAR", "1/ER"),
        ("MEAN_MOTION_DOT", "rev/day**2"),
    ],
)
def test_recognized_explicit_units(field, unit):
    report = inspect(changed(".//" + field, attribute=("units", unit)))
    assert report["records"][0]["static_candidate"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("REF_FRAME", "ITRS"),
        ("TIME_SYSTEM", "GPS"),
        ("MEAN_ELEMENT_THEORY", "OTHER"),
        ("CENTER_NAME", "MARS"),
        ("EPHEMERIS_TYPE", 4),
    ],
)
def test_unsupported_model_declarations_stay_excluded(field, value):
    record = inspect(source([synthetic(**{field: value})]))["records"][0]
    assert not record["static_candidate"] and record["field_failures"]


def test_schema_hint_is_never_fetched_and_synthetic_label_is_only_a_label():
    raw = changed(
        "omm", attribute=(TOOL["SCHEMA_HINT"], "https://invalid.example/schema.xsd")
    )
    report = inspect(raw)
    assert report["parsing_status"] == "VERIFIED"
    unlabelled = TOOL["inspect_attachment"](raw)
    assert unlabelled["evidence_class"] == "UNVERIFIED_LOCAL_ATTACHMENT"
    assert unlabelled["scientific_status"] == "BLOCKED"
    assert unlabelled["selected_source_index"] is None


def test_no_candidate_no_header_and_blank_required_fields_are_explicit():
    report = inspect(source([synthetic(EPOCH="2026-10-24T00:00:00Z")]))
    assert report["counts"]["static_candidates"] == 0
    assert report["latest_unique_static_candidate_index"] is None
    record = inspect(changed(".//header", delete=True))["records"][0]
    assert record["missing_header_metadata"] == ["CREATION_DATE", "ORIGINATOR"]
    record = inspect(changed(".//OBJECT_NAME", text=""))["records"][0]
    assert "OBJECT_NAME" in record["missing_required_fields"]
    assert not record["static_candidate"]


def test_resource_limits_and_nonprivate_archive_are_refused(tmp_path, monkeypatch):
    glob = TOOL["document"].__globals__
    monkeypatch.setitem(glob["INTAKE"], "MAX_RECORDS", 1)
    assert inspect(source([synthetic(), synthetic()]))["document_errors"] == [
        "empty_or_oversized_omm_response"
    ]
    raw = changed(".//OBJECT_NAME", text="x" * (TOOL["CSV"]["MAX_CELL"] + 1))
    assert inspect(raw)["document_errors"] == ["xml_field_budget"]
    original = tmp_path / "synthetic.xml"
    original.write_bytes(source())
    archive = tmp_path / "private"
    archive.mkdir(mode=0o755)
    archive.chmod(0o755)
    assert command(tmp_path, original).returncode == 1
    assert original.read_bytes() == source() and not list(archive.iterdir())


# E8.7.1 SYNTHETIC controls: invented labels on reused numeric test fields.
# No input here was acquired from a historical GPS provider.
def g05(**changes):
    return synthetic(NORAD_CAT_ID=35752, OBJECT_ID="2009-043A", **changes)


def inspect_g05(raw=None):
    return TOOL["inspect_attachment"](
        source([g05()]) if raw is None else raw, synthetic=True, norad_id=35752
    )


def test_synthetic_g05_explicit_target_and_arbitrary_name_are_diagnostic_only():
    raw = source([g05(OBJECT_NAME="SYNTHETIC UNRELATED DISPLAY LABEL")])
    report = inspect_g05(raw)
    r = report["records"][0]
    assert report["policy"]["target_norad_id"] == 35752
    assert report["policy"]["target_cospar_id"] == "2009-043A"
    assert report["policy"]["target_svn"] == "G050"
    assert r["static_candidate"] and report["document_identity_matches"]
    assert r["identity_checks"]["svn_check"] == "not_available_in_supported_omm_schema"
    assert report["evidence_class"] == "SYNTHETIC_TEST_ONLY"
    assert report["scientific_status"] == "BLOCKED"
    assert report["selected_source_index"] is None
    assert not report["comparison_ready"]
    assert not report["propagation_executed"] and not report["residuals_calculated"]
    assert inspect_g05(raw)["attachment_sha256"] == hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize(
    "field,value",
    [
        ("NORAD_CAT_ID", 39533),
        ("OBJECT_ID", "2014-008A"),
        ("NORAD_CAT_ID", "35752.0"),
        ("OBJECT_ID", "not-cospar"),
    ],
)
def test_synthetic_g05_wrong_or_malformed_identity_never_qualifies(field, value):
    fields = g05()
    fields[field] = value
    report = inspect_g05(source([fields]))
    assert not report["document_identity_matches"]
    assert not report["records"][0]["static_candidate"]
    assert not report["records"][0]["target_identity_matches"]


@pytest.mark.parametrize("field", ["NORAD_CAT_ID", "OBJECT_ID", "OBJECT_NAME"])
def test_synthetic_g05_missing_identity_is_explicit(field):
    fields = g05()
    del fields[field]
    r = inspect_g05(source([fields]))["records"][0]
    assert field in r["missing_required_fields"]
    assert not r["static_candidate"]


def test_synthetic_g05_mixed_objects_and_no_silent_default_substitution():
    raw = source([g05(), synthetic()])
    report = inspect_g05(raw)
    assert report["mixed_object_content"]
    assert not report["document_identity_matches"]
    assert report["catalog_ids"] == [35752, 39533]
    assert report["counts"]["static_candidates"] == 1  # Per-record diagnostic only.
    assert report["selected_source_index"] is None
    assert not inspect(source([g05()]))["records"][0]["static_candidate"]
    assert not inspect_g05(source())["records"][0]["static_candidate"]


@pytest.mark.parametrize("conflict", [False, True])
def test_synthetic_g05_duplicate_or_conflicting_latest_epoch_never_falls_back(conflict):
    a = g05()
    b = dict(a)
    if conflict:
        b["MEAN_ANOMALY"] = (float(b["MEAN_ANOMALY"]) + 1) % 360
    report = inspect_g05(source([g05(EPOCH="2023-12-30T00:00:00Z"), a, b]))
    assert report["latest_unique_static_candidate_index"] is None
    assert "same_epoch_ambiguity" in report["selection_status"]
    assert report["same_epoch_conflict_groups"] == ([[1, 2]] if conflict else [])
    assert report["duplicate_groups"] == ([] if conflict else [[1, 2]])


@pytest.mark.parametrize(
    "epoch,eligible",
    [
        ("2023-12-25T23:44:41.999999Z", False),
        ("2023-12-25T23:44:42Z", True),
        ("2023-12-31T23:59:42Z", True),
        ("2023-12-31T23:59:42.000001Z", False),
        ("2023-12-31T23:59:42.0000001Z", False),
        ("not-a-time", False),
    ],
)
def test_synthetic_g05_exact_bounds_and_no_rounding(epoch, eligible):
    r = inspect_g05(source([g05(EPOCH=epoch)]))["records"][0]
    assert r["epoch_source_text"] == epoch
    assert r["static_candidate"] is eligible


@pytest.mark.parametrize("raw", [b"<ndm>", b"<ndm/>", b"<html>LOGIN</html>"])
def test_synthetic_g05_bad_documents_stay_blocked(raw):
    report = inspect_g05(raw)
    assert report["document_errors"]
    assert report["policy"]["target_norad_id"] == 35752
    assert report["scientific_status"] == "BLOCKED"


@pytest.mark.parametrize("target", [None, True, "35752", 12345])
def test_synthetic_unsupported_configuration_is_not_guessed(target):
    with pytest.raises(ValueError, match="unsupported_target"):
        TOOL["inspect_attachment"](source(), synthetic=True, norad_id=target)


def test_synthetic_g05_cli_capture_hashes_and_default_g30_regression(tmp_path):
    p = tmp_path / "synthetic-g05.xml"
    raw = source([g05()])
    p.write_bytes(raw)
    before = p.stat().st_mtime_ns
    for _ in range(2):
        result = command(tmp_path, p, "--norad-id", "35752")
        assert result.returncode == 0, result.stderr
        output = json.loads(result.stdout)
        assert output["target_norad_id"] == 35752
        assert output["document_identity_matches"]
        assert output["attachment_sha256"] == hashlib.sha256(raw).hexdigest()
        assert output["evidence_class"] == "SYNTHETIC_TEST_ONLY"
    assert p.read_bytes() == raw and p.stat().st_mtime_ns == before
    for capture in (tmp_path / "private").iterdir():
        assert (capture / "attachment.original").read_bytes() == raw
        report = json.loads((capture / "inspection.json").read_text())
        assert report["provenance"]["asserted"]["received_at"] is None
        assert report["selected_source_index"] is None
    p.write_bytes(source())
    default = json.loads(command(tmp_path, p).stdout)
    assert default["target_norad_id"] == 39533 and default["document_identity_matches"]
    result = command(tmp_path, p, "--norad-id", "99999")
    assert result.returncode == 2  # argparse rejects before capture.
    assert len(list((tmp_path / "private").iterdir())) == 3
