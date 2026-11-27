#!/usr/bin/env python3
"""Create the folder for a new artifact, always with the same name and layout.

  sh .agents/system/bin/py -I .agents/system/scripts/new_artifact.py \
      --type report|presentation|dashboard|app --title "Weekly sales" [--streamlit]

Every artifact (an HTML report, a presentation, a dashboard, a small web app) is one folder:

  <artifacts>/private/<type>/<YYYY-MM-DD>-<short-name>/
      index.html     what opens: the report, the slides, the app
      assets/        its images, data, styles and code
      README.md      what it is, who made it, and how to make it again

With --streamlit (apps and dashboards that need Python: files, spreadsheets, AI), the folder
holds app.py instead of index.html, already in the company's look, and a launcher named after
the app (Weekly-sales.command for Mac, Weekly-sales.bat for Windows): double-click it to open
the app. The team page's Open button starts it the same way (.agents/system/facade/run_app.py).
Extra Python packages go in requirements.txt next to app.py.

<artifacts> is artifacts/ (artefactos/ for a Spanish team); <type> is reports, presentations,
dashboards or apps (reportes, presentaciones, tableros, aplicaciones). Every artifact starts in
the private subfolder (privado/), only on this computer, until the person shares it with the team
(the team page's Share button, or share_artifact.py). The short name is the title in lowercase,
without accents, with hyphens. Prints the folder as JSON; the caller writes index.html.
Standard library only.
"""

import argparse
import datetime
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TYPES = {
    "en": {"report": "reports", "presentation": "presentations", "dashboard": "dashboards", "app": "apps"},
    "es": {"report": "reportes", "presentation": "presentaciones", "dashboard": "tableros", "app": "aplicaciones"},
}
README = {
    "en": "# {title}\n\n- Type: {type}\n- Made by: {who}, {date}\n\n## What it is\n\n(One or two lines.)\n\n"
          "## How to make it again\n\n(What to ask the AI, or the script that builds it, and where the data comes from.)\n",
    "es": "# {title}\n\n- Tipo: {type}\n- Hecho por: {who}, {date}\n\n## Qué es\n\n(Una o dos líneas.)\n\n"
          "## Cómo volver a hacerlo\n\n(Qué pedirle a la IA, o el script que lo arma, y de dónde salen los datos.)\n",
}


APP = '''"""{title}: a team app. Open it with {launcher}.command (Mac) or {launcher}.bat (Windows),
or from the team page."""

import json
import sys
from pathlib import Path

import streamlit as st

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / ".agents").is_dir())
sys.path.insert(0, str(ROOT / ".agents/system/facade"))
import look  # noqa: E402  the company's look, like the team page

TITLE = {title!r}

st.set_page_config(page_title=TITLE, layout="wide")
try:
    brand = json.loads((ROOT / ".agents/brand.json").read_text(encoding="utf-8"))
except (OSError, ValueError):
    brand = {{}}
st.markdown(look.css(brand), unsafe_allow_html=True)
st.title(TITLE)

# The app starts here. Its data and images go in assets/ (HERE / "assets").
'''

MAC_LAUNCHER = """#!/bin/bash
# Opens this app in the browser. Keep this window open while you use it.
cd "$(dirname "$0")" || exit 1
APP="$(pwd)"
ROOT="$APP"
while [ ! -d "$ROOT/.agents" ] && [ "$ROOT" != "/" ]; do ROOT="$(dirname "$ROOT")"; done
export PATH="$HOME/.local/bin:$PATH"
if [ ! -d "$ROOT/.agents" ] || ! command -v uv >/dev/null 2>&1; then
  echo "Open the team folder with its icon once first: it installs what the app needs."
  read -r -p "Press Enter to close this window." _
  exit 1
fi
REQ=()
[ -f requirements.txt ] && REQ=(--with-requirements requirements.txt)
uv run --quiet --no-project --python 3.12 --with streamlit==1.41.1 "${{REQ[@]}}" "$ROOT/.agents/system/facade/run_app.py" "$APP"
"""

WINDOWS_LAUNCHER = """@echo off
rem Opens this app in the browser. Keep this window open while you use it.
setlocal
cd /d "%~dp0"
set "APP=%CD%"
set "ROOT=%CD%"
:up
if exist "%ROOT%\\.agents\\" goto found
for %%I in ("%ROOT%\\..") do set "PARENT=%%~fI"
if "%PARENT%"=="%ROOT%" goto missing
set "ROOT=%PARENT%"
goto up
:found
set "PATH=%USERPROFILE%\\.local\\bin;%PATH%"
where uv >nul 2>nul
if errorlevel 1 goto missing
set "REQ="
if exist requirements.txt set "REQ=--with-requirements requirements.txt"
uv run --quiet --no-project --python 3.12 --with streamlit==1.41.1 %REQ% "%ROOT%\\.agents\\system\\facade\\run_app.py" "%APP%"
exit /b 0
:missing
echo Open the team folder with its icon once first: it installs what the app needs.
pause
exit /b 1
"""

README_APP = {
    "en": "\n## How to open it\n\nDouble-click `{launcher}.command` (Mac) or `{launcher}.bat` (Windows) in this folder, "
          "or use Open on the team page. Keep the window that appears open while you use it.\n",
    "es": "\n## Cómo abrirla\n\nHacé doble clic en `{launcher}.command` (Mac) o `{launcher}.bat` (Windows) en esta "
          "carpeta, o usá Abrir en la página del equipo. Dejá abierta la ventana que aparece mientras la usás.\n",
}


def launcher_name(title):
    """'Weekly sales' -> 'Weekly-sales': the app's name, readable, safe on Mac and Windows."""
    name = slug(title)
    return name[:1].upper() + name[1:]


def language():
    try:
        lang = json.loads((ROOT / ".agents/team.json").read_text(encoding="utf-8")).get("language")
    except (OSError, ValueError):
        lang = "en"
    return lang if lang in TYPES else "en"


def folders(lang):
    base = ROOT / ("artefactos" if lang == "es" else "artifacts")
    return base, base / ("privado" if lang == "es" else "private")


def slug(title):
    plain = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    words = re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")
    return words[:50].rstrip("-") or "artifact"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--type", required=True, choices=sorted(TYPES["en"]))
    parser.add_argument("--title", required=True)
    parser.add_argument("--private", action="store_true", help=argparse.SUPPRESS)  # always private now
    parser.add_argument("--streamlit", action="store_true", help="a Streamlit app (app.py) instead of index.html")
    args = parser.parse_args()
    if args.streamlit and args.type not in ("app", "dashboard"):
        parser.error("--streamlit is for apps and dashboards")

    lang = language()
    base, private = folders(lang)
    today = datetime.date.today().isoformat()
    parent = private / TYPES[lang][args.type]
    folder = parent / f"{today}-{slug(args.title)}"
    n = 2
    while folder.exists():
        folder = parent / f"{today}-{slug(args.title)}-{n}"
        n += 1
    (folder / "assets").mkdir(parents=True)
    (folder / "assets" / ".gitkeep").touch()
    who = subprocess.run(["git", "-C", str(ROOT), "config", "user.name"], capture_output=True, text=True).stdout.strip()
    readme = README[lang].format(title=args.title.strip(), type=TYPES[lang][args.type], who=who or "?", date=today)
    entry = folder / "index.html"
    if args.streamlit:
        launcher = launcher_name(args.title)
        entry = folder / "app.py"
        entry.write_text(APP.format(title=args.title.strip(), launcher=launcher), encoding="utf-8")
        mac = folder / f"{launcher}.command"
        mac.write_text(MAC_LAUNCHER.format(), encoding="utf-8")
        mac.chmod(0o755)
        (folder / f"{launcher}.bat").write_bytes(WINDOWS_LAUNCHER.format().replace("\n", "\r\n").encode())
        readme += README_APP[lang].format(launcher=launcher)
    (folder / "README.md").write_text(readme, encoding="utf-8")
    print(json.dumps({"folder": str(folder.relative_to(ROOT)), "entry": str(entry.relative_to(ROOT))}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
