#!/usr/bin/env python3
"""Manage the team's ideas in IDEAS.md (used by the agent and the team page).

  ideas.py add --title "An idea" --text "More detail"
                                            adds it as new, with today's date and your git name
                                            (--text, the description, is optional)
  ideas.py list                             prints the ideas as JSON
  ideas.py status --id 3 --to planned       (or new, done, archived) changes an idea's status (anyone on the team)
  ideas.py comment --id 3 --text "..."      adds a comment to an idea, with today's date and your git name
  ideas.py assign --id 3 [--to "Ana Lopez"] assigns the idea to someone (you, by default)
  ideas.py assign --id 3 --clear            leaves it unassigned again
  ideas.py flow --id 3 --file flow.mmd      saves the idea's workflow diagram (Mermaid flowchart)
  ideas.py flow --id 3 --clear              removes it

One line per idea (its title), readable by people and easy to edit, with an optional description
line ("> ..."), who is working on it ("@ ...") and its comments indented under it:
  - [New] 2026-11-10 · Juan Perez — Automate the weekly sales report
    > Every Monday, from the sales sheet
    @ Ana Lopez
    - 2026-11-12 · Ana Lopez: Let's add the web sales too

An idea about a way of working can have a flow diagram, one file per idea in .agents/ideas/
(idea-<n>.mmd), shown on the team page. Status words follow the team's language (team.json).
Standard library only.
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
FLOWS = ROOT / ".agents/ideas"
STATUSES = {
    "en": {"new": "New", "planned": "Planned", "done": "Done", "archived": "Archived"},
    "es": {"new": "Nueva", "planned": "En camino", "done": "Hecha", "archived": "Archivada"},
}
HEADER = {
    "en": "# Team ideas\n\nIdeas for the team's AI workspace. Anyone can add one or update its status.\n\n",
    "es": "# Ideas del equipo\n\nIdeas para el espacio de IA del equipo. Cualquiera puede sumar una o cambiar su estado.\n\n",
}
LINE = re.compile(r"^- \[(?P<status>[^\]]+)\] (?P<date>\d{4}-\d{2}-\d{2}) · (?P<who>.+?) — (?P<text>.+)$")
DESCRIPTION = re.compile(r"^\s+> (?P<text>.+)$")
ASSIGNEE = re.compile(r"^\s+@ (?P<who>.+)$")
COMMENT = re.compile(r"^\s+- (?P<date>\d{4}-\d{2}-\d{2}) · (?P<who>.+?): (?P<text>.+)$")


def team():
    try:
        return json.loads((ROOT / ".agents/team.json").read_text(encoding="utf-8"))
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
            ideas.append(dict(m.groupdict(), description="", assignee="", comments=[]))
            continue
        d = DESCRIPTION.match(l)
        if d and ideas and not ideas[-1]["comments"]:
            ideas[-1]["description"] = d["text"]
            continue
        a = ASSIGNEE.match(l)
        if a and ideas and not ideas[-1]["comments"]:
            ideas[-1]["assignee"] = a["who"].strip()
            continue
        c = COMMENT.match(l)
        if c and ideas:
            ideas[-1]["comments"].append(c.groupdict())
    return header, ideas


def write(header, ideas):
    body = "".join(f"- [{i['status']}] {i['date']} · {i['who']} — {i['text']}\n"
                   + (f"  > {i['description']}\n" if i.get("description") else "")
                   + (f"  @ {i['assignee']}\n" if i.get("assignee") else "")
                   + "".join(f"  - {c['date']} · {c['who']}: {c['text']}\n" for c in i.get("comments", []))
                   for i in ideas)
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
    add.add_argument("--title", required=True)
    add.add_argument("--text", default="")
    sub.add_parser("list")
    st = sub.add_parser("status")
    st.add_argument("--id", type=int, required=True)
    st.add_argument("--to", required=True, choices=["new", "planned", "done", "archived"])
    cm = sub.add_parser("comment")
    cm.add_argument("--id", type=int, required=True)
    cm.add_argument("--text", required=True)
    asg = sub.add_parser("assign")
    asg.add_argument("--id", type=int, required=True)
    asg.add_argument("--to", default="")
    asg.add_argument("--clear", action="store_true")
    fl = sub.add_parser("flow")
    fl.add_argument("--id", type=int, required=True)
    fl.add_argument("--file")
    fl.add_argument("--clear", action="store_true")
    args = parser.parse_args()

    header, ideas = read()
    words = STATUSES[lang()]
    if args.cmd == "list":
        def flow(n):
            f = FLOWS / f"idea-{n}.mmd"
            return f.read_text(encoding="utf-8") if f.is_file() else ""
        print(json.dumps([dict(i, id=n + 1, me=git_config("user.name"), flow=flow(n + 1), key=status_key(i["status"])) for n, i in enumerate(ideas)], ensure_ascii=False))
        return 0
    if args.cmd == "add":
        title = " ".join(args.title.split())
        description = " ".join(args.text.split())
        if not title:
            print(json.dumps({"ok": False, "problem": "empty idea"}))
            return 1
        ideas.append({"status": words["new"], "date": datetime.date.today().isoformat(),
                      "who": git_config("user.name") or "?", "text": title,
                      "description": description, "comments": []})
        write(header, ideas)
        print(json.dumps({"ok": True, "id": len(ideas)}))
        return 0
    if not 1 <= args.id <= len(ideas):
        print(json.dumps({"ok": False, "problem": "no idea with that number"}))
        return 1
    if args.cmd == "flow":
        target = FLOWS / f"idea-{args.id}.mmd"
        if args.clear:
            target.unlink(missing_ok=True)
            print(json.dumps({"ok": True}))
            return 0
        try:
            diagram = Path(args.file).read_text(encoding="utf-8").strip()
        except (OSError, TypeError):
            print(json.dumps({"ok": False, "problem": "give the diagram with --file"}))
            return 1
        diagram = diagram.removeprefix("```mermaid").removesuffix("```").strip()
        if not diagram.startswith(("flowchart", "graph")):
            print(json.dumps({"ok": False, "problem": "the diagram must be a Mermaid flowchart"}))
            return 1
        FLOWS.mkdir(parents=True, exist_ok=True)
        target.write_text(diagram + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, "path": target.relative_to(ROOT).as_posix()}))
        return 0
    if args.cmd == "assign":
        who = "" if args.clear else (" ".join(args.to.split()) or git_config("user.name") or "?")
        ideas[args.id - 1]["assignee"] = who
        write(header, ideas)
        print(json.dumps({"ok": True, "assignee": who}))
        return 0
    if args.cmd == "comment":
        text = " ".join(args.text.split())
        if not text:
            print(json.dumps({"ok": False, "problem": "empty comment"}))
            return 1
        ideas[args.id - 1]["comments"].append({"date": datetime.date.today().isoformat(),
                                               "who": git_config("user.name") or "?", "text": text})
        write(header, ideas)
        print(json.dumps({"ok": True}))
        return 0
    ideas[args.id - 1]["status"] = words[args.to]
    write(header, ideas)
    print(json.dumps({"ok": True}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
