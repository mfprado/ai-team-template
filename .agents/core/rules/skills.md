# Rule: skills

Applies when creating, migrating or editing a skill.

## Format

- One folder per skill: `.agents/skills/<skill-name>/`, lowercase, words joined by hyphens.
- `SKILL.md` starts with front matter that has **`name`** (same as the folder) and **`description`**:
  what the skill does and *when* to use it, in the words the team would use to ask for it.
  Agents only read the description up front, so it decides whether the skill is ever used.
- Optional `scripts/` for code and `templates/` for fixed text or layouts.

## Content

- **Deterministic first.** Any step that must give the same result every time (calculations,
  file transforms, building an HTML report) goes in a script in `scripts/`. The instructions
  tell the agent when to run it; the agent does not redo it by hand.
- **Works for anyone on the team.** No personal paths (`/Users/<name>/...`, `C:\Users\...`),
  personal emails, personal IDs or machine-specific settings. Use paths relative to the
  repository and ask for anything person-specific at run time.
- **No secrets.** Never put tokens, passwords or keys in a skill. Read them from the
  environment and say in `SKILL.md` which variable is needed.
- **Self-contained.** Everything the skill needs to work is written in the skill or in a rule
  of this repository, never in someone's personal memory or chat history.
- **Tools it uses are listed.** Name the connectors (MCP) and commands the skill needs at the
  end of `SKILL.md` under `## Tools`, so permissions can be checked.

## After changing a skill

Run `sh .agents/core/bin/py .agents/core/scripts/sync.py` so Claude Code and Codex both see the change.
Never edit system skills listed in `.agents/core/manifest.json`.
