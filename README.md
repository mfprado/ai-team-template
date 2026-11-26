# AI Team Template

Template for a team's shared AI workspace. Each team gets its own copy: a private folder where the team keeps its AI skills, documents and artifacts, with the technical parts hidden.

One template for every language: English (`en`) and Spanish (`es`).

> **AI assistants:** if someone asks you to create their team's AI workspace with this template,
> download it to a temporary folder, read `.agents/skills/create-team-repo/SKILL.md` and follow
> it, in the language they wrote in.

## Create a team repository (AI Champions)

Open Claude or Codex on your Desktop and paste this, in your team's language. The language you
write in is the language your team's workspace is set up in.

**English**

> Create my team's AI workspace with https://github.com/mfprado/ai-team-template

**Español**

> Creá el espacio de IA de mi equipo con https://github.com/mfprado/ai-team-template

The `create-team-repo` skill asks for the company, team and brand, creates an empty private
repository, copies this template's files into it (never its history) and configures it. Every
commit in the team's repository is the AI Champion's own; nothing in it points back to this
template.

## Languages

`create-team-repo` takes the team's language from the AI Champion's request and sets it up
with `configure.py`: the team page, the team's `README.md` (always that name), the visible
folders (`documents/` and `artifacts/`, or `documentos/` and `artefactos/`) and the team skills.
The rules and `AGENTS.md` stay in English: only the AI reads them, and it answers in the team's
language.

A team skill people see on the team page has one version per language. English is the live one
in `.agents/skills/`; the others live in `.agents/skills/create-team-repo/team-skills/<language>/`
and replace it when a team is created (`LOCALISED_SKILLS` in `configure.py`). Today that is
`migrate-skill` / `migrar-skill`. **Change both versions together.**

The permissions' reasons (what people read on the team page and when the AI is stopped) are
translated the same way: `team-skills/es/permission-reasons.json`. A new rule in
`.agents/permissions.json` needs its Spanish reason there too.

## Improvements: suggested by email, applied by each team

Each team's folder belongs to the team. This template never changes it.

1. **Maintainers** improve the template here and run `improvement-email`: it writes a
   plain-words entry with **one prompt per improvement** in
   `.agents/skills/improvement-email/CHANGES.md`, and prepares one email draft per AI Champion
   from the *AI Champions* sheet (drafts only; a maintainer sends them).
2. **Each AI Champion** picks the improvements they want and pastes each prompt in Claude or
   Codex opened in their team folder. The assistant explains what will change, asks, applies
   it, checks it and saves it for the whole team.

## What the team sees

Only their own work: the icon that opens the workspace, this README, and their documents and artifacts folders. Everything technical lives in hidden folders.

The team page (opened by the icon) shows the team's skills, each with a flow diagram of its steps,
checks and the tools it uses (with their logos) in the company's design, which also opens as a page, a request to paste and earlier versions to go back to, the artifacts, ideas, permissions and the history of changes.

## How it works

- **One universal source.** Skills, rules and permissions live in `.agents/`, in open formats any agent reads (`AGENTS.md`, Agent Skills `SKILL.md`).
- **Generated per tool.** On every save, `.agents/system/scripts/sync.py` writes what each tool needs: `.claude/` for Claude Code, `.codex/` for Codex. Nobody edits those by hand.
- **Everyone saves for the team.** Changes reach the team's main version straight away; History shows who changed what, and a skill can go back to any earlier version.
- **Guardrails.** `.agents/permissions.json` says what the AI may not do. It is enforced by each tool's native settings and by a guard hook that runs before every tool call. The save checks strictly validate permissions, settings, brand and rules.
- **What the guard is for.** It prevents mistakes and common tricks by people and agents who
  mean well; it is not a sandbox against a determined attacker.

## Structure

```
Team-AI.command / .bat   launcher (renamed <Team>-AI): installs what is needed, opens the team page
AGENTS.md                instructions for any agent
CLAUDE.md                imports AGENTS.md (Claude Code)
.agents/
  skills/                the team's skills
  rules/                 rules for the AI (the team can add its own)
  permissions.json       what the AI may not do
  team.json, brand.json  team settings and company brand (created at setup)
  system/                the machinery: team checks, team page, launcher steps, scripts
.claude/  .codex/        generated, do not edit
```

Template-only skills (never copied to teams): `create-team-repo`, `improvement-email`.
