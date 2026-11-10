#!/usr/bin/env python3
"""Bring a team's repository up to the template's current core version.

Run from the TEMPLATE folder (a fresh copy of ai-team-template):

  # 1. See what would change (nothing is modified)
  sh .agents/core/bin/py .agents/skills/update-team-repo/scripts/update.py plan --target "<team repo>"

  # 2. Apply it on a new branch; add the proposed permission rules the Champion approved
  sh .agents/core/bin/py .agents/skills/update-team-repo/scripts/update.py apply --target "<team repo>" \
      --add-rules 0,2

The team's repository receives plain files, never the template's history. This script does
not commit: the AI Champion commits under their own name (see the skill).

Copied: .agents/core/ (mirrored), AGENTS.md, CLAUDE.md, .gitattributes, system skills and subagents, and the
launchers' content (keeping the team's launcher name). Never touched: .agents/local/,
the team's own skills, documents, artifacts. Permissions are only ever added, never removed.

Standard library only. Output is JSON for the agent to explain in plain words.
"""

import argparse
import datetime
import json
import shutil
import subprocess
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[4]
CORE = ".agents/core"
ROOT_FILES = ["AGENTS.md", "CLAUDE.md", ".gitattributes"]
TEMPLATE_LAUNCHER = "Team-AI"
CHANGES = f"{CORE}/CHANGES.md"


def git(cwd, *args, check=True):
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=check).stdout


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def template_manifest():
    return load_json(TEMPLATE / CORE / "manifest.json")


def entries(changes_path):
    """Changelog entries as {heading: text}, in file order (newest first)."""
    if not changes_path.is_file():
        return {}
    result, current = {}, None
    for line in changes_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            result[current] = []
        elif current:
            result[current].append(line)
    return {k: "\n".join(v).strip() for k, v in result.items()}


def rule_key(rule):
    return json.dumps({k: rule.get(k) for k in ("tool", "pattern", "tier", "unless")}, sort_keys=True)


def missing_rules(target):
    template_rules = load_json(TEMPLATE / ".agents/permissions.json").get("rules", [])
    team_rules = load_json(target / ".agents/permissions.json").get("rules", [])
    have = {rule_key(r) for r in team_rules}
    return [r for r in template_rules if rule_key(r) not in have]


def check_target(target):
    problems = []
    if not (target / ".git").exists():
        problems.append("The folder is not a team repository (no git).")
    for f in (f"{CORE}/manifest.json", ".agents/local/team.json", ".agents/permissions.json"):
        if not (target / f).is_file():
            problems.append(f"Missing {f}: this does not look like a team repository.")
    if not problems and git(target, "status", "--porcelain").strip():
        problems.append("The team repository has unsaved changes. Save or discard them first.")
    if git(TEMPLATE, "status", "--porcelain").strip():
        problems.append("The template copy has unsaved changes; download a fresh copy of the template first.")
    return problems


def plan(target):
    team_manifest = load_json(target / CORE / "manifest.json")
    commit, date = git(TEMPLATE, "log", "-1", "--format=%H %cs").split()
    team_version = team_manifest.get("core_version") or {}
    new_entries = {h: t for h, t in entries(TEMPLATE / CHANGES).items() if h not in entries(target / CHANGES)}
    return {
        "team_version": team_version,
        "new_version": {"date": date, "commit": commit},
        "up_to_date": team_version.get("commit") == commit,
        "improvements": [{"title": h, "text": t} for h, t in new_entries.items()],
        "proposed_rules": [dict(r, index=i) for i, r in enumerate(missing_rules(target))],
    }


def mirror(src_dir, dst_dir):
    """Make dst_dir an exact copy of the files git tracks in src_dir."""
    tracked = {p for p in git(TEMPLATE, "ls-files", "-z", "--", src_dir).split("\0") if p}
    for rel in tracked:
        src, dst = TEMPLATE / rel, dst_dir / rel
        if src.is_symlink() or not src.is_file():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    if (dst_dir / src_dir).is_dir():
        for p in sorted((dst_dir / src_dir).rglob("*"), reverse=True):
            rel = p.relative_to(dst_dir).as_posix()
            if p.is_file() and rel not in tracked:
                p.unlink()
            elif p.is_dir() and not any(p.iterdir()):
                p.rmdir()


def apply(target, add_rules):
    info = plan(target)
    proposed = info["proposed_rules"]
    chosen = [proposed[i] for i in add_rules if 0 <= i < len(proposed)]

    branch = f"core-update-{datetime.date.today().isoformat()}"
    git(target, "checkout", "-b", branch)

    manifest = template_manifest()
    template_only = manifest.get("template_only_skills", [])

    mirror(CORE, target)
    for f in ROOT_FILES:
        if (TEMPLATE / f).is_file():
            shutil.copy2(TEMPLATE / f, target / f)
    for skill in manifest.get("system_skills", []):
        if skill not in template_only:
            mirror(f".agents/skills/{skill}", target)
    for agent in manifest.get("system_agents", []):  # system subagents; the team's own are kept
        src = TEMPLATE / ".agents/agents" / f"{agent}.md"
        if src.is_file():
            (target / ".agents/agents").mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target / ".agents/agents" / f"{agent}.md")

    launcher = load_json(target / ".agents/local/team.json").get("launcher", TEMPLATE_LAUNCHER)
    for ext in (".command", ".bat"):
        if (TEMPLATE / f"{TEMPLATE_LAUNCHER}{ext}").is_file():
            shutil.copy2(TEMPLATE / f"{TEMPLATE_LAUNCHER}{ext}", target / f"{launcher}{ext}")

    manifest.pop("template_only_skills", None)
    manifest["system_skills"] = [s for s in manifest.get("system_skills", []) if s not in template_only]
    manifest["core_version"] = info["new_version"]
    (target / CORE / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if chosen:
        perms_path = target / ".agents/permissions.json"
        perms = load_json(perms_path)
        perms.setdefault("rules", []).extend({k: v for k, v in r.items() if k != "index"} for r in chosen)
        perms_path.write_text(json.dumps(perms, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    sync = subprocess.run([sys.executable, "-I", str(target / CORE / "scripts/sync.py")], cwd=target,
                          capture_output=True, text=True)
    test = subprocess.run([sys.executable, "-I", str(target / CORE / "scripts/selftest.py")], cwd=target,
                          capture_output=True, text=True)
    return {
        "branch": branch,
        "version": info["new_version"],
        "rules_added": len(chosen),
        "sync_ok": sync.returncode == 0,
        "selftest_ok": test.returncode == 0,
        "selftest_output": test.stdout.strip(),
        "changed_files": [l[3:] for l in git(target, "status", "--porcelain").splitlines()],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=["plan", "apply"])
    parser.add_argument("--target", required=True)
    parser.add_argument("--add-rules", default="", help="comma-separated indexes from plan's proposed_rules")
    args = parser.parse_args()
    target = Path(args.target).expanduser().resolve()

    problems = check_target(target)
    if problems:
        print(json.dumps({"ok": False, "problems": problems}, ensure_ascii=False))
        return 1
    if args.action == "plan":
        print(json.dumps(dict(plan(target), ok=True), indent=2, ensure_ascii=False))
        return 0
    indexes = [int(x) for x in args.add_rules.split(",") if x.strip().isdigit()]
    result = apply(target, indexes)
    print(json.dumps(dict(result, ok=result["sync_ok"] and result["selftest_ok"]), indent=2, ensure_ascii=False))
    return 0 if result["sync_ok"] and result["selftest_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
