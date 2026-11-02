"""Apply pending migrations to the blog database.

    python scripts/migrate.py --verify --backup

--verify  refuse to run if an applied migration was edited or deleted
--backup  copy the database to backups/ before applying anything
--status  list pending migrations and exit
"""

import argparse
import sqlite3
import sys
from contextlib import closing
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from blog.db import MigrationError, migrate, pending, verify  # noqa: E402


def backup(db_path: Path, backups_dir: Path) -> Path:
    """Copy the database to a new file in backups_dir; never overwrite an older backup."""
    backups_dir.mkdir(exist_ok=True)
    stem = f"{db_path.stem}-{datetime.now():%Y%m%d-%H%M%S}"
    target = backups_dir / f"{stem}.db"
    n = 1
    while target.exists():
        n += 1
        target = backups_dir / f"{stem}-{n}.db"
    # closing(): a Connection used as a context manager commits but does not close.
    with closing(sqlite3.connect(db_path)) as src, closing(sqlite3.connect(target)) as dst:
        src.backup(dst)
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="blog.db")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--backup", action="store_true")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()
    db_path = Path(args.db)
    is_new = not db_path.exists()

    try:
        conn = sqlite3.connect(db_path)
    except sqlite3.Error as exc:
        print(f"error: can't open {db_path}: {exc}. Check --db and that its folder exists", file=sys.stderr)
        return 1
    try:
        if args.verify:
            verify(conn)
        waiting = pending(conn)
        if args.status or not waiting:
            print("\n".join(p.name for p in waiting) or "no pending migrations")
            return 0
        if args.backup and is_new:
            print("backup: skipped, new database")
        elif args.backup:
            print(f"backup: {backup(db_path, db_path.parent / 'backups')}")
        for name in migrate(conn):
            print(f"applied: {name}")
    except MigrationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except (sqlite3.Error, OSError) as exc:
        # Backup or file access failed before any migration ran.
        print(f"error: nothing applied; backup or database access failed: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
