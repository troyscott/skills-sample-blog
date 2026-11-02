# skills-sample-blog

A small Flask + SQLite blog that shows one thing: what goes in `CLAUDE.md` and what goes in a Claude Code Skill.

- **`CLAUDE.md`** is what Claude needs to work on the project at all: how to install, run and test it, where things are, and the rules every change follows. Claude Code loads it into every session, so it stays short.
- **A Skill** is one procedure, in `.claude/skills/<name>/SKILL.md`. Claude reads only its name and description until a request matches, then loads the rest.

The test for which is which: does it apply to every task? Then it's `CLAUDE.md`. Is it a procedure for one kind of task? Then it's a Skill.

## The three Skills

Each one shows a different amount of freedom, following Anthropic's [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices).

| Skill | Freedom | Why |
|---|---|---|
| [`writing-a-post`](.claude/skills/writing-a-post/SKILL.md) | High | Many good ways to write a post. Guidelines, plus the file format and one check. |
| [`adding-a-migration`](.claude/skills/adding-a-migration/SKILL.md) | Low | A bad migration damages data. One exact command, with backup and verify. |
| [`releasing`](.claude/skills/releasing/SKILL.md) | Low | Steps must run in order, and pushing is outward-facing, so Claude asks first. |

Every description says what the Skill does **and** when to use it ("Use when the user asks to…"). Claude picks a Skill from its description alone. If the description doesn't match how you ask, the Skill never loads and the procedure is skipped without any warning.

## Try it

```bash
git clone https://github.com/troyscott/skills-sample-blog && cd skills-sample-blog
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python scripts/migrate.py --verify --backup
python -m blog sync
flask --app blog run --debug
```

Then open the folder in Claude Code and test each Skill two ways:

1. Name it: `/adding-a-migration add a summary column to posts`
2. Don't name it: "Posts need a short summary field." Check that Claude loads `adding-a-migration` and runs `python scripts/migrate.py --verify --backup` as written.

If it doesn't load, fix the description first. Restart the session after editing a Skill.

## Further reading

- [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) (Anthropic)
- [Decoding Anthropic's Skill authoring guide](https://www.bluemat.ca/article/2026-11-01-decode-1681) (bluemat)
