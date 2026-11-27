#!/usr/bin/env python3
"""Check that this computer is ready for the team folder, and say how to fix what is not.

  sh .agents/system/bin/py -I .agents/system/scripts/doctor.py

Read only: it changes nothing. Prints JSON: {"ok": bool, "system": ..., "checks": [...]},
each check with "id", "ok", and when not ok a plain "problem" and a "fix" the AI follows
(.agents/rules/setup-problems.md explains each one). Works on Mac and Windows.

Checks:
  sh          a POSIX shell the AI tools' hooks can call (Windows: from Git for Windows)
  uv          uv, which installs and runs the right Python
  python      the Python the hooks use really runs (not the Windows Store placeholder)
  guard       the team checks block what they must (selftest.py)
  git_hooks   the team's git checks are turned on (core.hooksPath)
  codex_trust Codex applies this folder's rules (folder trusted in Codex's settings)
  gh          GitHub's tool is installed and signed in (needed to share changes)

Standard library only.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WINDOWS = platform.system() == "Windows"
HOOKS_PATH = ".agents/system/git-hooks"


def run(*args, timeout=60):
    try:
        return subprocess.run(list(args), cwd=ROOT, capture_output=True, text=True, timeout=timeout,
                              encoding="utf-8", errors="replace")
    except (OSError, subprocess.SubprocessError) as exc:
        return subprocess.CompletedProcess(args, 127, "", str(exc))


def git_sh():
    """sh.exe from Git for Windows, when it is installed but not on the PATH."""
    roots = [os.environ.get("ProgramFiles", r"C:\Program Files"), os.environ.get("ProgramW6432", ""),
             str(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs")]
    for root in filter(None, roots):
        candidate = Path(root) / "Git" / "usr" / "bin" / "sh.exe"
        if candidate.exists():
            return candidate
    git = shutil.which("git")
    if git:  # ...\Git\cmd\git.exe -> ...\Git\usr\bin\sh.exe
        candidate = Path(git).resolve().parents[1] / "usr" / "bin" / "sh.exe"
        if candidate.exists():
            return candidate
    return None


def windows_path_has_sh():
    """Whether sh is on the PATH Windows gives new programs (user + system settings).

    The AI's own shell (Git Bash in Claude Code) adds Git's tools to its PATH, so checking the
    current PATH would say yes even when Codex, started from Windows, cannot find sh."""
    import winreg  # Windows only
    folders = []
    for hive, key in ((winreg.HKEY_CURRENT_USER, "Environment"),
                      (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment")):
        try:
            with winreg.OpenKey(hive, key) as k:
                folders += os.path.expandvars(winreg.QueryValueEx(k, "Path")[0]).split(";")
        except OSError:
            pass
    return any(f and (Path(f) / "sh.exe").exists() for f in folders)


def check_sh():
    if (windows_path_has_sh() if WINDOWS else shutil.which("sh")):
        return {"ok": True}
    if not WINDOWS:
        return {"ok": False, "problem": "No sh on this computer.", "fix": "contact_champion"}
    found = git_sh()
    if found:
        return {"ok": False, "problem": "Git for Windows is installed, but its sh is not on the PATH, so "
                "Codex's team checks cannot run.", "fix": "add_git_sh_to_path", "folder": str(found.parent)}
    return {"ok": False, "problem": "Git for Windows is missing.", "fix": "run_launcher"}


def find_uv():
    found = shutil.which("uv")
    if found:
        return found
    for folder in (Path.home() / ".local/bin", Path.home() / ".cargo/bin"):
        for name in ("uv.exe", "uv") if WINDOWS else ("uv",):
            if (folder / name).exists():
                return str(folder / name)
    return None


def check_uv():
    return {"ok": True} if find_uv() else {"ok": False, "problem": "uv is not installed.", "fix": "run_launcher"}


def check_python(sh_ok):
    if not sh_ok:
        return {"ok": False, "problem": "Cannot test the hooks' Python without sh.", "fix": "fix_sh_first"}
    out = run("sh", ".agents/system/bin/py", "-I", "-c", "import sys; print(sys.version_info[:2] >= (3, 9))")
    if out.returncode == 0 and out.stdout.strip() == "True":
        return {"ok": True}
    return {"ok": False, "problem": "The Python the team checks use does not run (on Windows, often the "
            "Microsoft Store placeholder).", "fix": "run_launcher"}


def check_guard(sh_ok):
    if not sh_ok:
        return {"ok": False, "problem": "The team checks need sh.", "fix": "fix_sh_first"}
    out = run(sys.executable, "-I", str(ROOT / ".agents/system/scripts/selftest.py"), timeout=120)
    if out.returncode == 0:
        return {"ok": True}
    return {"ok": False, "problem": "The team checks do not block what they must.", "fix": "run_launcher",
            "details": (out.stdout + out.stderr).strip()[-600:]}


def check_git_hooks():
    current = run("git", "config", "--get", "core.hooksPath").stdout.strip()
    if current == HOOKS_PATH:
        return {"ok": True}
    return {"ok": False, "problem": "The team's git checks are off on this computer.", "fix": "run_launcher"}


def check_codex_trust():
    config = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "config.toml"
    if not shutil.which("codex") and not config.parent.exists():
        return {"ok": True, "note": "Codex is not used on this computer."}
    try:
        text = config.read_text(encoding="utf-8")
    except OSError:
        text = ""
    root = str(ROOT)
    keys = {f"'{root}'", json.dumps(root)}
    if any(f"[projects.{k}]" in text for k in keys):
        return {"ok": True}
    return {"ok": False, "problem": "Codex does not trust this folder yet, so it ignores the team's rules here.",
            "fix": "run_launcher"}


def check_gh():
    if not shutil.which("gh") and not (WINDOWS and Path(os.environ.get("ProgramFiles", ""), "GitHub CLI", "gh.exe").exists()):
        return {"ok": False, "problem": "GitHub's tool is not installed, so changes cannot be shared.",
                "fix": "run_launcher"}
    if run("gh", "auth", "status", "--hostname", "github.com").returncode != 0:
        return {"ok": False, "problem": "GitHub's tool is not signed in.", "fix": "gh_login"}
    return {"ok": True}


def main():
    checks = []

    def add(name, result):
        checks.append({"id": name, **result})
        return result["ok"]

    sh_ok = add("sh", check_sh())
    add("uv", check_uv())
    add("python", check_python(sh_ok))
    add("guard", check_guard(sh_ok))
    add("git_hooks", check_git_hooks())
    add("codex_trust", check_codex_trust())
    add("gh", check_gh())
    ok = all(c["ok"] for c in checks)
    print(json.dumps({"ok": ok, "system": platform.system(), "folder": str(ROOT), "checks": checks},
                     ensure_ascii=False, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
