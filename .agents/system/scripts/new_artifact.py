#!/usr/bin/env python3
"""Create the folder for a new artifact, always with the same name and layout.

  sh .agents/system/bin/py -I .agents/system/scripts/new_artifact.py \
      --type report|presentation|dashboard|app --title "Weekly sales" [--private]

Every artifact (an HTML report, a presentation, a dashboard, a small web app) is one folder:

  <artifacts>/<type>/<YYYY-MM-DD>-<short-name>/
      index.html     what opens: the report, the slides, the app
      assets/        its images, data, styles and code
      README.md      what it is, who made it, and how to make it again

<artifacts> is artifacts/ (artefactos/ for a Spanish team); <type> is reports, presentations,
dashboards or apps (reportes, presentaciones, tableros, aplicaciones). --private puts it in the
private subfolder, which stays on this computer. The short name is the title in lowercase,
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
    parser.add_argument("--private", action="store_true")
    args = parser.parse_args()

    lang = language()
    base, private = folders(lang)
    today = datetime.date.today().isoformat()
    parent = (private if args.private else base) / TYPES[lang][args.type]
    folder = parent / f"{today}-{slug(args.title)}"
    n = 2
    while folder.exists():
        folder = parent / f"{today}-{slug(args.title)}-{n}"
        n += 1
    (folder / "assets").mkdir(parents=True)
    (folder / "assets" / ".gitkeep").touch()
    who = subprocess.run(["git", "-C", str(ROOT), "config", "user.name"], capture_output=True, text=True).stdout.strip()
    (folder / "README.md").write_text(README[lang].format(title=args.title.strip(), type=TYPES[lang][args.type],
                                                          who=who or "?", date=today), encoding="utf-8")
    print(json.dumps({"folder": str(folder.relative_to(ROOT)), "entry": str((folder / "index.html").relative_to(ROOT))}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
