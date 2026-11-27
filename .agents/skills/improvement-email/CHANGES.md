# Improvements to the team workspace

Newest first. Each entry says, in plain words, what improves for the team and whether
anyone has to do anything. Written for people who are not technical.

## 2026-11-27 — A simpler list of artifacts

**What the team gets**
- On the team page, each artifact is just its name: one click opens the app, or shows the report
  or presentation. An (i) icon next to it says what it is, when its description has that part.
  The folder buttons and the long descriptions are gone.
- The team's shared artifacts come first; your own come after, each with a button to delete it
  (it asks first: they are only on your computer).

**What you need to do**
- Paste this in your AI assistant, opened in your team folder:

  > Bring the simpler artifacts list from ai-team-template: update `app.py` and `look.py` in
  > `.agents/system/facade/` as in the template, check the Artifacts section of the team page,
  > and save it for the team.

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
