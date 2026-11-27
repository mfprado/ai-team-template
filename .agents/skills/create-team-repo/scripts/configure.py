#!/usr/bin/env python3
"""Copy the template's skeleton into a team's new, empty repository and configure it.

Run from the TEMPLATE folder (a fresh copy of ai-team-template):

  sh .agents/system/bin/py .agents/skills/create-team-repo/scripts/configure.py \
      --target "<path to the team's empty repository>" \
      --company "Acme" --team "Sales" --language en \
      --champion-name "Maria Prado" --champion-email "maria@acme.com"

The team's repository receives plain files, never the template's git history, so every
commit in it is made by the AI Champion. Nothing in it points back to the template.

--champion-github is optional: when left out, the GitHub username is read from the GitHub CLI
(gh) if it is signed in, and left empty otherwise. Only the email is needed by the team checks.

What it does (deterministic, so every team repository starts the same way):
- copies every file the template tracks, except the template-only skills (TEMPLATE_ONLY)
- swaps the team skills that have a version in the team's language (LOCALISED_SKILLS)
- writes the permissions' reasons in the team's language (team-skills/<language>/permission-reasons.json)
- writes .agents/team.json (company, team, language, launcher name, AI Champion)
- creates the visible folders in the team's language (documents/ and artifacts/, or
  documentos/ and artefactos/)
- writes the team's README.md in the team's language
- renames the launchers Team-AI.* to <Team>-AI.*
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
# Skills that only make sense in the template itself (creating teams, writing improvement emails).
TEMPLATE_ONLY = ["create-team-repo", "improvement-email"]
# Team skills with a version per language. English is the live skill in .agents/skills/; other
# languages are kept in create-team-repo/team-skills/<language>/<name>/ and replace it.
LOCALISED_SKILLS = {"migrate-skill": {"es": "migrar-skill"}}
TEAM_SKILLS = TEMPLATE / ".agents/skills/create-team-repo/team-skills"
VISIBLE_DIRS = {"en": ["documents", "artifacts"], "es": ["documentos", "artefactos"]}
IDEAS = {
    "en": "# Team ideas\n\nIdeas for the team's AI workspace. Anyone can add one or update its status.\n\n",
    "es": "# Ideas del equipo\n\nIdeas para el espacio de IA del equipo. Cualquiera puede sumar una o cambiar su estado.\n\n",
}

README = {
    "en": """# {team} AI workspace

The shared AI workspace of the {team} team at {company}.

## How to use it

1. Double-click **{launcher}** in this folder. The first time, it installs what is needed.
2. Open your AI assistant, choose this folder, and ask for what you need in your own words.

## What is here

| Folder | What goes in it |
|---|---|
| `documents/` | The team's documents |
| `artifacts/` | Reports, presentations, dashboards and small apps, each in its own folder by type (`reports/2026-11-26-weekly-sales/`) |
| `artifacts/private/` | The same, only for you: it stays on your computer |
| `IDEAS.md` | The team's ideas: tell the assistant "I have an idea", or add it on the team page |

Anything else is organised as the team likes. Questions: ask your AI Champion.
""",
    "es": """# Espacio de IA de {team}

El espacio de IA compartido del equipo {team} de {company}.

## Cómo usarlo

1. Hacé doble clic en **{launcher}** en esta carpeta. La primera vez instala lo necesario.
2. Abrí tu asistente de IA, elegí esta carpeta y pedí lo que necesites con tus palabras.

## Qué hay acá

| Carpeta | Qué va adentro |
|---|---|
| `documentos/` | Los documentos del equipo |
| `artefactos/` | Reportes, presentaciones, tableros y pequeñas apps, cada uno en su carpeta por tipo (`reportes/2026-11-26-ventas-semanales/`) |
| `artefactos/privado/` | Lo mismo, solo para vos: queda en tu computadora |
| `IDEAS.md` | Las ideas del equipo: decile al asistente "tengo una idea", o sumala en la página del equipo |

Lo demás se organiza como el equipo prefiera. Dudas: preguntale a tu IA Champion.
""",
}


def git(*args, cwd=TEMPLATE):
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True).stdout


def launcher_name(team):
    """'sales ops' -> 'Sales-Ops-AI'; drops characters Windows does not allow in file names."""
    clean = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", team).strip()
    words = [w[:1].upper() + w[1:] for w in re.split(r"[\s_-]+", clean) if w]
    return "-".join(words + ["AI"])


SYSTEM_FILES = (".DS_Store", "Thumbs.db", "desktop.ini")


def target_is_empty_repo(target):
    if not (target / ".git").exists():
        return False
    # Files the system adds on its own (Finder, Explorer) do not count as content.
    entries = [p for p in target.iterdir() if p.name not in (".git", *SYSTEM_FILES)]
    has_commits = subprocess.run(["git", "-C", str(target), "rev-parse", "--verify", "HEAD"],
                                 capture_output=True).returncode == 0
    return not entries and not has_commits


def copy_skeleton(target, template_only, language):
    replaced = [s for s, versions in LOCALISED_SKILLS.items() if language in versions]
    left_out = template_only + replaced
    skip = tuple(f".agents/skills/{s}/" for s in left_out) + tuple(f".claude/skills/{s}/" for s in left_out)
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
    for skill in replaced:
        local = LOCALISED_SKILLS[skill][language]
        shutil.copytree(TEAM_SKILLS / language / local, target / ".agents/skills" / local)
    return copied


def localise_permissions(target, language):
    """The reasons people read on the team page and when the AI is stopped, in the team's language."""
    reasons = TEAM_SKILLS / language / "permission-reasons.json"
    if not reasons.is_file():
        return
    translated = json.loads(reasons.read_text(encoding="utf-8"))
    path = target / ".agents/permissions.json"
    permissions = json.loads(path.read_text(encoding="utf-8"))
    for rule in permissions.get("rules", []):
        rule["reason"] = translated.get(rule.get("reason"), rule.get("reason"))
    path.write_text(json.dumps(permissions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def gh_username():
    try:
        out = subprocess.run(["gh", "api", "user", "--jq", ".login"], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", required=True)
    parser.add_argument("--company", required=True)
    parser.add_argument("--team", required=True)
    parser.add_argument("--language", required=True, choices=["en", "es"])
    parser.add_argument("--champion-name", required=True)
    parser.add_argument("--champion-email", required=True)
    parser.add_argument("--champion-github", default=None)
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    if not target_is_empty_repo(target):
        print("The target must be the team's new, EMPTY repository, already downloaded (cloned).")
        return 1
    if git("status", "--porcelain").strip():
        print("The template copy has unsaved changes; download a fresh copy of the template first.")
        return 1

    copied = copy_skeleton(target, TEMPLATE_ONLY, args.language)
    github = args.champion_github if args.champion_github is not None else gh_username()
    launcher = launcher_name(args.team)
    team_file = target / ".agents/team.json"
    team_file.parent.mkdir(parents=True, exist_ok=True)
    team_file.write_text(json.dumps({
        "company": args.company, "team": args.team, "language": args.language, "launcher": launcher,
        "champion": {"name": args.champion_name, "email": args.champion_email, "github": github},
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    localise_permissions(target, args.language)

    for d in VISIBLE_DIRS[args.language]:
        (target / d).mkdir(exist_ok=True)
        (target / d / ".gitkeep").touch()

    (target / "IDEAS.md").write_text(IDEAS[args.language], encoding="utf-8")
    (target / "README.md").write_text(
        README[args.language].format(team=args.team, company=args.company, launcher=launcher), encoding="utf-8")

    for ext in (".command", ".bat"):
        src = target / f"{TEMPLATE_LAUNCHER}{ext}"
        if src.exists():
            src.rename(target / f"{launcher}{ext}")

    sync = subprocess.run([sys.executable, "-I", str(target / ".agents/system/scripts/sync.py")], cwd=target,
                          capture_output=True, text=True)
    print(json.dumps({
        "launcher": launcher, "files_copied": copied, "left_out": TEMPLATE_ONLY, "sync_ok": sync.returncode == 0,
    }))
    return 0 if sync.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
