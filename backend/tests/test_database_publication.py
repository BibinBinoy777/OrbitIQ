"""Synthetic database publication, including the Windows flush requirement."""

import errno
import os
import sqlite3
from contextlib import closing

import pytest
from orbitiq import database


def test_init_backup_restore_flushes_writable_handles(tmp_path, monkeypatch):
    """A zero-length write enforces Windows' writable-fsync contract on Linux."""
    real_fsync = os.fsync
    synced = []

    def writable_fsync(descriptor):
        os.write(descriptor, b"")  # No content change; rejects a read-only handle.
        real_fsync(descriptor)
        synced.append(descriptor)

    monkeypatch.setattr(database.os, "fsync", writable_fsync)
    source, backup, restored = [
        tmp_path / f"{name}.sqlite3" for name in ("source", "backup", "restored")
    ]
    database.initialize(source)
    with closing(sqlite3.connect(source)) as db, db:
        db.execute("CREATE TABLE synthetic_marker(value TEXT NOT NULL)")
        db.execute("INSERT INTO synthetic_marker VALUES ('synthetic fixture only')")
    before = source.read_bytes()
    database.copy_database(source, backup)
    database.copy_database(backup, restored)
    assert len(synced) == 3
    for path in (source, backup, restored):
        with closing(database.connect_existing(path)) as db:
            database.validate(db)
            assert db.execute("SELECT value FROM synthetic_marker").fetchall() == [
                ("synthetic fixture only",)
            ]
    assert source.read_bytes() == before
    assert set(tmp_path.iterdir()) == {source, backup, restored}
    with pytest.raises(FileExistsError):
        database.copy_database(backup, source)
    assert source.read_bytes() == before


@pytest.mark.parametrize("operation", ["initialize", "copy"])
def test_flush_failure_publishes_nothing_and_preserves_source(
    tmp_path, monkeypatch, operation
):
    source, target = tmp_path / "source.sqlite3", tmp_path / "target.sqlite3"
    database.initialize(source)
    before = source.read_bytes()

    def failed_flush(descriptor):
        raise OSError(errno.EIO, "Synthetic flush failure")

    monkeypatch.setattr(database.os, "fsync", failed_flush)
    with pytest.raises(OSError, match="Synthetic flush failure"):
        if operation == "initialize":
            database.initialize(target)
        else:
            database.copy_database(source, target)
    assert not target.exists()
    assert list(tmp_path.iterdir()) == [source]
    assert source.read_bytes() == before
