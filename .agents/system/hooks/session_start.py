#!/usr/bin/env python3
"""SessionStart hook: bring the latest team changes, then make sure the team page is running.

Fast-forward only: never merges, never rewrites, never fails the session. Unsaved work on this
computer is set aside and put back (autostash), and the person's own git settings (such as
pull.rebase) do not change how this works.
The team page is started in the background without opening the person's browser
(TEAM_PAGE_NO_BROWSER=1), and its address is printed so the AI assistant opens it in its own
built-in browser. If this folder's page is already running, it is left as it is.
Standard library only.
"""

import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PORT_FILE = ROOT / ".git/team-page-port"
PAGE = ROOT / ".agents/system/facade/page.py"
PAGE_LOG = ROOT / ".git/team-page.log"
STREAMLIT = "streamlit==1.41.1"


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, timeout=60)


def main():
    try:
        update()
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        open_team_page()
    except (OSError, subprocess.SubprocessError):
        pass
    return 0


def update():
    if git("rev-parse", "--abbrev-ref", "@{upstream}").returncode != 0:
        return  # no remote branch yet
    git("fetch", "--quiet")
    result = git("merge", "--ff-only", "--autostash", "--quiet", "@{upstream}")
    if result.returncode == 0:
        print("Team workspace is up to date.")
    else:
        print("Could not update the team workspace automatically; continuing with the local copy.")


def page_ready():
    """Address of this folder's team page if it is answering, else None."""
    try:
        port = int(PORT_FILE.read_text().strip())
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=1):
            return f"http://127.0.0.1:{port}"
    except (OSError, ValueError):
        return None


def find_uv():
    found = shutil.which("uv")
    if found:
        return found
    for folder in (Path.home() / ".local/bin", Path.home() / ".cargo/bin"):
        local = folder / ("uv.exe" if os.name == "nt" else "uv")
        if local.exists():
            return str(local)
    return None


def needs_setup():
    """This computer has not been prepared yet (no uv, or the team's git checks are off)."""
    hooks = git("config", "--get", "core.hooksPath").stdout.strip()
    return not find_uv() or hooks != ".agents/system/git-hooks"


def open_team_page(seconds=15):  # short: the session waits for this, and Windows starts slower
    if os.environ.get("CLAUDE_CODE_REMOTE") or os.environ.get("CI"):
        return  # cloud sessions have no team page
    if needs_setup():
        print("This computer is not set up for the team folder yet. Set it up yourself now, without asking "
              "the person and without asking them to open the launcher: run `sh .agents/system/bin/setup` "
              "in Bash (on Windows: Git Bash, not PowerShell) with a 10-minute timeout, because the first run "
              "takes 2 to 4 minutes on Windows (it never asks anything). Then start the team page "
              "in the background with `sh .agents/system/bin/team-page` and open the address it prints in "
              "your built-in browser. Tell the person in one plain line that you are preparing their computer.")
        return
    url = page_ready()
    if not url:
        uv = find_uv()
        if not uv:
            return  # the launcher has not run on this computer yet
        detach = ({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS}
                  if os.name == "nt" else {"start_new_session": True})
        with open(PAGE_LOG, "w") as log:
            subprocess.Popen([uv, "run", "--quiet", "--no-project", "--python", "3.12", "--with", STREAMLIT, str(PAGE)],
                             cwd=ROOT, env=dict(os.environ, TEAM_PAGE_NO_BROWSER="1"),
                             stdin=subprocess.DEVNULL, stdout=log, stderr=log, **detach)
        deadline = time.time() + seconds
        while not url and time.time() < deadline:
            time.sleep(0.5)
            url = page_ready()
    if url:
        print(f"The team page is running at {url}. If you have a built-in browser, open this address "
              "in it now, without asking and without opening the person's own browser.")
    elif find_uv():
        print("The team page is still starting (slower the first time, especially on Windows). Its address "
              f"will be in {PORT_FILE.relative_to(ROOT).as_posix()} as http://127.0.0.1:<port>; open it in "
              "your built-in browser once the person needs it. Do not wait for it now.")


if __name__ == "__main__":
    sys.exit(main())
