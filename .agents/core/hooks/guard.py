#!/usr/bin/env python3
"""Guard hook: runs before every tool call in Claude Code and Codex (PreToolUse).

Reads the tool call as JSON on stdin and checks it against .agents/permissions.json.
- deny: exit 2 with the reason on stderr (both tools block the call)
- ask:  print a JSON 'ask' decision (the person approves or rejects)
- otherwise: exit 0, the call goes ahead

Covers what native settings cannot: tool-name globs (any MCP tool that sends),
commands where the dangerous part is not at the start (`git -C . push origin +main`,
`bash -c "git push --force"`), reading secrets through the shell or search tools,
and edits to the policy itself.

This is a guardrail against mistakes and common prompt-injection tricks, not a
sandbox. If the policy file is unreadable it lets calls through with a warning
(team decision); the pre-commit check refuses to save an invalid policy.

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
READ_TOOLS = {"read", "view", "read_file", "notebookread", "grep", "glob", "search", "ls"}
EDIT_TOOLS = {"edit", "write", "multiedit", "notebookedit", "apply_patch", "create_file", "str_replace", "write_file"}

WRAPPERS = {"env", "command", "exec", "nohup", "time", "sudo", "nice", "xargs"}
SHELLS = {"sh", "bash", "zsh", "dash"}
GIT_GLOBAL_WITH_ARG = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
SHELL_WRITE_HINTS = re.compile(r">|\btee\b|\bsed\s+-i|\bperl\s+-i|\bmv\b|\bcp\b|\brm\b|\btruncate\b|\bchmod\b|\bln\b|\bpython3?\s+-c\b")


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
        cmd = shlex.join(str(c) for c in cmd)
    return str(cmd)


def expand_flags(tokens):
    """-uf -> -u -f ; --force-with-lease=main -> --force-with-lease"""
    out = []
    for t in tokens:
        if t.startswith("--") and "=" in t:
            out.append(t.split("=", 1)[0])
        elif re.fullmatch(r"-[A-Za-z]{2,}", t):
            out += [f"-{c}" for c in t[1:]]
        else:
            out.append(t)
    return out


def normalize(tokens):
    """Strip wrappers, env assignments and paths; drop git global options; mark +refspec pushes."""
    while tokens and (re.match(r"^\w+=", tokens[0]) or PurePosixPath(tokens[0]).name in WRAPPERS):
        tokens = tokens[1:]
    if not tokens:
        return tokens
    tokens = [PurePosixPath(tokens[0].replace("\\", "/")).name] + tokens[1:]
    if tokens[0] == "git":
        rest, i = [], 1
        while i < len(tokens) and tokens[i].startswith("-"):
            i += 2 if tokens[i] in GIT_GLOBAL_WITH_ARG else 1
        rest = tokens[i:]
        tokens = ["git"] + rest
        if len(tokens) > 1 and tokens[1] == "push" and any(t.startswith("+") for t in tokens[2:]):
            tokens.append("--force")
    return expand_flags(tokens)


def segments(command, depth=0):
    """Yield normalized simple commands, recursing into `bash -c "..."`."""
    for part in re.split(r"&&|\|\||;|\||\n|`|\$\(|\)", command):
        part = part.strip()
        if not part:
            continue
        try:
            tokens = shlex.split(part)
        except ValueError:
            tokens = part.split()
        tokens = normalize(tokens)
        if not tokens:
            continue
        if tokens[0] in SHELLS and "-c" in tokens and depth < 3:
            idx = tokens.index("-c")
            if idx + 1 < len(tokens):
                yield from segments(tokens[idx + 1], depth + 1)
            continue
        yield tokens


def command_matches(rule_pattern, command):
    want = rule_pattern.split()
    positional = [t for t in want if not t.startswith("-")]
    flags = [t for t in want if t.startswith("-")]
    for tokens in segments(command):
        seg_positional = [t for t in tokens if not t.startswith("-")]
        if seg_positional[: len(positional)] == positional and all(f in tokens for f in flags):
            return True
    return False


def relative(path):
    p = Path(str(path))
    try:
        return PurePosixPath(p.resolve().relative_to(ROOT).as_posix()) if p.is_absolute() else PurePosixPath(str(path).replace("\\", "/"))
    except ValueError:
        return PurePosixPath(str(path).replace("\\", "/"))


def path_matches(pattern, path):
    if not path:
        return False
    p = relative(path)
    bare = pattern
    while bare.startswith("**/"):
        bare = bare[3:]
    s = str(p).lstrip("./") if str(p).startswith("./") else str(p)
    return fnmatch.fnmatch(p.name, bare) or fnmatch.fnmatch(s, pattern) or fnmatch.fnmatch(s, bare)


def paths_in(tool_input):
    keys = ("file_path", "path", "notebook_path", "pattern", "glob")
    found = [tool_input[k] for k in keys if isinstance(tool_input.get(k), str)]
    patch = tool_input.get("patch") or tool_input.get("input")
    if isinstance(patch, str):
        found += re.findall(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", patch, re.M)
    return found


def decide(rule, tool, tool_input):
    rule_tool = rule.get("tool", "")
    pattern = rule.get("pattern")
    name = tool.lower()

    if rule_tool == "Bash":
        return name in SHELL_TOOLS and bool(pattern) and command_matches(pattern, command_of(tool_input))

    if rule_tool in ("Read", "Edit"):
        if not pattern:
            return False
        tools = READ_TOOLS if rule_tool == "Read" else EDIT_TOOLS
        if name in tools:
            return any(path_matches(pattern, p) for p in paths_in(tool_input))
        if name in SHELL_TOOLS:
            cmd = command_of(tool_input)
            if rule_tool == "Edit" and not SHELL_WRITE_HINTS.search(cmd):
                return False
            return any(path_matches(pattern, t) for seg in segments(cmd) for t in seg[1:])
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
