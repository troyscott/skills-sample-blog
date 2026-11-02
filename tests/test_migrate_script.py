import importlib.util
import sqlite3
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "migrate_script", Path(__file__).resolve().parent.parent / "scripts" / "migrate.py"
)
migrate_script = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migrate_script)


def test_an_unopenable_db_path_is_an_error_line_not_a_traceback(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["migrate.py", "--db", str(tmp_path / "missing" / "blog.db")])
    assert migrate_script.main() == 1
    err = capsys.readouterr().err
    assert err.startswith("error: can't open") and "missing" in err


def test_a_failing_backup_applies_nothing(tmp_path, monkeypatch, capsys):
    def boom(*_a, **_kw):
        raise OSError("disk full")

    monkeypatch.setattr(migrate_script, "backup", boom)
    db = tmp_path / "blog.db"
    sqlite3.connect(db).close()  # an existing database, so --backup is attempted
    monkeypatch.setattr("sys.argv", ["migrate.py", "--db", str(db), "--backup"])
    assert migrate_script.main() == 1
    assert "nothing applied" in capsys.readouterr().err
    assert migrate_script.pending(sqlite3.connect(db)) != []


def test_backups_in_the_same_second_do_not_overwrite(tmp_path):
    db = tmp_path / "blog.db"
    sqlite3.connect(db).close()
    first = migrate_script.backup(db, tmp_path / "backups")
    second = migrate_script.backup(db, tmp_path / "backups")
    assert first != second
    assert first.exists() and second.exists()
