"""python -m blog sync: load posts/*.md into the database."""

import argparse
import sqlite3
import sys
from pathlib import Path

from blog.db import pending
from blog.posts import PostError, sync


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m blog")
    sub = parser.add_subparsers(dest="command", required=True)
    s = sub.add_parser("sync", help="load posts/*.md into the database")
    s.add_argument("--db", default="blog.db")
    s.add_argument("--posts", default="posts")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    try:
        if waiting := pending(conn):
            print(f"{len(waiting)} migration(s) pending; run scripts/migrate.py first", file=sys.stderr)
            return 1
        count = sync(conn, Path(args.posts))
    except PostError as exc:
        print(f"no posts loaded: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()
    print(f"loaded {count} post(s) into {args.db}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
