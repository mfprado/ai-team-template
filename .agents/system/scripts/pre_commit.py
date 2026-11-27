#!/usr/bin/env python3
"""Pre-commit checks for a team repository. Runs with or without an agent.

1. Regenerate .claude/ and .codex/ from the staged .agents/ files and add them to the commit.
2. Block private artifacts (artifacts/private/, artefactos/privado/).
3. Block likely secrets in staged files.
4. Check every staged skill has a valid SKILL.md (name + description, name = folder, a
   flow diagram the team page draws, and only narrow permissions in allowed-tools).
5. Strictly check what programs read: permissions, team settings, brand, team rules and hooks.
6. Self-test the guard hook: a broken guard is never saved.

Messages are plain words: the person committing may not be technical.
Standard library only.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PRIVATE_DIRS = ("artifacts/private/", "artefactos/privado/")
SECRET_PATTERNS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "a private key"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "an AWS access key"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"), "an API key (sk-...)"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"), "a GitHub token"),
    (re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{10,}"), "a Slack token"),
    (re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"), "a Google API key"),
]


def git(*args, binary=False):
    out = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, check=False)
    return out.stdout if binary else out.stdout.decode("utf-8", "replace")


def staged_files():
    return [f for f in git("diff", "--cached", "--name-only", "--diff-filter=ACMR").splitlines() if f]


def check_private(files):
    return [f"'{f}' is a private artifact and stays on this computer." for f in files if f.startswith(PRIVATE_DIRS)]


def check_secrets(files):
    problems = []
    for f in files:  # generated .claude/ and .codex/ copies are scanned too
        data = git("show", f":{f}", binary=True)
        if b"\0" in data[:8000]:
            continue  # binary file
        text = data.decode("utf-8", "replace")
        for regex, label in SECRET_PATTERNS:
            if regex.search(text):
                problems.append(f"'{f}' seems to contain {label}. Remove it and keep secrets out of the repository.")
                break
    return problems


def front_matter(text):
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    fields = {}
    for line in text[3:end].splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip("\"'")
    return fields


def load_skill_permissions():
    # Run with -I, so this folder is not importable by name: load it from its path.
    import importlib.util
    spec = importlib.util.spec_from_file_location("skill_permissions", Path(__file__).with_name("skill_permissions.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SKILL_PERMS = load_skill_permissions()


def skill_rules(skill_md):
    text = skill_md.read_text(encoding="utf-8")
    return SKILL_PERMS.read_field(text, SKILL_PERMS.FIELD) + SKILL_PERMS.read_field(text, SKILL_PERMS.OFF_FIELD)


FLOWCHART = re.compile(r"^```mermaid[ \t]*\n\s*(?:flowchart|graph)\b", re.M)


def check_skills(files):
    problems = []
    skills = {Path(f).parts[2] for f in files if f.startswith(".agents/skills/") and len(Path(f).parts) > 3}
    for name in sorted(skills):
        skill_md = ROOT / ".agents" / "skills" / name / "SKILL.md"
        if not skill_md.is_file():
            problems.append(f"The skill '{name}' has no SKILL.md.")
            continue
        fields = front_matter(skill_md.read_text(encoding="utf-8"))
        if not fields or not fields.get("name") or not fields.get("description"):
            problems.append(f"The skill '{name}' needs a name and a description at the top of SKILL.md.")
        elif fields["name"] != name:
            problems.append(f"The skill folder '{name}' and its name '{fields['name']}' must be the same.")
        for rule in skill_rules(skill_md):
            why = SKILL_PERMS.problem(rule)
            if why:
                problems.append(f"The skill '{name}' asks for a permission it cannot have: {why}")
        if not FLOWCHART.search(skill_md.read_text(encoding="utf-8")):
            problems.append(f"The skill '{name}' needs its flow diagram (a Mermaid flowchart under '## Flow', "
                            "right after the title). Ask the AI to add it; it is explained in the skills rule.")
    return problems


TIERS = ("deny", "ask", "allow")


def staged_text(f):
    return git("show", f":{f}", binary=True).decode("utf-8", "replace")


def check_permissions(files):
    if ".agents/permissions.json" not in files:
        return []
    try:
        rules = json.loads(staged_text(".agents/permissions.json")).get("rules")
    except (ValueError, AttributeError):
        return ["The permissions file is damaged (it is not valid). Undo the last change to it."]
    if not isinstance(rules, list):
        return ["The permissions file has no list of rules. Undo the last change to it."]
    problems = []
    for n, rule in enumerate(rules, 1):
        if not isinstance(rule, dict):
            problems.append(f"Permission rule {n} is damaged.")
            continue
        label = rule.get("reason") or rule.get("pattern") or rule.get("tool") or f"rule {n}"
        if rule.get("tier", "deny") not in TIERS:
            problems.append(f"Permission '{label}' must be one of: {', '.join(TIERS)}.")
        if not rule.get("pattern") and not rule.get("tool"):
            problems.append(f"Permission '{label}' does not say what it applies to.")
        if not str(rule.get("reason", "")).strip():
            problems.append(f"Permission '{label}' needs a plain reason, so the team understands it.")
        if "unless" in rule and not isinstance(rule["unless"], list):
            problems.append(f"Permission '{label}' has a damaged exception list.")
    return problems


def check_team_settings(files):
    if ".agents/team.json" not in files:
        return []
    try:
        info = json.loads(staged_text(".agents/team.json"))
    except ValueError:
        return ["The team settings file is damaged (it is not valid). Undo the last change to it."]
    if not isinstance(info, dict) or not str(info.get("champion", {}).get("email", "")).strip():
        return ["The team settings must keep the AI Champion's name and email."]
    return []


def check_brand(files):
    if ".agents/brand.json" not in files:
        return []
    try:
        brand = json.loads(staged_text(".agents/brand.json"))
    except ValueError:
        return ["The brand file is damaged (it is not valid). Undo the last change to it."]
    colours = {k: brand.get(k) for k in ("primary", "background", "text") if k in brand}
    bad = [k for k, v in colours.items() if not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(v))]
    if "primary" not in brand or bad:
        return ["The brand needs a main colour, and every colour written like #0B5FFF."]
    family = brand.get("font_family")
    if family is not None and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 \-]{0,60}", str(family)):
        return ["The brand's typeface must be a plain name like Montserrat or Open Sans."]
    return []


def check_local_rules_and_hooks(files):
    problems = []
    for f in files:
        if f.startswith(".agents/rules/"):
            if not f.endswith(".md"):
                problems.append(f"'{f}': team rules are written as .md files.")
            elif not staged_text(f).strip():
                problems.append(f"'{f}': this team rule is empty.")
        elif f.startswith(".agents/system/hooks/"):
            text = staged_text(f)
            if f.endswith(".py"):
                try:
                    compile(text, f, "exec")
                except SyntaxError as e:
                    problems.append(f"'{f}' has a mistake on line {e.lineno}, so it would not run.")
            elif f.endswith(".sh"):
                check = subprocess.run(["sh", "-n"], input=text, capture_output=True, text=True)
                if check.returncode != 0:
                    problems.append(f"'{f}' has a mistake, so it would not run.")
    return problems


def check_guard():
    test = subprocess.run([sys.executable, "-I", str(ROOT / ".agents/system/scripts/selftest.py")],
                          capture_output=True, text=True, cwd=ROOT)
    if test.returncode == 0:
        return []
    detail = test.stdout.strip().replace("\n", "; ")
    return [f"The team checks (guard) no longer work, so this change would remove the team's protection. "
            f"Undo the change to .agents/system/ ({detail})."]


def main():
    sync = subprocess.run([sys.executable, str(ROOT / ".agents/system/scripts/sync.py"), "--staged"], cwd=ROOT)
    if sync.returncode != 0:
        print("Could not update the tool files (.claude/, .codex/).")
        return 1
    git("add", "--all", "--", ".claude", ".codex")

    files = staged_files()
    problems = (check_private(files) + check_secrets(files) + check_skills(files) + check_permissions(files)
                + check_team_settings(files) + check_brand(files) + check_local_rules_and_hooks(files) + check_guard())
    if problems:
        print("This change was not saved:")
        for p in problems:
            print(f"  - {p}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
