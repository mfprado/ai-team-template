#!/usr/bin/env python3
"""A skill's own permissions: what it may do without asking, while it runs.

They live in the skill's SKILL.md front matter as Claude Code's `allowed-tools`, one line of
permission rules separated by spaces, for example:

  allowed-tools: Read Bash(git log *) mcp__Gmail__create_draft

They only add to the team's general permissions (.agents/permissions.json) while the skill runs:
anything blocked for the whole folder stays blocked (the guard hook checks every action).
Codex ignores them.

A permission switched off on the team page moves to `allowed-tools-off` (the team's own field,
which Claude does not read), so it can be switched on again without rewriting it.

Usage:
  sh .agents/system/bin/py -I .agents/system/scripts/skill_permissions.py list --skill <name>
  sh .agents/system/bin/py -I .agents/system/scripts/skill_permissions.py add --skill <name> --rule "<rule>"
  sh .agents/system/bin/py -I .agents/system/scripts/skill_permissions.py remove --skill <name> --rule "<rule>"
  sh .agents/system/bin/py -I .agents/system/scripts/skill_permissions.py off --skill <name> --rule "<rule>"
  sh .agents/system/bin/py -I .agents/system/scripts/skill_permissions.py on --skill <name> --rule "<rule>"

Prints JSON. Standard library only.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FIELD = "allowed-tools"
OFF_FIELD = "allowed-tools-off"
# One rule: a tool name, optionally with what it applies to in parentheses (which may hold spaces).
RULE = re.compile(r"[^\s,()]+(?:\([^()]*\))?")
TOOL = re.compile(r"^(?:[A-Z][A-Za-z]+|mcp__[\w-]+__[\w*-]+|mcp__[\w-]+__\*)(?:\([^()]+\))?$")
# Too broad for a skill: they would let it do anything of that kind without asking.
TOO_BROAD = {"Bash", "Bash(*)", "Write", "Edit", "MultiEdit", "NotebookEdit", "*"}

WORDS = {
    "en": {"read": "Read files", "read_in": "Read files in {x}", "change_in": "Change files in {x}",
           "run": "Run: {x}", "web": "Read web pages", "web_from": "Read web pages from {x}",
           "search": "Search the web", "skill": "Use the {x} skill", "any": "anything in {x}",
           "script": "Run the {x} script", "git": "Git: {x}"},
    "es": {"read": "Leer archivos", "read_in": "Leer archivos en {x}", "change_in": "Cambiar archivos en {x}",
           "run": "Ejecutar: {x}", "web": "Leer páginas web", "web_from": "Leer páginas de {x}",
           "search": "Buscar en internet", "skill": "Usar la skill {x}", "any": "cualquier cosa en {x}",
           "script": "Ejecutar el script {x}", "git": "Git: {x}"},
}


def parse(value):
    """The rules in an allowed-tools value (string, comma or space separated)."""
    return RULE.findall(value or "")


def problem(rule):
    """Why a rule cannot be a skill permission, or None."""
    if rule in TOO_BROAD:
        return f"'{rule}' would let the skill do anything of that kind without asking; name the exact command or folder."
    if not TOOL.match(rule):
        return f"'{rule}' is not a permission rule like Read, Bash(git log *) or mcp__Gmail__create_draft."
    return None


def describe(rule, language="en"):
    """A rule in plain words, for the team page."""
    w = WORDS.get(language, WORDS["en"])
    m = re.match(r"^([^(]+)(?:\((.*)\))?$", rule)
    tool, target = m.group(1), m.group(2)
    if tool.startswith("mcp__"):
        _, server, action = tool.split("__", 2)
        action = w["any"].format(x=server) if action == "*" else action.replace("_", " ")
        return f"{server.replace('_', ' ')}: {action}"
    if tool == "Read":
        return w["read_in"].format(x=target) if target else w["read"]
    if tool in ("Write", "Edit", "MultiEdit"):
        return w["change_in"].format(x=target)
    if tool == "Bash":
        script = re.search(r"scripts/([\w-]+)\.(?:py|sh)\b", target or "")
        if script:
            return w["script"].format(x=script.group(1).replace("_", " "))
        if (target or "").startswith("git "):
            return w["git"].format(x=target[4:].rstrip(" *"))
        return w["run"].format(x=target)
    if tool == "WebFetch":
        return w["web_from"].format(x=target.removeprefix("domain:")) if target else w["web"]
    if tool == "WebSearch":
        return w["search"]
    if tool == "Skill" and target:
        return w["skill"].format(x=target.split()[0])
    return rule


def skill_file(name):
    path = ROOT / ".agents/skills" / name / "SKILL.md"
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name) or not path.is_file():
        raise SystemExit(json.dumps({"ok": False, "problem": f"no skill called '{name}'"}))
    return path


def read_field(text, field):
    """The rules in one front-matter field."""
    if not text.startswith("---"):
        return []
    for line in text[:text.find("\n---", 3)].split("\n"):
        if line.startswith(f"{field}:"):
            return parse(line.split(":", 1)[1])
    return []


def read_rules(text):
    """The rules the skill has switched on, and the index of their line (kept for callers)."""
    return read_field(text, FIELD), None


def write_rules(path, on, off):
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---", 3)
    head = [l for l in text[:end].split("\n") if not l.startswith((f"{FIELD}:", f"{OFF_FIELD}:"))]
    if on:
        head.append(f"{FIELD}: {' '.join(on)}")
    if off:
        head.append(f"{OFF_FIELD}: {' '.join(off)}")
    path.write_text("\n".join(head) + text[end:], encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=["list", "add", "remove", "on", "off"])
    parser.add_argument("--skill", required=True)
    parser.add_argument("--rule")
    parser.add_argument("--language", default="en")
    args = parser.parse_args()

    path = skill_file(args.skill)
    text = path.read_text(encoding="utf-8")
    on, off = read_field(text, FIELD), read_field(text, OFF_FIELD)
    if args.action == "list":
        print(json.dumps([{"rule": r, "plain": describe(r, args.language), "on": r in on} for r in on + off],
                         ensure_ascii=False))
        return 0
    if not args.rule:
        print(json.dumps({"ok": False, "problem": "say which permission with --rule"}))
        return 1
    rule = args.rule.strip()
    if args.action in ("add", "on"):
        if args.action == "on" and rule not in off:
            print(json.dumps({"ok": False, "problem": f"the skill has no switched-off '{rule}'"}))
            return 1
        why = problem(rule)
        if why:
            print(json.dumps({"ok": False, "problem": why}))
            return 1
        on, off = on + ([rule] if rule not in on else []), [r for r in off if r != rule]
    elif args.action == "off":
        if rule not in on:
            print(json.dumps({"ok": False, "problem": f"the skill does not have '{rule}' switched on"}))
            return 1
        on, off = [r for r in on if r != rule], off + [rule]
    else:
        if rule not in on + off:
            print(json.dumps({"ok": False, "problem": f"the skill does not have '{rule}'"}))
            return 1
        on, off = [r for r in on if r != rule], [r for r in off if r != rule]
    write_rules(path, on, off)
    print(json.dumps({"ok": True, "path": str(path.relative_to(ROOT))}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
