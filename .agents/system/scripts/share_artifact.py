#!/usr/bin/env python3
"""Share a private artifact with the team: move it from the private folder to the team's and save it.

  sh .agents/system/bin/py -I .agents/system/scripts/share_artifact.py --path "<artifact folder or file>"

Every artifact starts private (<artifacts>/private/, or artefactos/privado/), only on the computer
of whoever made it. Sharing moves it to the same place in the team's artifacts folder
(private/reports/2026-11-26-weekly-sales/ -> reports/2026-11-26-weekly-sales/; a name already
taken gets -2) and saves it for the whole team with propose_change.py. Used by the team page's
Share button and by the AI when someone asks to share an artifact.

Prints JSON: {"ok": true, "path": ..., "message": ...} or {"ok": false, "problem": ...}.
Standard library only.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def folders():
    try:
        lang = json.loads((ROOT / ".agents/team.json").read_text(encoding="utf-8")).get("language")
    except (OSError, ValueError):
        lang = "en"
    base = ROOT / ("artefactos" if lang == "es" else "artifacts")
    return base, base / ("privado" if lang == "es" else "private"), lang


def title_of(path):
    readme = path / "README.md" if path.is_dir() else None
    if readme and readme.is_file():
        for line in readme.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    return path.stem.replace("-", " ").capitalize()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--path", required=True)
    args = parser.parse_args()

    base, private, lang = folders()
    source = Path(args.path)
    source = (source if source.is_absolute() else ROOT / source).resolve()
    if not source.exists() or private.resolve() not in source.parents:
        print(json.dumps({"ok": False, "problem": "that is not a private artifact"}))
        return 1
    target = base / source.relative_to(private.resolve())
    n = 2
    while target.exists():
        target = target.with_name(f"{target.stem}-{n}{target.suffix}" if source.is_file() else f"{source.name}-{n}")
        n += 1
    target.parent.mkdir(parents=True, exist_ok=True)
    source.rename(target)

    title = title_of(target)
    summary = ("Artefacto compartido: " if lang == "es" else "Shared artifact: ") + title
    saved = subprocess.run([sys.executable, "-I", str(ROOT / ".agents/system/scripts/propose_change.py"),
                            "--summary", summary, "--paths", str(target.relative_to(ROOT))],
                           cwd=ROOT, capture_output=True, text=True)
    try:
        outcome = json.loads(saved.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        outcome = {"status": "blocked", "message": saved.stderr.strip() or saved.stdout.strip()}
    print(json.dumps({"ok": outcome.get("status") == "published", "path": str(target.relative_to(ROOT)),
                      "status": outcome.get("status"), "message": outcome.get("message", "")}, ensure_ascii=False))
    return 0 if outcome.get("status") == "published" else 1


if __name__ == "__main__":
    sys.exit(main())
