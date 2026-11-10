# Rule: artifacts

Applies when producing a report, dashboard, presentation or any HTML output.

- Artifacts are files the team opens in a browser. Save them in the visible artifacts folder
  (`artifacts/` or `artefactos/`, depending on the team's language).
- **Ask whether it is for the team or private** before saving, unless the person already said.
  - Team: the artifacts folder. It is committed and everyone with the repository sees it.
  - Private: the `private/` (`privado/`) subfolder. It is never committed and stays on this computer.
- One self-contained HTML file per artifact (styles and data inline), so it opens anywhere.
- If an artifact will be rebuilt regularly, build it with a script inside the skill so every
  run looks the same (see the skills rule).
- Follow any team standard in `.agents/local/rules/` (colours, logo, layout).
