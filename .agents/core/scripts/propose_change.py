#!/usr/bin/env python3
"""Share a change with the whole team. Used by the agent and by the team UI.

  sh .agents/core/bin/py -I .agents/core/scripts/propose_change.py --summary "Added a weekly report skill" \
      --paths .agents/skills/weekly-report

--paths limits the change to those files or folders (plus the generated .claude/ and .codex/),
so unrelated unsaved work in the folder is left alone. Without it, everything changed is shared.

- The AI Champion's changes go straight to the team's main version.
- Anyone else's changes become a change request (a pull request, behind the scenes) that
  the AI Champion reviews and approves. The person never needs to know what that is.

Every commit is made under the person's own git name. Output is JSON for the agent or UI:
  status: nothing | published | requested | saved_not_shared | blocked
  message: what to tell the person, in the team's language
  note_for_champion: (requested) a very short message the person can send to the Champion

Standard library only.
"""

import argparse
import datetime
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEAM = ROOT / ".agents/local/team.json"

TEXT = {
    "en": {
        "nothing": "There is nothing new to share.",
        "published": "Done: the change is now available to the whole team.",
        "requested": "The change request was created. Please let {champion} know so they can review and approve it.",
        "saved": "The change was saved on this computer, but it could not be sent to the team yet ({why}). Please let {champion} know.",
        "blocked": "The change was not saved: {why}",
        "note": "Hi {first}, I sent a change request in our team AI workspace: {summary}. Could you review it? {url}",
    },
    "es": {
        "nothing": "No hay nada nuevo para compartir.",
        "published": "Listo: el cambio ya está disponible para todo el equipo.",
        "requested": "Se creó el pedido de cambio. Avisale a {champion} para que lo revise y lo apruebe.",
        "saved": "El cambio quedó guardado en esta computadora, pero todavía no se pudo enviar al equipo ({why}). Avisale a {champion}.",
        "blocked": "El cambio no se guardó: {why}",
        "note": "Hola {first}, envié un pedido de cambio en el espacio de IA del equipo: {summary}. ¿Lo podés revisar? {url}",
    },
}


def run(*args, check=False):
    return subprocess.run(list(args), cwd=ROOT, capture_output=True, text=True, check=check)


def git(*args):
    return run("git", *args)


def team():
    try:
        return json.loads(TEAM.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def slug(text):
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")[:40] or "change"


def is_champion(info):
    email = git("config", "user.email").stdout.strip().lower()
    return bool(email) and email == str(info.get("champion", {}).get("email", "")).lower()


def remote_url_to_web(url):
    m = re.search(r"github\.com[:/](.+?)(?:\.git)?$", url.strip())
    return f"https://github.com/{m.group(1)}" if m else None


GENERATED = [".claude", ".codex"]


def commit_all(summary, paths=None):
    if paths:
        git("add", "--all", "--", *paths, *[g for g in GENERATED if (ROOT / g).exists()])
    else:
        git("add", "--all")
    result = git("commit", "-m", summary)
    if result.returncode != 0:
        return (result.stdout + result.stderr).strip()
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--summary", required=True, help="one plain sentence describing the change")
    parser.add_argument("--paths", nargs="*", default=None, help="only share these files or folders")
    args = parser.parse_args()

    info = team()
    lang = info.get("language", "en") if info.get("language") in TEXT else "en"
    t = TEXT[lang]
    champion = info.get("champion", {})
    champion_name = champion.get("name") or "your AI Champion"
    out = lambda status, message, **extra: print(json.dumps(dict(status=status, message=message, **extra), ensure_ascii=False)) or 0

    git("fetch", "--quiet", "origin")
    has_upstream = git("rev-parse", "--verify", "--quiet", "origin/main").returncode == 0
    status_args = ["status", "--porcelain"] + (["--", *args.paths, *GENERATED] if args.paths else [])
    dirty = bool(git(*status_args).stdout.strip())
    ahead = int(git("rev-list", "--count", "origin/main..HEAD").stdout.strip() or 0) if has_upstream else 0
    if not dirty and not ahead:
        return out("nothing", t["nothing"])

    # Straight to the team's main version: everyone by default, only the Champion if they approve changes.
    if is_champion(info) or not info.get("changes_need_approval"):
        if dirty:
            problem = commit_all(args.summary, args.paths)
            if problem:
                return out("blocked", t["blocked"].format(why=problem)) or 1
        if has_upstream and git("pull", "--rebase", "--autostash", "--quiet", "origin", "main").returncode != 0:
            git("rebase", "--abort")
            return out("saved_not_shared", t["saved"].format(why="the team version changed meanwhile", champion=champion_name))
        push = git("push", "origin", "HEAD:main")
        if push.returncode != 0:
            return out("saved_not_shared", t["saved"].format(why=push.stderr.strip()[:200], champion=champion_name))
        return out("published", t["published"])

    # Anyone else: a change request on its own branch.
    branch = f"change/{slug(args.summary)}-{datetime.datetime.now():%Y%m%d-%H%M}"
    # Unrelated unsaved work stays on this computer, untouched, while the change is sent.
    stashed = False
    if args.paths:
        others = [l[3:] for l in git("status", "--porcelain").stdout.splitlines()
                  if not any(l[3:].startswith(p.rstrip("/")) for p in [*args.paths, *GENERATED])]
        if others:
            stashed = git("stash", "push", "--include-untracked", "--quiet", "--", *others).returncode == 0
    if git("checkout", "-b", branch).returncode != 0:
        return out("blocked", t["blocked"].format(why=f"could not create {branch}")) or 1
    if dirty:
        problem = commit_all(args.summary, args.paths)
        if problem:
            git("checkout", "-")
            git("branch", "-D", branch)
            if stashed:
                git("stash", "pop", "--quiet")
            return out("blocked", t["blocked"].format(why=problem)) or 1
    if has_upstream:  # keep the local main version identical to the team's
        git("branch", "-f", "main", "origin/main")

    push = git("push", "-u", "origin", branch)
    if push.returncode != 0:
        return out("saved_not_shared", t["saved"].format(why=push.stderr.strip()[:200], champion=champion_name), branch=branch)

    url = None
    if shutil.which("gh"):
        body = f"{args.summary}\n\nRequested by {git('config', 'user.name').stdout.strip()}."
        pr = run("gh", "pr", "create", "--base", "main", "--head", branch, "--title", args.summary, "--body", body)
        if pr.returncode == 0:
            url = pr.stdout.strip().splitlines()[-1]
    if not url:
        web = remote_url_to_web(git("remote", "get-url", "origin").stdout)
        url = f"{web}/compare/main...{branch}?expand=1" if web else branch

    git("checkout", "main")
    if stashed:
        git("stash", "pop", "--quiet")
    first = champion_name.split()[0] if champion.get("name") else champion_name
    return out("requested", t["requested"].format(champion=champion_name), branch=branch, url=url,
               note_for_champion=t["note"].format(first=first, summary=args.summary, url=url))


if __name__ == "__main__":
    sys.exit(main())
