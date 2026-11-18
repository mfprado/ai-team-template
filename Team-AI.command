#!/bin/bash
# Team launcher for Mac: double-click to open the team folder.
# Installs what is needed the first time, then prepares this computer.
cd "$(dirname "$0")" || exit 1
# Everything this window shows also goes to .git/launch.log (hidden, never shared), so the assistant can read it
# instead of asking the person to copy the window.
LOG=".git/launch.log"
: > "$LOG"
exec > >(tee -a "$LOG") 2>&1
echo "Opening your team folder... ($(date '+%Y-%m-%d %H:%M'), Mac)"

finish() { echo; read -r -p "Press Enter to close this window." _; exit "$1"; }

# Git: comes with Apple's developer tools.
if ! git --version >/dev/null 2>&1; then
  echo "Your computer needs Apple's developer tools (they include git, used to keep the team folder in sync)."
  read -r -p "Install them now? [y/n] " answer
  if [[ "$answer" =~ ^[yYsS] ]]; then
    xcode-select --install
    echo "Follow the installation window. When it finishes, open this file again."
  fi
  finish 1
fi

# uv: installs and runs the right Python. Installed automatically the first time.
export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  echo "Installing the tools your team folder needs (one time only)..."
  if ! curl -LsSf https://astral.sh/uv/install.sh | sh >>"$LOG" 2>&1; then
    echo "The installation failed. Check your internet connection and try again, or ask your AI Champion."
    finish 1
  fi
fi
uv python install 3.12 --quiet >>"$LOG" 2>&1

uv run --quiet --no-project --python 3.12 .agents/core/facade/setup.py || finish 1
echo "Setup finished."

# GitHub's tool: lets the assistant share changes with the team.
if ! command -v gh >/dev/null 2>&1; then
  echo "Your computer needs GitHub's tool to share your changes with the team."
  read -r -p "Install it now? [y/n] " answer
  if [[ "$answer" =~ ^[yYsS] ]]; then
    if command -v brew >/dev/null 2>&1; then
      brew install gh
    else
      uv run --quiet --no-project --python 3.12 .agents/core/facade/install_gh.py
    fi
  fi
fi
if command -v gh >/dev/null 2>&1; then
  if ! gh auth status --hostname github.com >/dev/null 2>&1; then
    echo "Now sign in to GitHub in the browser window that opens (one time only)."
    gh auth login --hostname github.com --git-protocol https --web
  fi
  gh auth setup-git --hostname github.com >/dev/null 2>&1
fi

# The team page: opens in the browser. Keep this window open while you use it.
PORT=8501
uv run --quiet --no-project --python 3.12 --with streamlit==1.41.1 \
  streamlit run .agents/core/facade/app.py --server.headless true --server.port "$PORT" \
  --server.address 127.0.0.1 --browser.gatherUsageStats false --client.toolbarMode viewer >/dev/null 2>&1 &
APP=$!
for _ in $(seq 1 60); do
  curl -s "http://127.0.0.1:$PORT/_stcore/health" >/dev/null 2>&1 && break
  sleep 1
done
open "http://127.0.0.1:$PORT"
echo "The team page is open in your browser. Close this window when you are done."
echo "Launcher finished."
wait $APP
