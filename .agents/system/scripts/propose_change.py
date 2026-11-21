#!/usr/bin/env python3
"""Save a change for the whole team. Used by the agent and by the team page.

  sh .agents/system/bin/py -I .agents/system/scripts/propose_change.py --summary "Added a weekly report skill" \
      --paths .agents/skills/weekly-report

--paths limits the change to those files or folders (plus the generated .claude/ and .codex/),
so unrelated unsaved work in the folder is left alone. Without it, everything changed is shared.

The change goes straight to the team's main version, under the person's own git name, and
the team page's History shows who changed what. It works from any branch (cloud sessions
start on their own): what is shared is always the team's main version.

Output is JSON for the agent or the team page:
  status: nothing | published | conflict | saved_not_shared | blocked
  message: what to tell the person, in the team's language

Standard library only.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEAM = ROOT / ".agents/team.json"
GENERATED = [".claude", ".codex"]

TEXT = {
    "en": {
        "nothing": "There is nothing new to share.",
        "published": "Done: the change is now available to the whole team.",
        "conflict": "Someone else changed the same thing meanwhile. Your change is saved on this computer; "
                    "ask the AI to combine both before sharing again.",
        "saved": "The change was saved on this computer, but it could not be sent to the team yet ({why}).",
        "blocked": "The change was not saved: {why}",
    },
    "es": {
        "nothing": "No hay nada nuevo para compartir.",
        "published": "Listo: el cambio ya está disponible para todo el equipo.",
        "conflict": "Alguien más cambió lo mismo mientras tanto. Tu cambio quedó guardado en esta computadora; "
                    "pedile a la IA que combine los dos antes de compartir de nuevo.",
        "saved": "El cambio quedó guardado en esta computadora, pero todavía no se pudo enviar al equipo ({why}).",
        "blocked": "El cambio no se guardó: {why}",
    },
}


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)


def language():
    try:
        lang = json.loads(TEAM.read_text(encoding="utf-8")).get("language")
    except (OSError, ValueError):
        lang = None
    return lang if lang in TEXT else "en"


def commit(summary, paths=None):
    if paths:
        git("add", "--all", "--", *paths, *[g for g in GENERATED if (ROOT / g).exists()])
    else:
        git("add", "--all")
    result = git("commit", "-m", summary)
    return None if result.returncode == 0 else (result.stdout + result.stderr).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--summary", required=True, help="one plain sentence describing the change")
    parser.add_argument("--paths", nargs="*", default=None, help="only share these files or folders")
    args = parser.parse_args()

    t = TEXT[language()]
    out = lambda status, message: print(json.dumps({"status": status, "message": message}, ensure_ascii=False))

    git("fetch", "--quiet", "origin")
    has_upstream = git("rev-parse", "--verify", "--quiet", "origin/main").returncode == 0
    status_args = ["status", "--porcelain"] + (["--", *args.paths, *GENERATED] if args.paths else [])
    dirty = bool(git(*status_args).stdout.strip())
    ahead = int(git("rev-list", "--count", "origin/main..HEAD").stdout.strip() or 0) if has_upstream else 0
    if not dirty and not ahead:
        out("nothing", t["nothing"])
        return 0

    if dirty:
        problem = commit(args.summary, args.paths)
        if problem:
            out("blocked", t["blocked"].format(why=problem))
            return 1
    if has_upstream and git("pull", "--rebase", "--autostash", "--quiet", "origin", "main").returncode != 0:
        git("rebase", "--abort")
        out("conflict", t["conflict"])
        return 0
    push = git("push", "origin", "HEAD:main")
    if push.returncode != 0:
        out("saved_not_shared", t["saved"].format(why=push.stderr.strip()[:200]))
        return 0
    out("published", t["published"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
