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


def pending(conn: sqlite3.Connection, migrations_dir: Path = MIGRATIONS_DIR) -> list[Path]:
    done = applied(conn)
    return [p for p in sorted(migrations_dir.glob("*.sql")) if p.name not in done]


def verify(conn: sqlite3.Connection, migrations_dir: Path = MIGRATIONS_DIR) -> None:
    """Fail if an applied migration was edited or deleted since it ran."""
    files = {p.name: p for p in migrations_dir.glob("*.sql")}
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
        conn.execute("BEGIN")
        for statement in filter(str.strip, sql.split(";")):
            conn.execute(statement)
        conn.execute(
            "INSERT INTO schema_migrations (name, checksum) VALUES (?, ?)",
            (path.name, _checksum(path)),
        )
        conn.execute("COMMIT")
    except sqlite3.Error as exc:
        conn.execute("ROLLBACK")
        raise MigrationError(f"{path.name} failed and was rolled back: {exc}") from exc
    return path.name
