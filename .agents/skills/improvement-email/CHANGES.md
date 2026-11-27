# Improvements to the team workspace

Newest first. Each entry says, in plain words, what improves for the team and whether
anyone has to do anything. Written for people who are not technical.

## 2026-11-27 — The AI learns how your team works

**What the team gets**
- A short interview with the AI Champion (about 10 minutes) about how the team works: roles,
  routines, main processes and how it uses each tool. The AI assistant reads it before every
  task, so its answers fit the team, and it suggests the solutions that would help the team most.
- New team folders are always created in the company's GitHub organization, and the AI adoption
  team can follow them.

**What you need to do**
- Paste this in your AI assistant, opened in your team folder:

  > Add the team context rule from ai-team-template: create `.agents/rules/team-context.md` as
  > in the template, add its row to the rules table and the "The team's context" section to
  > AGENTS.md, save it for the team, and then interview me to set up how my team works.

## 2026-11-27 — Apps have a way back to the team page

**What the team gets**
- Every app the team makes (the ones that open in their own browser tab) shows a
  "Back to the team page" link at the top.

**What you need to do**
- Paste this in your AI assistant, opened in your team folder:

  > Bring the "back to the team page" link from ai-team-template: update `run_app.py` and
  > `look.py` in `.agents/system/facade/` and the apps note in `.agents/rules/artifacts.md` as in
  > the template, check that an app opened from the team page shows the link, and save it for
  > the team.

## 2026-11-10 — First version

**What the team gets**
- One shared folder where the team keeps its AI skills, documents and reports.
- Works the same with Claude and with Codex.
- Safety limits: the AI can prepare messages but never send them, never reads passwords or
  keys, and never erases the team's history.
- The team's checks repair themselves: if something breaks, opening the team launcher fixes it.
- A guided way to bring an existing automation into the team (`migrate-skill`).

**What you need to do**
- Nothing. This is the version your workspace started with.
