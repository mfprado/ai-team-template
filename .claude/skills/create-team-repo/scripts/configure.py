#!/usr/bin/env python3
"""Copy the template's skeleton into a team's new, empty repository and configure it.

Run from the TEMPLATE folder (a fresh copy of ai-team-template):

  sh .agents/core/bin/py .agents/skills/create-team-repo/scripts/configure.py \
      --target "<path to the team's empty repository>" \
      --company "Acme" --team "Sales" --language en \
      --champion-name "Maria Prado" --champion-email "maria@acme.com" --champion-github "mariap"

The team's repository receives plain files, never the template's git history, so every
commit in it is made by the AI Champion. Nothing in it points back to the template.

What it does (deterministic, so every team repository starts the same way):
- copies every file the template tracks, except template-only skills
- writes .agents/local/team.json (company, team, language, launcher name, AI Champion)
- creates the visible folders documents/ and artifacts/
- writes the team's README
- renames the launchers Team-AI.* to <Team>-AI.*
- records the core version (date + commit of the template) in .agents/core/manifest.json
- regenerates .claude/ and .codex/

Standard library only.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[4]
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


def git(*args, cwd=TEMPLATE):
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True).stdout


def launcher_name(team):
    """'sales ops' -> 'Sales-Ops-AI'; drops characters Windows does not allow in file names."""
    clean = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", team).strip()
    words = [w[:1].upper() + w[1:] for w in re.split(r"[\s_-]+", clean) if w]
    return "-".join(words + ["AI"])


def target_is_empty_repo(target):
    if not (target / ".git").exists():
        return False
    entries = [p for p in target.iterdir() if p.name != ".git"]
    has_commits = subprocess.run(["git", "-C", str(target), "rev-parse", "--verify", "HEAD"],
                                 capture_output=True).returncode == 0
    return not entries and not has_commits


def copy_skeleton(target, template_only):
    skip = tuple(f".agents/skills/{s}/" for s in template_only) + tuple(f".claude/skills/{s}/" for s in template_only)
    copied = 0
    for rel in git("ls-files", "-z").split("\0"):
        if not rel or rel.startswith(skip):
            continue
        src, dst = TEMPLATE / rel, target / rel
        if src.is_symlink() or not src.is_file():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1
    return copied


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", required=True)
    parser.add_argument("--company", required=True)
    parser.add_argument("--team", required=True)
    parser.add_argument("--language", required=True, choices=["en", "es"])
    parser.add_argument("--champion-name", required=True)
    parser.add_argument("--champion-email", required=True)
    parser.add_argument("--champion-github", required=True)
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    if not target_is_empty_repo(target):
        print("The target must be the team's new, EMPTY repository, already downloaded (cloned).")
        return 1
    if git("status", "--porcelain").strip():
        print("The template copy has unsaved changes; download a fresh copy of the template first.")
        return 1

    manifest = json.loads((TEMPLATE / ".agents/core/manifest.json").read_text(encoding="utf-8"))
    template_only = manifest.get("template_only_skills", [])
    copied = copy_skeleton(target, template_only)

    commit, date = git("log", "-1", "--format=%H %cs").split()
    manifest.pop("template_only_skills", None)
    manifest["system_skills"] = [s for s in manifest.get("system_skills", []) if s not in template_only]
    manifest["core_version"] = {"date": date, "commit": commit}
    (target / ".agents/core/manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    launcher = launcher_name(args.team)
    team_file = target / ".agents/local/team.json"
    team_file.parent.mkdir(parents=True, exist_ok=True)
    team_file.write_text(json.dumps({
        "company": args.company, "team": args.team, "language": args.language, "launcher": launcher,
        "champion": {"name": args.champion_name, "email": args.champion_email, "github": args.champion_github},
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for d in VISIBLE_DIRS:
        (target / d).mkdir(exist_ok=True)
        (target / d / ".gitkeep").touch()

    (target / "README.md").write_text(
        README.format(team=args.team, company=args.company, launcher=launcher), encoding="utf-8")

    for ext in (".command", ".bat"):
        src = target / f"{TEMPLATE_LAUNCHER}{ext}"
        if src.exists():
            src.rename(target / f"{launcher}{ext}")

    sync = subprocess.run([sys.executable, "-I", str(target / ".agents/core/scripts/sync.py")], cwd=target,
                          capture_output=True, text=True)
    print(json.dumps({
        "launcher": launcher, "files_copied": copied, "core_version": f"{date} ({commit[:7]})",
        "left_out": template_only, "sync_ok": sync.returncode == 0,
    }))
    return 0 if sync.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
