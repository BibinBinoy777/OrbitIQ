"""Explicit catalog-only synthetic demo; no scientific evidence is generated."""

import hashlib
import json
import os
import runpy
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
M = runpy.run_path(str(ROOT / "scripts/seed_browser_fixtures.py"))
REFERENCE = ROOT / "backend/tests/fixtures/vallado-leo.json"


def test_catalog_only_creates_two_readonly_snapshots_without_bundles(
    tmp_path, monkeypatch, capsys
):
    def forbidden(*args, **kwargs):
        raise AssertionError("Catalog-only demo must not create evidence bundles")

    monkeypatch.setitem(M["seed"].__globals__, "create", forbidden)
    monkeypatch.setattr(M["analysis"], "position", forbidden)
    monkeypatch.setattr(M["os"], "chown", forbidden, raising=False)
    M["main"](["--directory", str(tmp_path), "--local-owner", "--catalog-only"])
    receipt = json.loads(capsys.readouterr().out)
    path = tmp_path / "archive.sqlite3"
    assert receipt["synthetic_only"] is True
    assert receipt["validation_fixture_created"] is False
    assert receipt["catalog"] == 6251
    assert (receipt["first"], receipt["second"]) == (1, 2)
    assert "run_id" not in receipt
    assert receipt["database_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert path.stat().st_mode & 0o222 == 0
    assert list(tmp_path.iterdir()) == [path]
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
        assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert db.execute(
            "SELECT catalog_id FROM snapshots ORDER BY id"
        ).fetchall() == [
            (6251,),
            (6251,),
        ]
    before = path.read_bytes()
    with pytest.raises(ValueError, match="nonempty"):
        M["seed"](tmp_path, REFERENCE, local_owner=True, catalog_only=True)
    assert path.read_bytes() == before


def test_catalog_only_cannot_change_default_container_mode(tmp_path):
    with pytest.raises(ValueError, match="local-owner"):
        M["seed"](tmp_path, REFERENCE, catalog_only=True)
    assert list(tmp_path.iterdir()) == []


def test_catalog_only_cli_requires_explicit_local_owner(tmp_path):
    with pytest.raises(SystemExit) as error:
        M["main"](["--directory", str(tmp_path), "--catalog-only"])
    assert error.value.code == 2
    assert list(tmp_path.iterdir()) == []


def test_catalog_only_real_cli_receipt_and_nonoverwrite(tmp_path):
    directory = tmp_path / "catalog-only"
    directory.mkdir()
    sentinel = tmp_path / "synthetic-operator-sentinel.sqlite3"
    sentinel.write_bytes(b"SYNTHETIC SENTINEL; NOT AN OPERATOR DATABASE")
    before_sentinel = sentinel.read_bytes()
    unused_archive = tmp_path / "must-not-create-validation-archive"
    env = {
        **os.environ,
        "PYTHONPATH": str(ROOT / "backend"),
        "ORBITIQ_DATABASE_PATH": str(sentinel),
        "ORBITIQ_VALIDATION_ARCHIVE": str(unused_archive),
    }
    command = [
        sys.executable,
        str(ROOT / "scripts/seed_browser_fixtures.py"),
        "--directory",
        str(directory),
        "--local-owner",
        "--catalog-only",
    ]
    result = subprocess.run(
        command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 0, result.stderr
    receipt = json.loads(result.stdout)
    path = directory / "archive.sqlite3"
    assert receipt["synthetic_only"] is True
    assert receipt["validation_fixture_created"] is False
    assert receipt["catalog"] == 6251
    assert (receipt["first"], receipt["second"]) == (1, 2)
    assert "NOT SATELLITE OBSERVATIONS" in receipt["fixture"]
    assert "run_id" not in receipt
    assert receipt["database"] == str(path)
    assert receipt["database_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert path.stat().st_mode & 0o222 == 0
    assert list(directory.iterdir()) == [path]
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
        assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert db.execute(
            "SELECT id,catalog_id,object_name FROM snapshots ORDER BY id"
        ).fetchall() == [
            (1, 6251, "E1 SYNTHETIC UI FIXTURE - NOT OBSERVED HISTORY"),
            (2, 6251, "E1 SYNTHETIC UI FIXTURE - NOT OBSERVED HISTORY"),
        ]
    before = path.read_bytes()
    refused = subprocess.run(
        command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=60
    )
    assert refused.returncode != 0
    assert "nonempty" in refused.stderr
    assert path.read_bytes() == before
    assert sentinel.read_bytes() == before_sentinel
    assert not unused_archive.exists()
    assert list(directory.iterdir()) == [path]
