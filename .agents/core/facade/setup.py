#!/usr/bin/env python3
"""Per-computer setup. The launcher runs it every time the team folder is opened.

Safe to repeat: each step checks before changing anything.
1. Turn on the team's git checks (core.hooksPath).
2. Hide technical files so they don't show in Finder / File Explorer.
3. Mark the folder as trusted in Codex, so its rules and hooks load (with a notice).
4. Check the team checks (guard) work; if not, restore .agents/core/ from the last saved version.
5. Apply the team's brand (.agents/local/brand.json): team page colours and the folder's icon.

Standard library only. Messages are plain words for non-technical people.
"""

import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HOOKS_PATH = ".agents/core/git-hooks"
# Folders starting with a dot are already hidden on Mac; Windows needs the attribute.
HIDDEN_DIRS = [".agents", ".claude", ".codex", ".git", ".streamlit"]
# Must stay at the root with these names (agents look for them there): hide them on both systems.
HIDDEN_FILES = ["AGENTS.md", "CLAUDE.md", ".gitignore"]

SYSTEM = platform.system()


def run(*args):
    return subprocess.run(list(args), capture_output=True, text=True, check=False)


def git_hooks():
    current = run("git", "-C", str(ROOT), "config", "--get", "core.hooksPath").stdout.strip()
    if current != HOOKS_PATH:
        run("git", "-C", str(ROOT), "config", "core.hooksPath", HOOKS_PATH)
        return "Team checks turned on."
    return None


def hide_files():
    # Each system only shows its own launcher: Mac hides the Windows one (.bat) and the other way round.
    if SYSTEM == "Darwin":
        targets = [ROOT / f for f in HIDDEN_FILES] + list(ROOT.glob("*.bat"))
        for t in targets:
            if t.exists():
                run("chflags", "hidden", str(t))
    elif SYSTEM == "Windows":
        targets = [ROOT / name for name in HIDDEN_DIRS + HIDDEN_FILES] + list(ROOT.glob("*.command"))
        for t in targets:
            if t.exists():
                run("attrib", "+h", str(t))
    # Linux: names starting with a dot are hidden; AGENTS.md/CLAUDE.md stay visible.
    return None


def codex_home():
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def toml_key(path):
    """A TOML key for a path. Literal strings ('...') keep Windows backslashes as they are."""
    return f"'{path}'" if "'" not in path else '"' + path.replace("\\", "\\\\").replace('"', '\\"') + '"'


def codex_trust():
    config = codex_home() / "config.toml"
    key = toml_key(str(ROOT))
    header = f"[projects.{key}]"
    text = config.read_text(encoding="utf-8") if config.exists() else ""
    if header in text:
        return None
    config.parent.mkdir(parents=True, exist_ok=True)
    with config.open("a", encoding="utf-8") as f:
        f.write(("\n" if text and not text.endswith("\n") else "") + f'\n{header}\ntrust_level = "trusted"\n')
    return ("Codex will now apply this team's rules in this folder "
            "(the folder was marked as trusted in Codex's settings).")


def guard_ok():
    test = run(sys.executable, "-I", str(ROOT / ".agents/core/scripts/selftest.py"))
    return test.returncode == 0


def repair_guard():
    if guard_ok():
        return None
    run("git", "-C", str(ROOT), "checkout", "HEAD", "--", ".agents/core")
    if guard_ok():
        return "The team checks were broken on this computer and have been repaired."
    run("git", "-C", str(ROOT), "pull", "--ff-only", "--quiet")
    run("git", "-C", str(ROOT), "checkout", "HEAD", "--", ".agents/core")
    if guard_ok():
        return "The team checks were broken and have been repaired with the team's latest version."
    return ("The team checks are still not working. Please contact your AI Champion "
            "before using the AI in this folder.")


def page_theme(brand):
    """The team page reads .streamlit/config.toml from the folder it starts in (the team folder)."""
    lines = ["[theme]"]
    if brand.get("background") or brand.get("text"):
        lines += [f'backgroundColor = "{brand["background"]}"'] if brand.get("background") else []
        lines += [f'textColor = "{brand["text"]}"'] if brand.get("text") else []
    else:
        lines.append('base = "light"')
    lines += [f'primaryColor = "{brand["primary"]}"', f'font = "{"serif" if brand.get("font") == "serif" else "sans serif"}"']
    config = ROOT / ".streamlit/config.toml"
    text = "# Made from .agents/local/brand.json every time the team folder opens. Do not edit.\n" + "\n".join(lines) + "\n"
    if not config.exists() or config.read_text(encoding="utf-8") != text:
        config.parent.mkdir(exist_ok=True)
        config.write_text(text, encoding="utf-8")


MAC_SET_ICON = """function run(argv) {
  ObjC.import('AppKit');
  var image = $.NSImage.alloc.initWithContentsOfFile(argv[0]);
  for (var i = 1; i < argv.length; i++) $.NSWorkspace.sharedWorkspace.setIconForFileOptions(image, argv[i], 0);
}"""


def folder_icon(icon_png, icon_ico, team):
    """Give the team folder (and the Mac launcher) the company's icon. True the first time or when it changes."""
    stamp = ROOT / ".git/brand-icon"
    source = icon_ico if SYSTEM == "Windows" else icon_png
    if not source.exists():
        return False
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    unchanged = stamp.exists() and stamp.read_text().strip() == digest
    if unchanged and SYSTEM != "Darwin":
        return False
    if SYSTEM == "Darwin":  # every launch: an update replaces the launcher file and drops its icon
        targets = [str(ROOT)] + [str(p) for p in ROOT.glob("*.command")]
        if run("osascript", "-l", "JavaScript", "-e", MAC_SET_ICON, str(source), *targets).returncode != 0:
            return False
    elif SYSTEM == "Windows":
        ini = ROOT / "desktop.ini"
        if ini.exists():
            run("attrib", "-h", "-s", str(ini))
        ini.write_text("[.ShellClassInfo]\r\nIconResource=" + str(source.relative_to(ROOT)) + ",0\r\n"
                       f"InfoTip={team} AI workspace\r\n", encoding="utf-8")
        run("attrib", "+h", "+s", str(ini))
        run("attrib", "+r", str(ROOT))  # Windows only reads desktop.ini in read-only or system folders
    else:
        return False
    stamp.write_text(digest + "\n")
    return not unchanged


WINDOWS_SHORTCUT = """$s = (New-Object -ComObject WScript.Shell).CreateShortcut($env:TEAM_LNK)
$s.TargetPath = $env:TEAM_BAT
$s.WorkingDirectory = $env:TEAM_ROOT
$s.IconLocation = "$env:TEAM_ICO,0"
$s.Save()"""


def windows_shortcut(icon_ico):
    """Windows cannot give a .bat file an icon: show a shortcut with the company icon instead, and hide the .bat."""
    if SYSTEM != "Windows" or not icon_ico.exists():
        return False
    bats = sorted(ROOT.glob("*.bat"))
    if not bats:
        return False
    lnk = bats[0].with_suffix(".lnk")
    created = False
    if not lnk.exists():
        env = dict(os.environ, TEAM_LNK=str(lnk), TEAM_BAT=str(bats[0]), TEAM_ROOT=str(ROOT), TEAM_ICO=str(icon_ico))
        subprocess.run(["powershell", "-NoProfile", "-Command", WINDOWS_SHORTCUT], env=env,
                       capture_output=True, text=True, check=False)
        created = lnk.exists()
    if lnk.exists():
        run("attrib", "+h", str(bats[0]))
    return created


def apply_brand():
    try:
        brand = json.loads((ROOT / ".agents/local/brand.json").read_text(encoding="utf-8"))
        team = json.loads((ROOT / ".agents/local/team.json").read_text(encoding="utf-8")).get("team", "Team")
    except (OSError, ValueError):
        return None  # no brand yet: default look
    if not brand.get("primary"):
        return None
    page_theme(brand)
    brand_dir = ROOT / ".agents/local/brand"
    changed = folder_icon(brand_dir / "icon.png", brand_dir / "icon.ico", team)
    changed = windows_shortcut(brand_dir / "icon.ico") or changed
    if changed:
        return "The team folder now has your company's icon."
    return None


def main():
    if not (ROOT / ".git").exists():
        print("This folder is not connected to the team yet. Ask your AI Champion for help.")
        return 1
    notes = [n for n in (git_hooks(), apply_brand(), hide_files(), codex_trust(), repair_guard()) if n]
    for n in notes:
        print(f"- {n}")
    print("Your team folder is ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
