# AGENTS.md

Instructions for any AI agent (Codex, Claude Code, others) working in this team repository.

## Who you are working with

- The people using this repository are **not technical**. Most have never used git, a terminal or Markdown, and they should not need to.
- Answer in the **team's language** (see `.agents/local/team.json`, key `language`; if missing, use the language the person writes in).
- Keep answers short and plain. No jargon, no file paths unless asked. Say what you did and what they should check.
- Ask questions in natural language. Never say commit, push, branch, merge or repository: say
  "save it for the whole team", "get the team's latest", "the team's shared folder" (full list
  in `.agents/core/rules/changes.md`).
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
| Changing a skill, rule, permission, hook or team setting, or sharing a change that clashes with someone else's | `.agents/core/rules/changes.md` |
| Someone shares an idea for the team, or asks about the team's ideas | `.agents/core/rules/ideas.md` |
| An "IMPROVEMENT REVIEW" note appears, or someone asks what could work better | `.agents/core/rules/improvements.md` |
| Any task covered by a file in `.agents/local/rules/` | That file |

## Sharing changes with the team

After you change anything the team uses (a skill, a rule, a permission, a hook, a document),
ask: **"Do you want to save this for the whole team?"** If yes, run:

```
sh .agents/core/bin/py -I .agents/core/scripts/propose_change.py --summary "<one plain sentence>" --paths <files or folders you changed>
```

List in `--paths` only what belongs to this change, so other unsaved work stays where it is.

Tell the person its `message`. By default every change reaches the team's main version
straight away, and the team page's History shows who changed what. If the Champion turned on
approval in Settings, a teammate's change becomes a change request instead: when the script
returns `note_for_champion`, offer it as a very short message they can send to their AI
Champion (never send it yourself). Never push to `main` yourself; always use the script.

**Cloud sessions** (Claude Code on the web, Codex cloud) often start on a branch of their own.
That branch is not the team's version: nobody sees it. Still share with the script, which
sends the change to the team's main version (or a change request, if approval is on). Do not
leave the work on the session's branch or open a pull request instead, even if the tool
suggests it.

Before changing how the AI works for the whole team (skills, rules, permissions, hooks,
settings), read `.agents/core/rules/changes.md`.

## Always

- **Deterministic first.** Fixed steps belong in scripts inside the skill; you only reason where judgement is needed.
- **Never send or schedule** messages, emails or posts. Prepare a draft and tell the person where it is.
- **Never read or print secrets** (`.env`, keys, tokens). Ask the person to configure them instead.
- **Nothing is lost.** Every change goes through git. Do not force-push or rewrite history.
- After changing anything in `.agents/`, regenerate the tool files: `sh .agents/core/bin/py .agents/core/scripts/sync.py`.
- **If a team check stops you** (a message starting with "TEAM CHECKS", or a blocked save), never work around it. Follow its instructions, and tell the person what to do in one simple sentence (usually: double-click the team launcher).
