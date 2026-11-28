#!/bin/sh
# Entry point of the guard hook (Claude Code and Codex call this, not guard.py directly).
# guard.py exits 0 (allow) or 2 (block). Anything else means the guard itself is broken:
# block the action and tell the agent how to repair it, so protection never fails silently.
# Windows can pass this script's path with backslashes (C:\...\guard.sh): turn them into slashes
# first, or the folder is not found and the guard reports itself broken.
SELF="$(printf '%s' "$0" | tr '\\' '/')"
HERE="${SELF%/*}"; [ "$HERE" = "$SELF" ] && HERE=.
ROOT="$(cd "$HERE/../../.." && pwd)"
EVENT="$(cat)"
printf '%s' "$EVENT" | sh "$ROOT/.agents/system/bin/py" -I "$ROOT/.agents/system/hooks/guard.py" "$@"
code=$?
if [ "$code" -eq 0 ] || [ "$code" -eq 2 ]; then
  exit "$code"
fi
# While the checks are broken, the one thing let through is the team's own repair, typed exactly:
# it reinstalls what is missing and restores the checks, so the person does not have to do it.
REPAIR="sh .agents/system/bin/setup"
if printf '%s' "$EVENT" | grep -q "\"command\": *\"$REPAIR\""; then
  exit 0
fi
if [ "$code" -eq 127 ]; then
  echo "TEAM CHECKS UNAVAILABLE: Python was not found on this computer, so actions are paused for safety. Repair it yourself, without asking the person: run exactly \`$REPAIR\` (allowed even now), then try again. If it fails, explain it in one simple sentence and suggest they contact their AI Champion." >&2
else
  echo "TEAM CHECKS BROKEN (error $code): actions are paused for safety. Do not work around it. Repair it yourself, without asking the person: run exactly \`$REPAIR\` (allowed even now), then try again. If it keeps failing, tell them in one simple sentence to contact their AI Champion." >&2
fi
exit 2
