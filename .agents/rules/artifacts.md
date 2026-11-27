# Rule: artifacts

Applies when producing a report, presentation, dashboard, small web app or any HTML output.

## Everything goes in the artifacts folder, one folder per artifact

Every artifact lives in the visible artifacts folder (`artifacts/`, or `artefactos/` for a
Spanish team), in its own folder with everything it needs. Create that folder with the script,
never by hand, so names and places are always the same:

```
sh .agents/system/bin/py -I .agents/system/scripts/new_artifact.py --type <report|presentation|dashboard|app> --title "<plain title>" [--streamlit]
```

It answers with the folder, laid out like this:

```
artifacts/                                (artefactos/)
  private/                                (privado/) where every artifact starts, only on this computer
    reports/2026-11-26-weekly-sales/      (reportes/, presentaciones/, tableros/, aplicaciones/)
      index.html     what opens: the report, the slides, the app
      assets/        its images, data, styles and code
      README.md      what it is, who made it, how to make it again
  reports/2026-11-20-monthly-close/       once shared: the same layout, for the whole team
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
- **It starts private.** Every new artifact is created in the private folder: only on this
  computer, never saved for the team. Do not ask whether it is for the team. When it is ready,
  the person shares it with the **Share with the team** button on the team page (it asks them
  to confirm), or asks you to: then run
  `sh .agents/system/bin/py -I .agents/system/scripts/share_artifact.py --path "<its folder>"`,
  which moves it to the team's artifacts folder and saves it for the team. Tell them its message.
- **A new version** of an artifact the team keeps updating (the weekly report) replaces the files
  in the same folder; git keeps the earlier versions. A different artifact gets a new folder.

## Buttons

Controls that are a common action use their usual icon, with the words in a tooltip
(`title` and `aria-label`): full screen is an expand icon (a collapse icon while in full
screen), close is ×, next and previous are arrows. Keep words on buttons whose action is not obvious.

## Apps: HTML or Streamlit

An app (`--type app`) or a dashboard can be built two ways. Choose by what it needs:

- **HTML (`index.html`)**, the default: when the browser is enough. A calculator, a form that
  does not save anything, a presentation, a dashboard over a fixed data file. It opens anywhere.
- **Streamlit (`--streamlit`)**: when it needs Python: reading or writing files, a spreadsheet,
  calling the AI, heavier data work. The script makes the folder with:
  - `app.py`, already in the company's look (it uses the team page's `look.py`); write the app
    below the title,
  - a launcher named after the app, `<App-name>.command` (Mac) and `<App-name>.bat` (Windows):
    double-click it to open the app in the browser. Do not rename or edit the launchers,
  - `requirements.txt`, only if it needs Python packages beyond Streamlit (one per line, with
    its version),
  - `assets/` and the README, as for any artifact; the README says how to open it.

  Every Streamlit app shows a **Back to the team page** link at the top on its own (from
  `look.css`): do not add another one.

  The team page's Open button starts it the same way. It runs on the person's computer, while
  its window is open; anything it saves goes to a file in `assets/` or a team spreadsheet, and
  the README says where. To use it without the team folder it would need hosting: say so, do not
  set it up.

## Dashboards

Build a dashboard (`--type dashboard`) on the pattern of
https://advanced-dashboard-demo.streamlit.app/, in the company's colours and type:

- **Header:** the title, and under it one line saying what is shown right now ("All regions,
  all plans, last 12 months"). On the right, Reset and Export.
- **Controls in one row:** the period as quick choices (3M, 6M, 12M, 24M) and the other filters
  in one Filters menu. Every chart follows them.
- **First row: 3 to 5 key numbers**, each in its own card: its name, the number large, the change
  as a small green or red chip with what it is compared to ("+5.4 pts vs. 24 months ago"), and
  a small trend line or bars underneath.
- **Then the charts**, each in a card with a short title and one line saying what it shows, the
  legend above the chart, values formatted for people ($1.2M, 12%), and a tooltip on hover.
  Choose the chart for the question: lines for change over time, stacked areas for parts of a
  total, a waterfall for what moved a number, a heatmap for when, bars for comparing.
- **Clicking a part of a chart filters the rest** (a slice, a bar), and the header line says so.
- **Last, a table** of the rows that matter most (top accounts, open deals), sortable.
- **Colour:** the brand's main colour for the main series, then a few colours that sit well
  with it for the others; green and red only for good and bad changes. Background, text and
  font from the brand. Light grid lines, no 3D, no decoration.
- It stays one artifact folder: `index.html` with the charts (a charting library from a CDN is
  fine), the data in `assets/`, and in the README where the data comes from and how to refresh it.

## Look at it before you finish

Open what you made (the `index.html`, or the app with its launcher) and look at every view
before saying it is done; take screenshots if your tools can. Fix what looks wrong: text that
is hard to read on the brand's background (dark brands especially), logos that disappear,
buttons or labels that break onto two lines, cut or overlapping parts, empty views with no
explanation, warnings or errors on screen. Then say in one line that you checked it.

## Brand and repeat runs

- **Brand:** if `.agents/brand.json` exists, use its colours, logo (`.agents/brand/logo.png`,
  copied into the artifact's `assets/`) and type: its `font_family` first (its files from
  `.agents/brand/fonts/`, copied into `assets/`, or from Google Fonts), then `font` (sans or
  serif) as the fallback. A Streamlit app gets all of this from `look.py` already.
- If an artifact will be rebuilt regularly, build it with a script inside the skill so every
  run looks the same (see the skills rule), and name that script in the README.
- Follow any team standard in `.agents/rules/` (colours, logo, layout).

## Bringing in an artifact made in Claude (or ChatGPT, Gemini...)

Someone may have made an artifact in the Claude app (a page, a dashboard, a small app) and now
wants it in the team's folder. When they ask ("upload my Claude artifact", "save this artifact
for the team", "cargá mi artefacto"), guide them one short step at a time:

1. **Ask for it, the easy way first.** Ask them to paste the artifact's link, or, if you cannot
   open links, to download it: in Claude, open the artifact, use its menu (the three dots or the
   download button) and choose **Download**; then attach the file here or say where it is
   (usually Downloads). If there is no download option, ask them to choose **Copy** and paste
   the code here. Never ask them to log in for you or to share passwords.
2. **Read it before you keep it.** Look at the whole file. If it sends data somewhere, loads
   scripts from unknown sites, or contains keys or passwords, tell them in plain words and do
   not save it until they fix it.
3. **Create its folder with `new_artifact.py`** as for any artifact (choose the type from what it
   is), and put the file in as `index.html`. A React or JSX artifact does not open on its own:
   turn it into a plain `index.html` that loads React from a CDN, and check it works. Move
   large data or images into `assets/`.
4. **Fill in the README:** what it is, that it came from Claude, and its link if they have one.
   If there is a link, also record it with `artifact_link.py` (below) so the team page lists it.
5. **Open it and look** (see "Look at it before you finish"). It starts private like every
   artifact; tell them they can share it with the **Share with the team** button, or ask you.

## Also publishing it in Claude or Codex (optional)

If the person also wants a link to share (a Claude artifact or Codex's equivalent), publish it
there too, then record the link so the team page lists it, and write it in the artifact's
README:

```
sh .agents/system/bin/py -I .agents/system/scripts/artifact_link.py --title "<plain title>" --url "<link>"
```

The folder in the artifacts folder is still the team's copy.
