"""Read posts/*.md (front matter + markdown body) and load them into the database."""

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED = ("title", "published")


class PostError(ValueError):
    """A post file can't be loaded; the message names the file and the fix."""


@dataclass(slots=True)
class Post:
    slug: str
    title: str
    published: str
    tags: str
    body: str


def parse_post(path: Path) -> Post:
    text = path.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"  # a closing '---' on the last line still closes the block
    if not text.startswith("---\n"):
        raise PostError(f"{path.name}: must start with a '---' front matter block")
    try:
        header, body = text[4:].split("\n---\n", 1)
    except ValueError:
        raise PostError(f"{path.name}: front matter has no closing '---' line") from None
    fields: dict[str, str] = {}
    for line in header.splitlines():
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip()
    missing = [k for k in REQUIRED if not fields.get(k)]
    if missing:
        raise PostError(f"{path.name}: front matter is missing {', '.join(missing)}")
    if not DATE.match(fields["published"]):
        raise PostError(f"{path.name}: published must be YYYY-MM-DD, got {fields['published']!r}")
    return Post(
        slug=path.stem,
        title=fields["title"],
        published=fields["published"],
        tags=fields.get("tags", ""),
        body=body.strip() + "\n",
    )


def sync(conn: sqlite3.Connection, posts_dir: Path) -> int:
    """Make the posts table match posts_dir: insert or update every file, delete rows
    whose file is gone. All or nothing: one bad file changes nothing."""
    if not posts_dir.is_dir():
        raise PostError(f"posts folder not found: {posts_dir}; run from the project root")
    files = sorted(posts_dir.glob("*.md"))
    if not files:
        raise PostError(f"no .md files in {posts_dir}; nothing to load, nothing deleted")
    posts = [parse_post(p) for p in files]
    with conn:
        for p in posts:
            conn.execute(
                "INSERT INTO posts (slug, title, published, tags, body) VALUES (?, ?, ?, ?, ?)"
                " ON CONFLICT(slug) DO UPDATE SET title = excluded.title,"
                " published = excluded.published, tags = excluded.tags, body = excluded.body",
                (p.slug, p.title, p.published, p.tags, p.body),
            )
        placeholders = ", ".join("?" * len(posts))
        conn.execute(
            f"DELETE FROM posts WHERE slug NOT IN ({placeholders})",  # noqa: S608 — placeholders only
            [p.slug for p in posts],
        )
    return len(posts)
