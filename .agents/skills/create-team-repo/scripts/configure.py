#!/usr/bin/env python3
"""Turn a fresh copy of the template into a team's repository. Run once, from its root.

  sh .agents/core/bin/py .agents/skills/create-team-repo/scripts/configure.py \
      --company "Acme" --team "Sales" --language en --template-commit <40-char hash>

What it does (deterministic, so every team repository starts the same way):
- writes .agents/local/team.json (company, team, language, launcher name)
- creates the visible folders documents/ and artifacts/
- replaces the template README with the team's README
- renames the launchers Team-AI.* to <Team>-AI.*
- records the template commit in .agents/core/manifest.json (core version)
- removes the template-only skills (this one), then regenerates .claude/ and .codex/

Standard library only.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
MANIFEST = ROOT / ".agents" / "core" / "manifest.json"
TEAM_FILE = ROOT / ".agents" / "local" / "team.json"
TEMPLATE_LAUNCHER = "Team-AI"
VISIBLE_DIRS = ["documents", "artifacts"]

README = """# {team} AI workspace

The shared AI workspace of the {team} team at {company}.

## How to use it

1. Double-click **{launcher}** in this folder. The first time, it installs what is needed.
2. Open Claude or Codex, choose this folder, and ask for what you need in your own words.

## What is here

| Folder | What goes in it |
|---|---|
| `documents/` | The team's documents |
| `artifacts/` | Reports and dashboards to share with the team |
| `artifacts/private/` | Reports only for you: they stay on your computer |

Anything else is organised as the team likes. Questions: ask your AI Champion.
"""


def launcher_name(team):
    """'sales ops' -> 'Sales-Ops-AI'; drops characters Windows does not allow in file names."""
    clean = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", team).strip()
    words = [w[:1].upper() + w[1:] for w in re.split(r"[\s_-]+", clean) if w]
    return "-".join(words + ["AI"])


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--company", required=True)
    parser.add_argument("--team", required=True)
    parser.add_argument("--language", required=True, choices=["en", "es"])
    parser.add_argument("--template-commit", required=True)
    args = parser.parse_args()

    if not MANIFEST.is_file():
        print("Run this from the root of the new team repository.")
        return 1
    if TEAM_FILE.exists():
        print("This repository is already configured for a team.")
        return 1
    if not re.fullmatch(r"[0-9a-f]{40}", args.template_commit):
        print("--template-commit must be the full 40-character commit hash.")
        return 1

    launcher = launcher_name(args.team)
    TEAM_FILE.parent.mkdir(parents=True, exist_ok=True)
    TEAM_FILE.write_text(json.dumps({
        "company": args.company,
        "team": args.team,
        "language": args.language,
        "launcher": launcher,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for d in VISIBLE_DIRS:
        (ROOT / d).mkdir(exist_ok=True)
        (ROOT / d / ".gitkeep").touch()

    (ROOT / "README.md").write_text(
        README.format(team=args.team, company=args.company, launcher=launcher), encoding="utf-8")

    for ext in (".command", ".bat"):
        src = ROOT / f"{TEMPLATE_LAUNCHER}{ext}"
        if src.exists():
            src.rename(ROOT / f"{launcher}{ext}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["source"]["commit"] = args.template_commit
    template_only = manifest.pop("template_only_skills", [])
    manifest["system_skills"] = [s for s in manifest.get("system_skills", []) if s not in template_only]
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for skill in template_only:
        shutil.rmtree(ROOT / ".agents" / "skills" / skill, ignore_errors=True)

    sync = subprocess.run([sys.executable, str(ROOT / ".agents/core/scripts/sync.py")], check=False)

    print(json.dumps({"launcher": launcher, "removed_skills": template_only, "sync_ok": sync.returncode == 0}))
    return 0 if sync.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
