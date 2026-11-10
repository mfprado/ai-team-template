#!/usr/bin/env python3
"""UserPromptSubmit hook: every REVIEW_EVERY messages, ask the agent for an improvement review.

Counts the person's messages per session (state kept inside .git/, never committed) and, on
every 12th message, adds an instruction to the agent's context: delegate a short review of
the session to the improvement-reviewer subagent and, only if it finds something worth it,
mention one idea. The rule .agents/core/rules/improvements.md says how.

Never blocks and never fails the session. Standard library only.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STATE = ROOT / ".git" / "ai-team-review.json"
REVIEW_EVERY = 12
KEEP_SESSIONS = 50

MESSAGE = (
    "IMPROVEMENT REVIEW: after answering this message, follow .agents/core/rules/improvements.md: "
    "ask the improvement-reviewer subagent to review this session and, only if it finds something "
    "that really improves a step, mention one idea at the end of your reply. Otherwise say nothing about it."
)


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    session = str(event.get("session_id") or "default")
    try:
        state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.is_file() else {}
    except (OSError, ValueError):
        state = {}
    count = int(state.pop(session, 0)) + 1
    state[session] = count  # most recent last
    while len(state) > KEEP_SESSIONS:
        state.pop(next(iter(state)))
    try:
        STATE.write_text(json.dumps(state), encoding="utf-8")
    except OSError:
        return 0
    if count % REVIEW_EVERY == 0:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": MESSAGE}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
