#!/usr/bin/env python3
"""Find the logo of a tool, for the tool shapes in a skill's flow diagram.

Usage:
  sh .agents/system/bin/py .agents/system/scripts/find_logo.py "Google Sheets" ["Gmail" ...]

Prints one JSON line per tool: {"tool": ..., "icon": "<set>:<name>"} or "icon": null when
no colour logo was found (draw the tool without a logo then). Searches Iconify
(api.iconify.design) and prefers full-colour brand logos over one-colour symbols, and a
brand's symbol over its wordmark.
Standard library only.
"""

import json
import re
import sys
import urllib.parse
import urllib.request

API = "https://api.iconify.design"
# Full-colour logo collections, best first. One-colour sets are never used: they look like
# generic symbols, not the tool people recognise.
COLOUR_SETS = ["logos", "devicon", "skill-icons", "thesvg-color", "selfhst", "vscode-icons"]
SKIP = re.compile(r"-(dark|light|outline|wordmark|line|20\d\d)$")


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def search(query):
    url = f"{API}/search?" + urllib.parse.urlencode({"query": query, "limit": 999})
    request = urllib.request.Request(url, headers={"User-Agent": "team-skill-logo-finder"})
    with urllib.request.urlopen(request, timeout=15) as r:
        return json.load(r).get("icons", [])


def best(tool):
    """The closest full-colour logo: exact name first, then names that contain the tool."""
    wanted = slug(tool)
    variants = {wanted, wanted.replace("microsoft-", "ms-"), wanted.replace("google-", "")}
    found = [i for i in search(tool) if i.split(":")[0] in COLOUR_SETS and not SKIP.search(i)]

    def rank(icon):
        prefix, name = icon.split(":", 1)
        base = re.sub(r"^(file-type-)", "", re.sub(r"-icon$", "", name))
        closeness = 0 if base in variants else 1 if any(v in base for v in variants) else 2
        # Prefer the symbol ("github-icon") over the wordmark: it reads at badge size.
        return (closeness, COLOUR_SETS.index(prefix), not name.endswith("-icon"), len(name))

    found = sorted((i for i in found if rank(i)[0] < 2), key=rank)
    if not found:
        return None
    # The search does not always list a brand's symbol: ask for it directly.
    prefix, name = found[0].split(":", 1)
    if not name.endswith("-icon") and exists(prefix, name + "-icon"):
        return f"{prefix}:{name}-icon"
    return found[0]


def exists(prefix, name):
    url = f"{API}/{prefix}.json?" + urllib.parse.urlencode({"icons": name})
    request = urllib.request.Request(url, headers={"User-Agent": "team-skill-logo-finder"})
    with urllib.request.urlopen(request, timeout=15) as r:
        return name in json.load(r).get("icons", {})


def main(tools):
    if not tools:
        print(__doc__.strip())
        return 2
    for tool in tools:
        try:
            print(json.dumps({"tool": tool, "icon": best(tool)}))
        except OSError as exc:
            print(json.dumps({"tool": tool, "icon": None, "error": f"Could not reach the logo search ({exc})."}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
