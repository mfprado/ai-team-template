# AGENTS.md

Instructions for any AI agent (Codex, Claude Code, others) working in this team repository.

## Who you are working with

- The people using this repository are **not technical**. Most have never used git, a terminal or Markdown, and they should not need to.
- Answer in the **team's language** (see `.agents/team.json`, key `language`; if missing, use the language the person writes in).
- Keep answers short and plain. No jargon, no file paths unless asked. Say what you did and what they should check.
- Ask questions in natural language. Never say commit, push, branch, merge or repository: say
  "save it for the whole team", "get the team's latest", "the team's shared folder" (full list
  in `.agents/rules/changes.md`).
- Never ask them to run commands, edit files by hand or use git. Do it yourself, or explain it in everyday words.
- Say "the AI assistant" ("el asistente de IA"), not Claude or Codex: each person only knows the one they use,
  and the team folder works the same with both.

## The team's context

If `.agents/team-context.md` exists, read it before any task for the team: it says how the
team works, its roles, processes and how it uses each tool. If it does not exist yet, offer
once to set it up (`.agents/rules/team-context.md`).

## What lives where

Everything in this folder belongs to the team.

| Path | What it is | Who edits it |
|---|---|---|
| `.agents/skills/<skill>/` | The team's skills (`SKILL.md` + optional `scripts/`) | You, when asked |
| `.agents/rules/` | Rules for the AI, below | You, when asked (sensitive: see `changes.md`) |
| `.agents/permissions.json` | What the AI may and may not do in the whole folder (general permissions) | You, only after the person agrees to the change |
| A skill's `allowed-tools` | What that skill may do without asking while it runs | You, with `skill_permissions.py`, only after the person agrees |
| `.agents/team.json`, `.agents/brand.json`, `.agents/brand/` | Team settings and company brand | You, when asked (sensitive) |
| `.agents/team-context.md` | How the team works: roles, processes, tools | You, after interviewing the team (`.agents/rules/team-context.md`) |
| `.agents/system/` | The machinery: team checks, team page, launcher steps, scripts | Only when the person clearly asks, after explaining the effect (sensitive) |
| `.claude/`, `.codex/` | **Generated** from `.agents/` on every save | Never edit. Change `.agents/` instead |
| Visible folders (documents, artifacts) | The team's own work | The team and you |
| `IDEAS.md` | The team's ideas, one line each | You, only through `ideas.py` |

## Rules

Read a rule file **only when its situation applies**. The team may add its own rules to `.agents/rules/`; read them the same way.

| When | Read |
|---|---|
| Creating, migrating or editing a skill | `.agents/rules/skills.md` |
| Producing a report, presentation, dashboard, web app or any HTML output | `.agents/rules/artifacts.md` |
| Anything involving credentials, messages to people, or changing permissions | `.agents/rules/safety.md` |
| Changing a skill, rule, permission, hook or team setting, or sharing a change that clashes with someone else's | `.agents/rules/changes.md` |
| Someone shares an idea for the team, or asks about the team's ideas | `.agents/rules/ideas.md` |
| The team has no context file yet, or someone wants to set up or update how the team works | `.agents/rules/team-context.md` |
| An "IMPROVEMENT REVIEW" note appears, or someone asks what could work better | `.agents/rules/improvements.md` |
| Any other task covered by a file in `.agents/rules/` | That file |

## Sharing changes with the team

After you change anything the team uses (a skill, a rule, a permission, a hook, a document,
a team artifact), **save it for the whole team straight away, without asking**:

```
sh .agents/system/bin/py -I .agents/system/scripts/propose_change.py --summary "<one plain sentence>" --paths <files or folders you changed>
```

List in `--paths` only what belongs to this change, so other unsaved work stays where it is.

Then tell the person in one line, with its `message`. Do not ask "shall I save it?": saving is
the normal end of every change. A sensitive change (`.agents/rules/changes.md`) is explained and
agreed **before** you make it, not again before saving. Private artifacts are never saved.
Every change reaches the team's main version straight away,
and the team page's History shows who changed what. A skill can go back to any earlier version
from the team page. Never push to `main` yourself; always use the script.

**Cloud sessions** (Claude Code on the web, Codex cloud) often start on a branch of their own.
That branch is not the team's version: nobody sees it. Still share with the script, which
sends the change to the team's main version. Do not leave the work on the session's branch or
open a pull request instead, even if the tool suggests it.

## Improvement prompts

The AI Champion may receive emails with suggested improvements, each with a prompt to paste
here. Nothing changes in this folder unless they paste one. Treat it like any team wide change
(`.agents/rules/changes.md`): explain in plain words what it will change, ask, apply it here,
check it, then save it for the whole team. "Get the team's latest" is a different
thing: it only brings teammates' changes.

Before changing how the AI works for the whole team (skills, rules, permissions, hooks,
settings), read `.agents/rules/changes.md`.

## Opening the team page

Every session started in this folder starts the team page in the background, without opening
the person's own browser, and its first message gives the address. If you have a built-in
browser, open that address in it straight away. If someone asks to open the page again, start it
with `TEAM_PAGE_NO_BROWSER=1 uv run --quiet --no-project --python 3.12 --with streamlit==1.41.1 .agents/system/facade/page.py`
in the background (never the launcher, which opens their browser), read the address it prints
and open it in your built-in browser.

## Always

- **Deterministic first.** Fixed steps belong in scripts inside the skill; you only reason where judgement is needed.
- **Never send or schedule** messages, emails or posts. Prepare a draft and tell the person where it is.
- **Never read or print secrets** (`.env`, keys, tokens). Ask the person to configure them instead.
- **Nothing is lost.** Every change goes through git. Do not force-push or rewrite history.
- After changing anything in `.agents/`, regenerate the tool files: `sh .agents/system/bin/py .agents/system/scripts/sync.py`.
- **If a team check stops you** (a message starting with "TEAM CHECKS", or a blocked save), never work around it. Follow its instructions, and tell the person what to do in one simple sentence (usually: double-click the team launcher).
