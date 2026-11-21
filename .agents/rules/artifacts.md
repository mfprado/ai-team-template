# Rule: artifacts

Applies when producing a report, dashboard, presentation, small app or any HTML output.

- **Default: publish it in the tool you are running in** (a Claude artifact, or Codex's own
  hosted equivalent). It gets a link, opens anywhere, and the person can share it and keep
  working on it with the tool's own features.
- **Ask whether it is for the team or private** before saving, unless the person already said.
- Then record the link so the team page lists it:

  ```
  sh .agents/system/bin/py -I .agents/system/scripts/artifact_link.py --title "<plain title>" --url "<link>" [--private]
  ```

  A team link is a change like any other: offer to share it with the team (see AGENTS.md).
- **A file instead of a hosted artifact** only when the person asks for a file, or the tool
  cannot publish one. Save it in the visible artifacts folder (`artifacts/` or `artefactos/`):
  - Team: the artifacts folder. It is committed and everyone with the repository sees it.
  - Private: the `private/` (`privado/`) subfolder. It is never committed and stays on this computer.
  - One self-contained HTML file per artifact (styles and data inline), so it opens anywhere.
- If an artifact will be rebuilt regularly, build it with a script inside the skill so every
  run looks the same (see the skills rule).
- **Brand:** if `.agents/brand.json` exists, use its colours, font and logo
  (`.agents/brand/logo.png`, embedded inline in files).
- Follow any team standard in `.agents/rules/` (colours, logo, layout).
