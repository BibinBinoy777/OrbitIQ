"""E3 failure probes use only temporary, explicitly initialized databases."""

import sqlite3
from contextlib import closing

import pytest
from fastapi.testclient import TestClient
from orbitiq import database
from orbitiq.main import create_app


@pytest.mark.parametrize("operation", ["initialize", "copy"])
def test_destination_not_visible_until_validation_completes(
    tmp_path, monkeypatch, operation
):
    source, target = tmp_path / "source.sqlite3", tmp_path / "target.sqlite3"
    database.initialize(source)
    validate = database.validate
    observations = []

    def inspect(connection):
        observations.append(target.exists())
        validate(connection)

    monkeypatch.setattr(database, "validate", inspect)
    if operation == "initialize":
        database.initialize(target)
    else:
        database.copy_database(source, target)
    assert observations and not any(observations)
    with closing(database.connect_existing(target)) as db:
        validate(db)


@pytest.mark.parametrize("operation", ["initialize", "copy"])
def test_keyboard_interruption_leaves_no_published_or_staging_file(
    tmp_path, monkeypatch, operation
):
    source, target = tmp_path / "source.sqlite3", tmp_path / "target.sqlite3"
    database.initialize(source)
    before = source.read_bytes()
    validate = database.validate

    def interrupt(connection):
        if operation == "copy":
            filename = connection.execute("PRAGMA database_list").fetchone()[2]
            if filename == str(source):
                return validate(connection)
        raise KeyboardInterrupt

    monkeypatch.setattr(database, "validate", interrupt)
    with pytest.raises(KeyboardInterrupt):
        if operation == "initialize":
            database.initialize(target)
        else:
            database.copy_database(source, target)
    assert not target.exists()
    assert list(tmp_path.iterdir()) == [source]
    assert source.read_bytes() == before


def test_missing_collection_gate_is_not_operational_readiness(tmp_path, monkeypatch):
    path = tmp_path / "missing-gate.sqlite3"
    database.initialize(path)
    with closing(sqlite3.connect(path)) as db, db:
        db.execute("DELETE FROM collection_gate")
    monkeypatch.setenv("ORBITIQ_DATABASE_PATH", str(path))
    with TestClient(create_app()) as client:
        assert client.get("/api/health").status_code == 200
        response = client.get("/api/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    with closing(database.connect_existing(path)) as db:
        with pytest.raises(ValueError, match="collection gate"):
            database.validate(db)


@pytest.mark.parametrize("operation", ["initialize", "copy"])
def test_publication_race_preserves_other_creators_file(
    tmp_path, monkeypatch, operation
):
    source, target = tmp_path / "source.sqlite3", tmp_path / "target.sqlite3"
    database.initialize(source)
    link = database.os.link

    def racing_link(temporary, destination):
        destination.write_bytes(b"other creator owns this destination")
        link(temporary, destination)

    monkeypatch.setattr(database.os, "link", racing_link)
    with pytest.raises(FileExistsError):
        if operation == "initialize":
            database.initialize(target)
        else:
            database.copy_database(source, target)
    assert target.read_bytes() == b"other creator owns this destination"
    assert sorted(p.name for p in tmp_path.iterdir()) == [source.name, target.name]


def test_broken_symlink_destination_is_refused(tmp_path):
    target = tmp_path / "target.sqlite3"
    missing = tmp_path / "missing.sqlite3"
    target.symlink_to(missing)
    with pytest.raises(FileExistsError):
        database.initialize(target)
    assert target.is_symlink() and not missing.exists()


def test_backup_progress_budget_cleans_target_and_preserves_source(
    tmp_path, monkeypatch
):
    from types import SimpleNamespace

    source, target = tmp_path / "source.sqlite3", tmp_path / "backup.sqlite3"
    database.initialize(source)
    before = source.read_bytes()
    clock = iter([0, database.BACKUP_PROGRESS_SECONDS + 1])
    monkeypatch.setattr(
        database, "time", SimpleNamespace(monotonic=lambda: next(clock))
    )
    with pytest.raises(TimeoutError, match="progress budget"):
        database.copy_database(source, target)
    assert not target.exists() and list(tmp_path.iterdir()) == [source]
    assert source.read_bytes() == before


def test_real_lock_during_backup_is_bounded(tmp_path, monkeypatch):
    from types import SimpleNamespace

    source, target = tmp_path / "source.sqlite3", tmp_path / "backup.sqlite3"
    database.initialize(source)
    before = source.read_bytes()
    validate = database.validate
    with closing(sqlite3.connect(source)) as writer:

        def lock_after_validation(connection):
            validate(connection)
            writer.execute("BEGIN EXCLUSIVE")

        clock = iter([0, database.BACKUP_PROGRESS_SECONDS + 1])
        monkeypatch.setattr(database, "validate", lock_after_validation)
        monkeypatch.setattr(
            database, "time", SimpleNamespace(monotonic=lambda: next(clock))
        )
        with pytest.raises(TimeoutError, match="progress budget"):
            database.copy_database(source, target)
        writer.rollback()
    assert not target.exists() and list(tmp_path.iterdir()) == [source]
    assert source.read_bytes() == before


@pytest.mark.parametrize("operation", ["initialize", "copy"])
def test_process_death_before_publication_and_restart(tmp_path, operation):
    import os
    import subprocess
    import sys
    from pathlib import Path

    target = tmp_path / "killed.sqlite3"
    source = tmp_path / "source.sqlite3"
    database.initialize(source)
    before = source.read_bytes()
    script = """
import os,sys
from pathlib import Path
from orbitiq import database
validate = database.validate
def die(connection):
    filename = connection.execute('PRAGMA database_list').fetchone()[2]
    if filename == sys.argv[2]:
        return validate(connection)
    os._exit(23)
database.validate=die
if sys.argv[3] == 'initialize':
    database.initialize(Path(sys.argv[1]))
else:
    database.copy_database(Path(sys.argv[2]), Path(sys.argv[1]))
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(target), str(source), operation],
        env={**os.environ, "PYTHONPATH": str(Path(__file__).parents[1])},
        check=False,
        timeout=20,
    )
    assert result.returncode == 23
    assert not target.exists()
    assert source.read_bytes() == before
    staging = list(tmp_path.glob(".killed.sqlite3.orbitiq-*.tmp*"))
    assert staging  # Uncatchable death deliberately leaves identifiable artifacts.
    database.initialize(target)
    with closing(database.connect_existing(target)) as db:
        database.validate(db)
    # Remove only the paths created by the terminated temporary test process.
    for path in staging:
        path.unlink()


@pytest.mark.parametrize("kind", ["missing", "corrupt", "gate_missing"])
def test_failed_restore_cli_has_nonzero_diagnostic_and_no_target(tmp_path, kind):
    import os
    import subprocess
    import sys
    from pathlib import Path

    source, target = tmp_path / "bad.sqlite3", tmp_path / "restored.sqlite3"
    if kind == "corrupt":
        source.write_bytes(b"not a database")
    elif kind == "gate_missing":
        database.initialize(source)
        with closing(sqlite3.connect(source)) as db, db:
            db.execute("DELETE FROM collection_gate")
    result = subprocess.run(
        [sys.executable, "-m", "orbitiq.database", "restore", str(source)],
        env={
            **os.environ,
            "PYTHONPATH": str(Path(__file__).parents[1]),
            "ORBITIQ_DATABASE_PATH": str(target),
        },
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )
    assert result.returncode == 1
    assert "Database operation refused:" in result.stderr
    assert "successful" not in result.stdout and not target.exists()


def test_backup_and_restore_include_committed_uncheckpointed_wal(tmp_path):
    from orbitiq.maintenance.recovery import fingerprint

    source, backup, restored = [
        tmp_path / f"{name}.sqlite3" for name in ("wal-source", "backup", "restored")
    ]
    database.initialize(source)
    with closing(sqlite3.connect(source)) as writer:
        assert writer.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
        writer.execute("PRAGMA wal_autocheckpoint=0")
        writer.execute("CREATE TABLE recovery_marker(value TEXT NOT NULL)")
        writer.execute("INSERT INTO recovery_marker VALUES ('committed WAL evidence')")
        writer.commit()
        assert source.with_name(source.name + "-wal").stat().st_size > 0
        point = fingerprint(source)
        database.copy_database(source, backup)
        database.copy_database(backup, restored)
        assert fingerprint(backup) == point == fingerprint(restored)
        with closing(database.connect_existing(restored)) as recovered:
            assert recovered.execute(
                "SELECT value FROM recovery_marker"
            ).fetchone() == ("committed WAL evidence",)
        assert fingerprint(source) == point
