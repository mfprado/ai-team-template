#!/usr/bin/env python3
"""Record a hosted artifact (published in Claude or Codex) so the team page lists it.

  sh .agents/system/bin/py -I .agents/system/scripts/artifact_link.py \
      --title "Weekly sales" --url "https://claude.ai/..."

Like every artifact, a link starts private: <artifacts>/private/links.json, only on this computer.
The team page's Share button moves it to <artifacts>/links.json and saves it for the team.
Adding the same address again updates its title. Prints the file it wrote, as JSON.
Standard library only.
"""

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def folders():
    """The visible artifacts folder and its private subfolder, in the team's language."""
    try:
        lang = json.loads((ROOT / ".agents/team.json").read_text(encoding="utf-8")).get("language")
    except (OSError, ValueError):
        lang = "en"
    base = ROOT / ("artefactos" if lang == "es" else "artifacts")
    return base, base / ("privado" if lang == "es" else "private")


def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--title", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--private", action="store_true", help=argparse.SUPPRESS)  # always private now
    args = parser.parse_args()
    if not args.url.startswith("https://"):
        print(json.dumps({"error": "The address must start with https://"}))
        return 1

    base, private = folders()
    path = private / "links.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    who = subprocess.run(["git", "-C", str(ROOT), "config", "user.name"], capture_output=True, text=True).stdout.strip()
    links = [l for l in load(path) if l.get("url") != args.url]
    links.append({"title": args.title, "url": args.url, "by": who, "date": f"{datetime.date.today()}"})
    path.write_text(json.dumps(links, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"file": str(path.relative_to(ROOT)), "links": len(links)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
