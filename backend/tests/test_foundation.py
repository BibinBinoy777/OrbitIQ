import sqlite3

import pytest
from fastapi.testclient import TestClient
from orbitiq.database import configured_path, copy_database, initialize
from orbitiq.main import app


def test_health_does_not_create_database(tmp_path, monkeypatch):
    path = tmp_path / "absent.sqlite3"
    monkeypatch.setenv("ORBITIQ_DATABASE_PATH", str(path))
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "OrbitIQ"}
    assert not path.exists()


def test_configuration_requires_absolute_path(monkeypatch):
    for value in ("", "relative.sqlite3"):
        monkeypatch.setenv("ORBITIQ_DATABASE_PATH", value)
        with pytest.raises(ValueError):
            configured_path()


def test_init_backup_restore_preserves_data(tmp_path):
    source = tmp_path / "source.sqlite3"
    backup = tmp_path / "backup.sqlite3"
    restored = tmp_path / "restored.sqlite3"
    initialize(source)
    with sqlite3.connect(source) as db:
        db.execute("CREATE TABLE evidence (value TEXT)")
        db.execute("INSERT INTO evidence VALUES ('test fixture')")
    copy_database(source, backup)
    copy_database(backup, restored)
    with sqlite3.connect(restored) as db:
        assert db.execute("SELECT value FROM evidence").fetchone() == ("test fixture",)
    before = source.read_bytes()
    with pytest.raises(FileExistsError):
        initialize(source)
    with pytest.raises(FileExistsError):
        copy_database(backup, source)
    assert source.read_bytes() == before


def test_missing_or_invalid_source_creates_no_destination(tmp_path):
    missing = tmp_path / "missing.sqlite3"
    destination = tmp_path / "destination.sqlite3"
    with pytest.raises(sqlite3.Error):
        copy_database(missing, destination)
    assert not missing.exists()
    assert not destination.exists()
    invalid = tmp_path / "invalid.sqlite3"
    invalid.write_text("not a database")
    with pytest.raises(sqlite3.Error):
        copy_database(invalid, destination)
    assert not destination.exists()


def test_unsupported_schema_is_refused_without_creating_backup(tmp_path):
    source = tmp_path / "future.sqlite3"
    destination = tmp_path / "backup.sqlite3"
    initialize(source)
    with sqlite3.connect(source) as db:
        db.execute("UPDATE schema_version SET version = 999")
    before = source.read_bytes()
    with pytest.raises(ValueError, match="Unsupported"):
        copy_database(source, destination)
    assert not destination.exists()
    assert source.read_bytes() == before


def test_same_source_and_destination_is_refused(tmp_path):
    source = tmp_path / "source.sqlite3"
    initialize(source)
    before = source.read_bytes()
    with pytest.raises(ValueError, match="must differ"):
        copy_database(source, source)
    assert source.read_bytes() == before
