# AI Team Template

Template for a team's shared AI workspace. Each team gets its own copy: a private folder where the team keeps its AI skills, documents and artifacts, with the technical parts hidden.

> Spanish version: [ia-team-template](https://github.com/mfprado/ia-team-template).

## Create a team repository (AI Champions)

Open Claude or Codex in an empty folder and paste:

> Create my team's AI workspace from the template https://github.com/mfprado/ai-team-template.
> Download it to a temporary folder, read `.agents/skills/create-team-repo/SKILL.md` and follow
> it step by step, asking me before each action.

The `create-team-repo` skill asks for the language, company and team, creates an empty
private repository, copies this template's files into it (never its history) and configures
it. Every commit in the team's repository is the AI Champion's own; nothing in it points back
to this template.

## Improvements reach every team (by email, never automatically)

Team repositories never point back to this template and never pull from it. To ship an
improvement:

1. **Maintainers** change the core here and run `release-core`: it writes the plain-words
   entry in `.agents/core/CHANGES.md` and prepares one email draft per AI Champion from the
   *AI Champions* sheet (drafts only; a maintainer sends them).
2. **Each AI Champion** follows the email: opens Claude or Codex, pastes the prompt, and
   `update-team-repo` (run from a fresh copy of this template) shows what changes, proposes
   any new safety rule, copies the new files onto a branch, commits under the Champion's name
   and opens a pull request in the team's repository.
3. The Champion (or their IT team) reviews and merges it. Teammates get it on their next session.

The team's own skills, rules (`.agents/local/`) and permissions are never changed; new
default permissions are only added if the Champion accepts them.

## What the team sees

Only their own work: the launcher that opens the workspace, this README, and their documents and artifacts folders (created in the team's language at setup). Everything technical lives in hidden folders.

## How it works

- **One universal source.** Skills, rules and permissions live in `.agents/`, in open formats any agent reads (`AGENTS.md`, Agent Skills `SKILL.md`).
- **Generated per tool.** On every commit, `.agents/core/scripts/sync.py` writes what each tool needs: `.claude/` for Claude Code, `.codex/` for Codex. Nobody edits those by hand.
- **Guardrails.** `.agents/permissions.json` says what the AI may not do. It is enforced by each tool's native settings and by a guard hook that runs before every tool call.
- **Core and local.** `.agents/core/` is identical in every team repository and is updated from this template; `.agents/local/` belongs to the team.

## Structure

```
Team-AI.command / .bat   launcher (renamed <Team>-AI): installs what is needed, prepares the computer
AGENTS.md                instructions for any agent
CLAUDE.md                imports AGENTS.md (Claude Code)
.agents/
  skills/                all skills (team + system)
  permissions.json       what the AI may not do
  core/                  shared: manifest, rules, hooks, git-hooks, scripts, bin/py, facade/setup.py
  local/                 the team's own rules and hooks
.claude/  .codex/        generated, do not edit
```

## Status

Each team repository records in `.agents/core/manifest.json` the core version it has: date + commit of this template.

Done: structure, rules, permissions, sync, guard hook, launcher and per-computer setup,
`migrate-skill`, `create-team-repo`, `update-team-repo`, `release-core`. Next: the team UI (Streamlit).

Template-only skills (never copied to teams): `create-team-repo`, `update-team-repo`, `release-core`.
