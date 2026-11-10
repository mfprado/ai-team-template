---
name: release-core
description: For the template's maintainers only. Publish a new version of the team workspace core - write the plain-words entry in .agents/core/CHANGES.md and prepare one email draft per onboarded AI Champion from the AI Champions sheet. Use when a maintainer says "release the core", "publish a new version", "announce the update to the champions".
---

# Release a new core version

For **maintainers of this template**, never for AI Champions. The audience of everything you
write here is **non-technical**: AI Champions and their teams.

This skill is **template-only**: it is never copied into a team's repository.

## 1. What changed

Find the last release (the newest `## ` heading in `.agents/core/CHANGES.md` and the commit
that added it), then list what changed for teams since then:

```
git log --oneline <that commit>..HEAD -- .agents/core AGENTS.md CLAUDE.md Team-AI.command Team-AI.bat .agents/permissions.json .agents/skills/migrate-skill
```

Summarize the changes for the maintainer and confirm which ones teams will notice.

## 2. Write the entry

Add a new entry at the top of `.agents/core/CHANGES.md` (below the intro), in this shape:

```
## <YYYY-MM-DD> — <short title>

**What the team gets**
- <one line per improvement, in everyday words: what gets better or safer, not how>

**What you need to do**
- <usually: "Nothing beyond accepting the update." Mention new safety rules they will be asked about.>
```

No jargon (no "hook", "repo", "commit", "MCP"). Show it to the maintainer and adjust until
approved. Then commit and push it to the template (the maintainer's own commit).

The version teams will see is the date of this entry plus the commit that contains it.

## 3. Prepare the emails (drafts only)

Read the **AI Champions** Google Sheet (columns: Name, Email, Company, Team, Team repository,
Language, Core version, Onboarding date, Last email sent, Notes). Skip rows without an email.

For each Champion, **create a draft** (never send) in their `Language`, using this structure:

- **Subject:** New improvements for your team's AI workspace (<date>)
- **Body:**
  1. Greeting by first name; one sentence on why this matters for their team.
  2. The "What the team gets" bullets, translated if needed.
  3. How to apply it, step by step:
     - Open Claude or Codex in an empty folder and paste:
       "Update my team's AI workspace with the latest version of
       https://github.com/mfprado/ai-team-template. Download it to a temporary folder, read
       `.agents/skills/update-team-repo/SKILL.md` and follow it step by step, asking me before
       each action."
     - The assistant will show what changes and ask before doing anything.
     - At the end, review the pull request on GitHub and click **Merge pull request**.
  4. "Reply to this email if anything is unclear."

Use the Spanish template URL (`ia-team-template`) for Spanish-speaking Champions once it exists.

## 4. Report and wait

List the drafts created (name, email, language) and tell the maintainer they can review and
send them. Do **not** change the sheet yet.

When the maintainer confirms the emails were sent, fill **Last email sent** with
`<date> — version <YYYY-MM-DD>` for those rows. If no tool can edit the sheet, give the
maintainer the exact values to paste.

## Tools

- Shell: `git`
- Google Drive (read the AI Champions sheet), Gmail (create drafts only)
