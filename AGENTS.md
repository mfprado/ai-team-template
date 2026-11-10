# AGENTS.md

Instructions for any AI agent (Codex, Claude Code, others) working in this team repository.

## Who you are working with

- The people using this repository are **not technical**. Most have never used git, a terminal or Markdown, and they should not need to.
- Answer in the **team's language** (see `.agents/local/team.json`, key `language`; if missing, use the language the person writes in).
- Keep answers short and plain. No jargon, no file paths unless asked. Say what you did and what they should check.
- Never ask them to run commands, edit files by hand or use git. Do it yourself, or explain it in everyday words.

## What lives where

| Path | What it is | Who edits it |
|---|---|---|
| `.agents/skills/<skill>/` | Every skill of the team (`SKILL.md` + optional `scripts/`) | You, when asked; the team through the UI |
| `.agents/permissions.json` | What the AI may and may not do | You, only after the person agrees to the change |
| `.agents/core/` | Shared rules, hooks and scripts, identical in every team repo | Nobody by hand. Never edit it |
| `.agents/local/` | This team's extra rules and hooks | You, when the team asks |
| `.claude/`, `.codex/` | **Generated** from `.agents/` on every commit | Never edit. Change `.agents/` instead |
| Visible folders (documents, artifacts) | The team's own work | The team and you |
| `IDEAS.md` | The team's ideas, one line each | You, only through `ideas.py` |

`.agents/core/manifest.json` lists the system skills owned by core (for example `migrate-skill`). Do not modify them; the team's own skills are everything else in `.agents/skills/`.

## Rules

Read a rule file **only when its situation applies**. Team rules in `.agents/local/rules/` follow the same idea and win over core rules when they conflict; say so when that happens.

| When | Read |
|---|---|
| Creating, migrating or editing a skill | `.agents/core/rules/skills.md` |
| Producing a report, dashboard or any HTML output | `.agents/core/rules/artifacts.md` |
| Anything involving credentials, messages to people, or changing permissions | `.agents/core/rules/safety.md` |
| Someone shares an idea for the team, or asks about the team's ideas | `.agents/core/rules/ideas.md` |
| An "IMPROVEMENT REVIEW" note appears, or someone asks what could work better | `.agents/core/rules/improvements.md` |
| Any task covered by a file in `.agents/local/rules/` | That file |

## Sharing changes with the team

After you change anything the team uses (a skill, a rule, a permission, a hook, a document),
ask: **"Do you want to apply this change so everyone on the team can use it?"** If yes, run:

```
sh .agents/core/bin/py -I .agents/core/scripts/propose_change.py --summary "<one plain sentence>" --paths <files or folders you changed>
```

List in `--paths` only what belongs to this change, so other unsaved work stays where it is.

Tell the person its `message`. If it returns `note_for_champion`, offer it as a very short
message they can send to their AI Champion (never send it yourself). Only the AI Champion
updates the team's main version directly; for everyone else this creates a change request
the Champion approves. Never push to `main` yourself.

## Always

- **Deterministic first.** Fixed steps belong in scripts inside the skill; you only reason where judgement is needed.
- **Never send or schedule** messages, emails or posts. Prepare a draft and tell the person where it is.
- **Never read or print secrets** (`.env`, keys, tokens). Ask the person to configure them instead.
- **Nothing is lost.** Every change goes through git. Do not force-push or rewrite history.
- After changing anything in `.agents/`, regenerate the tool files: `sh .agents/core/bin/py .agents/core/scripts/sync.py`.
- **If a team check stops you** (a message starting with "TEAM CHECKS", or a blocked save), never work around it. Follow its instructions, and tell the person what to do in one simple sentence (usually: double-click the team launcher).
