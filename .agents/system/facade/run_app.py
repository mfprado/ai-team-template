"""Start a team Streamlit app (an artifact folder with app.py) and open it in the browser.

Used by the artifact's own launcher (Open.command / Open.bat, or Abrir.*) and by the team page's
Open button, both through uv with Streamlit:

  uv run --no-project --python 3.12 --with streamlit==1.41.1 [--with-requirements requirements.txt] \
      .agents/system/facade/run_app.py <artifact folder>

It runs from the team folder, so the app gets the team's theme (.streamlit/config.toml). An app
that is already running is only opened again in the browser. Keeps running until the app stops.

With --no-browser (the team page, which shows the app inside itself) nothing opens in the browser.
"""

import json
import os
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


def alive(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    args = [a for a in sys.argv[1:] if a != "--no-browser"]
    browser = "--no-browser" not in sys.argv[1:]
    folder = Path(args[0]).resolve()
    app = folder / "app.py"
    if not app.is_file():
        print(f"There is no app.py in {folder}.")
        return 1
    root = next((p for p in folder.parents if (p / ".agents").is_dir()), None)
    if root is None:
        print("This app is not inside a team folder.")
        return 1
    state_file = root / ".git/apps.json"
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    key = str(folder.relative_to(root))
    port = state.get(key)
    if port and alive(port):
        if browser:
            webbrowser.open(f"http://localhost:{port}")
        print(f"The app is already open: http://localhost:{port}")
        return 0

    port = free_port()
    state[key] = port
    try:
        state_file.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass
    # The app shows a link back to the team page (look.css), at this team's own address (page.py).
    env = dict(os.environ)
    try:
        env["TEAM_PAGE_URL"] = f"http://localhost:{int((root / '.git/team-page-port').read_text().strip())}"
    except (OSError, ValueError):
        env.pop("TEAM_PAGE_URL", None)
    if not browser:  # shown inside the team page: no link back to it
        env.pop("TEAM_PAGE_URL", None)
    process = subprocess.Popen([sys.executable, "-m", "streamlit", "run", str(app), "--server.port", str(port),
                                "--server.headless", "true", "--browser.gatherUsageStats", "false"], cwd=root, env=env)
    for _ in range(120):  # up to a minute for the first start
        if alive(port) or process.poll() is not None:
            break
        time.sleep(0.5)
    if process.poll() is not None:
        print("The app could not start. Ask the assistant to look at it.")
        return 1
    if browser:
        webbrowser.open(f"http://localhost:{port}")
    print(f"The app is open in your browser: http://localhost:{port}")
    print("Keep this window open while you use it.")
    return process.wait()


if __name__ == "__main__":
    sys.exit(main())
