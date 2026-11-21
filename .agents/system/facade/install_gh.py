#!/usr/bin/env python3
"""Install GitHub's command-line tool (gh) on a Mac without Homebrew and without admin rights.

Downloads the latest official release from github.com/cli/cli, checks it against the
release's published SHA-256 checksums, and puts `gh` in ~/.local/bin (already on the
launcher's PATH). The launcher only calls this after the person agreed.

Standard library only.
"""

import hashlib
import io
import json
import os
import platform
import stat
import sys
import urllib.request
import zipfile
from pathlib import Path

API = "https://api.github.com/repos/cli/cli/releases/latest"
DEST = Path.home() / ".local" / "bin" / "gh"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "team-launcher", "Accept": "application/octet-stream"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def main():
    if platform.system() != "Darwin":
        print("This installer is only for Mac.")
        return 1
    release = json.loads(fetch(API))
    assets = {a["name"]: a["browser_download_url"] for a in release.get("assets", [])}
    arch = "arm64" if platform.machine() in ("arm64", "aarch64") else "amd64"
    candidates = [n for n in assets if n.endswith(".zip") and "macOS" in n and (arch in n or "universal" in n)]
    checksums = next((n for n in assets if n.endswith("checksums.txt")), None)
    if not candidates or not checksums:
        print("Could not find GitHub's tool for this Mac.")
        return 1
    name = sorted(candidates, key=lambda n: "universal" in n)[0]  # prefer the exact architecture

    expected = {}
    for line in fetch(assets[checksums]).decode().splitlines():
        parts = line.split()
        if len(parts) == 2:
            expected[parts[1]] = parts[0]
    data = fetch(assets[name])
    if hashlib.sha256(data).hexdigest() != expected.get(name):
        print("The download did not pass the safety check, so it was not installed.")
        return 1

    with zipfile.ZipFile(io.BytesIO(data)) as z:
        member = next((m for m in z.namelist() if m.endswith("/bin/gh")), None)
        if not member:
            print("Unexpected download contents; nothing was installed.")
            return 1
        DEST.parent.mkdir(parents=True, exist_ok=True)
        DEST.write_bytes(z.read(member))
    DEST.chmod(DEST.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"GitHub's tool is installed ({release.get('tag_name', 'latest')}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
