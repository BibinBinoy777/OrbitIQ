"""Synthetic owner-acceptance setup; never reads the operator/research archive."""

import json
import runpy
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
M = runpy.run_path(str(ROOT / "scripts/seed_browser_fixtures.py"))
REFERENCE = ROOT / "backend/tests/fixtures/vallado-leo.json"


def test_local_owner_archive_is_explicit_synthetic_readonly_and_nonoverwriting(
    tmp_path, monkeypatch, capsys
):
    def forbidden(*args):
        raise AssertionError("Local acceptance must not change ownership")

    monkeypatch.setattr(M["os"], "chown", forbidden)
    directory = tmp_path / "acceptance"
    directory.mkdir()
    M["main"](["--directory", str(directory), "--local-owner"])
    receipt = json.loads(capsys.readouterr().out)
    db = directory / "archive.sqlite3"
    assert receipt["synthetic_only"] and receipt["catalog"] == 6251
    assert receipt["database"] == str(db)
    assert "NOT SATELLITE OBSERVATIONS" in receipt["fixture"]
    assert db.stat().st_mode & 0o222 == 0
    with sqlite3.connect(db.as_uri() + "?mode=ro", uri=True) as conn:
        assert conn.execute("SELECT count(*) FROM snapshots").fetchone() == (2,)
        assert conn.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    before = {str(p): p.read_bytes() for p in directory.rglob("*") if p.is_file()}
    with pytest.raises(ValueError, match="nonempty"):
        M["main"](["--directory", str(directory), "--local-owner"])
    assert all(Path(p).read_bytes() == raw for p, raw in before.items())


def test_container_default_retains_release_owner_and_fixture_contract(
    tmp_path, monkeypatch
):
    owners = []
    monkeypatch.setattr(M["os"], "chown", lambda p, uid, gid: owners.append((uid, gid)))
    receipt = M["seed"](tmp_path, REFERENCE)
    assert owners and set(owners) == {(10001, 10001)}
    assert receipt["catalog"] == 6251 and receipt["first"] != receipt["second"]
    assert "database" not in receipt  # Existing container receipt unchanged.


def test_local_setup_refuses_symlink_and_relative_targets(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    for directory in [link, Path("relative-acceptance")]:
        with pytest.raises(ValueError, match="absolute fresh"):
            M["seed"](directory, REFERENCE, local_owner=True)
    assert list(target.iterdir()) == []


def test_no_argument_container_cli_keeps_existing_paths_and_owner(monkeypatch, capsys):
    calls = []

    def container_seed(directory, reference, *, local_owner):
        calls.append((directory, reference, local_owner))
        return {"fixture": "SYNTHETIC container contract"}

    monkeypatch.setitem(M["main"].__globals__, "seed", container_seed)
    M["main"]([])
    assert calls == [(Path("/fixtures"), Path("/reference.json"), False)]
    assert json.loads(capsys.readouterr().out) == {
        "fixture": "SYNTHETIC container contract"
    }
