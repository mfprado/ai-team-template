#!/usr/bin/env python3
"""Check that the guard hook still blocks what it must, the way the tools call it.

Runs .agents/system/hooks/guard.sh (the real hook entry point) against a fixed test
policy and known cases. Used by the pre-commit check and by the launcher's setup.
Exit 0 when every case behaves as expected; 1 otherwise (problems printed).

Standard library only.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GUARD_SH = ROOT / ".agents/system/hooks/guard.sh"
POLICY = ROOT / ".agents/system/tests/guard_policy.json"
CASES = ROOT / ".agents/system/tests/guard_cases.json"


def outcome(event):
    proc = subprocess.run(
        ["sh", str(GUARD_SH), "--policy", str(POLICY)],
        input=json.dumps(event), capture_output=True, text=True, timeout=30, cwd=ROOT,
    )
    if proc.returncode == 2:
        return "deny" if "TEAM CHECKS" not in proc.stderr else "broken"
    if proc.returncode == 0:
        return "ask" if '"ask"' in proc.stdout else "allow"
    return "broken"


def main():
    try:
        cases = json.loads(CASES.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"guard self-test: cannot read the test cases ({exc})")
        return 1
    problems = []
    for case in cases:
        got = outcome(case["event"])
        if got != case["expect"]:
            problems.append(f"{case['event'].get('tool_name')}: expected {case['expect']}, got {got}")
    for p in problems:
        print(f"guard self-test: {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
