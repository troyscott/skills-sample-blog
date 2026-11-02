import sqlite3

import pytest

from blog.db import MigrationError, migrate, pending, verify


def test_migrations_apply_in_order_once(tmp_path):
    conn = sqlite3.connect(tmp_path / "blog.db")
    assert migrate(conn) == ["001_create_posts.sql", "002_add_tags.sql"]
    assert migrate(conn) == []
    assert pending(conn) == []


def copy_migrations(tmp_path):
    from blog.db import MIGRATIONS_DIR

    d = tmp_path / "migrations"
    d.mkdir()
    for p in MIGRATIONS_DIR.glob("*.sql"):
        (d / p.name).write_text(p.read_text())
    return d


def test_verify_catches_an_edited_migration(tmp_path):
    d = copy_migrations(tmp_path)
    conn = sqlite3.connect(tmp_path / "blog.db")
    migrate(conn, d)
    (d / "002_add_tags.sql").write_text("ALTER TABLE posts ADD COLUMN topic TEXT;")
    with pytest.raises(MigrationError, match="changed after it was applied"):
        verify(conn, d)


def test_a_failing_migration_rolls_back(tmp_path):
    d = copy_migrations(tmp_path)
    (d / "003_broken.sql").write_text(
        "CREATE TABLE half_done (id INTEGER);\nALTER TABLE no_such_table ADD COLUMN x TEXT;"
    )
    conn = sqlite3.connect(tmp_path / "blog.db")
    with pytest.raises(MigrationError, match="003_broken.sql failed and was rolled back"):
        migrate(conn, d)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "half_done" not in tables
    assert [p.name for p in pending(conn, d)] == ["003_broken.sql"]
