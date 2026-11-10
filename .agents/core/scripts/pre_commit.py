#!/usr/bin/env python3
"""Pre-commit checks for a team repository. Runs with or without an agent.

1. Regenerate .claude/ and .codex/ from the staged .agents/ files and add them to the commit.
2. Block private artifacts (artifacts/private/, artefactos/privado/).
3. Block likely secrets in staged files.
4. Check every staged skill has a valid SKILL.md (name + description, name = folder).

Messages are plain words: the person committing may not be technical.
Standard library only.
"""

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
    return problems


def main():
    sync = subprocess.run([sys.executable, str(ROOT / ".agents/core/scripts/sync.py"), "--staged"], cwd=ROOT)
    if sync.returncode != 0:
        print("Could not update the tool files (.claude/, .codex/).")
        return 1
    git("add", "--all", "--", ".claude", ".codex")

    files = staged_files()
    problems = check_private(files) + check_secrets(files) + check_skills(files)
    if problems:
        print("This change was not saved:")
        for p in problems:
            print(f"  - {p}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
