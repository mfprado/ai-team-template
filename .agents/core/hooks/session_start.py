#!/usr/bin/env python3
"""SessionStart hook: bring the latest team changes before the session starts.

Fast-forward only: never merges, never rewrites, never fails the session. Unsaved work on this
computer is set aside and put back (autostash), and the person's own git settings (such as
pull.rebase) do not change how this works.
Standard library only.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, timeout=60)


def main():
    try:
        if git("rev-parse", "--abbrev-ref", "@{upstream}").returncode != 0:
            return 0  # no remote branch yet
        git("fetch", "--quiet")
        result = git("merge", "--ff-only", "--autostash", "--quiet", "@{upstream}")
        if result.returncode == 0:
            print("Team workspace is up to date.")
        else:
            print("Could not update the team workspace automatically; continuing with the local copy.")
    except (OSError, subprocess.SubprocessError):
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
