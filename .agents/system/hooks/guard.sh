#!/bin/sh
# Entry point of the guard hook (Claude Code and Codex call this, not guard.py directly).
# guard.py exits 0 (allow) or 2 (block). Anything else means the guard itself is broken:
# block the action and tell the agent how to repair it, so protection never fails silently.
HERE="${0%/*}"; [ "$HERE" = "$0" ] && HERE=.
ROOT="$(cd "$HERE/../../.." && pwd)"
sh "$ROOT/.agents/system/bin/py" -I "$ROOT/.agents/system/hooks/guard.py" "$@"
code=$?
if [ "$code" -eq 0 ] || [ "$code" -eq 2 ]; then
  exit "$code"
fi
LAUNCHER="the team launcher"
if [ -f "$ROOT/.agents/team.json" ]; then
  name="$(sed -n 's/.*"launcher": *"\([^"]*\)".*/\1/p' "$ROOT/.agents/team.json")"
  [ -n "$name" ] && LAUNCHER="$name"
fi
if [ "$code" -eq 127 ]; then
  echo "TEAM CHECKS UNAVAILABLE: Python was not found on this computer, so actions are paused for safety. Ask the person, in one simple sentence, to double-click '$LAUNCHER' in the team folder, then try again." >&2
else
  echo "TEAM CHECKS BROKEN (error $code): actions are paused for safety. Do not work around it. Ask the person, in one simple sentence, to double-click '$LAUNCHER' in the team folder: it repairs the team checks. Then try again. If it keeps failing, tell them to contact their AI Champion." >&2
fi
exit 2
