import importlib.util
import sqlite3
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "migrate_script", Path(__file__).resolve().parent.parent / "scripts" / "migrate.py"
)
migrate_script = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migrate_script)


def test_backups_in_the_same_second_do_not_overwrite(tmp_path):
    db = tmp_path / "blog.db"
    sqlite3.connect(db).close()
    first = migrate_script.backup(db, tmp_path / "backups")
    second = migrate_script.backup(db, tmp_path / "backups")
    assert first != second
    assert first.exists() and second.exists()
