# Sample blog

A small Flask + SQLite blog. Posts are markdown files in `posts/`; `python -m blog sync` loads them into `blog.db`, and Flask serves them.

## Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python scripts/migrate.py --verify --backup   # create or update blog.db
python -m blog sync                           # load posts/ into the database
flask --app blog run --debug                  # http://127.0.0.1:5000
pytest                                        # must pass before every commit
```

## Layout

- `blog/`: the app (`create_app`), post loading (`posts.py`), migrations (`db.py`)
- `posts/`: one markdown file per post; the filename is the URL slug
- `migrations/`: numbered SQL files, applied in order
- `scripts/migrate.py`: applies migrations

## Rules

- Parameterised SQL only. Never format values into a query string.
- Every schema change is a new migration. Never change the database by hand.
- Errors name the file or migration and say how to fix it. Never report success after a failure.
- Ask before adding a dependency.
- One branch per change. The only commit made on `main` is a release (see the `releasing` Skill).

## Skills

Procedures live in `.claude/skills/` and load only when the task matches: `writing-a-post`, `adding-a-migration`, `releasing`.
