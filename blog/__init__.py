"""A small blog: markdown posts loaded into SQLite and served by Flask."""

import sqlite3
from pathlib import Path

import markdown
from flask import Flask, abort, g, render_template

__version__ = "0.1.0"


def create_app(db_path: str | Path = "blog.db") -> Flask:
    app = Flask(__name__)
    app.config["DB_PATH"] = str(db_path)

    def db() -> sqlite3.Connection:
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DB_PATH"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_exc: BaseException | None) -> None:
        conn = g.pop("db", None)
        if conn is not None:
            conn.close()

    @app.get("/")
    def index() -> str:
        posts = db().execute(
            "SELECT slug, title, published, tags FROM posts ORDER BY published DESC"
        ).fetchall()
        return render_template("index.html", posts=posts)

    @app.get("/posts/<slug>")
    def post(slug: str) -> str:
        row = db().execute("SELECT * FROM posts WHERE slug = ?", (slug,)).fetchone()
        if row is None:
            abort(404)
        return render_template("post.html", post=row, body=markdown.markdown(row["body"]))

    return app
