---
name: create-team-repo
description: Guide an AI Champion, step by step, to create their team's AI workspace (a private GitHub repository) from this template. Use when someone says "create my team's repository", "create a repo for my team from this template", "set up my team's AI workspace", or pastes the workshop prompt that points to ai-team-template.
---

# Create a team's repository

You are helping an **AI Champion** create their team's shared AI workspace, usually during
the first workshop. Go **one step at a time**: explain the step in a sentence, ask what you
need, and **ask before every action** that creates, downloads or publishes anything.
Talk in the Champion's language. Keep it short and friendly; they may not be technical.
When you ask for OK, say what will happen in plain words (one or two lines). Do not show
commands, file paths or how scripts work unless they ask; you still read scripts before running them.

This skill is **template-only**: it is never copied into the team's repository.

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

## 2. Company, team and the AI Champion

The Champion is learning: most have never used GitHub. With them, never say "repository",
"owner", "clone" or "launcher". Say **the team's shared folder** (it lives on GitHub and on
each teammate's computer) and **the icon you double-click to open it**.

Ask only three things:

1. The **company** name.
2. The **team** name.
3. Their **full name** and the **email** they use for GitHub (or will use, if they have no
   account yet).

Do not ask for their GitHub username: you learn it later (step 3 or 5).

Then ask: **"Did someone at your company (for example IT) already create a shared folder on
GitHub for your team and send you a link?"**

- **Yes:** ask for the link. It looks like `https://github.com/<owner>/<repo-name>`; take both
  from it and skip creating it in step 3. It must be empty and the Champion must be able to
  manage it; if not, tell them to ask the person who created it.
- **No:** ask if they already have a GitHub account with that email. If not, guide them: open
  https://github.com/signup, sign up with that email, choose the **Free** plan, confirm the
  email GitHub sends, and tell you when done. The shared folder will live in their own account.

The Champion is the only person who updates the team's main version directly; everyone
else's changes reach them as change requests to approve. Say it in one sentence.

Propose the name, and confirm:

- **Shared folder name:** `<company>-<team>-ai`, lowercase, hyphens (e.g. `acme-sales-ai`).
  This is the repository name on GitHub. Skip it when the folder already exists.

Then just tell them (nothing to choose): on their Desktop they will get a folder called
`<Team>-AI` (e.g. `Sales-AI`), with an icon of the same name they double-click to open it.
Internally that is the launcher name, `<Team>-AI`.

## 3. Create the EMPTY shared folder on GitHub

Skip this step when the company already created it (step 2).

The team's repository must contain only the Champion's own commits, never ours. So it starts
**empty** and receives the template's files as plain files (no template history).

**If you can create it yourself** (`gh auth status` succeeds, or a GitHub connector can create
repositories): the owner is the signed-in account (`gh api user --jq .login`), which is also
the Champion's GitHub username. Say what you will create, in plain words, and wait for OK.

```
gh repo create <owner>/<repo-name> --private
```

**Otherwise, guide the Champion click by click:**
1. Open https://github.com/new (sign in if GitHub asks).
2. Repository name: `<repo-name>`. Visibility: **Private**. Leave the owner as it is.
3. Leave **everything else empty**: no README, no .gitignore, no license.
4. Click **Create repository**, then paste you the address of the page that opens
   (`https://github.com/<owner>/<repo-name>`). The owner in it is their GitHub username.

## 4. Download it to the Desktop

The Champion opened you on their Desktop. Still find the real Desktop (it moves with
OneDrive and language on Windows) and use that path:

```
sh TEMPLATE_DIR/.agents/core/bin/py TEMPLATE_DIR/.agents/skills/create-team-repo/scripts/desktop_path.py "<Team>-AI"
```

It prints the Desktop path, then `free` or `exists` for `<Desktop>/<Team>-AI`. Do not check
with another command (a failing check looks like an error to the Champion). If it `exists`, stop and ask the Champion what it is; never mix
files into it. Otherwise ask before downloading the empty shared folder there:

```
git clone https://github.com/<owner>/<repo-name>.git "<Desktop>/<Team>-AI"
```

Git warns that the repository is empty: that is expected. If it asks the Champion to sign in
to GitHub, tell them to follow the window that opens.

## 5. Copy the skeleton and configure it

From `TEMPLATE_DIR`:

```
sh .agents/core/bin/py .agents/skills/create-team-repo/scripts/configure.py \
  --target "<Desktop>/<Team>-AI" --company "<company>" --team "<team>" --language <en|es> \
  --champion-name "<full name>" --champion-email "<GitHub account email>" [--champion-github "<username>"]
```

Pass `--champion-github` only when you learned the username in step 3 and the shared folder
is in the Champion's own account; otherwise leave it out and the script reads it from `gh`
when it can.

It copies the template's files (not its history, and not the template-only skills), writes
the team settings, creates `documents/` and `artifacts/`, writes the team README, renames the
launchers and records the core version (date + commit). Nothing in the new repository points
back to the template.

## 6. Make sure commits are in the Champion's name

Every commit must be authored by the Champion. In the new folder, check:

```
git config user.name
git config user.email
```

Show the result: "Your changes will be saved as: <name> <email>". If either is missing or
does not match the name and GitHub email from step 2, set them for this repository only:

```
git config user.name "<full name>"
git config user.email "<GitHub account email>"
```

Then, after showing a one-line summary of what will be saved and getting OK:

```
git add --all
git commit -m "Set up <team> AI workspace"
git branch -M main
git push -u origin main
```

The team's checks run on this commit (generated files, secrets, skills). If they stop it,
explain the message in plain words and fix it. Never commit or push under any other name.

## 6b. Protect the team's main version

Only the Champion should update `main`; teammates send change requests. The team's checks
already enforce this on every computer. If `gh` is available, also ask GitHub to require a
change request for `main` (the owner can still update it directly), after OK:

```
gh api -X PUT repos/<owner>/<repo-name>/branches/main/protection --input - <<'JSON'
{"required_status_checks": null, "enforce_admins": false,
 "required_pull_request_reviews": {"required_approving_review_count": 0},
 "restrictions": null}
JSON
```

If GitHub answers that the plan does not allow it (private repositories need a paid plan),
tell the Champion, in two short sentences: the team's checks already prevent mistakes on
every computer, and with a paid GitHub plan (Pro or Team) the main version can be protected
for real, so nobody but them can change it. Then continue.

## 7. Prepare this computer

Ask the Champion to double-click the **`<Team>-AI`** icon in the new folder. The first time it
installs what is needed, turns on the team checks, hides technical files and lets Codex
use the team rules. If it shows an error, read it with them and help.

## 8. First automation

Offer to bring their first automation into the team now with **migrate-skill**: they can
paste or attach a skill, script, instructions or macro they already use.

## 9. Clean up and close

- Delete `TEMPLATE_DIR` (the temporary copy), after saying so.
- Tell the Champion, in three short lines: where the folder is, how to open it (the
  `<Team>-AI` icon, then choose the folder in Claude or Codex), and what comes next (adding
  teammates is a later step with their facilitator).

## Tools

- Shell: `git`, `gh` (optional), `sh .agents/core/bin/py <script>`
- Never cherry-pick, merge or push template commits into the team's repository.
- Scripts: `scripts/desktop_path.py`, `scripts/configure.py`
