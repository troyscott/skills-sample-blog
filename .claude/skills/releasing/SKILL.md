---
name: releasing
description: Cut a new release of the blog: checks, version bump, changelog entry and git tag. Use when the user asks to release, ship, cut, tag or version the project.
---

# Releasing

Run these steps in order. Stop at the first failure and show the user the output.

1. `git status` shows a clean tree on `main`. If not, stop and say what's uncommitted.
2. `pytest` passes. It also applies every migration to a fresh database.
3. Ask the user for the new version if they didn't give one. Set `__version__` in `blog/__init__.py` and `version` in `pyproject.toml` to it.
4. Add a section at the top of `CHANGELOG.md`: `## <version> — <YYYY-MM-DD>`, then one line per change since the last tag. List them with `git log v<last-version>..HEAD --oneline`. If `git tag` shows no tags yet, list every commit with `git log --oneline`.
5. Commit and tag:

   ~~~bash
   git commit -am "Release <version>"
   git tag v<version>
   ~~~

6. Ask before pushing. Pushing publishes the release:

   ~~~bash
   git push origin main --tags
   ~~~
