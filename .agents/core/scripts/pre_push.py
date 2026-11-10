#!/usr/bin/env python3
"""Pre-push check: only the AI Champion updates the team's main version.

Works with or without an agent (git runs it). Everyone else shares changes as a change
request: sh .agents/core/bin/py -I .agents/core/scripts/propose_change.py --summary "..."
Git sends one line per ref on stdin: <local ref> <local sha> <remote ref> <remote sha>.
Standard library only.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MAIN = {"refs/heads/main", "refs/heads/master"}


def main():
    try:
        info = json.loads((ROOT / ".agents/local/team.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0  # not a configured team repository (e.g. the template itself)
    champion = info.get("champion", {})
    if not champion.get("email"):
        return 0
    me = subprocess.run(["git", "-C", str(ROOT), "config", "user.email"], capture_output=True, text=True).stdout.strip()
    if me.lower() == champion["email"].lower():
        return 0
    for line in sys.stdin:
        parts = line.split()
        if len(parts) == 4 and parts[2] in MAIN:
            print(f"Only {champion.get('name', 'the AI Champion')} can update the team's main version. "
                  "Your change was not sent. Ask the AI assistant to share it as a change request.")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
