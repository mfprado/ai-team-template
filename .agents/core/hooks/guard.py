#!/usr/bin/env python3
"""Guard hook: runs before every tool call in Claude Code and Codex (PreToolUse).

Reads the tool call as JSON on stdin and checks it against .agents/permissions.json.
- deny: exit 2 with the reason on stderr (both tools block the call)
- ask:  print a JSON 'ask' decision
- otherwise: exit 0, the call goes ahead

Covers what native settings cannot: tool-name globs (any MCP tool that sends),
commands where the flag is not at the start (`git push origin main --force`),
and reading secret files through the shell (`cat .env`).

Standard library only.
"""

import fnmatch
import json
import re
import shlex
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[3]
POLICY = ROOT / ".agents" / "permissions.json"

SHELL_TOOLS = {"bash", "shell", "local_shell", "exec_command"}
READ_TOOLS = {"read", "view", "read_file", "notebookread"}


def load_rules():
    try:
        with POLICY.open(encoding="utf-8") as f:
            return json.load(f).get("rules", [])
    except (OSError, ValueError) as exc:
        print(f"guard: cannot read {POLICY.name} ({exc}); not enforcing", file=sys.stderr)
        return []


def command_of(tool_input):
    cmd = tool_input.get("command") or tool_input.get("cmd") or ""
    if isinstance(cmd, list):
        cmd = " ".join(str(c) for c in cmd)
    return str(cmd)


def segments(command):
    """Split a shell line into simple commands on && || ; | and newlines."""
    for part in re.split(r"&&|\|\||;|\||\n", command):
        part = part.strip()
        if not part:
            continue
        try:
            tokens = shlex.split(part)
        except ValueError:
            tokens = part.split()
        # drop env assignments and sudo in front
        while tokens and (re.match(r"^\w+=", tokens[0]) or tokens[0] == "sudo"):
            tokens.pop(0)
        if tokens:
            yield tokens


def command_matches(rule_pattern, command):
    want = rule_pattern.split()
    for tokens in segments(command):
        if tokens[0] != want[0]:
            continue
        positional = [t for t in want if not t.startswith("-")]
        flags = [t for t in want if t.startswith("-")]
        seg_positional = [t for t in tokens if not t.startswith("-")]
        if seg_positional[: len(positional)] == positional and all(f in tokens for f in flags):
            return True
    return False


def path_matches(pattern, path):
    if not path:
        return False
    p = PurePosixPath(str(path).replace("\\", "/"))
    bare = pattern
    while bare.startswith("**/"):
        bare = bare[3:]
    return fnmatch.fnmatch(p.name, bare) or fnmatch.fnmatch(str(p), pattern) or fnmatch.fnmatch(str(p), bare)


def decide(rule, tool, tool_input):
    rule_tool = rule.get("tool", "")
    pattern = rule.get("pattern")
    name = tool.lower()

    if rule_tool == "Bash":
        return name in SHELL_TOOLS and bool(pattern) and command_matches(pattern, command_of(tool_input))

    if rule_tool == "Read":
        if not pattern:
            return False
        if name in READ_TOOLS:
            path = tool_input.get("file_path") or tool_input.get("path") or tool_input.get("notebook_path")
            return path_matches(pattern, path)
        if name in SHELL_TOOLS:
            return any(path_matches(pattern, t) for seg in segments(command_of(tool_input)) for t in seg[1:])
        return False

    if not fnmatch.fnmatch(name, rule_tool.lower()):
        return False
    return not any(fnmatch.fnmatch(name, u.lower()) for u in rule.get("unless", []))


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    tool = str(event.get("tool_name") or event.get("tool") or "")
    tool_input = event.get("tool_input") or event.get("input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {"command": tool_input}

    rules = load_rules()
    for tier in ("deny", "ask"):
        for rule in (r for r in rules if r.get("tier", "deny") == tier):
            if decide(rule, tool, tool_input):
                reason = rule.get("reason") or "Blocked by .agents/permissions.json."
                if tier == "deny":
                    print(f"Blocked by team permissions: {reason}", file=sys.stderr)
                    return 2
                print(json.dumps({"hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": reason,
                }}))
                return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
