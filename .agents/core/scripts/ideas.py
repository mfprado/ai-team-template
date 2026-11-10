#!/usr/bin/env python3
"""Manage the team's ideas in IDEAS.md (used by the agent and the team page).

  ideas.py add --text "An idea"             adds it as new, with today's date and your git name
  ideas.py list                             prints the ideas as JSON
  ideas.py status --id 3 --to planned       changes an idea's status (AI Champion only)

One line per idea, readable by people and easy to edit:
  - [New] 2026-11-10 · Juan Perez — Automate the weekly sales report

Status words follow the team's language (team.json). Standard library only.
"""

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FILE = ROOT / "IDEAS.md"
STATUSES = {
    "en": {"new": "New", "planned": "Planned", "done": "Done"},
    "es": {"new": "Nueva", "planned": "En camino", "done": "Hecha"},
}
HEADER = {
    "en": "# Team ideas\n\nIdeas for the team's AI workspace. Anyone can add one; the AI Champion updates its status.\n\n",
    "es": "# Ideas del equipo\n\nIdeas para el espacio de IA del equipo. Cualquiera puede sumar una; el IA Champion actualiza su estado.\n\n",
}
LINE = re.compile(r"^- \[(?P<status>[^\]]+)\] (?P<date>\d{4}-\d{2}-\d{2}) · (?P<who>.+?) — (?P<text>.+)$")


def team():
    try:
        return json.loads((ROOT / ".agents/local/team.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def lang():
    return team().get("language") if team().get("language") in STATUSES else "en"


def git_config(key):
    return subprocess.run(["git", "-C", str(ROOT), "config", key], capture_output=True, text=True).stdout.strip()


def read():
    if not FILE.is_file():
        return HEADER[lang()], []
    text = FILE.read_text(encoding="utf-8")
    lines = text.splitlines()
    first = next((i for i, l in enumerate(lines) if LINE.match(l)), len(lines))
    header = "\n".join(lines[:first]).rstrip() + "\n\n"
    ideas = []
    for l in lines[first:]:
        m = LINE.match(l)
        if m:
            ideas.append(m.groupdict())
    return header, ideas


def write(header, ideas):
    body = "".join(f"- [{i['status']}] {i['date']} · {i['who']} — {i['text']}\n" for i in ideas)
    FILE.write_text(header + body, encoding="utf-8")


def status_key(label):
    for words in STATUSES.values():
        for key, word in words.items():
            if word.lower() == label.lower():
                return key
    return "new"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    add = sub.add_parser("add")
    add.add_argument("--text", required=True)
    sub.add_parser("list")
    st = sub.add_parser("status")
    st.add_argument("--id", type=int, required=True)
    st.add_argument("--to", required=True, choices=["new", "planned", "done"])
    args = parser.parse_args()

    header, ideas = read()
    words = STATUSES[lang()]
    if args.cmd == "list":
        print(json.dumps([dict(i, id=n + 1, key=status_key(i["status"])) for n, i in enumerate(ideas)], ensure_ascii=False))
        return 0
    if args.cmd == "add":
        text = " ".join(args.text.split())
        if not text:
            print(json.dumps({"ok": False, "problem": "empty idea"}))
            return 1
        ideas.append({"status": words["new"], "date": datetime.date.today().isoformat(),
                      "who": git_config("user.name") or "?", "text": text})
        write(header, ideas)
        print(json.dumps({"ok": True, "id": len(ideas)}))
        return 0
    champion = str(team().get("champion", {}).get("email", "")).lower()
    if not champion or git_config("user.email").lower() != champion:
        print(json.dumps({"ok": False, "problem": "only the AI Champion changes an idea's status"}))
        return 1
    if not 1 <= args.id <= len(ideas):
        print(json.dumps({"ok": False, "problem": "no idea with that number"}))
        return 1
    ideas[args.id - 1]["status"] = words[args.to]
    write(header, ideas)
    print(json.dumps({"ok": True}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
