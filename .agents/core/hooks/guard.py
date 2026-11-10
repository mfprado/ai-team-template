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
sandbox. If the policy file is unreadable it falls back to FALLBACK_RULES (the
critical basics) with a warning; the pre-commit check refuses to save an invalid policy.

Standard library only.
"""

import fnmatch
import json
import os
import re
import subprocess
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
SEARCH_TOOLS = {"grep", "search"}
# Shell commands that only read, allowed to name protected files without asking.
READ_ONLY_PROGRAMS = {"cat", "less", "more", "head", "tail", "grep", "rg", "ls", "wc", "diff", "file", "stat"}
READ_ONLY_GIT = {"diff", "log", "status", "show", "blame"}
# Core scripts the agent runs as part of normal work: running them is not editing core.
CORE_SCRIPTS = {PurePosixPath(f".agents/core/scripts/{n}") for n in ("sync.py", "propose_change.py", "selftest.py")}
PY_FINDER = ".agents/core/bin/py"

# Used when .agents/permissions.json cannot be read: the critical basics stay enforced.
FALLBACK_RULES = [
    {"tool": "Bash", "pattern": "git push --force", "tier": "deny"},
    {"tool": "Bash", "pattern": "git push -f", "tier": "deny"},
    {"tool": "Bash", "pattern": "git push --force-with-lease", "tier": "deny"},
    {"tool": "Bash", "pattern": "git reset --hard", "tier": "deny"},
    {"tool": "Read", "pattern": "**/.env", "tier": "deny"},
    {"tool": "Read", "pattern": "**/.env.*", "tier": "deny"},
    {"tool": "Read", "pattern": "**/*.pem", "tier": "deny"},
    {"tool": "Read", "pattern": "**/*.key", "tier": "deny"},
    {"tool": "mcp__*send*", "unless": ["*draft*"], "tier": "deny"},
    {"tool": "mcp__*send_draft*", "tier": "deny"},
    {"tool": "mcp__*schedule*", "unless": ["*draft*"], "tier": "deny"},
    {"tool": "mcp__*post_message*", "unless": ["*draft*"], "tier": "deny"},
    {"tool": "mcp__*reply*", "unless": ["*draft*"], "tier": "deny"},
    {"tool": "mcp__*forward*", "unless": ["*draft*"], "tier": "deny"},
    {"tool": "Edit", "pattern": ".agents/permissions.json", "tier": "ask"},
    {"tool": "Edit", "pattern": ".agents/core/**", "tier": "ask"},
    {"tool": "Edit", "pattern": ".claude/**", "tier": "ask"},
    {"tool": "Edit", "pattern": ".codex/**", "tier": "ask"},
    {"tool": "Bash", "pattern": "git push --no-verify", "tier": "deny"},
    {"tool": "Bash", "pattern": "git commit --no-verify", "tier": "deny"},
    {"tool": "Bash", "pattern": "git commit -n", "tier": "deny"},
    {"tool": "Bash", "pattern": "git config core.hooksPath", "tier": "deny"},
    {"tool": "Edit", "pattern": ".agents/local/team.json", "tier": "ask"},
    {"tool": "Edit", "pattern": "**/.venv", "tier": "ask"},
    {"tool": "Edit", "pattern": "**/.venv/**", "tier": "ask"},
    {"tool": "Edit", "pattern": "**/.python-version", "tier": "ask"},
]


def load_rules(policy=POLICY):
    try:
        with policy.open(encoding="utf-8") as f:
            rules = json.load(f).get("rules")
        if not isinstance(rules, list):
            raise ValueError("no 'rules' list")
        return [r for r in rules if r.get("enabled", True) is not False]  # switched off in the team UI
    except (OSError, ValueError) as exc:
        print(f"guard: cannot read {policy.name} ({exc}); using built-in basic rules", file=sys.stderr)
        return FALLBACK_RULES


def command_of(tool_input):
    cmd = tool_input.get("command") or tool_input.get("cmd") or ""
    if isinstance(cmd, list):
        cmd = shlex.join(str(c) for c in cmd)
    return str(cmd)


def expand_flags(tokens):
    """-uf -> -u -f ; --force-with-lease=main -> --force-with-lease main"""
    out = []
    for t in tokens:
        if t.startswith("--") and "=" in t:
            out += t.split("=", 1)  # keep the value: it may be a path
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


def tokenize(part):
    """Split like a shell, with redirections (> >> <) as separate tokens."""
    try:
        lex = shlex.shlex(part, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        return list(lex)
    except ValueError:
        return re.sub(r"([<>]+)", r" \1 ", part).split()


def segments(command, depth=0):
    """Yield normalized simple commands, recursing into `bash -c "..."`."""
    for part in re.split(r"&&|\|\||;|\||\n|`|\$\(|\)", command):
        part = part.strip()
        if not part:
            continue
        tokens = tokenize(part)
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
        # Look for the program anywhere, so wrapper options (`env -i`, `sudo -u x`) cannot hide it.
        for i, t in enumerate(tokens):
            if PurePosixPath(t.replace("\\", "/")).name != want[0]:
                continue
            sub = normalize(tokens[i:])
            sub_positional = [x for x in sub if not x.startswith("-")]
            if sub_positional[: len(positional)] == positional and all(f in sub for f in flags):
                return True
    return False


def relative(path):
    """Normalize any spelling (./a/../b, a//b, absolute) to a path relative to the repo when inside it."""
    raw = str(path).replace("\\", "/")
    full = os.path.normpath(raw if os.path.isabs(raw) else os.path.join(str(ROOT), raw))
    try:
        return PurePosixPath(Path(full).relative_to(ROOT).as_posix())
    except ValueError:
        return PurePosixPath(full)


def path_matches(pattern, path):
    if not path:
        return False
    p = relative(path)
    bare = pattern
    while bare.startswith("**/"):
        bare = bare[3:]
    s = str(p)
    return fnmatch.fnmatch(p.name, bare) or fnmatch.fnmatch(s, pattern) or fnmatch.fnmatch(s, bare)


def paths_in(tool_input):
    keys = ("file_path", "path", "notebook_path", "pattern", "glob")
    found = [tool_input[k] for k in keys if isinstance(tool_input.get(k), str)]
    patch = tool_input.get("patch") or tool_input.get("input")
    if isinstance(patch, str):
        found += re.findall(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", patch, re.M)
    return found


def read_only_or_sync(command):
    """True when every part of the command only reads, or runs a known core script."""
    if re.search(r"[<>]", command):
        return False
    for seg in segments(command):
        prog = seg[0]
        if prog in READ_ONLY_PROGRAMS:
            continue
        if prog == "git" and len(seg) > 1 and seg[1] in READ_ONLY_GIT:
            continue
        args = seg[1:]
        if prog == "sh" and args and relative(args[0]) == PurePosixPath(PY_FINDER):
            args = [a for a in args[1:] if a not in ("-I", "-E", "-s", "-P")]  # sh .agents/core/bin/py [-I] <script>
        elif prog == "py":
            pass  # .agents/core/bin/py run directly, or Windows' py launcher
        elif not prog.startswith("python"):
            return False
        else:
            args = [a for a in args if a not in ("-I", "-E", "-s", "-P")]
        if args and relative(args[0]) in CORE_SCRIPTS:
            continue
        return False
    return True


def search_reaches(pattern, tool_input):
    """A folder-wide search can read a secret file without naming it. Search tools skip
    git-ignored files, so it is only a problem if a matching file is NOT ignored."""
    scope = tool_input.get("path") or "."
    try:
        out = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "--cached", "--others", "--exclude-standard", "--", str(relative(scope))],
            capture_output=True, text=True, timeout=10,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return True
    return any(path_matches(pattern, f) for f in out.splitlines())


MAIN_BRANCHES = {"main", "master"}


def team_info():
    try:
        return json.loads((ROOT / ".agents/local/team.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def git_out(*args):
    try:
        return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def pushes_to_main(command):
    """True if any part of the command pushes to the team's main version."""
    current = None
    for seg in segments(command):
        if seg[0] != "git" or len(seg) < 2 or seg[1] != "push":
            continue
        targets = [t for t in seg[2:] if not t.startswith("-")]
        refspecs = targets[1:]  # first positional is the remote
        if not refspecs:
            current = current or git_out("rev-parse", "--abbrev-ref", "HEAD")
            if current in MAIN_BRANCHES or "--all" in seg or "--mirror" in seg:
                return True
            continue
        for ref in refspecs:
            dest = ref.lstrip("+").split(":")[-1].replace("refs/heads/", "")
            if dest in MAIN_BRANCHES or (ref.lstrip("+") == "HEAD" and git_out("rev-parse", "--abbrev-ref", "HEAD") in MAIN_BRANCHES):
                return True
    return False


def disables_hooks(tool, tool_input):
    """`git -c core.hooksPath=... <cmd>` runs git without the team checks."""
    if tool.lower() not in SHELL_TOOLS:
        return False
    for part in re.split(r"&&|\|\||;|\||\n|`|\$\(|\)", command_of(tool_input)):
        tokens = tokenize(part.strip())
        for i, t in enumerate(tokens[:-1]):
            if t == "-c" and tokens[i + 1].lower().startswith("core.hookspath"):
                return True
        if any(t.lower().startswith("-ccore.hookspath") for t in tokens):
            return True
    return False


def champion_only_push(tool, tool_input):
    """Only the AI Champion updates the team's main version; everyone else sends a change request."""
    if tool.lower() not in SHELL_TOOLS:
        return None
    info = team_info()
    champion = str(info.get("champion", {}).get("email", "")).lower()
    if not champion or not pushes_to_main(command_of(tool_input)):
        return None
    if git_out("config", "user.email").lower() == champion:
        return None
    name = info.get("champion", {}).get("name", "the AI Champion")
    return (f"Only {name} can update the team's main version. Share this change as a change request instead: "
            f"sh .agents/core/bin/py -I .agents/core/scripts/propose_change.py --summary \"<one plain sentence>\"")


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
            if any(path_matches(pattern, p) for p in paths_in(tool_input)):
                return True
            if rule_tool == "Read" and name in SEARCH_TOOLS and search_reaches(pattern, tool_input):
                return "ask"  # folder-wide search that could reach a secret: the person decides
            return False
        if name in SHELL_TOOLS:
            cmd = command_of(tool_input)
            if rule_tool == "Edit" and read_only_or_sync(cmd):
                return False
            words = []
            for seg in segments(cmd):
                args = seg[1:]
                if seg[0] in SHELLS and args and relative(args[0]) == PurePosixPath(PY_FINDER):
                    args = args[1:]  # `sh .agents/core/bin/py script`: bin/py is the interpreter, not a target
                words += args
            words += [t.split("=", 1)[1] for t in words if "=" in t]  # of=path, --file=path
            return any(path_matches(pattern, t) for t in words)
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

    # --policy <file> is only used by the self-test (selftest.py); hooks never pass it.
    argv = sys.argv[1:]
    policy = Path(argv[argv.index("--policy") + 1]) if "--policy" in argv else POLICY
    rules = load_rules(policy)
    if disables_hooks(tool, tool_input):
        print("Blocked by team permissions: Turns off the team checks.", file=sys.stderr)
        return 2
    blocked = champion_only_push(tool, tool_input)
    if blocked:
        print(f"Blocked by team permissions: {blocked}", file=sys.stderr)
        return 2
    for tier in ("deny", "ask"):
        for rule in (r for r in rules if r.get("tier", "deny") == tier):
            result = decide(rule, tool, tool_input)
            if result:
                reason = rule.get("reason") or "Blocked by .agents/permissions.json."
                if result == "ask":
                    tier = "ask"
                    reason = f"This search could read a protected file ({rule.get('pattern')}). {reason}"
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
