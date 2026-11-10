#!/usr/bin/env python3
"""Per-computer setup. The launcher runs it every time the team folder is opened.

Safe to repeat: each step checks before changing anything.
1. Turn on the team's git checks (core.hooksPath).
2. Hide technical files so they don't show in Finder / File Explorer.
3. Mark the folder as trusted in Codex, so its rules and hooks load (with a notice).

Standard library only. Messages are plain words for non-technical people.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HOOKS_PATH = ".agents/core/git-hooks"
# Folders starting with a dot are already hidden on Mac; Windows needs the attribute.
HIDDEN_DIRS = [".agents", ".claude", ".codex", ".git"]
# Must stay at the root with these names (agents look for them there): hide them on both systems.
HIDDEN_FILES = ["AGENTS.md", "CLAUDE.md", ".gitignore"]

SYSTEM = platform.system()


def run(*args):
    return subprocess.run(list(args), capture_output=True, text=True, check=False)


def git_hooks():
    current = run("git", "-C", str(ROOT), "config", "--get", "core.hooksPath").stdout.strip()
    if current != HOOKS_PATH:
        run("git", "-C", str(ROOT), "config", "core.hooksPath", HOOKS_PATH)
        return "Team checks turned on."
    return None


def hide_files():
    if SYSTEM == "Darwin":
        targets = [ROOT / f for f in HIDDEN_FILES]
        for t in targets:
            if t.exists():
                run("chflags", "hidden", str(t))
    elif SYSTEM == "Windows":
        for name in HIDDEN_DIRS + HIDDEN_FILES:
            t = ROOT / name
            if t.exists():
                run("attrib", "+h", str(t))
    # Linux: names starting with a dot are hidden; AGENTS.md/CLAUDE.md stay visible.
    return None


def codex_home():
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def toml_key(path):
    """A TOML key for a path. Literal strings ('...') keep Windows backslashes as they are."""
    return f"'{path}'" if "'" not in path else '"' + path.replace("\\", "\\\\").replace('"', '\\"') + '"'


def codex_trust():
    config = codex_home() / "config.toml"
    key = toml_key(str(ROOT))
    header = f"[projects.{key}]"
    text = config.read_text(encoding="utf-8") if config.exists() else ""
    if header in text:
        return None
    config.parent.mkdir(parents=True, exist_ok=True)
    with config.open("a", encoding="utf-8") as f:
        f.write(("\n" if text and not text.endswith("\n") else "") + f'\n{header}\ntrust_level = "trusted"\n')
    return ("Codex will now apply this team's rules in this folder "
            "(the folder was marked as trusted in Codex's settings).")


def main():
    if not (ROOT / ".git").exists():
        print("This folder is not connected to the team yet. Ask your AI Champion for help.")
        return 1
    notes = [n for n in (git_hooks(), hide_files(), codex_trust()) if n]
    for n in notes:
        print(f"- {n}")
    print("Your team folder is ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
