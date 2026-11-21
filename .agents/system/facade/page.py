#!/usr/bin/env python3
"""Start this team folder's page (the launcher's last step), one per team folder.

A person can be in several teams, so each team folder gets its own address:
- First, stop this folder's page if one was left running (only this folder's, never another team's).
- Then use the address this folder used before (kept in .git/team-page-port), or the first free
  one from 8501, so each team keeps the same address while the others are open too.
- Open it in the browser and keep running until the window is closed.

Run by the launchers with streamlit available (uv run --with streamlit ...).
Standard library only otherwise.
"""

import os
import platform
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = Path(__file__).resolve().parent / "app.py"
PORT_FILE = ROOT / ".git/team-page-port"
FIRST_PORT, LAST_PORT = 8501, 8599
WINDOWS = platform.system() == "Windows"


def own_pages():
    """Process ids of team pages started from THIS folder (their command line names this app.py)."""
    me = os.getpid()
    if WINDOWS:
        script = ("Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like ('*' + $env:TEAM_APP + '*') "
                  "-and $_.CommandLine -like '*streamlit*' } | ForEach-Object { $_.ProcessId }")
        out = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True,
                             env=dict(os.environ, TEAM_APP=str(APP)), check=False).stdout
    else:
        out = subprocess.run(["pgrep", "-f", f"streamlit.*{APP}"], capture_output=True, text=True, check=False).stdout
        out += " " + " ".join(older_pages())
    return [int(p) for p in set(out.split()) if p.isdigit() and int(p) != me]


def older_pages():
    """Pages started by older launchers name app.py by a short path: keep those running in this folder."""
    out = subprocess.run(["pgrep", "-f", "streamlit run .agents/system/facade/app.py"], capture_output=True,
                         text=True, check=False).stdout
    found = []
    for pid in out.split():
        cwd = subprocess.run(["lsof", "-a", "-p", pid, "-d", "cwd", "-Fn"], capture_output=True,
                             text=True, check=False).stdout
        if any(line[1:] == str(ROOT) for line in cwd.splitlines() if line.startswith("n")):
            found.append(pid)
    return found


def stop(pids):
    for pid in pids:
        if WINDOWS:
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, check=False)
        else:
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass
    deadline = time.time() + 5
    while pids and time.time() < deadline and own_pages():
        time.sleep(0.2)


def free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if not WINDOWS:  # like the page itself: a just-closed page's address counts as free
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def pick_port(just_stopped):
    try:
        preferred = int(PORT_FILE.read_text().strip())
    except (OSError, ValueError):
        preferred = None
    # This team's own page was just closed: give its address a moment to be released.
    for _ in range(20 if preferred and just_stopped else 0):
        if free(preferred):
            break
        time.sleep(0.25)
    for port in ([preferred] if preferred else []) + list(range(FIRST_PORT, LAST_PORT + 1)):
        if free(port):
            PORT_FILE.write_text(f"{port}\n")
            return port
    return None


def wait_until_ready(port, seconds=60):
    url = f"http://127.0.0.1:{port}/_stcore/health"
    for _ in range(seconds * 2):
        try:
            with urllib.request.urlopen(url, timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False


def main():
    left = own_pages()
    if left:
        print("Closing this team's page that was still open from before...")
        stop(left)
    port = pick_port(bool(left))
    if port is None:
        print("The team page could not start: too many pages are open. Restart the computer and try again.")
        return 1
    page = subprocess.Popen([sys.executable, "-m", "streamlit", "run", str(APP),
                             "--server.headless", "true", "--server.port", str(port), "--server.address", "127.0.0.1",
                             "--browser.gatherUsageStats", "false", "--client.toolbarMode", "viewer"],
                            cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not wait_until_ready(port):
        page.terminate()
        print("The team page did not start. Close this window and open the team folder again.")
        return 1
    url = f"http://127.0.0.1:{port}"
    webbrowser.open(url)
    print(f"The team page is open in your browser ({url}). Close this window when you are done.")
    try:
        return page.wait()
    except KeyboardInterrupt:
        page.terminate()
        return 0


if __name__ == "__main__":
    sys.exit(main())
