---
name: create-team-repo
description: Guide an AI Champion, step by step, to create their team's AI workspace (a private GitHub repository) from this template. Use when someone says "create my team's repository", "create a repo for my team from this template", "set up my team's AI workspace", or pastes the workshop prompt that points to ai-team-template.
---

# Create a team's repository

You are helping an **AI Champion** create their team's shared AI workspace, usually during
the first workshop. Go **one step at a time**: explain the step in a sentence, ask what you
need, and **ask before every action** that creates, downloads or publishes anything.
Talk in the Champion's language. Keep it short and friendly; they may not be technical.

This skill is **template-only**: it is removed from the team's repository at the end.

You are probably running from a temporary copy of the template. Call it `TEMPLATE_DIR`.

## 1. Language

Ask which language the team works in. The language decides the template:

| Language | Template |
|---|---|
| English | `https://github.com/mfprado/ai-team-template` |
| Spanish | `https://github.com/mfprado/ia-team-template` |

If the chosen template is not the one you are running from, explain it and continue with
that template's own `create-team-repo` skill. If that template is still empty, say the
Spanish version is not ready yet and offer to continue in English or stop.

## 2. Company and team

Ask for the **company** and the **team** names. Propose, and confirm:

- Repository name: `<company>-<team>-ai`, lowercase, hyphens (e.g. `acme-sales-ai`).
- Launcher name: `<Team>-AI` (e.g. `Sales-AI`), the file the team double-clicks.
- GitHub owner: the Champion's account or the company's organization. Ask which.

## 3. Create the repository on GitHub

Record the template commit first (the version the team starts from):

```
git ls-remote <template URL> HEAD
```

Keep the 40-character hash.

**If you can create it yourself** (`gh auth status` succeeds, or a GitHub connector can
create a repository from a template): say exactly what you will create and wait for OK.

```
gh repo create <owner>/<repo-name> --private --template <template owner>/<template name>
```

**Otherwise, guide the Champion click by click:**
1. Open the template page and click **Use this template** → **Create a new repository**.
2. Owner: `<owner>`. Repository name: `<repo-name>`. Visibility: **Private**.
3. Click **Create repository**, and tell you when it is done.

## 4. Download it to the Desktop

Find the real Desktop (it moves with OneDrive and language on Windows):

```
sh TEMPLATE_DIR/.agents/core/bin/py TEMPLATE_DIR/.agents/skills/create-team-repo/scripts/desktop_path.py
```

Ask before cloning into `<Desktop>/<Launcher name>` (e.g. `Desktop/Sales-AI`):

```
git clone https://github.com/<owner>/<repo-name>.git "<Desktop>/<Launcher name>"
```

If the clone asks the Champion to sign in to GitHub, tell them to follow the window that opens.

## 5. Configure it for the team

From the new folder (not `TEMPLATE_DIR`):

```
sh .agents/core/bin/py .agents/skills/create-team-repo/scripts/configure.py \
  --company "<company>" --team "<team>" --language <en|es> --template-commit <hash>
```

It writes the team settings, creates `documents/` and `artifacts/`, writes the team README,
renames the launchers, records the core version and removes this skill.

## 6. Publish

Show the Champion a one-line summary of what will be saved, then, after OK:

```
git add --all
git commit -m "Set up <team> AI workspace"
git push origin main
```

The team's checks run on this commit (generated files, secrets, skills). If they stop it,
explain the message in plain words and fix it.

## 7. Prepare this computer

Ask the Champion to double-click **`<Launcher name>`** in the new folder. The first time it
installs what is needed, turns on the team checks, hides technical files and lets Codex
use the team rules. If it shows an error, read it with them and help.

## 8. First automation

Offer to bring their first automation into the team now with **migrate-skill**: they can
paste or attach a skill, script, instructions or macro they already use.

## 9. Clean up and close

- Delete `TEMPLATE_DIR` (the temporary copy), after saying so.
- Tell the Champion, in three short lines: where the folder is, how to open it (the
  launcher, then choose the folder in Claude or Codex), and what comes next (adding
  teammates is a later step with their facilitator).

## Tools

- Shell: `git`, `gh` (optional), `sh .agents/core/bin/py <script>`
- Scripts: `scripts/desktop_path.py`, `scripts/configure.py`
