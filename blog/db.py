"""Numbered SQL migrations, applied in order and recorded with a checksum."""

import hashlib
import sqlite3
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


class MigrationError(RuntimeError):
    """Migrations can't be applied safely; the message says why."""


def _checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        " name TEXT PRIMARY KEY, checksum TEXT NOT NULL,"
        " applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    )


def applied(conn: sqlite3.Connection) -> dict[str, str]:
    _ensure_table(conn)
    return dict(conn.execute("SELECT name, checksum FROM schema_migrations"))


def _files(migrations_dir: Path) -> list[Path]:
    """The migration files in order. A missing folder is an error, not "nothing to do"."""
    if not migrations_dir.is_dir():
        raise MigrationError(
            f"migrations folder not found: {migrations_dir}; run from the project root"
        )
    return sorted(migrations_dir.glob("*.sql"))


def pending(conn: sqlite3.Connection, migrations_dir: Path = MIGRATIONS_DIR) -> list[Path]:
    done = applied(conn)
    return [p for p in _files(migrations_dir) if p.name not in done]


def verify(conn: sqlite3.Connection, migrations_dir: Path = MIGRATIONS_DIR) -> None:
    """Fail if an applied migration was edited or deleted since it ran."""
    files = {p.name: p for p in _files(migrations_dir)}
    for name, checksum in applied(conn).items():
        if name not in files:
            raise MigrationError(f"{name} was applied but its file is gone; restore it")
        if _checksum(files[name]) != checksum:
            raise MigrationError(
                f"{name} changed after it was applied; revert the edit and add a new migration"
            )


def migrate(conn: sqlite3.Connection, migrations_dir: Path = MIGRATIONS_DIR) -> list[str]:
    """Apply pending migrations in order, each in its own transaction."""
    # Manage transactions here, not through sqlite3's implicit ones.
    conn.commit()
    previous, conn.isolation_level = conn.isolation_level, None
    try:
        return [_apply(conn, path) for path in pending(conn, migrations_dir)]
    finally:
        conn.isolation_level = previous


def _apply(conn: sqlite3.Connection, path: Path) -> str:
    sql = path.read_text(encoding="utf-8")
    try:
        # executescript parses the file as SQLite does, so a ';' inside a string
        # literal, a comment or a trigger body doesn't split a statement. With
        # isolation_level None there is no implicit commit, so BEGIN holds until
        # the COMMIT below.
        conn.executescript("BEGIN;\n" + sql)
        conn.execute(
            "INSERT INTO schema_migrations (name, checksum) VALUES (?, ?)",
            (path.name, _checksum(path)),
        )
        conn.execute("COMMIT")
    except sqlite3.Error as exc:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise MigrationError(f"{path.name} failed and was rolled back: {exc}") from exc
    return path.name
