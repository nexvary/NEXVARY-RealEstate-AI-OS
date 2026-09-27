import sys
from pathlib import Path


DESKTOP_DIR = Path(__file__).resolve().parents[3] / "desktop"
if str(DESKTOP_DIR) not in sys.path:
    sys.path.insert(0, str(DESKTOP_DIR))

from launcher import archive_orphaned_sqlite_sidecars  # noqa: E402


def test_orphaned_sqlite_sidecars_are_archived_when_database_was_renamed(tmp_path):
    wal = tmp_path / "realestate.db-wal"
    shm = tmp_path / "realestate.db-shm"
    wal.write_bytes(b"wal-data")
    shm.write_bytes(b"shm-data")

    archived = archive_orphaned_sqlite_sidecars(tmp_path)

    assert len(archived) == 2
    assert not wal.exists()
    assert not shm.exists()
    assert {path.name for path in archived} == {"realestate.db-wal", "realestate.db-shm"}
    assert {path.read_bytes() for path in archived} == {b"wal-data", b"shm-data"}


def test_existing_database_keeps_its_sqlite_sidecars(tmp_path):
    (tmp_path / "realestate.db").write_bytes(b"database")
    wal = tmp_path / "realestate.db-wal"
    wal.write_bytes(b"wal-data")

    assert archive_orphaned_sqlite_sidecars(tmp_path) == []
    assert wal.exists()
