# Rule: artifacts

Applies when producing a report, presentation, dashboard, small web app or any HTML output.

## Everything goes in the artifacts folder, one folder per artifact

Every artifact lives in the visible artifacts folder (`artifacts/`, or `artefactos/` for a
Spanish team), in its own folder with everything it needs. Create that folder with the script,
never by hand, so names and places are always the same:

```
sh .agents/system/bin/py -I .agents/system/scripts/new_artifact.py --type <report|presentation|dashboard|app> --title "<plain title>" [--private]
```

It answers with the folder, laid out like this:

```
artifacts/                                (artefactos/)
  reports/2026-11-26-weekly-sales/        (reportes/, presentaciones/, tableros/, aplicaciones/)
    index.html     what opens: the report, the slides, the app
    assets/        its images, data, styles and code
    README.md      what it is, who made it, how to make it again
  private/                                (privado/) the same layout, only on this computer
```

- **Type:** `report` (a document to read), `presentation` (slides), `dashboard` (numbers and
  charts to check), `app` (something people use: a form, a calculator, a small tool).
- **Name:** `<date>-<short-name>`, made by the script from the title. Do not rename it.
- **`index.html`** is the entry point. It opens straight from the folder by double-click: link
  to its files with relative paths (`assets/chart.js`), never to other artifacts or to files
  outside its folder.
- **`assets/`** holds everything else it uses. Data it reads, images, styles, scripts.
- **`README.md`:** fill in the two short sections the script leaves: what it is, and how to make
  it again (what to ask, or the script that builds it, and where the data comes from).
- **Team or private:** ask whether it is for the team or only for the person, unless they said.
  `--private` puts it in the private folder: it is never shared and stays on this computer.
  A team artifact is a change like any other: offer to share it with the team (AGENTS.md).
- **A new version** of an artifact the team keeps updating (the weekly report) replaces the files
  in the same folder; git keeps the earlier versions. A different artifact gets a new folder.

## Brand and repeat runs

- **Brand:** if `.agents/brand.json` exists, use its colours, font and logo
  (`.agents/brand/logo.png`, copied into the artifact's `assets/`).
- If an artifact will be rebuilt regularly, build it with a script inside the skill so every
  run looks the same (see the skills rule), and name that script in the README.
- Follow any team standard in `.agents/rules/` (colours, logo, layout).

## Also publishing it in Claude or Codex (optional)

If the person also wants a link to share (a Claude artifact or Codex's equivalent), publish it
there too, then record the link so the team page lists it, and write it in the artifact's
README:

```
sh .agents/system/bin/py -I .agents/system/scripts/artifact_link.py --title "<plain title>" --url "<link>" [--private]
```

The folder in the artifacts folder is still the team's copy.
