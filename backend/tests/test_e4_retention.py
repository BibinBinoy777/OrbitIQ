"""Retention rejects changed image bytes and unsafe archives, using fake metadata."""

import hashlib
import importlib
import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest


@pytest.fixture
def retained(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).parents[2] / "scripts"))
    return importlib.import_module("verify_retained_candidate")


@pytest.fixture
def example(tmp_path):
    # Metadata-only synthetic layers; these are not runnable images or observations.
    source = {"revision": "a" * 40, "tree": "b" * 40, "kind": "committed"}
    layer = b"SYNTHETIC filesystem bytes, not a satellite record"
    layer_name = "blobs/sha256/" + hashlib.sha256(layer).hexdigest()
    files = {layer_name: layer}
    images, manifests = {}, []
    for role in ("api", "web"):
        config = json.dumps(
            {
                "config": {
                    "Env": ["SYNTHETIC_ROLE=" + role],
                    "Labels": {
                        "org.opencontainers.image.revision": source["revision"],
                        "io.orbitiq.source-tree": source["tree"],
                    },
                },
                "rootfs": {
                    "type": "layers",
                    "diff_ids": ["sha256:" + hashlib.sha256(layer).hexdigest()],
                },
            },
            sort_keys=True,
        ).encode()
        sha = hashlib.sha256(config).hexdigest()
        config_name = "blobs/sha256/" + sha
        files[config_name] = config
        images[role] = {"id": "sha256:" + sha}
        manifests.append({"Config": config_name, "Layers": [layer_name]})
    files["manifest.json"] = json.dumps(manifests).encode()
    return tmp_path / "images.tar.gz", files, images, source


def write_archive(path, files, extra=None):
    with tarfile.open(path, "w:gz") as archive:
        for name, content in files.items():
            member = tarfile.TarInfo(name)
            member.size = len(content)
            archive.addfile(member, io.BytesIO(content))
        if extra is not None:
            archive.addfile(extra, io.BytesIO(b"x") if extra.isfile() else None)


def test_real_tar_structure_matches_expected_image_content_ids(retained, example):
    path, files, images, source = example
    write_archive(path, files)
    result = retained.image_archive(path, images, source)
    assert result["distinct_layers"] == 1
    assert set(result["images"]) == {image["id"] for image in images.values()}


@pytest.mark.parametrize(
    "change", ["config", "layer", "missing", "extra-image", "labels"]
)
def test_changed_or_incomplete_image_archive_is_refused(retained, example, change):
    path, files, images, source = example
    manifest = json.loads(files["manifest.json"])
    if change == "config":
        files[manifest[0]["Config"]] += b" "
    elif change == "layer":
        files[manifest[0]["Layers"][0]] = b"substituted bytes"
    elif change == "missing":
        del files[manifest[0]["Layers"][0]]
    elif change == "extra-image":
        manifest.append(manifest[0])
        files["manifest.json"] = json.dumps(manifest).encode()
    else:
        source["revision"] = "c" * 40
    write_archive(path, files)
    with pytest.raises((ValueError, KeyError)):
        retained.image_archive(path, images, source)


@pytest.mark.parametrize("name", ["../outside", "/absolute", "bad\\name"])
def test_unsafe_names_are_refused_without_extracting(retained, example, name):
    path, files, images, source = example
    files[name] = b"private test canary"
    write_archive(path, files)
    with pytest.raises(ValueError, match="Unsafe"):
        retained.image_archive(path, images, source)
    assert not (path.parent / "outside").exists()


def test_symbolic_archive_member_is_refused(retained, example):
    path, files, images, source = example
    link = tarfile.TarInfo("link")
    link.type = tarfile.SYMTYPE
    link.linkname = "/private"
    write_archive(path, files, link)
    with pytest.raises(ValueError, match="links"):
        retained.image_archive(path, images, source)


def test_duplicate_member_is_refused(retained, example):
    path, files, images, source = example
    member = tarfile.TarInfo("manifest.json")
    member.size = 1
    write_archive(path, files, member)
    with pytest.raises(ValueError, match="Duplicate"):
        retained.image_archive(path, images, source)


def test_decompression_limit_is_enforced(retained, example, monkeypatch):
    path, files, images, source = example
    write_archive(path, files)
    monkeypatch.setattr(retained, "MAX_UNPACKED", 1)
    with pytest.raises(ValueError, match="limit"):
        retained.image_archive(path, images, source)


def test_existing_output_is_preserved(retained, tmp_path):
    output = tmp_path / "owned"
    output.mkdir()
    canary = output / "keep.txt"
    canary.write_text("user owned")
    with pytest.raises(ValueError, match="must not exist"):
        retained.pack(tmp_path / "missing", tmp_path, tmp_path, output)
    assert canary.read_text() == "user owned"


def test_index_candidate_cannot_be_retained_as_verified_commit(retained, tmp_path):
    record = tmp_path / "record.json"
    record.write_text(
        json.dumps({"release_candidate": False, "source": {"kind": "reviewed-index"}})
    )
    with pytest.raises(ValueError, match="committed"):
        retained.pack(record, tmp_path, tmp_path, tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_cli_refuses_partial_directory_without_approval_or_private_echo(
    retained, tmp_path
):
    (tmp_path / "candidate.json").write_text('{"private":"do-not-echo"}')
    result = subprocess.run(
        [
            sys.executable,
            str(Path(retained.__file__)),
            "verify",
            "--directory",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 1 and not result.stdout
    assert "Candidate retention refused" in result.stderr
    assert "do-not-echo" not in result.stderr


@pytest.fixture
def bundle(retained, example, monkeypatch):
    path, files, images, source = example
    write_archive(path, files)
    directory = path.parent
    evidence = directory / "evidence"
    evidence.mkdir()
    (directory / "frontend").mkdir()
    (directory / "frontend/index.html").write_text("PUBLIC SYNTHETIC BUILD")
    # E4 sealing semantics have their own full test suite. Isolate retention here.
    monkeypatch.setattr(
        retained.release, "verify_files", lambda *args: {"status": "PASS"}
    )
    (evidence / "record.json").write_text(
        json.dumps({"source": source, "images": images})
    )
    manifest = {
        "schema_version": 1,
        "kind": "orbitiq_retained_candidate",
        "production_approved": False,
        "source": source,
        "images": images,
        "record_name": "record.json",
        "files_sha256": retained.release.inventory(directory),
    }
    (directory / "candidate.json").write_text(json.dumps(manifest))
    return directory


def test_complete_candidate_integrity_is_not_production_approval(retained, bundle):
    result = retained.verify(bundle, "a" * 40)
    assert result["status"] == "PASS" and "not deployment approval" in result["scope"]


@pytest.mark.parametrize(
    "change", ["added", "modified", "removed", "approval", "revision"]
)
def test_changed_candidate_files_or_claims_are_refused(retained, bundle, change):
    if change == "added":
        (bundle / "unexpected.txt").write_text("unexpected")
    elif change == "modified":
        (bundle / "frontend/index.html").write_text("changed after tests")
    elif change == "removed":
        (bundle / "frontend/index.html").unlink()
    elif change == "approval":
        path = bundle / "candidate.json"
        data = json.loads(path.read_text())
        data["production_approved"] = True
        path.write_text(json.dumps(data))
    else:
        with pytest.raises(ValueError, match="revision"):
            retained.verify(bundle, "c" * 40)
        return
    with pytest.raises(ValueError):
        retained.verify(bundle)
