---
name: update-team-repo
description: Guide an AI Champion to bring the latest improvements of this template into their team's repository, through a pull request they own. Use when someone says "update my team repo", "apply the new version to my team", "bring the latest improvements to my team's workspace", or pastes the update prompt from an improvement email.
---

# Update a team's repository

You are helping an **AI Champion** apply the latest improvements of this template to their
team's repository. They received an email describing the improvements and pasted a prompt.
Go **one step at a time**, explain each step in a sentence, and **ask before every action**
that changes or publishes anything. Talk in the Champion's language; they are not technical.

Ground rules:
- The team's repository only receives **plain files**. Never merge, cherry-pick or push
  template commits into it, and never point it at the template.
- Every commit is **the Champion's own**, and the change arrives as a **pull request** they
  review and accept.
- Never change the team's own things: `.agents/local/`, their skills, documents, artifacts.
  Permissions are only ever **added**, with the Champion's approval.

This skill is **template-only**: it is never copied into a team's repository. You are running
from a fresh copy of the template; call it `TEMPLATE_DIR`.

## 1. Find the team's repository

Ask where their team folder is (usually on the Desktop, named like `Sales-AI`). If they are
not sure, look on the real Desktop:

```
sh .agents/core/bin/py .agents/skills/create-team-repo/scripts/desktop_path.py
```

Then make sure it is current with the team's latest work (ask first):

```
git -C "<team repo>" checkout main
git -C "<team repo>" pull --ff-only
```

## 2. See what changes

From `TEMPLATE_DIR`:

```
sh .agents/core/bin/py .agents/skills/update-team-repo/scripts/update.py plan --target "<team repo>"
```

The result is JSON. If `ok` is false, explain each problem in plain words and help solve it.
If `up_to_date` is true, tell them their workspace already has every improvement, and stop.

Otherwise explain, briefly and without jargon:
- each item in `improvements` (title + what it means for the team),
- that their own skills, documents and settings stay as they are.

## 3. New safety rules (if any)

`proposed_rules` lists default rules their workspace does not have yet. For each one, explain
in one plain sentence what it prevents (use its `reason`), and ask whether to add it. Note the
`index` of each rule they accept. Never add a rule they did not accept.

## 4. Apply on a new branch

After OK:

```
sh .agents/core/bin/py .agents/skills/update-team-repo/scripts/update.py apply --target "<team repo>" --add-rules <accepted indexes, comma-separated>
```

It creates a branch `core-update-<date>`, copies the new core files, adds the accepted rules,
regenerates the tool files and runs the team checks. If `ok` is false, do not continue: explain
the problem in plain words, then undo with `git -C "<team repo>" checkout main` and
`git -C "<team repo>" branch -D <branch>` after asking.

## 5. Commit in the Champion's name

In the team repository, check `git config user.name` and `git config user.email` and show:
"This update will be saved as: <name> <email>". If missing or not theirs, ask for their full
name and their GitHub account email, and set them for this repository only. Then, after OK:

```
git -C "<team repo>" add --all
git -C "<team repo>" commit -m "Update team workspace to version <date>"
git -C "<team repo>" push -u origin <branch>
```

## 6. Open the pull request

If `gh auth status` works, after OK:

```
gh pr create --repo <owner>/<team repo name> --head <branch> --base main \
  --title "Update team workspace to version <date>" --body "<the improvements, in plain words>"
```

Otherwise give them the link `https://github.com/<owner>/<team repo name>/compare/main...<branch>`
and guide them: **Create pull request**, then **Create pull request** again.

## 7. Close

Tell them in three short lines: the pull request is ready, they (or their IT team) can review
it on GitHub, and clicking **Merge pull request** applies the improvements for everyone on the
team (teammates get them automatically the next time they open their AI app).
Then delete `TEMPLATE_DIR`, after saying so.

## Tools

- Shell: `git`, `gh` (optional), `sh .agents/core/bin/py <script>`
- Scripts: `scripts/update.py`, and `create-team-repo/scripts/desktop_path.py`
