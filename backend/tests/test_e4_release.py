"""Release evidence failure probes use fake metadata and isolated Git/artifacts."""

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "release_evidence", Path(__file__).parents[2] / "scripts/verify_release_evidence.py"
)
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


@pytest.fixture
def artifacts(tmp_path):
    browser = tmp_path / "browser"
    browser.mkdir()
    (tmp_path / "proxy.json").write_text(
        json.dumps(
            {
                "status": "PASS",
                "tls_verified": True,
                "archive_unchanged": True,
                "checks": [{}] * 10,
            }
        )
    )
    (browser / "summary.json").write_text(
        json.dumps(
            {
                "status": "PASS",
                "engineering_e2": True,
                "fixture_unchanged": True,
                "pdf_checks": 7,
                "additional_fault_injection_cases": 5,
                "fixture_kind": "SYNTHETIC TEST ONLY",
                "total_flows": 3,
                "browser_flows": {"chromium": 1, "firefox": 1, "webkit": 1},
            }
        )
    )
    (browser / "commands.json").write_text(
        json.dumps(
            [
                {"expected_failure": True, "exit_code": 1},
                {"expected_failure": True, "exit_code": 1},
                {"expected_failure": False, "exit_code": 0},
            ]
        )
    )
    for engine in ["chromium", "firefox", "webkit"]:
        folder = browser / f"{engine}-engineering-e2"
        folder.mkdir()
        (folder / "evidence.json").write_text(
            json.dumps(
                {
                    "checks": [{"pass": True}],
                    "issues": [],
                    "accessibility": [
                        {"violations": [], "incomplete": ["manual review"]}
                    ]
                    * 6,
                }
            )
        )
    pdfs = []
    for index in range(7):
        path = browser / f"fixture-{index}.pdf"
        path.write_bytes(b"%PDF-synthetic-test-bytes")
        report = path.with_suffix(".json")
        report.write_text('{"fixture":"NOT OBSERVED HISTORY"}')
        pdfs.append(
            {
                "file": path.name,
                "status": "PASS",
                "bytes": path.stat().st_size,
                "sha256": release.digest(path),
                "report_sha256": release.digest(report),
            }
        )
    (browser / "pdf-results.json").write_text(json.dumps(pdfs))
    return tmp_path


@pytest.fixture
def candidate(artifacts, monkeypatch):
    identity = {
        "kind": "committed",
        "revision": "a" * 40,
        "tree": "b" * 40,
        "files_sha256": {},
    }
    images = {
        "api": {"reference": "orbitiq-api:test", "id": "sha256:" + "a" * 64},
        "web": {"reference": "orbitiq-web:test", "id": "sha256:" + "b" * 64},
    }
    frontend = artifacts / "frontend"
    frontend.mkdir()
    (frontend / "index.html").write_text("public test build")
    monkeypatch.setattr(release, "source", lambda **kwargs: identity)
    monkeypatch.setattr(release, "images", lambda *args: images)
    monkeypatch.setattr(release, "web_files", lambda *args: release.inventory(frontend))
    capture = artifacts / "capture.json"
    release.capture("test", frontend, capture)
    return identity, images, frontend, capture


def test_successful_record_is_not_production_approval(candidate, artifacts):
    _, _, frontend, capture = candidate
    output = artifacts / "record.json"
    record = release.seal(capture, frontend, artifacts, output)
    assert record["release_candidate"] and record["production_approved"] is False
    assert release.verify_files(output, artifacts)["status"] == "PASS"
    assert len(record["evidence_sha256"]) == 21


def test_local_index_candidate_cannot_become_committed_release(candidate, artifacts):
    identity, _, frontend, _ = candidate
    identity["kind"] = "reviewed-index"
    capture = artifacts / "local-capture.json"
    release.capture("test", frontend, capture, candidate=True)
    record = release.seal(capture, frontend, artifacts, artifacts / "local-record.json")
    assert (
        record["release_candidate"] is False and record["production_approved"] is False
    )


@pytest.mark.parametrize("what", ["source", "image", "frontend"])
def test_substituted_input_is_refused_after_capture(candidate, artifacts, what):
    identity, images, frontend, capture = candidate
    if what == "source":
        identity["tree"] = "c" * 40
    elif what == "image":
        images["api"]["id"] = "sha256:" + "c" * 64
    else:
        (frontend / "index.html").write_text("substituted build")
    target = artifacts / "record.json"
    with pytest.raises(ValueError):
        release.seal(capture, frontend, artifacts, target)
    assert not target.exists()


@pytest.mark.parametrize(
    "case", ["cancelled", "skipped-engine", "bad-TLS", "a11y", "PDF", "report"]
)
def test_incomplete_or_changed_test_evidence_refuses_seal(candidate, artifacts, case):
    _, _, frontend, capture = candidate
    browser = artifacts / "browser"
    if case == "cancelled":
        path = browser / "commands.json"
        data = json.loads(path.read_text())
        data[-1]["exit_code"] = 124
    elif case == "skipped-engine":
        path = browser / "summary.json"
        data = json.loads(path.read_text())
        del data["browser_flows"]["webkit"]
    elif case == "bad-TLS":
        path = artifacts / "proxy.json"
        data = json.loads(path.read_text())
        data["tls_verified"] = False
    elif case == "a11y":
        path = browser / "chromium-engineering-e2/evidence.json"
        data = json.loads(path.read_text())
        data["accessibility"][0]["violations"] = ["confirmed violation"]
    else:
        path = browser / ("fixture-0.pdf" if case == "PDF" else "fixture-0.json")
        path.write_bytes(b"changed after validation")
        data = None
    if data is not None:
        path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        release.seal(capture, frontend, artifacts, artifacts / "record.json")
    assert not (artifacts / "record.json").exists()


def test_offline_receipt_detects_changed_artifact(candidate, artifacts):
    _, _, frontend, capture = candidate
    target = artifacts / "record.json"
    release.seal(capture, frontend, artifacts, target)
    (artifacts / "proxy.json").write_text('{"status":"failed"}')
    with pytest.raises(ValueError):
        release.verify_files(target, artifacts)


def test_image_labels_must_match_source(monkeypatch):
    monkeypatch.setattr(
        release,
        "command",
        lambda *a, **k: json.dumps(
            {
                "id": "sha256:" + "a" * 64,
                "labels": {"org.opencontainers.image.revision": "wrong"},
                "os": "linux",
                "architecture": "amd64",
            }
        ),
    )
    with pytest.raises(ValueError, match="labels/identity"):
        release.images("test", {"revision": "a" * 40, "tree": "b" * 40})


def test_default_capture_refuses_dirty_git_but_explicit_index_is_labelled(tmp_path):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=tmp_path, text=True)

    git("init", "-q")
    (tmp_path / "source.txt").write_text("initial")
    git("add", "source.txt")
    git(
        "-c",
        "user.name=fixture",
        "-c",
        "user.email=fixture.invalid",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "-qm",
        "fixture",
    )
    (tmp_path / "source.txt").write_text("new source")
    with pytest.raises(ValueError, match="clean source"):
        release.source(root=tmp_path)
    git("add", "source.txt")
    with pytest.raises(ValueError, match="clean source"):
        release.source(root=tmp_path)
    assert release.source(root=tmp_path, candidate=True)["kind"] == "reviewed-index"
    (tmp_path / "unreviewed.txt").write_text("untracked")
    with pytest.raises(ValueError, match="clean source"):
        release.source(root=tmp_path, candidate=True)


def test_mismatched_web_image_and_existing_output_are_refused(
    candidate, artifacts, monkeypatch
):
    _, _, frontend, _ = candidate
    monkeypatch.setattr(release, "web_files", lambda *args: {"index.html": "f" * 64})
    with pytest.raises(ValueError, match="differs"):
        release.capture("test", frontend, artifacts / "mismatched.json")
    target = artifacts / "must-preserve.json"
    target.write_text("user owned")
    with pytest.raises(FileExistsError):
        release.write_new(target, {"bad": "overwrite"})
    assert target.read_text() == "user owned"


def test_cli_failure_returns_nonzero_without_creating_success_record(artifacts):
    import sys

    record = artifacts / "invalid.json"
    record.write_text('{"kind":"unsupported","private":"do-not-echo"}')
    result = subprocess.run(
        [
            sys.executable,
            str(SPEC.origin),
            "verify-files",
            "--record",
            str(record),
            "--directory",
            str(artifacts),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 1 and "Release verification refused" in result.stderr
    assert "do-not-echo" not in result.stderr and not result.stdout


def test_artifact_symlink_is_refused_without_reading_external_contents(tmp_path):
    artifact = tmp_path / "artifact"
    artifact.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("private fixture canary")
    (artifact / "index.html").symlink_to(outside)
    with pytest.raises(ValueError, match="symlinks"):
        release.inventory(artifact)


def test_integrity_check_never_accepts_fabricated_production_approval(
    candidate, artifacts
):
    _, _, frontend, capture = candidate
    target = artifacts / "record.json"
    release.seal(capture, frontend, artifacts, target)
    value = json.loads(target.read_text())
    value["production_approved"] = True
    target.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="Unsupported"):
        release.verify_files(target, artifacts)


@pytest.mark.parametrize("changed", ["capture", "frontend"])
def test_offline_receipt_binds_capture_and_frontend(candidate, artifacts, changed):
    _, _, frontend, capture = candidate
    target = artifacts / "record.json"
    release.seal(capture, frontend, artifacts, target)
    if changed == "capture":
        data = json.loads(capture.read_text())
        data["source"]["revision"] = "c" * 40
        capture.write_text(json.dumps(data))
    else:
        (frontend / "index.html").write_text("changed public artifact")
    with pytest.raises(ValueError):
        release.verify_files(target, artifacts, frontend)
