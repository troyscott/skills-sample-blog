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


def test_semicolons_inside_sql_do_not_split_statements(tmp_path):
    d = copy_migrations(tmp_path)
    (d / "003_literal_and_trigger.sql").write_text(
        "-- a comment; with a semicolon\n"
        "ALTER TABLE posts ADD COLUMN sep TEXT NOT NULL DEFAULT 'a;b';\n"
        "CREATE TRIGGER touch AFTER UPDATE ON posts BEGIN\n"
        "  UPDATE posts SET sep = 'x;y' WHERE slug = NEW.slug;\n"
        "END;\n"
    )
    conn = sqlite3.connect(tmp_path / "blog.db")
    assert migrate(conn, d)[-1] == "003_literal_and_trigger.sql"
    assert conn.execute("SELECT count(*) FROM sqlite_master WHERE name = 'touch'").fetchone()[0] == 1


def test_a_missing_migrations_folder_is_an_error_not_nothing_to_do(tmp_path):
    conn = sqlite3.connect(tmp_path / "blog.db")
    with pytest.raises(MigrationError, match="migrations folder not found"):
        pending(conn, tmp_path / "nowhere")
    with pytest.raises(MigrationError, match="migrations folder not found"):
        verify(conn, tmp_path / "nowhere")


def test_a_migration_that_ends_its_own_transaction_still_reports_the_real_error(tmp_path):
    d = copy_migrations(tmp_path)
    (d / "003_commits.sql").write_text("COMMIT;\nALTER TABLE no_such_table ADD COLUMN x TEXT;")
    conn = sqlite3.connect(tmp_path / "blog.db")
    with pytest.raises(MigrationError, match="no such table"):
        migrate(conn, d)


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
